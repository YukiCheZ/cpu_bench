# Redis CPU Benchmark Wrapper

## Overview

This project provides a simple **CPU benchmarking wrapper for Redis** based on the official `redis-benchmark` tool.  
The goal is to evaluate **CPU performance** of Redis under configurable workloads while minimizing disk I/O interference.  
It is especially useful for:

- Measuring **single-core and multi-core performance**.
- Comparing Redis performance with different **data sizes**, **concurrent clients**, **pipeline depths**, and **benchmark threads**.
- Running repeatable iterations with a **warmup phase** to stabilize the CPU and cache state.

This script was developed for research and performance analysis purposes, providing a lightweight, automated way to benchmark Redis CPU utilization.

---

## Features

- Automatic start/stop of a Redis server with **persistence disabled** (`--save "" --appendonly no`).
- Configurable benchmark parameters: number of clients, threads, requests, data size, and pipeline depth.
- Warmup run to pre-fill CPU caches and stabilize performance.
- Multiple iterations with **timing measurement** to calculate average duration.
- Fully quiet mode (`-q`) to reduce console output.
- Minimal dependencies: Python 3 and a working Redis installation.

---

## Requirements

- Python 3.6+
- Redis server installed and accessible via `redis-server` and `redis-cli`.
- Linux/macOS/Windows with a Bash-like environment recommended.

---

## Installation

1. Install Redis on your system. For example:

```bash
# macOS (Homebrew)
brew install redis

# Ubuntu/Debian
sudo apt update
sudo apt install redis-server
```

2. Ensure `redis-server` and `redis-cli` are in your PATH.
3. Save the benchmark script, for example as `redis_cpu_benchmark.py`.

---

## Usage

```bash
python redis_cpu_benchmark.py [OPTIONS]
```

### Available Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--clients` | int | 50 | Number of concurrent client connections to Redis |
| `--threads` | int | 1 | Number of benchmark threads generating requests |
| `--requests` | int | 100000 | Total number of requests per iteration |
| `--datasize` | int | 3 | Size in bytes of each value in `SET`/`GET` operations |
| `--pipeline` | int | 1 | Number of requests to pipeline per client |
| `--iterations` | int | 1 | Number of repeated benchmark iterations |

---

## Example

Run a benchmark with 100 concurrent clients, 4 threads, 1 million requests of 1 KB each, pipelined by 16 requests, for 3 iterations:

```bash
python redis_cpu_benchmark.py --clients 100 --threads 4 --requests 1000000 --datasize 1024 --pipeline 16 --iterations 3
```

Sample output:

```
Starting warmup (with fresh Redis).
Warmup done.

Iteration 1/3 ...
  Duration: 5.237 seconds
Iteration 2/3 ...
  Duration: 5.124 seconds
Iteration 3/3 ...
  Duration: 5.310 seconds

Benchmark complete.
Average duration over 3 iterations: 5.224 seconds
```

---

## How it Works

1. **Warmup**  
   - Starts a fresh Redis server with persistence disabled.
   - Executes the benchmark once to stabilize caches and CPU state.
   - Stops the server.

2. **Benchmark Iterations**  
   - For each iteration:
     - Starts a fresh Redis server.
     - Runs the `redis-benchmark` command with the configured parameters.
     - Measures the elapsed time.
     - Stops the Redis server using `redis-cli shutdown nosave`.

3. **Result Reporting**  
   - Prints the duration of each iteration.
   - Calculates and prints the average duration across all iterations.

---

## Notes

- Persistence is disabled to avoid disk I/O affecting CPU performance measurement.
- If you want to simulate a production-like scenario with disk writes, remove `--save "" --appendonly no` from the Redis startup command.
- The script is designed for **local benchmarking**; network latency is minimal.
- The optimal number of threads depends on your CPU cores, Redis version, and workload type. Usually fewer threads than physical cores give the best single-server throughput.

```