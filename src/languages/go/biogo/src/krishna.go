package main

import (
	"bytes"
	"flag"
	"fmt"
	"math/rand"
	"runtime"
	"strings"
	"time"

	"biogo/biogo-examples/krishna"

	"github.com/biogo/biogo/align/pals"
)

const (
	minHitLen  = 400
	minId      = 0.94
	tubeOffset = 0
	tmpChunk   = 1e6
)

var (
	tmpDir     string
	seqSize    int
	seqCount   int
	repeatRate float64
	threads    int
	iterations int
	warmup     int
)

func init() {
	flag.StringVar(&tmpDir, "tmp", "", "directory to store temporary files (may still use morass)")
	flag.IntVar(&seqSize, "size", 10000, "length of each random DNA sequence")
	flag.IntVar(&seqCount, "count", 1000, "number of sequences to generate")
	flag.Float64Var(&repeatRate, "repeat", 0.8, "proportion of sequence to copy from first sequence to others (0~1)")
	flag.IntVar(&threads, "threads", 1, "number of threads (GOMAXPROCS) to use, 0 = auto")
	flag.IntVar(&iterations, "iterations", 5, "number of timed iterations to run")
	flag.IntVar(&warmup, "warmup", 0, "number of warmup iterations before timing")
}

// generateRandomFASTA generates sequences with controlled repeats
func generateRandomFASTA(n, length int, repeat float64) string {
	letters := []rune("ACGT")
	sequences := make([][]rune, n)

	// Generate first random sequence
	sequences[0] = make([]rune, length)
	for j := 0; j < length; j++ {
		sequences[0][j] = letters[rand.Intn(len(letters))]
	}

	// Generate other sequences with repeats from first
	for i := 1; i < n; i++ {
		sequences[i] = make([]rune, length)
		for j := 0; j < length; j++ {
			sequences[i][j] = letters[rand.Intn(len(letters))]
		}
		fragLen := int(float64(length) * repeat)
		if fragLen > 0 {
			startSrc := rand.Intn(length - fragLen + 1)
			startDst := rand.Intn(length - fragLen + 1)
			copy(sequences[i][startDst:startDst+fragLen], sequences[0][startSrc:startSrc+fragLen])
		}
	}

	var b strings.Builder
	for i := 0; i < n; i++ {
		b.WriteString(fmt.Sprintf(">seq%d\n", i+1))
		b.WriteString(string(sequences[i]))
		b.WriteByte('\n')
	}
	return b.String()
}

func main() {
	flag.Parse()
	const seed = 42
	rand.Seed(seed)

	if threads <= 0 {
		threads = runtime.NumCPU()
	}
	runtime.GOMAXPROCS(threads)

	fastaData := generateRandomFASTA(seqCount, seqSize, repeatRate)

	k, err := krishna.NewFromReader(
		strings.NewReader(fastaData),
		"inmem",
		tmpDir,
		krishna.Params{
			TmpChunkSize: tmpChunk,
			MinHitLen:    minHitLen,
			MinHitId:     minId,
			TubeOffset:   tubeOffset,
			AlignConc:    true,
			TmpConc:      true,
		},
	)
	if err != nil {
		panic(err)
	}
	defer k.CleanUp()

	writer := pals.NewWriter(&bytes.Buffer{}, 2, 60, false)

	for i := 0; i < warmup; i++ {
		if err := k.Run(writer); err != nil {
			panic(err)
		}
	}

	var total time.Duration
	for i := 0; i < iterations; i++ {
		start := time.Now()
		if err := k.Run(writer); err != nil {
			panic(err)
		}
		elapsed := time.Since(start)
		total += elapsed
	}

	fmt.Printf("[RESULT] Total elapsed time: %.4f s\n", total.Seconds())
}
