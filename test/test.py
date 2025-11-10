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
    ],
    "c_all": [
        "redis_benchmark", "zstd_benchmark", "openssl_benchmark", 
        "ffmpeg_benchmark", 
        # "lapack_benchmark", "c_compiler_benchmark"
    ]
}

workloads_sets = {
    "python_test": [
        "tuf_benchmark.tuf-metadata", "raytrace.raytrace",
        "transformer_inference.transformer_inference",
        "bert_cpu.bert_eval", "resnet50_cpu.resnet50_inference",
        "resnet50_cpu.resnet50_training", "pyflate.pyflate",
    ],
    "c_test": [
        "redis_benchmark.redis-benchmark", "ffmpeg_benchmark.ffmpeg",
        "openssl_benchmark.openssl", "c_compiler_benchmark.gcc_compile",
        "c_compiler_benchmark.clang_compile", "zstd_benchmark.zstd",
    ],
    "cpp_test" : [
        "rocksdb_benchmark.rocksdb_cpu", 
        # "opencv_benchmark.fft_batch",
        # "opencv_benchmark.conv_heavy", 
        # "opencv_benchmark.motion_blur",
        "opencv_benchmark.background_sub",
    ],
    "go_test" : [
        "biogo-benchmark.biogo-igor", "bleve_benchmark.bleve-index",
        "cockroachdb_benchmark.kv", "cockroachdb_benchmark.tpcc",
    ],
    "java_test": [
        "cassandra_benchmark.cassandra_stress_read",
        "kafka_benchmark.kafka_producer_perf",
    ],
    "test": [
        # "tuf_benchmark.tuf-metadata", "raytrace.raytrace",
        # "transformer_inference.transformer_inference",
        # "bert_cpu.bert_eval", "resnet50_cpu.resnet50_inference",
        # "resnet50_cpu.resnet50_training", "pyflate.pyflate",

        # "redis_benchmark.redis-benchmark", "ffmpeg_benchmark.ffmpeg",
        # "openssl_benchmark.openssl", "zstd_benchmark.zstd",
        # "c_compiler_benchmark.gcc_compile", "c_compiler_benchmark.clang_compile", 
        
        "rocksdb_benchmark.rocksdb_cpu", 
        # "opencv_benchmark.fft_batch", "opencv_benchmark.conv_heavy",
        # "opencv_benchmark.motion_blur", 
        "opencv_benchmark.background_sub",

        # "biogo-benchmark.biogo-igor", 
        "bleve_benchmark.bleve-index",
        "cockroachdb_benchmark.kv", 
        # "cockroachdb_benchmark.tpcc",

        "cassandra_benchmark.cassandra_stress_read",
        "kafka_benchmark.kafka_producer_perf",
    ]
}

# 3
c_compiler_env_params = [
    # "ffmpeg_benchmark._.setup.compiler=clang",
    # "lapack_benchmark._.setup.compiler=clang",
    # "openssl_benchmark._.setup.compiler=clang",
    # # "redis_benchmark._.setup.compiler=clang",
    # "zstd_benchmark._.setup.compiler=clang",

    "rocksdb_benchmark._.setup.compiler=clang",
    "opencv_benchmark._.setup.compiler=clang",
]

# 4
c_opt_env_params = [
    # "ffmpeg_benchmark._.setup.opt=-O1",
    # "lapack_benchmark._.setup.opt=-O1",
    # "openssl_benchmark._.setup.opt=-O1",
    # "redis_benchmark._.setup.opt=-O1",
    # "zstd_benchmark._.setup.opt=-O1",
    # "c_compiler_benchmark.gcc_compile.workload.opt=O1",
    # "c_compiler_benchmark.clang_compile.workload.opt=O1",

    "rocksdb_benchmark._.setup.opt=-O1",
    "opencv_benchmark._.setup.opt=-O1",
]

# 2
c_data_augmentation_params = [
    # "c_compiler_benchmark.gcc_compile.data.func_size=100",
    # "c_compiler_benchmark.clang_compile.data.func_size=100",
    # "ffmpeg_benchmark.ffmpeg.data.duration=240",
    # "lapack_benchmark.lapack_solve.workload.size=1024",
    # "lapack_benchmark.lapack_eigen.workload.size=1024",
    # "lapack_benchmark.lapack_svd.workload.size=1024",
    # "openssl_benchmark.openssl.data.size=25",
    # "redis_benchmark.redis-benchmark.workload.requests=2000000",
    # "zstd_benchmark.zstd.data.size=25"

    "rocksdb_benchmark.rocksdb_cpu.workload.num=2000000",
    "opencv_benchmark.background_sub.workload.size=540",

    "bleve_benchmark.bleve-index.workload.documents=2000",
    "cockroachdb_benchmark.kv.workload.max-ops=600000",

    "cassandra_benchmark.cassandra_stress_read.workload.write-n=1000000",
    "cassandra_benchmark.cassandra_stress_read.workload.read-n=1000000",
    "kafka_benchmark.kafka_producer_perf.workload.num-records=700000000",
]

