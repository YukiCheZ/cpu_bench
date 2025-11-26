#!/usr/bin/env python3
import subprocess
import sys
from datetime import datetime
from pathlib import Path
import json
import shutil

ROOT = Path(__file__).resolve().parent              
PROJECT_ROOT = ROOT.parent                          
RUN_CPU = PROJECT_ROOT / "scripts" / "run_cpu.py"
LOG_DIR = PROJECT_ROOT / "log"
RES_DIR = PROJECT_ROOT / "res"
SYSTEM_INFO_FILE = RES_DIR / "system_info.json"

LOG_DIR.mkdir(parents=True, exist_ok=True)
RES_DIR.mkdir(parents=True, exist_ok=True)

workloads_sets = {
    "python": [
        "numpy_benchmark.matmul", 
        "numpy_benchmark.svd",
        "numpy_benchmark.fft", 
        "tuf_benchmark.tuf-metadata", 
        "requests_benchmark.requests-json", 
        "raytrace.raytrace",
        "chaos_fractal.chaos-fractal", 
        "deltablue.deltablue",
        "pyflate.pyflate", 
        "go_board_game.go-board-game",
        "resnet50_cpu.resnet50_inference", 
        "resnet50_cpu.resnet50_training",
        "bert_cpu.bert_eval", 
        "transformer_inference.transformer_inference",
        "transformer_train.transformer_train",
    ],
    "c": [
        "redis_benchmark.redis-benchmark", 
        "ffmpeg_benchmark.ffmpeg",
        "openssl_benchmark.openssl", 
        "zstd_benchmark.zstd",
        "c_compiler_benchmark.gcc_compile", 
        "c_compiler_benchmark.clang_compile", 
        "lapack_benchmark.lapack_solve",
        "lapack_benchmark.lapack_eigen", 
        "lapack_benchmark.lapack_svd",
    ],
    "cpp" : [
        "rocksdb_benchmark.rocksdb_cpu", 
        "opencv_benchmark.fft_batch",
        "opencv_benchmark.conv_heavy", 
        "opencv_benchmark.motion_blur",
        "opencv_benchmark.background_sub",
        "opencv_benchmark.mandelbrot",
        "opencv_benchmark.jacobi",
        "opencv_benchmark.canny",
        "opencv_benchmark.optical_flow",
        "opencv_benchmark.color_tracking",
        "opencv_benchmark.feature_match",
    ],
    "go" : [
        "biogo-benchmark.biogo-igor", 
        "bleve_benchmark.bleve-index",
        "cockroachdb_benchmark.kv", 
        "cockroachdb_benchmark.tpcc",
        "esbuild_benchmark.ThreeJS",
        "esbuild_benchmark.RomeTS",
        "gc_garbage.gc_garbage",
        "go_compiler.go_compiler",
        "gopher_lua.gopher_lua",
        "go_json.json",
        "go_markdown.markdown_render",
        "tile38_sim.kdtree",

    ],
    "java": [
        "cassandra_benchmark.cassandra_stress_read",
        "kafka_benchmark.kafka_producer_perf",
        "guava_benchmark.guava_event",
        "guava_benchmark.guava_cache",
        "guava_benchmark.guava_graph",
        "guava_benchmark.guava_bloom",
        "guava_benchmark.guava_immutable",
        "smile_benchmark.smile_kmeans",
    ],
    "basic": [
        "numpy_benchmark.matmul", 
        "numpy_benchmark.svd",
        "numpy_benchmark.fft", 
        "tuf_benchmark.tuf-metadata", 
        "requests_benchmark.requests-json", 
        "raytrace.raytrace",
        "chaos_fractal.chaos-fractal", 
        "deltablue.deltablue",
        "pyflate.pyflate", 
        "go_board_game.go-board-game",
        "resnet50_cpu.resnet50_inference", 
        "resnet50_cpu.resnet50_training",
        "bert_cpu.bert_eval", 
        "transformer_inference.transformer_inference",

        "redis_benchmark.redis-benchmark", 
        "openssl_benchmark.openssl", 
        "zstd_benchmark.zstd",
        "c_compiler_benchmark.gcc_compile", 
        "c_compiler_benchmark.clang_compile", 
        "lapack_benchmark.lapack_solve",
        "lapack_benchmark.lapack_eigen", 
        "lapack_benchmark.lapack_svd",
        
        "opencv_benchmark.fft_batch",
        "opencv_benchmark.conv_heavy", 
        "opencv_benchmark.motion_blur",
        "opencv_benchmark.background_sub",
        "opencv_benchmark.mandelbrot",
        "opencv_benchmark.jacobi",
        "opencv_benchmark.canny",
        "opencv_benchmark.optical_flow",
        "opencv_benchmark.color_tracking",
        "opencv_benchmark.feature_match",

        "biogo-benchmark.biogo-igor", 
        "bleve_benchmark.bleve-index",
        "cockroachdb_benchmark.kv", 
        "esbuild_benchmark.ThreeJS",
        "esbuild_benchmark.RomeTS",
        "gc_garbage.gc_garbage",
        "go_compiler.go_compiler",
        "gopher_lua.gopher_lua",
        "go_json.json",
        "go_markdown.markdown_render",
        "tile38_sim.kdtree",

        "cassandra_benchmark.cassandra_stress_read",
        "guava_benchmark.guava_event",
        "guava_benchmark.guava_cache",
        "guava_benchmark.guava_graph",
        "guava_benchmark.guava_bloom",
        "guava_benchmark.guava_immutable",
        "smile_benchmark.smile_kmeans",
    ],
    "emerging":[
        "transformer_train.transformer_train",

        "ffmpeg_benchmark.ffmpeg",

        "rocksdb_benchmark.rocksdb_cpu", 

        "cockroachdb_benchmark.tpcc",

        "kafka_benchmark.kafka_producer_perf",
    ],
    "all": [
        "numpy_benchmark.matmul", 
        "numpy_benchmark.svd",
        "numpy_benchmark.fft", 
        "tuf_benchmark.tuf-metadata", 
        "requests_benchmark.requests-json", 
        "raytrace.raytrace",
        "chaos_fractal.chaos-fractal", 
        "deltablue.deltablue",
        "pyflate.pyflate", 
        "go_board_game.go-board-game",
        "resnet50_cpu.resnet50_inference", 
        "resnet50_cpu.resnet50_training",
        "bert_cpu.bert_eval", 
        "transformer_inference.transformer_inference",
        "transformer_train.transformer_train",
        "redis_benchmark.redis-benchmark", 
        "ffmpeg_benchmark.ffmpeg",
        "openssl_benchmark.openssl", 
        "zstd_benchmark.zstd",
        "c_compiler_benchmark.gcc_compile", 
        "c_compiler_benchmark.clang_compile", 
        "lapack_benchmark.lapack_solve",
        "lapack_benchmark.lapack_eigen", 
        "lapack_benchmark.lapack_svd",
        "rocksdb_benchmark.rocksdb_cpu", 
        "opencv_benchmark.fft_batch",
        "opencv_benchmark.conv_heavy", 
        "opencv_benchmark.motion_blur",
        "opencv_benchmark.background_sub",
        "opencv_benchmark.mandelbrot",
        "opencv_benchmark.jacobi",
        "opencv_benchmark.canny",
        "opencv_benchmark.optical_flow",
        "opencv_benchmark.color_tracking",
        "opencv_benchmark.feature_match",
        "biogo-benchmark.biogo-igor", 
        "bleve_benchmark.bleve-index",
        "cockroachdb_benchmark.kv", 
        "cockroachdb_benchmark.tpcc",
        "esbuild_benchmark.ThreeJS",
        "esbuild_benchmark.RomeTS",
        "gc_garbage.gc_garbage",
        "go_compiler.go_compiler",
        "gopher_lua.gopher_lua",
        "go_json.json",
        "go_markdown.markdown_render",
        "tile38_sim.kdtree",
        "cassandra_benchmark.cassandra_stress_read",
        "kafka_benchmark.kafka_producer_perf",
        "guava_benchmark.guava_event",
        "guava_benchmark.guava_cache",
        "guava_benchmark.guava_graph",
        "guava_benchmark.guava_bloom",
        "guava_benchmark.guava_immutable",
        "smile_benchmark.smile_kmeans",
    ]
}

