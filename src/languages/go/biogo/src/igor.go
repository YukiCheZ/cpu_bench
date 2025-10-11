package main

import (
	"bytes"
	"flag"
	"fmt"
	"math/rand"
	"runtime"
	"strings"
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
	flag.IntVar(&seqCount, "seq", 1000000, "number of sequences (hits) to generate")
	flag.IntVar(&maxPos, "maxpos", 100000, "maximum sequence position")
	flag.IntVar(&hitLen, "hitlen", 1000, "hit length")
	flag.IntVar(&threads, "threads", 1, "number of threads (GOMAXPROCS), 0 = auto")
	flag.IntVar(&iterations, "iterations", 50, "number of benchmark iterations")
	flag.BoolVar(&warmup, "warmup", true, "run one warmup iteration before benchmark")
}

// generateRandomGFF generates in-memory GFF lines simulating PALS hits
func generateRandomGFF(n, maxPos, hitLen int) string {
	var buf strings.Builder
	for i := 1; i <= n; i++ {
		if hitLen >= maxPos {
			hitLen = maxPos / 2
		}
		start := 1 + rand.Intn(maxPos-hitLen+1) // 1-based
		end := start + hitLen - 1               // end >= start
		targetStart := 1 + rand.Intn(maxPos-hitLen+1)
		targetEnd := targetStart + hitLen - 1

		fmt.Fprintf(&buf, "seq%d\tpals\thit\t%d\t%d\t%d.00\t+\t.\tTarget seq%d %d %d; maxe 0\n",
			i, start, end, hitLen, rand.Intn(n)+1, targetStart, targetEnd)
	}
	return buf.String()
}

func main() {
	flag.Parse()
	
	const seed = 42
	rand.Seed(seed)

	if threads <= 0 {
		threads = runtime.NumCPU()
	}
	runtime.GOMAXPROCS(threads)

	// Generate GFF data in memory once
	gffData := generateRandomGFF(seqCount, maxPos, hitLen)

	// Warmup
	if warmup {
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
			Procs:             threads,
		})
		_ = igor.Group(clusters, igor.GroupConfig{
			PileDiff:  0.05,
			ImageDiff: 0.05,
			Classic:   false,
		})
	}

	// Benchmark iterations
	var totalTime time.Duration
	for iter := 1; iter <= iterations; iter++ {
		start := time.Now()

		reader := gff.NewReader(bytes.NewReader([]byte(gffData)))
		var pf pals.PairFilter
		piles, err := igor.Piles(reader, 0, pf)
		if err != nil {
			panic(fmt.Sprintf("[INFO] iteration %d piling error: %v", iter, err))
		}
		_, clusters := igor.Cluster(piles, igor.ClusterConfig{
			BandWidth:         0.5,
			RequiredCover:     0.95,
			OverlapStrictness: 0,
			OverlapThresh:     0.95,
			Procs:             threads,
		})
		cc := igor.Group(clusters, igor.GroupConfig{
			PileDiff:  0.05,
			ImageDiff: 0.05,
			Classic:   false,
		})

		var out bytes.Buffer
		_ = igor.WriteJSON(cc, &out)
		elapsed := time.Since(start)
		totalTime += elapsed
	}

	fmt.Printf("[RESULT] Total elapsed time: %.4f s\n", totalTime.Seconds())
}
