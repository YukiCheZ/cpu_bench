<!-- <div align="center"> -->

# CPU Bench

Multi-language CPU benchmarking suite for reproducible, parameterized performance across **Python, C, C++, Go, and Java** — with configurable data scales and thread counts to exercise both single‑core and multi‑core performance on emerging workloads.

</div>

> Focus: multi-language coverage, emerging workloads (DL, video, KV/search, compilers), configurable data scales, configurable threading (single‑core → multi‑core sweeps), reproducible runs with parameter overrides, optional hardware counters, and clean artifact hygiene.

---

## Table of Contents
1. [Features](#features)
2. [Repository Layout](#repository-layout)
3. [Prerequisites & Installation](#prerequisites--installation)
4. [Quick Start](#quick-start)
5. [Benchmark Metadata Schema](#benchmark-metadata-schema)
6. [Transformer Inference Example](#transformer-inference-example)
7. [Parameter Override Cheat Sheet](#parameter-override-cheat-sheet)
8. [Running Setup Only](#running-setup-only)
9. [Running Workloads](#running-workloads)
10. [Perf Collection](#perf-collection)
11. [Preset Runner](#preset-runner)
12. [Add a New Benchmark](#add-a-new-benchmark)
13. [Cleaning Artifacts](#cleaning-artifacts)
14. [System Info Capture](#system-info-capture)
15. [Notes](#notes)

---

## Features
- Multi-language coverage: Python / C / C++ / Go / Java
- Emerging workloads: deep learning transformers/CNNs, video processing, key‑value stores & search, compilers/builds, numerical kernels
- Configurable data scales: tune dataset sizes and generation for small smoke tests → stress runs
- Configurable threading: sweep thread counts to measure single‑core and multi‑core scaling
- Toolchain flexibility: compilers/interpreters are a first‑class evaluation dimension
- Unified runner with structured logs & CSV outputs for analysis
- Per-benchmark setup and optional data generation hooks
- Declarative parameter overrides (data / workload / setup) for reproducibility
- Optional `perf stat` collection with cache dropping and curated event sets
- Utilities: artifact cleanup and system information capture

## Repository Layout
- `configs/benchmarks_index.yaml` – Registry of benchmarks (name → path)
- `src/` – Benchmark source trees grouped by language
- `scripts/run_cpu.py` – Core workload runner
- `scripts/setup_env.py` – Setup/build phase executor only
- `scripts/clean_artifacts.py` – Remove build/data/vendor artifacts
- `run_v_0_0_1.py` – Orchestrated preset workload + parameter set runner
- `res/` – Results & system info (e.g. `system_info.json`)
- `log/` – Logs from preset runs

## Prerequisites & Installation
Supported OS/Arch: **Linux (x86_64 & ARM64)**.

Minimum versions:
| Tool | Version |
|------|---------|
| Python | >= 3.10 |
| GCC/G++ | >= 11 |
| Clang/Clang++ | >= 14 |
| Java (JDK) | >= 17 |
| Go | >= 1.24.5 |
| (Optional) | `perf` |

> Compiler / interpreter choice is an **evaluation dimension**. Point `PATH` (or system alternatives) so `gcc`, `clang`, `java`, `go`, `python3` resolve to your selected versions.

## Quick Start
```bash
# Environment setup
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip gcc g++ clang openjdk-17-jdk
pip3 install pyyaml

# Go (x86_64) – adapt for ARM64
wget https://go.dev/dl/go1.24.5.linux-amd64.tar.gz -O /tmp/go.tar.gz \
  && sudo tar -C /usr/local -xzf /tmp/go.tar.gz \
  && echo 'export PATH=/usr/local/go/bin:$PATH' | sudo tee /etc/profile.d/go.sh

# perf
sudo apt-get install -y linux-perf || sudo apt-get install -y perf

# Setup and run a pair of workloads with override param
python3 scripts/run_cpu.py --workloads numpy_benchmark.matmul ffmpeg_benchmark.ffmpeg \
  --setup-env --set-param numpy_benchmark.matmul.workload.size=2048 --verbose

# CPU Bench full preset suite
python3 run_v_0_0_1.py

# Clean artifacts (preview then execute)
python3 scripts/clean_artifacts.py --all --verbose
```

## Benchmark Metadata Schema
Each benchmark has a `metadata.yaml` defining setup and workloads.

Key fields:
- `name`, `type`, `language`, `domain[]`
- `setup.command` + optional `setup.parameters`
- `workloads[]`: each workload may have:
  - `name`, `description`
  - `data.command` + `data.parameters` (optional pre-run generation)
  - `command` (main workload)
  - `parameters` (runtime options)
- `characteristics`: e.g. `cpu_bound`, `memory_intensive`
- `tags`: free-form grouping labels
- `dependencies`: e.g. `python>=3.8`, `torch>=2.0`

Parameter semantics:
- Scalars → `--param value`
- Boolean defaults → flag style (`--param`) when true
- Explicit boolean override: `...param=true|false` (only `true` emits flag)
- Unknown override keys are ignored with warning

## Transformer Inference Example
Location: `src/languages/python/transformer_inference/metadata.yaml`

Setup:
```yaml
setup:
  command: python3 setup.py
```
Data generation & workload:
```yaml
workloads:
  - name: transformer_inference
    data:
      command: python3 generate_data.py
      parameters:
        num_batches: { default: 50 }
        batch_size:  { default: 8 }
        seq_len:     { default: 256 }
        vocab_size:  { default: 10000 }
    command: python3 run_benchmark.py
    parameters:
      threads:           { default: 1 }
      num_encoder_layers:{ default: 24 }
      compile:           { default: false }
```
Run sequence:
```bash
# Setup
python3 scripts/setup_env.py --benches transformer_inference --verbose
# Data + workload with overrides
python3 scripts/run_cpu.py --workloads transformer_inference.transformer_inference \
  --set-param transformer_inference.transformer_inference.data.num_batches=10 \
  --set-param transformer_inference.transformer_inference.workload.threads=8 \
  --set-param transformer_inference.transformer_inference.workload.compile=true \
  --verbose
```

## Parameter Override Cheat Sheet
Format patterns:
```text
<benchmark>.<workload>.data.<param>=<value>       # data generation
<benchmark>.<workload>.workload.<param>=<value>   # workload runtime
<benchmark>._.setup.<param>=<value>               # setup phase
<benchmark>.<workload>.workload.<flag>            # boolean flag (default true or explicit true)
```
Examples:
```bash
--set-param numpy_benchmark.matmul.workload.size=4096
--set-param ffmpeg_benchmark._.setup.compiler=clang
--set-param ffmpeg_benchmark._.setup.opt=-O2
--set-param transformer_inference.transformer_inference.workload.compile
```

## Running Setup Only
```bash
python3 scripts/setup_env.py --benches <bench1> <bench2> --verbose
python3 scripts/setup_env.py --all --verbose
python3 scripts/setup_env.py --benches ffmpeg_benchmark \
  --set-param ffmpeg_benchmark._.setup.compiler=clang \
  --set-param ffmpeg_benchmark._.setup.opt=-O2 --verbose
```
Output log: `setup_logs_<timestamp>.log` (override with `--out-log`).

## Running Workloads
```bash
# Specific workloads
python3 scripts/run_cpu.py --workloads numpy_benchmark.matmul ffmpeg_benchmark.ffmpeg --verbose
# Entire benchmarks
python3 scripts/run_cpu.py --benches numpy_benchmark ffmpeg_benchmark --setup-env --verbose
```
CSV: `benchmark_name,workload_name,elapsed_time(s),param_overrides`

## Perf Collection
Enable counters:

Edit variable `PERF_CMD_PREFIX` of `scripts/run_cpu.py`, add the microarchitectural events you want to observe, the script contains an example of an event list for a Skylake architecture.

```bash
python3 scripts/run_cpu.py --workloads numpy_benchmark.matmul --use-perf --verbose
```
Behavior:
- Drops caches: `sync; echo 3 > /proc/sys/vm/drop_caches`
- Wraps command with predefined `perf stat` events
- Stores outputs under `perf/` near log file

Requires permission for `/proc/sys/vm/drop_caches` (may need `sudo`).

## Preset Runner
`run_v_0_0_1.py` is the suite orchestrator for version **v0.0.1** — it runs the full benchmark selection by combining curated workload sets with the parameter set `v0.0.1` (data augmentation, compiler/env choices, optimization flags, and threading).
```bash
python3 run_v_0_0_1.py
```
Artifacts:
- Logs → `log/logs_<tag>_<timestamp>.log`
- Results → `res/results_<tag>_<timestamp>.csv`

Networking policy:
- The full run flow is `setup → data → workload`. Only the **setup** phase may access the network (e.g., to download dependencies). The **data** and **workload** phases are designed to run offline.

Failure reporting:
- At the end of a run, the log aggregates all failed workloads with their error reasons under a "[WARNING SUMMARY] Failed workloads" section.

## Add a New Benchmark
1. Create `src/languages/<lang>/<benchmark_name>/` + `metadata.yaml`.
2. Register in `configs/benchmarks_index.yaml`.
3. Ensure workload prints result line.
4. (Optional) Add to a preset set in `run_v_0_0_1.py`.

Minimal template:
```yaml
name: my_benchmark
language: C
setup:
  command: ./build.sh
workloads:
  - name: main
    command: ./run.sh
    parameters:
      size: { default: 1024, description: problem size }
characteristics:
  cpu_bound: true
tags: [numeric]
dependencies:
  gcc: ">=11"
```

Note: Your workload must emit exactly one parseable line:
```text
[RESULT] Total elapsed time: <seconds> s
```
The runner extracts `<seconds>` as a float; absence triggers an error.

## Cleaning Artifacts
```bash
python3 scripts/clean_artifacts.py --benches ffmpeg_benchmark opencv_benchmark --verbose
python3 scripts/clean_artifacts.py --all --dry-run --verbose
python3 scripts/clean_artifacts.py --all --verbose
```
Targets removed: `data`, `bin`, `.m2`, `build`, `target`, `deps_vendored`, `go.mod`, `go.sum`, `vendor`.

## System Info Capture
`run_v_0_0_1.py` writes `res/system_info.json` with:
- CPU (`lscpu`), memory (`/proc/meminfo`), OS (`/etc/os-release`), `uname -a`
- Toolchain versions (gcc, clang, python, java, go)
- Optional DMI (if `dmidecode` present)

## Notes
- Large workload sizes may stress memory; scale down via overrides for smoke tests.
- Verify `benchmarks_index.yaml` paths before first run.
- Adjust thread counts to explore scaling; record toolchain versions for fairness.
- Perf requires appropriate kernel permissions; consider running as a privileged user if needed.
- Only the setup phase requires network connectivity; subsequent data/workload phases are offline.
- Check the run log for a summary of failed workloads and reasons.

## Contributing
Pull requests adding new benchmarks, refining metadata, or expanding parameter sets are welcome. Please include:
- `metadata.yaml` with descriptions & defaults
- Example result line in README or PR description
- Justification of benchmark relevance (CPU characteristics)

## License
MIT License. See `LICENSE` for full terms.

