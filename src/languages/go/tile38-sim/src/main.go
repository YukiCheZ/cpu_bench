package main

import (
	"context"
	"flag"
	"fmt"
	"math"
	"math/rand"
	"runtime"
	"sort"
	"sync/atomic"
	"time"

	"github.com/kyroy/kdtree"
)

// Config
var (
	threads = flag.Int("threads", runtime.NumCPU(), "number of threads (controls both goroutines and CPU cores)")
	points  = flag.Int("points", 10000, "number of points in dataset")
	iters   = flag.Int("iters", 1000, "total number of queries to run")
	seed    = flag.Int64("seed", 42, "random seed")
)

// Point struct implements kdtree.Point interface
type Point struct {
	Lat float64
	Lon float64
}

// kdtree.Point interface
func (p Point) Dimensions() int { return 2 }
func (p Point) Dimension(i int) float64 {
	if i == 0 {
		return p.Lat
	}
	return p.Lon
}
func (p Point) Distance(q kdtree.Point) float64 {
	qp := q.(Point)
	dlat := p.Lat - qp.Lat
	dlon := p.Lon - qp.Lon
	return math.Sqrt(dlat*dlat + dlon*dlon)
}

// Global dataset and KDTree
var dataset []kdtree.Point
var tree *kdtree.KDTree

// Generate random dataset
func generateDataset(n int) []kdtree.Point {
	points := make([]kdtree.Point, n)
	for i := 0; i < n; i++ {
		points[i] = Point{
			Lat: rand.Float64()*180 - 90,
			Lon: rand.Float64()*360 - 180,
		}
	}
	return points
}

// KDTree queries using KNN + distance filtering
func rangeQuery(center Point, radius float64) []Point {
	results := tree.KNN(center, len(dataset))
	out := make([]Point, 0)
	for _, r := range results {
		p := r.(Point)
		if center.Distance(p) <= radius {
			out = append(out, p)
		}
	}
	return out
}

func withinCircle(center Point, radius float64) int {
	return len(rangeQuery(center, radius))
}

func intersectsCircle(center Point, radius float64) bool {
	return len(rangeQuery(center, radius)) > 0
}

func nearby(center Point, k int) []Point {
	points := tree.KNN(center, k)
	out := make([]Point, 0, len(points))
	for _, p := range points {
		out = append(out, p.(Point))
	}
	return out
}

// Worker
type worker struct {
	iterCount *int64
	latencies []time.Duration
}

func (w *worker) Run(ctx context.Context) {
	for {
		count := atomic.AddInt64(w.iterCount, -1)
		if count < 0 {
			return
		}

		center := Point{
			Lat: rand.Float64()*180 - 90,
			Lon: rand.Float64()*360 - 180,
		}

		start := time.Now()

		switch rand.Intn(3) {
		case 0:
			withinCircle(center, rand.Float64()*4.9+0.1)
		case 1:
			intersectsCircle(center, rand.Float64()*4.9+0.1)
		case 2:
			nearby(center, rand.Intn(50)+1)
		}

		w.latencies = append(w.latencies, time.Since(start))
	}
}


func main() {
	flag.Parse()
	rand.Seed(*seed)

	if *threads <= 0 {
		*threads = runtime.NumCPU()
	}

	runtime.GOMAXPROCS(*threads)

	fmt.Printf("Generating dataset with %d points...\n", *points)
	dataset = generateDataset(*points)

	fmt.Println("Building KDTree...")
	tree = kdtree.New(dataset)

	var iterCount int64 = int64(*iters)
	workers := make([]*worker, *threads)
	for i := range workers {
		workers[i] = &worker{
			iterCount: &iterCount,
			latencies: make([]time.Duration, 0, *iters/(*threads)),
		}
	}

	start := time.Now()
	done := make(chan struct{})
	for _, w := range workers {
		go func(w *worker) {
			w.Run(context.Background())
			done <- struct{}{}
		}(w)
	}
	for range workers {
		<-done
	}
	totalElapsed := time.Since(start)

	// Collect latencies
	allLatencies := make([]time.Duration, 0, *iters)
	for _, w := range workers {
		allLatencies = append(allLatencies, w.latencies...)
	}
	sort.Slice(allLatencies, func(i, j int) bool { return allLatencies[i] < allLatencies[j] })


	fmt.Printf("\n--- Benchmark Results ---\n")
	fmt.Printf("Threads: %d\n", *threads)
	fmt.Printf("Total queries: %d\n", len(allLatencies))
	fmt.Printf("Total time: %v\n", totalElapsed)
}
