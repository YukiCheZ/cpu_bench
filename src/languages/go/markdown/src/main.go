// markdown_bench.go
package main

import (
	"bytes"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"sync"
	"time"

	"gitlab.com/golang-commonmark/markdown"
)

func runMarkdownOnce(contents [][]byte, threads int) time.Duration {
	runtime.GOMAXPROCS(threads)

	start := time.Now()

	var wg sync.WaitGroup
	tasks := make(chan []byte)

	for i := 0; i < threads; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			md := markdown.New(
				markdown.XHTMLOutput(true),
				markdown.Tables(true),
				markdown.MaxNesting(8),
				markdown.Typographer(true),
				markdown.Linkify(true),
			)

			out := bytes.Buffer{}
			out.Grow(1024 * 1024)

			for c := range tasks {
				md.Render(&out, c)
				out.Reset()
			}
		}()
	}

	go func() {
		for _, c := range contents {
			tasks <- c
		}
		close(tasks)
	}()

	wg.Wait()
	return time.Since(start)
}

func runMarkdownBenchmark(mddir string, threads, iterations int) error {
	files, err := os.ReadDir(mddir)
	if err != nil {
		return fmt.Errorf("[ERROR] failed to read directory %q: %w", mddir, err)
	}

	contents := make([][]byte, 0, len(files))
	for _, file := range files {
		if !file.IsDir() && filepath.Ext(file.Name()) == ".md" {
			content, err := os.ReadFile(filepath.Join(mddir, file.Name()))
			if err != nil {
				return fmt.Errorf("[ERROR] failed to read file %q: %w", file.Name(), err)
			}
			contents = append(contents, content)
		}
	}

	if len(contents) == 0 {
		return fmt.Errorf("[ERROR] no markdown files found in %q", mddir)
	}

	var total time.Duration
	for i := 0; i < iterations; i++ {
		total += runMarkdownOnce(contents, threads)
	}

	fmt.Printf("[RESULT] Total elapsed time: %.4f s\n", total.Seconds())

	return nil
}

func main() {
	var inputDir string
	var threads int
	var iterations int

	flag.StringVar(&inputDir, "data", "./data/markdown", "Path to the directory containing Markdown files")
	flag.IntVar(&threads, "threads", 1, "Number of threads (goroutines + CPU cores)")
	flag.IntVar(&iterations, "iterations", 1, "Number of iterations for the benchmark")
	flag.Parse()

	if threads <= 0 {
		fmt.Fprintf(os.Stderr, "[ERROR] Invalid --threads value: must be > 0\n")
		os.Exit(1)
	}
	if iterations <= 0 {
		fmt.Fprintf(os.Stderr, "[ERROR] Invalid --iterations value: must be > 0\n")
		os.Exit(1)
	}

	if err := runMarkdownBenchmark(inputDir, threads, iterations); err != nil {
		fmt.Fprintf(os.Stderr, "[ERROR] Benchmark error: %v\n", err)
		os.Exit(1)
	}
}
