#!/usr/bin/env python3
import subprocess
import time
import os
from pathlib import Path
import argparse
import socket
from concurrent.futures import ProcessPoolExecutor, as_completed

# ================= Default Configuration =================
KAFKA_VERSION = "3.8.0"
SCALA_VERSION = "2.13"
KAFKA_HOME = f"./bin/kafka_{SCALA_VERSION}-{KAFKA_VERSION}"
TOPIC = "perf-test"
NUM_PARTITIONS = 12
THROUGHPUT = -1
CONSUMER_GROUP = "perf-consumer"

RAMDISK_DIR = Path("/tmp/kafka_ramdisk")
TMP_DIR = Path("/tmp/kafka_tmp")
KAFKA_LOG_DIR = Path(KAFKA_HOME + "/logs")

RAMDISK_DIR.mkdir(parents=True, exist_ok=True)
TMP_DIR.mkdir(parents=True, exist_ok=True)

os.environ["JAVA_OPTS"] = (
    f"-Djava.io.tmpdir={TMP_DIR} "
    f"-XX:ActiveProcessorCount=1 "
    f"-XX:+UseSerialGC"
)

# ================= Helper Function =================
def run_cmd(cmd, ignore_output=True):
    if ignore_output:
        result = subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            print(f"[ERROR] Command failed: {cmd}\n{result.stderr}")
        return result.returncode
    else:
        result = subprocess.run(cmd, shell=True)
        return result.returncode

# ================= Kafka Control =================
def wait_for_kafka_ready(host="localhost", port=9092, timeout=30):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                print(f"[INFO] Kafka broker is ready at {host}:{port}")
                return True
        except OSError:
            time.sleep(1)
    print(f"[ERROR] Kafka broker not ready after {timeout} seconds.")
    return False


def start_kafka():
    print("[INFO] Starting Zookeeper...")
    run_cmd(f"{KAFKA_HOME}/bin/zookeeper-server-start.sh -daemon {KAFKA_HOME}/config/zookeeper.properties")
    time.sleep(5)

    print("[INFO] Starting Kafka Broker with RAM disk log...")
    server_properties = Path(KAFKA_HOME) / "config/server.properties"
    backup = server_properties.with_suffix(".properties.bak")
    if not backup.exists():
        server_properties.rename(backup)
        content = backup.read_text()
        content = content.replace("log.dirs=/tmp/kafka-logs", f"log.dirs={RAMDISK_DIR}")
        server_properties.write_text(content)

    run_cmd(f"{KAFKA_HOME}/bin/kafka-server-start.sh -daemon {server_properties}")

    print("[INFO] Waiting for Kafka to become ready...")
    if not wait_for_kafka_ready("localhost", 9092, timeout=60):
        raise RuntimeError("Kafka broker failed to start.")

def stop_kafka():
    print("[INFO] Stopping Kafka Broker...")
    run_cmd(f"{KAFKA_HOME}/bin/kafka-server-stop.sh")
    time.sleep(2)
    print("[INFO] Stopping Zookeeper...")
    run_cmd(f"{KAFKA_HOME}/bin/zookeeper-server-stop.sh")
    time.sleep(2)

    print("[INFO] Cleaning up log directories...")
    for d in [RAMDISK_DIR, TMP_DIR, KAFKA_LOG_DIR]:
        for item in d.iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                subprocess.run(f"rm -rf {item}", shell=True)

# ================= Topic Creation =================
def create_topic():
    cmd_list = f"{KAFKA_HOME}/bin/kafka-topics.sh --list --bootstrap-server localhost:9092"
    result = subprocess.run(cmd_list, shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    if TOPIC not in result.stdout:
        cmd_create = (
            f"{KAFKA_HOME}/bin/kafka-topics.sh --create "
            f"--bootstrap-server localhost:9092 "
            f"--replication-factor 1 "
            f"--partitions {NUM_PARTITIONS} "
            f"--topic {TOPIC}"
        )
        run_cmd(cmd_create)
        time.sleep(2)

# ================= Worker Process Task =================
def producer_worker(records, record_size, iters, core_id=None):

    cmd = (
        f"{KAFKA_HOME}/bin/kafka-producer-perf-test.sh "
        f"--topic {TOPIC} "
        f"--num-records {records} "
        f"--record-size {record_size} "
        f"--throughput {THROUGHPUT} "
        f"--producer-props bootstrap.servers=localhost:9092 acks=0 compression.type=none"
    )

    if core_id is not None:
        cmd = f"taskset -c {core_id} {cmd}"

    for i in range(iters):
        ret = run_cmd(cmd)
        if ret != 0:
            print(f"[ERROR] Producer on core {core_id} failed at iteration {i+1}")
    return 0

# ================= Producer Test =================
def run_producer_test(num_records, record_size, num_threads, iters):
    records_per_thread = num_records // num_threads
    cpu_count = os.cpu_count() or 1
    futures = []

    with ProcessPoolExecutor(max_workers=num_threads) as executor:
        for i in range(num_threads):
            core_id = i % cpu_count
            futures.append(executor.submit(producer_worker, records_per_thread, record_size, iters, core_id))

        for future in as_completed(futures):
            result = future.result()
            if result != 0:
                print("[ERROR] A producer task failed!")

# ================= Benchmark Runner =================
def benchmark(num_records, record_size, num_threads, iters, warmup):
    print(f"[INFO] Starting benchmark: {num_records} records, {record_size} bytes each, {num_threads} threads, {iters} iterations")

    if warmup:
        print("[INFO] Running warmup...")
        run_producer_test(1000000, record_size, num_threads, 1)
        print(f"[INFO] Warmup completed")

    print("[INFO] Running main benchmark...")
    start_time = time.perf_counter()
    run_producer_test(num_records, record_size, num_threads, iters)
    end_time = time.perf_counter()
    elapsed = end_time - start_time
    print(f"[RESULT] Total elapsed time: {elapsed:.4f} s")

# ================= Main Function =================
def main():
    parser = argparse.ArgumentParser(description="Kafka CPU Benchmark Script")
    parser.add_argument("--num-records", type=int, default=1400000000, help="Number of records to produce")
    parser.add_argument("--record-size", type=int, default=1, help="Size of each record in bytes")
    parser.add_argument("--threads", type=int, default=1, help="Number of producer threads (mapped to processes)")
    parser.add_argument("--iters", type=int, default=1, help="Number of benchmark iterations per thread")
    parser.add_argument("--warmup", action="store_false", help="Run a warmup iteration before benchmarking")

    args = parser.parse_args()

    print("[INFO] Kafka CPU Benchmark Start")
    start_kafka()
    try:
        create_topic()
        benchmark(args.num_records, args.record_size, args.threads, args.iters, args.warmup)
    except Exception as e:
        print(f"[ERROR] Benchmark aborted due to error: {e}")
        raise
    finally:
        stop_kafka()
        print("[INFO] Kafka CPU Benchmark Finished")

if __name__ == "__main__":
    main()