# 5
c_threads_param = [
    # "c_compiler_benchmark.gcc_compile.workload.threads=28",
    # "c_compiler_benchmark.clang_compile.workload.threads=28",
    # "ffmpeg_benchmark.ffmpeg.workload.threads=28",
    # "lapack_benchmark.lapack_solve.workload.threads=28",
    # "lapack_benchmark.lapack_eigen.workload.threads=28",
    # "lapack_benchmark.lapack_svd.workload.threads=28",
    # "openssl_benchmark.openssl.workload.threads=28",
    # "redis_benchmark.redis-benchmark.workload.threads=28",
    # "zstd_benchmark.zstd.workload.threads=28",

    "rocksdb_benchmark.rocksdb_cpu.workload.threads=28",
    "opencv_benchmark.background_sub.workload.threads=28",

    "bleve_benchmark.bleve-index.workload.threads=28",
    "cockroachdb_benchmark.kv.workload.threads=28",    

    "cassandra_benchmark.cassandra_stress_read.workload.threads=28",
    "kafka_benchmark.kafka_producer_perf.workload.threads=28",
]

python_data_augmentation_params = [
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

python_threads_param = [
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

python_opt_params = [
    "resnet50_cpu.resnet50_inference.workload.compile",
    "resnet50_cpu.resnet50_training.workload.compile",
    "bert_cpu.bert_eval.workload.compile",
    "transformer_inference.transformer_inference.workload.compile",
    "transformer_train.transformer_train.workload.compile"
]

param_sets = {
    "ex_p": [],
    "ex_p2": c_data_augmentation_params,
    "ex_p3": c_compiler_env_params,
    "ex_p4": c_opt_env_params,
    "ex_p5": c_threads_param,
    "ex_p23": c_data_augmentation_params + c_compiler_env_params,
    "ex_p24": c_data_augmentation_params + c_opt_env_params,
    "ex_p25": c_data_augmentation_params + c_threads_param,
    "ex_p34": c_compiler_env_params + c_opt_env_params,
    "ex_p35": c_compiler_env_params + c_threads_param,
    "ex_p45": c_opt_env_params + c_threads_param,
    "ex_p234": c_data_augmentation_params + c_compiler_env_params + c_opt_env_params,
    "ex_p235": c_data_augmentation_params + c_compiler_env_params + c_threads_param,
    "ex_p245": c_data_augmentation_params + c_opt_env_params + c_threads_param,
    "ex_p345": c_compiler_env_params + c_opt_env_params + c_threads_param,
    "ex_p2345": c_data_augmentation_params + c_compiler_env_params + c_opt_env_params + c_threads_param,
}

pairs = [
    ("test",        "ex_p", True),
    ("test",        "ex_p2", True),
    ("cpp_test",    "ex_p3", True),
    ("cpp_test",    "ex_p4", True),
    ("test",        "ex_p5", True),
    ("cpp_test",    "ex_p23", True),
    ("cpp_test",    "ex_p24", True),
    ("test",        "ex_p25", True),
    ("cpp_test",    "ex_p34", True),
    ("cpp_test",    "ex_p35", True),
    ("cpp_test",    "ex_p45", True),
    ("cpp_test",    "ex_p234", True),
    ("cpp_test",    "ex_p235", True),
    ("cpp_test",    "ex_p245", True),
    ("cpp_test",    "ex_p345", True),
    ("cpp_test",    "ex_p2345", True)
]

# param_sets = {
#     "py_p": [],
#     "py_p2": python_data_augmentation_params,
#     "py_p4": python_opt_params,
#     "py_p5": python_threads_param,
#     "py_p24": python_data_augmentation_params + python_opt_params,
#     "py_p25": python_data_augmentation_params + python_threads_param,
#     "py_p45": python_opt_params + python_threads_param,
#     "py_p245": python_data_augmentation_params + python_opt_params + python_threads_param
# }

# pairs = [
#     ("python_all", "py_p", True),
#     ("python_all", "py_p2", False),
#     ("python_ml", "py_p4", False),
#     ("python_all", "py_p5", False),
#     ("python_ml", "py_p24", False),
#     ("python_all", "py_p25", False),
#     ("python_ml", "py_p45", False),
#     ("python_ml", "py_p245", False)
# ]


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

    for workloads_set_name, param_set_name, setup_env in pairs:
        workloads = workloads_sets[workloads_set_name]
        params = param_sets[param_set_name]
        tag = f"{param_set_name}"
        run_workloads_set(tag, workloads, params, setup_env)

    print("\n[INFO] All tests finished.")


if __name__ == "__main__":
    main()
