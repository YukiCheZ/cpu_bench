package main

import (
	"bytes"
	"context"
	"errors"
	"flag"
	"fmt"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"sync"
	"syscall"
	"time"
)

const (
	basePort  = 26257
	cacheSize = "0.5"
	seed      = 42
)

type config struct {
	host           string
	cockroachdbBin string
	tmpDir         string
	procsPerInst   int
	maxOps         int
	// tpcc specific
	warehouses  int
	concurrency int
}

var cliCfg config

func init() {
	flag.StringVar(&cliCfg.host, "host", "localhost", "hostname of cockroachdb server")
	flag.StringVar(&cliCfg.cockroachdbBin, "cockroachdb-bin", "./bin/cockroach", "path to cockroachdb binary")
	flag.StringVar(&cliCfg.tmpDir, "tmp", "", "path to temporary directory")
	flag.IntVar(&cliCfg.maxOps, "max-ops", 40000, "maximum number of operations to run per thread")
	flag.IntVar(&cliCfg.warehouses, "warehouses", 1, "number of warehouses for TPCC data per thread (larger -> more data)")
	flag.IntVar(&cliCfg.concurrency, "concurrency", 200, "Number of concurrent workers (concurrency param passed to tpcc)")
	flag.IntVar(&cliCfg.procsPerInst, "threads", 1, "number of threads (GOMAXPROCS) for CockroachDB instance")
}

type cockroachdbInstance struct {
	name     string
	sqlPort  int
	httpPort int
	cmd      *exec.Cmd
	output   bytes.Buffer
	tmpStore string
	tmpLog   string
}

func (i *cockroachdbInstance) sqlAddr() string  { return fmt.Sprintf("%s:%d", cliCfg.host, i.sqlPort) }
func (i *cockroachdbInstance) httpAddr() string { return fmt.Sprintf("%s:%d", cliCfg.host, i.httpPort) }

func launchSingleNodeCluster(cfg *config) ([]*cockroachdbInstance, error) {
	inst := &cockroachdbInstance{
		name:     "roach-node",
		sqlPort:  basePort,
		httpPort: basePort + 1,
	}

	inst.tmpStore = filepath.Join(os.TempDir(), inst.name)
	inst.tmpLog = filepath.Join(os.TempDir(), inst.name+"-log")
	os.MkdirAll(inst.tmpStore, 0755)
	os.MkdirAll(inst.tmpLog, 0755)

	if cfg.procsPerInst <= 0 {
		cfg.procsPerInst = runtime.GOMAXPROCS(-1)
		if cfg.procsPerInst == 0 {
			cfg.procsPerInst = 1
		}
	}

	inst.cmd = exec.Command(cfg.cockroachdbBin,
		"start-single-node",
		"--insecure",
		"--listen-addr", inst.sqlAddr(),
		"--http-addr", inst.httpAddr(),
		"--cache", cacheSize,
		"--store", inst.tmpStore,
		"--log-dir", inst.tmpLog,
	)
	inst.cmd.Env = append(os.Environ(), fmt.Sprintf("GOMAXPROCS=%d", cfg.procsPerInst))
	inst.cmd.Stdout = &inst.output
	inst.cmd.Stderr = &inst.output
	if err := inst.cmd.Start(); err != nil {
		return nil, fmt.Errorf("[ERROR] failed to start instance %q: %v", inst.name, err)
	}
	return []*cockroachdbInstance{inst}, nil
}

func waitForCluster(instances []*cockroachdbInstance) error {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	var wg sync.WaitGroup
	for _, inst := range instances {
		inst := inst
		wg.Add(1)
		go func() {
			defer wg.Done()
			for {
				select {
				case <-ctx.Done():
					return
				case <-time.After(2 * time.Second):
					if err := inst.ping(); err == nil {
						return
					}
				}
			}
		}()
	}

	done := make(chan struct{})
	go func() { wg.Wait(); done <- struct{}{} }()

	select {
	case <-done:
	case <-time.After(60 * time.Second):
		return errors.New("[ERROR] timeout waiting for cluster")
	}
	return nil
}

func (i *cockroachdbInstance) ping() error {
	cmd := exec.Command(cliCfg.cockroachdbBin, "node", "status", "--insecure",
		fmt.Sprintf("--host=%s", cliCfg.host),
		fmt.Sprintf("--port=%d", i.sqlPort))
	cmd.Stdout = &i.output
	cmd.Stderr = &i.output
	if err := cmd.Run(); err != nil {
		return err
	}
	endpoint := fmt.Sprintf("http://%s:%d/debug/pprof/heap", cliCfg.host, i.httpPort)
	resp, err := http.Get(endpoint)
	if err != nil {
		return err
	}
	resp.Body.Close()
	return nil
}

func (i *cockroachdbInstance) shutdown() (killed bool, err error) {
	if i.cmd == nil || i.cmd.Process == nil {
		return false, nil
	}
	if err := i.cmd.Process.Signal(syscall.SIGTERM); err != nil {
		return false, err
	}
	done := make(chan struct{})
	go func() { i.cmd.Wait(); done <- struct{}{} }()
	select {
	case <-done:
	case <-time.After(1 * time.Minute):
		if err := i.cmd.Process.Signal(syscall.SIGKILL); err != nil {
			return true, err
		}
		<-done
		killed = true
	}
	os.RemoveAll(i.tmpStore)
	os.RemoveAll(i.tmpLog)
	return killed, nil
}

