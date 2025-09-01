// Copyright 2024 The Go Authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

//go:build !wasm

package main

import (
	"bytes"
	"context"
	"errors"
	"flag"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"sync"
	"syscall"
	"time"

	"golang.org/x/benchmarks/sweet/common/diagnostics"
)

const (
	basePort      = 26257
	cacheSize     = "0.25"
	defaultMaxOps = 1000000
)

type config struct {
	host           string
	cockroachdbBin string
	tmpDir         string
	short          bool
	procsPerInst   int
	maxOps         int
	readPercent    int
}

var cliCfg config

func init() {
	flag.StringVar(&cliCfg.host, "host", "localhost", "hostname of cockroachdb server")
	flag.StringVar(&cliCfg.cockroachdbBin, "cockroachdb-bin", "./bin/cockroach", "path to cockroachdb binary")
	flag.StringVar(&cliCfg.tmpDir, "tmp", "", "path to temporary directory")
	flag.BoolVar(&cliCfg.short, "short", false, "whether to run a short version of this benchmark")
	flag.IntVar(&cliCfg.maxOps, "max-ops", 0, "maximum number of operations to run (default 1000000)")
	flag.IntVar(&cliCfg.readPercent, "kv", 0, "kv read percentage to run (0,50,95)")
	flag.IntVar(&cliCfg.procsPerInst, "threads", 0, "number of threads (GOMAXPROCS) for CockroachDB instance")
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
		return nil, fmt.Errorf("failed to start instance %q: %v", inst.name, err)
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
	endpoint := fmt.Sprintf("http://%s:%d/%s", cliCfg.host, i.httpPort, diagnostics.MemProfile.HTTPEndpoint())
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
		"--min-block-bytes=1024",
		"--max-block-bytes=1024",
		"--concurrency=5000",
		"--scatter",
		"--splits=5",
	}
}

func runBenchmarkStandalone(cfg *config, instances []*cockroachdbInstance) error {
	if cfg.maxOps == 0 {
		cfg.maxOps = defaultMaxOps
	}

	var pgurls []string
	for _, inst := range instances {
		pgurls = append(pgurls, fmt.Sprintf("postgres://root@%s?sslmode=disable", inst.sqlAddr()))
	}

	// Init workload
	initArgs := append([]string{"workload", "init", "kv"}, pgurls...)
	initCmd := exec.Command(cfg.cockroachdbBin, initArgs...)
	if err := initCmd.Run(); err != nil {
		return err
	}

	// Run workload
	args := kvBenchmark(cfg.readPercent)
	args = append(args, fmt.Sprintf("--max-ops=%d", cfg.maxOps))
	args = append(args, pgurls...)

	cmd := exec.Command(cfg.cockroachdbBin, args...)
	cmd.Env = append(os.Environ(), fmt.Sprintf("GOMAXPROCS=%d", cfg.procsPerInst))

	start := time.Now()
	if err := cmd.Run(); err != nil {
		return err
	}
	elapsed := time.Since(start)

	fmt.Printf("Benchmark kv%d finished in %s (max-ops=%d, threads=%d)\n", cfg.readPercent, elapsed, cfg.maxOps, cfg.procsPerInst)
	return nil
}

func run(cfg *config) error {
	log.Println("launching cluster")
	instances, err := launchSingleNodeCluster(cfg)
	if err != nil {
		return err
	}
	defer func() {
		log.Println("shutting down cluster")
		for _, inst := range instances {
			inst.shutdown()
		}
	}()

	log.Println("waiting for cluster")
	if err = waitForCluster(instances); err != nil {
		return err
	}

	log.Println("running benchmark")
	return runBenchmarkStandalone(cfg, instances)
}

func runMain() error {
	flag.Parse()
	if flag.NArg() != 0 {
		return fmt.Errorf("unexpected args")
	}

	if cliCfg.readPercent != 0 && cliCfg.readPercent != 50 && cliCfg.readPercent != 95 {
		return fmt.Errorf("-kv must be 0, 50, or 95")
	}

	if cliCfg.cockroachdbBin == "" {
		envBin := os.Getenv("COCKROACH_BIN")
		if envBin != "" {
			if fi, err := os.Stat(envBin); err == nil && fi.Mode().IsRegular() && (fi.Mode().Perm()&0111) != 0 {
				cliCfg.cockroachdbBin = envBin
				fmt.Printf("Using CockroachDB binary from COCKROACH_BIN: %s\n", envBin)
			} else {
				return fmt.Errorf("COCKROACH_BIN is set but not executable: %s", envBin)
			}
		}
	}

	if cliCfg.cockroachdbBin == "" {
		return fmt.Errorf("CockroachDB binary not specified. Use --cockroachdb-bin or set COCKROACH_BIN")
	}

	if cliCfg.procsPerInst <= 0 {
		cliCfg.procsPerInst = runtime.GOMAXPROCS(-1)
		if cliCfg.procsPerInst == 0 {
			cliCfg.procsPerInst = 1
		}
	}
	runtime.GOMAXPROCS(cliCfg.procsPerInst)

	return run(&cliCfg)
}

func main() {
	if err := runMain(); err != nil {
		fmt.Fprintf(os.Stderr, "error: %v\n", err)
	}
}
