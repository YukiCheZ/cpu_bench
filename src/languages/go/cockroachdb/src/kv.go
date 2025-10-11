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
	basePort	= 26257
	cacheSize	= "0.25"
	seed		= 42
)

type config struct {
	host			string
	cockroachdbBin 	string
	tmpDir			string
	procsPerInst	int
	maxOps			int
	readPercent		int
}

var cliCfg config

func init() {
	flag.StringVar(&cliCfg.host, "host", "localhost", "hostname of cockroachdb server")
	flag.StringVar(&cliCfg.cockroachdbBin, "cockroachdb-bin", "./bin/cockroach", "path to cockroachdb binary")
	flag.StringVar(&cliCfg.tmpDir, "tmp", "", "path to temporary directory")
	flag.IntVar(&cliCfg.maxOps, "max-ops", 2000000, "Maximum number of operations to run PER CORE")
	flag.IntVar(&cliCfg.readPercent, "kv", 50, "KV read percentage to run (0,50,95)")
	flag.IntVar(&cliCfg.procsPerInst, "threads", 0, "Number of threads (GOMAXPROCS) for CockroachDB instance")
}

type cockroachdbInstance struct {
	name		string
	sqlPort		int
	httpPort	int
	cmd			*exec.Cmd
	output		bytes.Buffer
	tmpStore	string
	tmpLog		string
}

func (i *cockroachdbInstance) sqlAddr() string { return fmt.Sprintf("%s:%d", cliCfg.host, i.sqlPort) }
func (i *cockroachdbInstance) httpAddr() string { return fmt.Sprintf("%s:%d", cliCfg.host, i.httpPort) }

func launchSingleNodeCluster(cfg *config) ([]*cockroachdbInstance, error) {
	inst := &cockroachdbInstance{
		name:		"roach-node",
		sqlPort:	basePort,
		httpPort:	basePort + 1,
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
		return errors.New("timeout waiting for cluster")
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

func kvBenchmark(readPercent int) []string {
	return []string{
		"workload", "run", "kv",
		fmt.Sprintf("--read-percent=%d", readPercent),
		"--min-block-bytes=128",
		"--max-block-bytes=128",
		"--concurrency=2000",
		"--ramp=10s",
		"--scatter",
		"--splits=5",
		fmt.Sprintf("--seed=%d", seed),
	}
}

func runBenchmarkStandalone(cfg *config, instances []*cockroachdbInstance) error {

	var pgurls []string
	for _, inst := range instances {
		pgurls = append(pgurls, fmt.Sprintf("postgres://root@%s?sslmode=disable", inst.sqlAddr()))
	}

	// Init workload
	initArgs := append([]string{"workload", "init", "kv"}, pgurls...)
	initCmd := exec.Command(cfg.cockroachdbBin, initArgs...)
	fmt.Printf("[INFO] initializing kv ...\n")
	if err := initCmd.Run(); err != nil {
		return err
	}

	actualMaxOps := cfg.maxOps * cfg.procsPerInst
	fmt.Printf("[INFO] running kv workload with GOMAXPROCS=%d, actual-max-ops=%d (base-per-core=%d)\n",
		cfg.procsPerInst, actualMaxOps, cfg.maxOps)

	// Run workload
	args := kvBenchmark(cfg.readPercent)
	args = append(args, fmt.Sprintf("--max-ops=%d", actualMaxOps)) 
	args = append(args, pgurls...)

	cmd := exec.Command(cfg.cockroachdbBin, args...)
	cmd.Env = append(os.Environ(), fmt.Sprintf("GOMAXPROCS=%d", cfg.procsPerInst))

	start := time.Now()
	if err := cmd.Run(); err != nil {
		return err
	}
	elapsed := time.Since(start)
	fmt.Printf("[RESULT] total elapsed time: %.4f s\n", elapsed.Seconds())
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

	fmt.Println("[INFO] running benchmark")
	return runBenchmarkStandalone(cfg, instances)
}

func runMain() error {
	flag.Parse()
	if flag.NArg() != 0 {
		return fmt.Errorf("[ERROR] unexpected args")
	}

	if cliCfg.readPercent != 0 && cliCfg.readPercent != 50 && cliCfg.readPercent != 95 {
		return fmt.Errorf("[ERROR] -kv must be 0, 50, or 95")
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

	return run(&cliCfg)
}

func main() {
	if err := runMain(); err != nil {
		fmt.Fprintf(os.Stderr, "error: %v\n", err)
	}
}