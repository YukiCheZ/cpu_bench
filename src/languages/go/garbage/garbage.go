// Garbage is a benchmark that stresses the garbage collector.
// It repeatedly parses Go source files and discards results.
package main

import (
	"flag"
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
	"io/ioutil"
	"os"
	"runtime"
	"sync"
	"sync/atomic"
	"time"
)

type ParsedPackage *ast.File

var (
	parsed []ParsedPackage
	src    []byte
)

func main() {
	var inputPath string
	var iterations int
	var threads int

	flag.StringVar(&inputPath, "input", "./data/input.go", "path to input Go source file")
	flag.IntVar(&iterations, "iterations", 600, "number of parse iterations per thread to run")
	flag.IntVar(&threads, "threads", 1, "number of threads (GOMAXPROCS)")
	flag.Parse()

	if inputPath == "" {
		fmt.Fprintln(os.Stderr, "[ERROR] input path not specified")
		os.Exit(1)
	}

	data, err := ioutil.ReadFile(inputPath)
	if err != nil {
		panic(err)
	}
	src = data

	if threads < 1 {
		threads = runtime.NumCPU()
		if(threads < 1) {
			threads = 1
		}
	}

	runtime.GOMAXPROCS(threads)

	if parsed == nil {
		mem := packageMemConsumption()
		avail := int64(runtime.MemStats{}.Sys) * 4 / 5 // rough estimation
		npkg := avail / int64(mem) / 2
		if npkg < 1 {
			npkg = 1
		}
		parsed = make([]ParsedPackage, npkg)
		// warmup GC
		for n := 0; n < 2; n++ {
			for i := range parsed {
				parsed[i] = parsePackage()
			}
		}
	}

	start := time.Now()
	benchmarkN(iterations * threads)
	elapsed := time.Since(start)

	fmt.Printf("[RESULT] Total elapsed time: %.4f s\n", elapsed.Seconds())
}

func benchmarkN(N int) {
	P := runtime.GOMAXPROCS(0)
	G := P
	gate := make(chan bool, 2*P)
	var mu sync.Mutex
	var wg sync.WaitGroup
	wg.Add(G)
	remain := int64(N)
	pos := 0

	half := len(parsed) / 2
	if half == 0 {
		half = 1
	}

	for g := 0; g < G; g++ {
		go func() {
			defer wg.Done()
			for atomic.AddInt64(&remain, -1) >= 0 {
				gate <- true
				p := parsePackage()
				mu.Lock()
				parsed[pos%half] = p
				pos++
				mu.Unlock()
				<-gate
			}
		}()
	}
	wg.Wait()
}

func packageMemConsumption() int {
	runtime.GC()
	runtime.GC()
	ms0 := new(runtime.MemStats)
	runtime.ReadMemStats(ms0)

	const N = 10
	var tmp [N]ParsedPackage
	for i := range tmp {
		tmp[i] = parsePackage()
	}
	runtime.GC()
	runtime.GC()
	if tmp[0] == nil {
		_ = tmp
	}
	ms1 := new(runtime.MemStats)
	runtime.ReadMemStats(ms1)
	mem := int(ms1.Alloc-ms0.Alloc) / N
	if mem < 1<<16 {
		mem = 1 << 16
	}
	return mem
}

func parsePackage() ParsedPackage {
	fset := token.NewFileSet()
	pkgs, err := parser.ParseFile(fset, "input.go", src, parser.ParseComments)
	if err != nil {
		fmt.Fprintf(os.Stderr, "[ERROR] Parse error: %v\n", err)
		panic("fail")
	}
	return pkgs
}
