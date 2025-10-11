// igor.go
package main

import (
	"flag"
	"fmt"
	"math/rand"
	"runtime"
	"strings"
	"time"

	"github.com/blevesearch/bleve"
	_ "github.com/blevesearch/bleve/analysis/analyzer/keyword"
	blevebench "bleve-index/bleve-bench"
)

var (
	batchSize  int
	documents  int
	iterations int
	warmup     bool
	threads    int
	zipf       *rand.Zipf
)

func init() {
	flag.IntVar(&batchSize, "batch-size", 256, "number of index requests to batch together")
	flag.IntVar(&documents, "documents", 50000, "number of documents to index")
	flag.IntVar(&iterations, "iterations", 10, "number of benchmark iterations")
	flag.BoolVar(&warmup, "warmup", true, "run one warmup iteration before benchmark")
	flag.IntVar(&threads, "threads", 1, "number of threads (GOMAXPROCS), 0 = auto")
}

// generateRandomArticles creates n random articles with title + text
func generateRandomArticles(n int) []blevebench.Article {
	articles := make([]blevebench.Article, 0, n)
	for i := 0; i < n; i++ {
		title := fmt.Sprintf("Article_%d", i+1)
		text := randomText(200 + rand.Intn(800))
		articles = append(articles, blevebench.Article{
			Title: title,
			Text:  text,
		})
	}
	return articles
}

// randomText generates random English text from commonWords using Zipf distribution
func randomText(length int) string {
	var sb strings.Builder
	for i := 0; i < length; i++ {
		if i > 0 {
			sb.WriteByte(' ')
		}
		idx := zipf.Uint64() // Zipf index
		sb.WriteString(commonWords[idx])
	}
	return sb.String()
}

// runIndexBenchmark executes a single indexing benchmark
func runIndexBenchmark(articles []blevebench.Article, batchSize int) error {
	mapping := blevebench.ArticleMapping()
	index, err := bleve.NewMemOnly(mapping)
	if err != nil {
		return err
	}
	defer index.Close()

	b := index.NewBatch()
	for _, a := range articles {
		b.Index(a.Title, a)
		if b.Size() >= batchSize {
			if err := index.Batch(b); err != nil {
				return err
			}
			b = index.NewBatch()
		}
	}
	if b.Size() != 0 {
		if err := index.Batch(b); err != nil {
			return err
		}
	}
	return nil
}

func main() {
	flag.Parse()

	const seed = 42
	rnd := rand.New(rand.NewSource(seed))
	rand.Seed(seed)

	if threads <= 0 {
		threads = runtime.NumCPU()
	}
	runtime.GOMAXPROCS(threads)

	zipf = rand.NewZipf(rnd, 1.1, 1, uint64(len(commonWords)-1))

	articles := generateRandomArticles(documents)

	// Warmup
	if warmup {
		_ = runIndexBenchmark(articles, batchSize)
	}

	// Benchmark iterations
	var total time.Duration
	for iter := 1; iter <= iterations; iter++ {
		start := time.Now()
		if err := runIndexBenchmark(articles, batchSize); err != nil {
			panic(fmt.Sprintf("[ERROR] iteration %d index error: %v", iter, err))
		}
		elapsed := time.Since(start)
		total += elapsed
	}

	fmt.Printf("[RESULT] Total elapsed time: %.4f s\n", total.Seconds())
}
