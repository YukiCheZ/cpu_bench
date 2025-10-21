#!/usr/bin/env python3
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent              
PROJECT_ROOT = ROOT.parent                          
RUN_CPU = PROJECT_ROOT / "scripts" / "run_cpu_env.py"
LOG_DIR = ROOT / "log"
RES_DIR = ROOT / "res"

LOG_DIR.mkdir(parents=True, exist_ok=True)
RES_DIR.mkdir(parents=True, exist_ok=True)

bench_sets = {
    "python_all": [
        "numpy_benchmark", "tuf_benchmark", "requests_benchmark",
        "raytrace", "go_board_game", "chaos_fractal", "deltablue", "pyflate",
        "resnet50_cpu", "bert_cpu", "transformer_inference", "transformer_train"
    ],
    "python_ml": [
        "resnet50_cpu", "bert_cpu", "transformer_inference", "transformer_train"
    ]
}

data_augmentation_params = [
    "numpy_benchmark.matmul.workload.size=2048",
    "numpy_benchmark.svd.workload.size=1024",
    "numpy_benchmark.fft.workload.size=4194304",
    "tuf_benchmark.tuf-metadata.data.size=268435456",
    "requests_benchmark.requests-json.workload.size=131072",
    "raytrace.raytrace.workload.width=2048",
    "raytrace.raytrace.workload.height=2048",
    "chaos_fractal.chaos-fractal.data.width=2048",
    "chaos_fractal.chaos-fractal.data.height=2048",
    "deltablue.deltablue.workload.n=100000",
    "pyflate.pyflate.data.size=5000000",
    "go_board_game.go-board-game.workload.size=100",
    "resnet50_cpu.resnet50_inference.data.batch_size=2",
    "resnet50_cpu.resnet50_training.data.batch_size=2",
    "bert_cpu.bert_eval.data.batch_size=4",
    "transformer_inference.transformer_inference.data.batch_size=4",
    "transformer_train.transformer_train.data.batch_size=2"
]

all_threads_param = [
    "numpy_benchmark.matmul.workload.threads=28",
    "numpy_benchmark.svd.workload.threads=28",
    "numpy_benchmark.fft.workload.threads=28",
    "tuf_benchmark.tuf-metadata.workload.threads=28",
    "requests_benchmark.requests-json.workload.threads=28",
    "raytrace.raytrace.workload.threads=28",
    "chaos_fractal.chaos-fractal.workload.threads=28",
    "deltablue.deltablue.workload.threads=28",
    "pyflate.pyflate.workload.threads=28",
    "go_board_game.go-board-game.workload.threads=28",
    "resnet50_cpu.resnet50_inference.workload.threads=28",
    "resnet50_cpu.resnet50_training.workload.threads=28",
    "bert_cpu.bert_eval.workload.threads=28",
    "transformer_inference.transformer_inference.workload.threads=28",
    "transformer_train.transformer_train.workload.threads=28"
]

compile_params = [
    "resnet50_cpu.resnet50_inference.workload.compile",
    "resnet50_cpu.resnet50_training.workload.compile",
    "bert_cpu.bert_eval.workload.compile",
    "transformer_inference.transformer_inference.workload.compile",
    "transformer_train.transformer_train.workload.compile"
]

param_sets = {
    "p3": [],
    "p23": data_augmentation_params,
    "p34": compile_params,
    "p35": all_threads_param,
    "p234": data_augmentation_params + compile_params,
    "p235": data_augmentation_params + all_threads_param,
    "p345": compile_params + all_threads_param,
    "p2345": data_augmentation_params + compile_params + all_threads_param
}

pairs = [
    ("python_all", "p3", True),
    ("python_all", "p23", False),
    # ("python_ml", "p34", False),
    ("python_all", "p35", False),
    ("python_ml", "p234", False),
    ("python_all", "p235", False),
    ("python_ml", "p345", False),
    ("python_ml", "p2345", False)
]


def run_benchmark_set(tag: str, benches: list[str], params: list[str], setup_env: bool = False):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    result_file = RES_DIR / f"results_{tag}_{timestamp}.csv"
    log_file = LOG_DIR / f"logs_{tag}_{timestamp}.log"

    base_cmd = [
        sys.executable,
        str(RUN_CPU),
        "--verbose",
        "--out", str(result_file),
        "--log", str(log_file),
    ]

    if setup_env:
        base_cmd.append("--setup-env")

    if benches:
        base_cmd.extend(["--benches"] + benches)

    for p in params:
        base_cmd.extend(["--set-param", p])


    print(f"\n=== Running config: {tag} ===")
    print("Command:", " ".join(base_cmd))
    print(f"Working directory: {PROJECT_ROOT}")

    try:
        subprocess.run(base_cmd, check=True, cwd=PROJECT_ROOT)
        print(f"[OK] {tag} finished successfully.")
        print(f"    Result: {result_file}")
        print(f"    Log:    {log_file}")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {tag} failed with code {e.returncode}")
        print(f"    Check log: {log_file}")


def main():
    print(f"[INFO] Starting test batch from {PROJECT_ROOT}")
    print(f"[INFO] Logs → {LOG_DIR}")
    print(f"[INFO] Results → {RES_DIR}")

    for bench_set_name, param_set_name, setup_env in pairs:
        benches = bench_sets[bench_set_name]
        params = param_sets[param_set_name]
        tag = f"{param_set_name}"
        run_benchmark_set(tag, benches, params, setup_env)

    print("\n[INFO] All tests finished.")


if __name__ == "__main__":
    main()
