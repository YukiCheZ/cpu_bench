// Copyright 2014 The Go Authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

// Garbage is a benchmark that stresses garbage collector.
// It repeatedly parses net/http package with go/parser and then discards results.
package main

// The source of net/http was captured at git tag go1.5.2 by
//go:generate sh -c "(echo 'package garbage'; echo 'var src = `'; bundle net/http http '' | sed 's/`/`+\"`\"+`/g'; echo '`') > nethttp.go"

import (
	"flag"
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
	"runtime"
	"sync"
	"sync/atomic"
	"time"

	"golang_benchmark/driver"
)

type ParsedPackage *ast.File

var (
	parsed []ParsedPackage
)

func main() {
	iterations := flag.Uint64("iterations", 2000, "Number of parse iterations to run")
	threads := flag.Int("threads", runtime.NumCPU(), "Number of threads (sets GOMAXPROCS)")
	flag.Parse()

	// 设置 GOMAXPROCS
	runtime.GOMAXPROCS(*threads)

	// 初始化 parsed 切片
	if parsed == nil {
		mem := packageMemConsumption()
		avail := (driver.BenchMem() << 20) * 4 / 5 // 4/5 to account for non-heap memory
		npkg := avail / mem / 2                    // 2 to account for GOGC=100
		if npkg < 1 {
			npkg = 1
		}
		parsed = make([]ParsedPackage, npkg)
		for n := 0; n < 2; n++ { // warmup GC
			for i := range parsed {
				parsed[i] = parsePackage()
			}
		}
	}

	start := time.Now()
	benchmarkN(*iterations)
	elapsed := time.Since(start)

	fmt.Printf("Total run time: %v\n", elapsed)
}

func benchmarkN(N uint64) {
	P := runtime.GOMAXPROCS(0)
	G := 1024
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
	pkgs, err := parser.ParseFile(token.NewFileSet(), "net/http", src, parser.ParseComments)
	if err != nil {
		println("parse", err.Error())
		panic("fail")
	}
	return pkgs
}
