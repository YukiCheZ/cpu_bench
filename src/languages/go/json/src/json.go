package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"runtime"
	"sync"
	"time"
)

type Response struct {
	Tree     *Node  `json:"tree"`
	Username string `json:"username"`
}

type Node struct {
	Name     string  `json:"name"`
	Kids     []*Node `json:"kids"`
	CLWeight float64 `json:"cl_weight"`
	Touches  int     `json:"touches"`
	MinT     int64   `json:"min_t"`
	MaxT     int64   `json:"max_t"`
	MeanT    int64   `json:"mean_t"`
}

var (
	inputPath string
	threads   int
	iters     int
)

func main() {
	flag.StringVar(&inputPath, "input", "./data/input_50MB.json", "path to input JSON file")
	flag.IntVar(&threads, "threads", 1, "number of threads")
	flag.IntVar(&iters, "iterations", 1000, "number of iterations per thread")
	flag.Parse()

	if inputPath == "" {
		fmt.Fprintln(os.Stderr, "[ERROR] --input is required")
		os.Exit(1)
	}

	data, err := os.ReadFile(inputPath)
	if err != nil {
		panic(err)
	}

	var jsondata Response
	if err := json.Unmarshal(data, &jsondata); err != nil {
		panic(err)
	}

	runtime.GOMAXPROCS(threads)
	fmt.Printf("[INFO] Starting benchmark: threads=%d, iters=%d\n", threads, iters)

	start := time.Now()
	var wg sync.WaitGroup
	wg.Add(threads)

	for i := 0; i < threads; i++ {
		go func() {
			defer wg.Done()
			for j := 0; j < iters; j++ {
				var r Response
				if err := json.Unmarshal(data, &r); err != nil {
					panic(err)
				}
				if _, err := json.Marshal(&jsondata); err != nil {
					panic(err)
				}
			}
		}()
	}

	wg.Wait()
	elapsed := time.Since(start)
	fmt.Printf("[RESULT] Total elapsed time: %.4f s\n", elapsed.Seconds())
}