# 2
data_augmentation_params = [
    "numpy_benchmark.matmul.workload.size=4096",
    "numpy_benchmark.svd.workload.size=1126",
    "numpy_benchmark.fft.workload.size=4194304",
    "tuf_benchmark.tuf-metadata.data.size=375809638",
    "requests_benchmark.requests-json.workload.size=170394",
    "raytrace.raytrace.workload.width=2662",
    "raytrace.raytrace.workload.height=2458",
    "chaos_fractal.chaos-fractal.data.width=2253",
    "chaos_fractal.chaos-fractal.data.height=4096",
    "deltablue.deltablue.workload.n=180000",
    "pyflate.pyflate.data.size=5500000",
    "go_board_game.go-board-game.workload.size=190",
    "resnet50_cpu.resnet50_inference.data.batch_size=3",
    "resnet50_cpu.resnet50_training.data.batch_size=2",
    "bert_cpu.bert_eval.data.batch_size=4",
    "transformer_inference.transformer_inference.data.batch_size=4",
    "transformer_train.transformer_train.data.batch_size=3",
    "c_compiler_benchmark.gcc_compile.data.func_size=130",
    "c_compiler_benchmark.clang_compile.data.func_size=180",
    "ffmpeg_benchmark.ffmpeg.data.duration=456",
    "lapack_benchmark.lapack_solve.workload.size=1024",
    "lapack_benchmark.lapack_eigen.workload.size=1843",
    "lapack_benchmark.lapack_svd.workload.size=1331",
    "openssl_benchmark.openssl.data.size=50",
    "redis_benchmark.redis-benchmark.workload.requests=3600000",
    "zstd_benchmark.zstd.data.size=40",
    "rocksdb_benchmark.rocksdb_cpu.workload.num=2600000",
    "opencv_benchmark.background_sub.workload.size=918",
    "opencv_benchmark.mandelbrot.workload.size=973",
    "opencv_benchmark.jacobi.workload.size=1434",
    "opencv_benchmark.canny.workload.size=1024",
    "opencv_benchmark.optical_flow.workload.size=614",
    "opencv_benchmark.color_tracking.workload.size=1728",
    "opencv_benchmark.feature_match.workload.size=768",
    "opencv_benchmark.fft_batch.workload.size=717",
    "opencv_benchmark.conv_heavy.workload.size=614",
    "opencv_benchmark.motion_blur.workload.size=1331",
    "biogo-benchmark.biogo-igor.workload.seq=75000",
    "bleve_benchmark.bleve-index.workload.documents=2200",
    "cockroachdb_benchmark.kv.workload.max-ops=660000",
    "cockroachdb_benchmark.tpcc.workload.max-ops=24000",
    "esbuild_benchmark.ThreeJS.data.complexity=1100",
    "esbuild_benchmark.RomeTS.data.complexity=1500",
    "gc_garbage.gc_garbage.data.size=75000",
    "go_compiler.go_compiler.data.complex=190",
    "gopher_lua.gopher_lua.data.size=700000",
    "go_json.json.data.size=25",
    "go_markdown.markdown_render.data.size=850",
    "tile38_sim.kdtree.workload.points=90000",
    "cassandra_benchmark.cassandra_stress_read.workload.write-n=1100000",
    "cassandra_benchmark.cassandra_stress_read.workload.read-n=1600000",
    "kafka_benchmark.kafka_producer_perf.workload.num-records=770000000",
    "guava_benchmark.guava_event.workload.dataSize=180000",
    "guava_benchmark.guava_cache.workload.dataSize=70000",
    "guava_benchmark.guava_graph.workload.dataSize=400000",
    "guava_benchmark.guava_bloom.workload.dataSize=380000",
    "guava_benchmark.guava_immutable.workload.dataSize=300000",
    "smile_benchmark.smile_kmeans.data.samples=95000",
    "smile_benchmark.smile_kmeans.data.features=65",
]

