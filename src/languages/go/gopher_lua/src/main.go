package main

import (
	"flag"
	"fmt"
	"os"
	"runtime"
	"sync"
	"time"

	lua "github.com/yuin/gopher-lua"
)

var (
	luaFile   string
	inputFile string
	threads   int
	iters     int
)

func usageAndExit() {
	fmt.Fprintf(os.Stderr, "Usage: %s [--lua <lua file>] [--data <input file>] [--threads N]\n", os.Args[0])
	os.Exit(2)
}

func runLuaFromFile(luaPath, inputFile string, id int, iters int) error {
	data, err := os.ReadFile(inputFile)
	if err != nil {
		return fmt.Errorf("[ERROR] failed to read input file %q: %w", inputFile, err)
	}
	seq := string(data)

	L := lua.NewState()
	defer L.Close()

	if err := L.DoFile(luaPath); err != nil {
		return fmt.Errorf("[ERROR] failed to load lua file %q: %w", luaPath, err)
	}

	fn := L.GetGlobal("run_knucleotide")
	if fn.Type() != lua.LTFunction {
		return fmt.Errorf("[ERROR] lua file does not define run_knucleotide(seq) function")
	}

	for i := 0; i < iters; i++ {
		if err := L.CallByParam(lua.P{
			Fn:      fn,
			NRet:    0,
			Protect: true,
		}, lua.LString(seq)); err != nil {
			return fmt.Errorf("lua execution error: %w", err)
		}
	}
	return nil
}

func main() {
	flag.StringVar(&luaFile, "lua", "./src/knucleotide.lua", "Path to the Lua script")
	flag.StringVar(&inputFile, "data", "./data/dna_input.fasta", "Path to the DNA input file")
	flag.IntVar(&threads, "threads", 1, "Number of threads to use")
	flag.IntVar(&iters, "iters", 80, "Number of iterations per thread")
	flag.Parse()

	if _, err := os.Stat(luaFile); err != nil {
		fmt.Fprintf(os.Stderr, "[ERROR] Lua file error: %v\n", err)
		os.Exit(1)
	}
	if _, err := os.Stat(inputFile); err != nil {
		fmt.Fprintf(os.Stderr, "[ERROR] Input file error: %v\n", err)
		os.Exit(1)
	}

	runtime.GOMAXPROCS(threads)
	fmt.Printf("[INFO] Launching %d workers...\n", threads)

	var wg sync.WaitGroup
	wg.Add(threads)

	startAll := time.Now()

	for i := 0; i < threads; i++ {
		go func(id int) {
			defer wg.Done()
			if err := runLuaFromFile(luaFile, inputFile, id, iters); err != nil {
				fmt.Fprintf(os.Stderr, "[ERROR] Worker %d: %v\n", id, err)
			}
		}(i)
	}

	wg.Wait()
	total := time.Since(startAll)
	fmt.Printf("[RESULT] Total elapsed time: %.4f s\n", total.Seconds())
}
