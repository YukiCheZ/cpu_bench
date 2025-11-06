#!/usr/bin/env python3
import subprocess
import sys
from datetime import datetime
from pathlib import Path
import random
import json

random.seed(42)

ROOT = Path(__file__).resolve().parent              
PROJECT_ROOT = ROOT.parent                          
RUN_CPU = PROJECT_ROOT / "scripts" / "run_cpu_env.py"
LOG_DIR = ROOT / "log"
RES_DIR = ROOT / "res"

LOG_DIR.mkdir(parents=True, exist_ok=True)
RES_DIR.mkdir(parents=True, exist_ok=True)

bench_sets = {
    "test_python": [
        "tuf_benchmark", "raytrace", "transformer_inference", "bert_cpu", "resnet50_cpu"
    ],
    "test_c": [
        "redis_benchmark", "ffmpeg_benchmark", "openssl_benchmark", "c_compiler_benchmark", "zstd_benchmark"
    ],
    "test": [
        "tuf_benchmark", "raytrace", "transformer_inference", "bert_cpu", "resnet50_cpu",
        "redis_benchmark", "ffmpeg_benchmark", "openssl_benchmark", "c_compiler_benchmark", "zstd_benchmark",
    ]
}

workloads_sets = {
    "cpp_test" : [
        "rocksdb_benchmark.rocksdb_cpu", "opencv_benchmark.fft_batch",
        "opencv_benchmark.conv_heavy", "opencv_benchmark.motion_blur",
        "opencv_benchmark.background_sub"
    ]
}

data_params = [
    # "c_compiler_benchmark.gcc_compile.data.func_size=100",
    # "c_compiler_benchmark.clang_compile.data.func_size=100",
    # "ffmpeg_benchmark.ffmpeg.data.duration=240",
    # "openssl_benchmark.openssl.data.size=25",
    # "redis_benchmark.redis-benchmark.workload.requests=2000000",
    # "zstd_benchmark.zstd.data.size=25",

    # "tuf_benchmark.tuf-metadata.data.size=268435456",
    # "raytrace.raytrace.workload.width=2048",
    # "raytrace.raytrace.workload.height=2048",
    # "resnet50_cpu.resnet50_inference.data.batch_size=2",
    # "resnet50_cpu.resnet50_training.data.batch_size=2",
    # "bert_cpu.bert_eval.data.batch_size=4",
    # "transformer_inference.transformer_inference.data.batch_size=4",
    # "transformer_train.transformer_train.data.batch_size=2",

    "rocksdb_benchmark.rocksdb_cpu.workload.num=2000000",
    "opencv_benchmark.fft_batch.workload.size=512",
    "opencv_benchmark.conv_heavy.workload.size=512",
    "opencv_benchmark.motion_blur.workload.size=1024",
    "opencv_benchmark.background_sub.workload.size=540"
]

compiler_params = [
    # "ffmpeg_benchmark._.setup.compiler=clang",
    # "openssl_benchmark._.setup.compiler=clang",
    # "zstd_benchmark._.setup.compiler=clang",

    "rocksdb_benchmark._.setup.compiler=clang",
    "opencv_benchmark._.setup.compiler=clang"
]

opt_params = [
    # "ffmpeg_benchmark._.setup.opt=-O1",
    # "openssl_benchmark._.setup.opt=-O1",
    # "redis_benchmark._.setup.opt=-O1",
    # "zstd_benchmark._.setup.opt=-O1",
    # "c_compiler_benchmark.gcc_compile.workload.opt=-O1",
    # "c_compiler_benchmark.clang_compile.workload.opt=-O1",

    # "resnet50_cpu.resnet50_inference.workload.compile",
    # "resnet50_cpu.resnet50_training.workload.compile",
    # "bert_cpu.bert_eval.workload.compile",
    # "transformer_inference.transformer_inference.workload.compile",
    # "transformer_train.transformer_train.workload.compile",

    "rocksdb_benchmark._.setup.opt=-O1",
    "opencv_benchmark._.setup.opt=-O1"
]