# 3
compiler_env_params = [
    "ffmpeg_benchmark._.setup.compiler=clang",
    "lapack_benchmark._.setup.compiler=clang",
    "openssl_benchmark._.setup.compiler=clang",
    "rocksdb_benchmark._.setup.compiler=clang",
    "opencv_benchmark._.setup.compiler=clang",
]

# 4
opt_env_params = [
    "ffmpeg_benchmark._.setup.opt=-O1",
    "lapack_benchmark._.setup.opt=-O2",
    "openssl_benchmark._.setup.opt=-O2",
    "redis_benchmark._.setup.opt=-O2",
    "zstd_benchmark._.setup.opt=-O3",
    "c_compiler_benchmark.gcc_compile.workload.opt=O2",
    "c_compiler_benchmark.clang_compile.workload.opt=O1",
    "rocksdb_benchmark._.setup.opt=-O2",
    "opencv_benchmark._.setup.opt=-O2",
]

# 5
threads_param = [
    "numpy_benchmark.matmul.workload.threads=8",
    "numpy_benchmark.svd.workload.threads=40",
    "numpy_benchmark.fft.workload.threads=10",
    "tuf_benchmark.tuf-metadata.workload.threads=50",
    "requests_benchmark.requests-json.workload.threads=64",
    "raytrace.raytrace.workload.threads=40",
    "chaos_fractal.chaos-fractal.workload.threads=40",
    "deltablue.deltablue.workload.threads=2",
    "pyflate.pyflate.workload.threads=32",
    "go_board_game.go-board-game.workload.threads=40",
    "resnet50_cpu.resnet50_inference.workload.threads=4",
    "resnet50_cpu.resnet50_training.workload.threads=30",
    "bert_cpu.bert_eval.workload.threads=50",
    "transformer_inference.transformer_inference.workload.threads=8",
    "transformer_train.transformer_train.workload.threads=4",
    "c_compiler_benchmark.gcc_compile.workload.threads=28",
    "c_compiler_benchmark.clang_compile.workload.threads=20",
    "ffmpeg_benchmark.ffmpeg.workload.threads=10",
    "lapack_benchmark.lapack_solve.workload.threads=64",
    "lapack_benchmark.lapack_eigen.workload.threads=40",
    "lapack_benchmark.lapack_svd.workload.threads=50",
    "openssl_benchmark.openssl.workload.threads=30",
    "redis_benchmark.redis-benchmark.workload.threads=8",
    "zstd_benchmark.zstd.workload.threads=40",
    "rocksdb_benchmark.rocksdb_cpu.workload.threads=16",
    "opencv_benchmark.background_sub.workload.threads=60",
    "opencv_benchmark.mandelbrot.workload.threads=56",
    "opencv_benchmark.jacobi.workload.threads=56",
    "opencv_benchmark.canny.workload.threads=1",
    "opencv_benchmark.optical_flow.workload.threads=8",
    "opencv_benchmark.color_tracking.workload.threads=60",
    "opencv_benchmark.feature_match.workload.threads=1",
    "opencv_benchmark.fft_batch.workload.threads=56",
    "opencv_benchmark.conv_heavy.workload.threads=16",
    "opencv_benchmark.motion_blur.workload.threads=20",
    "biogo-benchmark.biogo-igor.workload.threads=10",
    "bleve_benchmark.bleve-index.workload.threads=2",
    "cockroachdb_benchmark.kv.workload.threads=8",
    "cockroachdb_benchmark.tpcc.workload.threads=64",
    "esbuild_benchmark.ThreeJS.workload.threads=32",
    "esbuild_benchmark.RomeTS.workload.threads=64",
    "gc_garbage.gc_garbage.workload.threads=50",
    "go_compiler.go_compiler.workload.threads=16",
    "gopher_lua.gopher_lua.workload.threads=8",
    "go_json.json.workload.threads=40",
    "go_markdown.markdown_render.workload.threads=28",
    "tile38_sim.kdtree.workload.threads=20",
    "cassandra_benchmark.cassandra_stress_read.workload.threads=64",
    "kafka_benchmark.kafka_producer_perf.workload.threads=64",
    "guava_benchmark.guava_event.workload.threads=40",
    "guava_benchmark.guava_cache.workload.threads=28",
    "guava_benchmark.guava_graph.workload.threads=4",
    "guava_benchmark.guava_bloom.workload.threads=10",
    "guava_benchmark.guava_immutable.workload.threads=4",
    "smile_benchmark.smile_kmeans.workload.threads=8",
]

