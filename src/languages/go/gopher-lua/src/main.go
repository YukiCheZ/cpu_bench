// main.go
package main

import (
	"flag"
	"fmt"
	"os"
	"runtime"
	"time"

	lua "github.com/yuin/gopher-lua"
)

var (
	luaFile   string
	inputFile string
	threads   int
)

func usageAndExit() {
	fmt.Fprintf(os.Stderr, "Usage: %s [--lua <lua file>] [--data <input file>] [--threads N]\n", os.Args[0])
	os.Exit(2)
}

func runLuaFromFile(luaPath, inputFile string) error {
	data, err := os.ReadFile(inputFile)
	if err != nil {
		return fmt.Errorf("failed to read input file %q: %w", inputFile, err)
	}
	seq := string(data)

	L := lua.NewState()
	defer L.Close()

	if err := L.DoFile(luaPath); err != nil {
		return fmt.Errorf("failed to load lua file %q: %w", luaPath, err)
	}

	fn := L.GetGlobal("run_knucleotide")
	if fn.Type() != lua.LTFunction {
		return fmt.Errorf("lua file does not define run_knucleotide(seq) function")
	}

	start := time.Now()
	if err := L.CallByParam(lua.P{
		Fn:      fn,
		NRet:    0,
		Protect: true,
	}, lua.LString(seq)); err != nil {
		return fmt.Errorf("lua execution error: %w", err)
	}
	elapsed := time.Since(start)
	fmt.Printf("[RESULT] KNucleotide elapsed time: %v\n", elapsed)
	return nil
}

func main() {
	flag.StringVar(&luaFile, "lua", "./knucleotide.lua", "Path to the Lua script")
	flag.StringVar(&inputFile, "data", "./data/dna_input.fasta", "Path to the DNA input file")
	flag.IntVar(&threads, "threads", 1, "Number of threads to use")
	flag.Parse()

	if _, err := os.Stat(luaFile); err != nil {
		fmt.Fprintf(os.Stderr, "Lua file error: %v\n", err)
		os.Exit(1)
	}
	if _, err := os.Stat(inputFile); err != nil {
		fmt.Fprintf(os.Stderr, "Input file error: %v\n", err)
		os.Exit(1)
	}

	if threads > 0 {
		runtime.GOMAXPROCS(threads)
		fmt.Printf("[INFO] Using %d threads\n", threads)
	}

	if err := runLuaFromFile(luaFile, inputFile); err != nil {
		fmt.Fprintf(os.Stderr, "Benchmark error: %v\n", err)
		os.Exit(1)
	}
}