// build tpcc run args oriented for CPU benchmarking
func tpccBenchmarkArgs(cfg *config, actualWarehouses int) []string {
	args := []string{
		"workload", "run", "tpcc",
		fmt.Sprintf("--warehouses=%d", actualWarehouses), // Use the scaled value
		fmt.Sprintf("--concurrency=%d", cfg.concurrency),
		"--wait=0",
		"--method=cache_statement",
		"--ramp=10s",
		"--split",
		"--scatter",
		fmt.Sprintf("--seed=%d", seed),
	}

	return args
}

func runBenchmarkStandalone(cfg *config, instances []*cockroachdbInstance) error {
	var pgurls []string
	for _, inst := range instances {
		pgurls = append(pgurls, fmt.Sprintf("postgres://root@%s?sslmode=disable", inst.sqlAddr()))
	}
	
	// ===================== MODIFICATION START =====================
	// Scale warehouses by the number of threads
	actualWarehouses := cfg.warehouses * cfg.procsPerInst
	// ===================== MODIFICATION END =======================

	// Init workload: create TPCC data with scaled warehouses
	initArgs := []string{"workload", "init", "tpcc", fmt.Sprintf("--warehouses=%d", actualWarehouses), fmt.Sprintf("--seed=%d", seed)}
	initArgs = append(initArgs, pgurls...)
	initCmd := exec.Command(cfg.cockroachdbBin, initArgs...)
	initCmd.Env = append(os.Environ(), fmt.Sprintf("GOMAXPROCS=%d", runtime.NumCPU()))
	var initErrBuf bytes.Buffer
	initCmd.Stderr = &initErrBuf
	fmt.Printf("[INFO] initializing tpcc with actual-warehouses=%d (base=%d * threads=%d)...\n",
		actualWarehouses, cfg.warehouses, cfg.procsPerInst)
	if err := initCmd.Run(); err != nil {
		return fmt.Errorf("[ERROR] tpcc init failed: %v, stderr: %s", err, initErrBuf.String())
	}

	// Run workload
	// ===================== MODIFICATION START =====================
	actualMaxOps := cfg.maxOps * cfg.procsPerInst // Scale max-ops by the number of threads

	// Pass the scaled warehouse count to the benchmark arguments as well
	args := tpccBenchmarkArgs(cfg, actualWarehouses)
	if actualMaxOps > 0 {
		args = append(args, fmt.Sprintf("--max-ops=%d", actualMaxOps))
	}
	args = append(args, pgurls...)

	fmt.Printf("[INFO] running tpcc workload (threads=%d concurrency=%d actual-warehouses=%d actual-max-ops=%d)\n",
		cfg.procsPerInst, cfg.concurrency, actualWarehouses, actualMaxOps)
	// ===================== MODIFICATION END =======================

	cmd := exec.Command(cfg.cockroachdbBin, args...)
	cmd.Env = append(os.Environ(), fmt.Sprintf("GOMAXPROCS=%d", runtime.NumCPU()))
	var runErrBuf bytes.Buffer
	cmd.Stderr = &runErrBuf
	fmt.Println("[INFO] running benchmark")
	start := time.Now()
	if err := cmd.Run(); err != nil {
		return fmt.Errorf("[ERROR] tpcc run failed: %v, stderr: %s", err, runErrBuf.String())
	}
	elapsed := time.Since(start)
	fmt.Printf("[RESULT] Total elapsed time: %.4f s\n", elapsed.Seconds())
	return nil
}

func run(cfg *config) error {
	fmt.Println("[INFO] launching cluster")
	instances, err := launchSingleNodeCluster(cfg)
	if err != nil {
		return err
	}
	defer func() {
		fmt.Println("[INFO] shutting down cluster")
		for _, inst := range instances {
			inst.shutdown()
		}
	}()

	fmt.Println("[INFO] waiting for cluster")
	if err = waitForCluster(instances); err != nil {
		return err
	}

	return runBenchmarkStandalone(cfg, instances)
}

func runMain() error {
	flag.Parse()
	if flag.NArg() != 0 {
		return fmt.Errorf("[ERROR] unexpected args")
	}

	if cliCfg.cockroachdbBin == "" {
		envBin := os.Getenv("COCKROACH_BIN")
		if envBin != "" {
			if fi, err := os.Stat(envBin); err == nil && fi.Mode().IsRegular() && (fi.Mode().Perm()&0111) != 0 {
				cliCfg.cockroachdbBin = envBin
				fmt.Printf("[INFO] Using CockroachDB binary from COCKROACH_BIN: %s\n", envBin)
			} else {
				return fmt.Errorf("[ERROR] COCKROACH_BIN is set but not executable: %s", envBin)
			}
		}
	}

	if cliCfg.cockroachdbBin == "" {
		return fmt.Errorf("[ERROR] CockroachDB binary not specified. Use --cockroachdb-bin or set COCKROACH_BIN")
	}
	
	// No need to set GOMAXPROCS for the main test runner process itself,
	// as it mainly just waits for subprocesses.
	// The GOMAXPROCS for cockroachdb and the workload runner are set via cmd.Env.

	return run(&cliCfg)
}

func main() {
	if err := runMain(); err != nil {
		fmt.Fprintf(os.Stderr, "error: %v\n", err)
		os.Exit(1)
	}
}