param_sets = {
    "v0.0.1": data_augmentation_params + compiler_env_params + opt_env_params + threads_param,
}

pairs = [
    ("all",        "v0.0.1",    True),
]


def run_cmd(cmd):
    """Run a command and return its output as list of lines."""
    try:
        out = subprocess.check_output(cmd, shell=True, text=True)
        return out.strip().split("\n")
    except Exception:
        return []

def parse_key_value_lines(lines):
    """Parse lines like 'Key: Value' into dict."""
    data = {}
    for ln in lines:
        if ":" in ln:
            k, v = ln.split(":", 1)
            data[k.strip()] = v.strip()
    return data

def collect_system_info():
    sysinfo = {}

    lscpu_lines = run_cmd("lscpu")
    sysinfo["cpu"] = parse_key_value_lines(lscpu_lines)

    meminfo_lines = run_cmd("cat /proc/meminfo")
    sysinfo["memory"] = parse_key_value_lines(meminfo_lines)

    osrelease_lines = run_cmd("cat /etc/os-release")
    sysinfo["os"] = parse_key_value_lines(osrelease_lines)

    sysinfo["uname"] = run_cmd("uname -a")

    sysinfo["software"] = {
        "gcc_version": run_cmd("gcc --version"),
        "clang_version": run_cmd("clang --version"),
        "python_version": run_cmd("python3 --version"),
        "java_version": run_cmd("java --version"),
        "go_version": run_cmd("go version"),
    }

    if shutil.which("dmidecode"):
        cpu_detail = run_cmd("sudo dmidecode -t processor")
        mem_detail = run_cmd("sudo dmidecode -t memory")
        sysinfo["dmidecode"] = {
            "processor": cpu_detail,
            "memory": mem_detail
        }

    return sysinfo


def save_system_info_json(path):
    info = collect_system_info()
    with open(path, "w") as f:
        json.dump(info, f, indent=2)   


def write_system_info_json(output_path):
    """Write collected system info to JSON file."""
    info = collect_system_info()
    with open(output_path, "w") as f:
        json.dump(info, f, indent=4)


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
        # "--use-perf"
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
    print(f"[INFO] System info → {SYSTEM_INFO_FILE}")

    write_system_info_json(SYSTEM_INFO_FILE)

    # for workloads_set_name, param_set_name, setup_env in pairs:
    #     workloads = workloads_sets[workloads_set_name]
    #     params = param_sets[param_set_name]
    #     tag = f"{param_set_name}"
    #     run_workloads_set(tag, workloads, params, setup_env)

    print("\n[INFO] All tests finished.")


if __name__ == "__main__":
    main()
