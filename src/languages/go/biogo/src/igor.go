package main

import (
	"bytes"
	"flag"
	"fmt"
	"math/rand"
	"runtime"
	"strings"
	"sync"
	"time"

	"biogo/biogo-examples/igor/igor"

	"github.com/biogo/biogo/align/pals"
	"github.com/biogo/biogo/io/featio/gff"
)

var (
	seqCount   int
	maxPos     int
	hitLen     int
	threads    int
	iterations int
	warmup     bool
)

func init() {
	flag.IntVar(&seqCount, "seq", 100000, "number of sequences (hits) to generate")
	flag.IntVar(&maxPos, "maxpos", 100000, "maximum sequence position")
	flag.IntVar(&hitLen, "hitlen", 1000, "hit length")
	flag.IntVar(&threads, "threads", 1, "number of benchmark replicas (each runs in one goroutine)")
	flag.IntVar(&iterations, "iterations", 120, "number of benchmark iterations per replica")
	flag.BoolVar(&warmup, "warmup", true, "run one warmup iteration before benchmark")
}

// generateRandomGFF generates in-memory GFF lines simulating PALS hits
func generateRandomGFF(n, maxPos, hitLen int) string {
	var buf strings.Builder
	for i := 1; i <= n; i++ {
		if hitLen >= maxPos {
			hitLen = maxPos / 2
		}
		start := 1 + rand.Intn(maxPos-hitLen+1)
		end := start + hitLen - 1
		targetStart := 1 + rand.Intn(maxPos-hitLen+1)
		targetEnd := targetStart + hitLen - 1

		fmt.Fprintf(&buf, "seq%d\tpals\thit\t%d\t%d\t%d.00\t+\t.\tTarget seq%d %d %d; maxe 0\n",
			i, start, end, hitLen, rand.Intn(n)+1, targetStart, targetEnd)
	}
	return buf.String()
}

func runBenchmark(replicaID int, gffData string) time.Duration {
	var total time.Duration
	for iter := 1; iter <= iterations; iter++ {
		start := time.Now()

		reader := gff.NewReader(bytes.NewReader([]byte(gffData)))
		var pf pals.PairFilter
		piles, err := igor.Piles(reader, 0, pf)
		if err != nil {
			panic(fmt.Sprintf("[replica %d][iter %d] piling error: %v", replicaID, iter, err))
		}
		_, clusters := igor.Cluster(piles, igor.ClusterConfig{
			BandWidth:         0.5,
			RequiredCover:     0.95,
			OverlapStrictness: 0,
			OverlapThresh:     0.95,
			Procs:             1, 
		})
		cc := igor.Group(clusters, igor.GroupConfig{
			PileDiff:  0.05,
			ImageDiff: 0.05,
			Classic:   false,
		})

		var out bytes.Buffer
		_ = igor.WriteJSON(cc, &out)
		elapsed := time.Since(start)
		total += elapsed
	}
	return total
}

func main() {
	flag.Parse()

	const seed = 42
	rand.Seed(seed)

	if threads <= 0 {
		threads = runtime.NumCPU()
	}
	runtime.GOMAXPROCS(threads)

	// Generate GFF data once (shared)
	gffData := generateRandomGFF(seqCount, maxPos, hitLen)

	// Warmup
	if warmup {
		fmt.Println("[INFO] Running warmup...")
		reader := gff.NewReader(bytes.NewReader([]byte(gffData)))
		var pf pals.PairFilter
		piles, err := igor.Piles(reader, 0, pf)
		if err != nil {
			panic(fmt.Sprintf("warmup piling error: %v", err))
		}
		_, clusters := igor.Cluster(piles, igor.ClusterConfig{
			BandWidth:         0.5,
			RequiredCover:     0.95,
			OverlapStrictness: 0,
			OverlapThresh:     0.95,
			Procs:             1,
		})
		_ = igor.Group(clusters, igor.GroupConfig{
			PileDiff:  0.05,
			ImageDiff: 0.05,
			Classic:   false,
		})
	}

	// Launch multiple replicas in parallel
	var wg sync.WaitGroup
	results := make([]time.Duration, threads)
	startAll := time.Now()

	for i := 0; i < threads; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			results[id] = runBenchmark(id, gffData)
		}(i)
	}

	wg.Wait()
	totalElapsed := time.Since(startAll)

	// Combine results
	var total time.Duration
	for _, t := range results {
		total += t
	}

	fmt.Printf("[INFO] %d replicas finished.\n", threads)
	fmt.Printf("[RESULT] Total elapsed time: %.4f s\n", totalElapsed.Seconds())
}