threads_param = [
    # "c_compiler_benchmark.gcc_compile.workload.threads=28",
    # "c_compiler_benchmark.clang_compile.workload.threads=28",
    # "ffmpeg_benchmark.ffmpeg.workload.threads=28",
    # "openssl_benchmark.openssl.workload.threads=28",
    # "redis_benchmark.redis-benchmark.workload.threads=28",
    # "zstd_benchmark.zstd.workload.threads=28",

    # "tuf_benchmark.tuf-metadata.workload.threads=28",
    # "raytrace.raytrace.workload.threads=28",
    # "resnet50_cpu.resnet50_inference.workload.threads=28",
    # "resnet50_cpu.resnet50_training.workload.threads=28",
    # "bert_cpu.bert_eval.workload.threads=28",
    # "transformer_inference.transformer_inference.workload.threads=28",
    # "transformer_train.transformer_train.workload.threads=28",

    "rocksdb_benchmark.rocksdb_cpu.workload.threads=28",
    "opencv_benchmark.fft_batch.workload.threads=28",
    "opencv_benchmark.conv_heavy.workload.threads=28",
    "opencv_benchmark.motion_blur.workload.threads=28",
    "opencv_benchmark.background_sub.workload.threads=28"
]

def random_select_config_by_load(config_list):
    load_configs = {}

    def get_load_name(cfg):
        parts = cfg.split(".")
        return ".".join(parts[:2])

    for config in config_list:
        load_name = get_load_name(config)
        load_configs.setdefault(load_name, []).append(config)

    selected_config = []
    for load_name, configs in sorted(load_configs.items()):
        if random.choice([True, False]):  
            selected_config.extend(configs)

    return selected_config


def get_lab_config(round_nums):
    param_sets = {}
    for i in range(round_nums):
        config_tags = f"round_{i+1}"
        selected_data_params = random_select_config_by_load(data_params)
        selected_compiler_params = random_select_config_by_load(compiler_params)
        selected_opt_params = random_select_config_by_load(opt_params)
        selected_threads_params = random_select_config_by_load(threads_param)
        round_config = selected_data_params + selected_compiler_params + selected_opt_params + selected_threads_params
        round_config.sort(key=lambda x: ".".join(x.split(".")[:2]))

        param_sets[config_tags] = round_config
    return param_sets

param_sets = get_lab_config(10)

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
with open(LOG_DIR / f"generated_params_{timestamp}.json", "w") as f:
    json.dump(param_sets, f, indent=2)

pairs = [
    ("cpp_test", "round_1", True),
    ("cpp_test", "round_2", True),
    ("cpp_test", "round_3", True),
    ("cpp_test", "round_4", True),
    ("cpp_test", "round_5", True),
    ("cpp_test", "round_6", True),
    ("cpp_test", "round_7", True),
    ("cpp_test", "round_8", True),
    ("cpp_test", "round_9", True),
    ("cpp_test", "round_10", True)
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


def run_workloads_set(tag: str, workloads: list[str], params: list[str], setup_env: bool = False):
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

    if workloads:
        base_cmd.extend(["--workloads"] + workloads)

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

    # for bench_set_name, param_set_name, setup_env in pairs:
    #     benches = bench_sets[bench_set_name]
    #     params = param_sets[param_set_name]
    #     tag = f"{param_set_name}"
    #     run_benchmark_set(tag, benches, params, setup_env)

    for workloads_set_name, param_set_name, setup_env in pairs:
        workloads = workloads_sets[workloads_set_name]
        params = param_sets[param_set_name]
        tag = f"{param_set_name}"
        run_workloads_set(tag, workloads, params, setup_env)

    print("\n[INFO] All tests finished.")


if __name__ == "__main__":
    main()
