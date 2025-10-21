package main

import (
	"flag"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"time"
)

var (
	esbuildBin string
	esbuildSrc string
	benchName  string
	threads    int
	iters      int
)

func init() {
	flag.StringVar(&esbuildBin, "bin", "./bin/esbuild", "path to esbuild binary (default from ESBUILD_BIN env)")
	flag.StringVar(&esbuildSrc, "src", "./data/demo_js", "path to JS/TS to pack")
	flag.StringVar(&benchName, "bench", "ThreeJS", "benchmark name (ThreeJS or RomeTS)")
	flag.IntVar(&threads, "threads", 1, "number of threads to use (GOMAXPROCS for esbuild)")
	flag.IntVar(&iters, "iters", 30, "number of iterations to run")
}

var benchArgsFuncs = map[string]func(src string) []string{
	"ThreeJS": func(src string) []string {
		return []string{
			"--bundle",
			"--global-name=THREE",
			"--sourcemap",
			"--minify",
			"--timing",
			"--outfile=" + filepath.Join(os.TempDir(), "out-three.js"),
			filepath.Join(src, "src", "entry.js"),
		}
	},
	"RomeTS": func(src string) []string {
		return []string{
			"--bundle",
			"--platform=node",
			"--sourcemap",
			"--minify",
			"--timing",
			"--outfile=" + filepath.Join(os.TempDir(), "out-rome.js"),
			filepath.Join(src, "src", "entry.ts"),
		}
	},
}

func main() {
	flag.Parse()

	if esbuildBin == "" {
		esbuildBin = os.Getenv("ESBUILD_BIN")
	}

	if esbuildBin == "" || esbuildSrc == "" || benchName == "" {
		fmt.Println("Usage: ./main [--bin ./esbuild] --src ./data/demo --bench ThreeJS|RomeTS [--threads N]")
		os.Exit(1)
	}

	argsFunc, ok := benchArgsFuncs[benchName]
	if !ok {
		fmt.Printf("Unknown benchmark: %s\n", benchName)
		os.Exit(1)
	}

	cmdArgs := argsFunc(esbuildSrc)

	start := time.Now()
	for i := 0; i < iters; i++ {
		cmd := exec.Command(esbuildBin, cmdArgs...)
		cmd.Stdout = nil
		cmd.Stderr = nil

		cmd.Env = os.Environ()
		if threads > 0 {
			cmd.Env = append(cmd.Env, fmt.Sprintf("GOMAXPROCS=%d", threads))
		}

		if err := cmd.Run(); err != nil {
			fmt.Printf("Error running esbuild: %v\n", err)
			os.Exit(1)
		}
	}
	elapsed := time.Since(start)
	fmt.Printf("[RESULT] Total elapsed time: %.4f s\n", elapsed.Seconds())
}
