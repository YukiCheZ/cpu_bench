#!/usr/bin/env python3
import subprocess
import time
import os
from pathlib import Path
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed

# ================= Default Configuration =================
KAFKA_HOME = "./bin/kafka_2.13-3.8.0"
TOPIC = "perf-test"
NUM_PARTITIONS = 12
THROUGHPUT = -1
CONSUMER_GROUP = "perf-consumer"

RAMDISK_DIR = Path("/tmp/kafka_ramdisk")
TMP_DIR = Path("/tmp/kafka_tmp")

RAMDISK_DIR.mkdir(parents=True, exist_ok=True)
TMP_DIR.mkdir(parents=True, exist_ok=True)

os.environ["JAVA_OPTS"] = f"-Djava.io.tmpdir={TMP_DIR}"

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
    time.sleep(5)

def stop_kafka():
    print("[INFO] Stopping Kafka Broker...")
    run_cmd(f"{KAFKA_HOME}/bin/kafka-server-stop.sh")
    time.sleep(2)
    print("[INFO] Stopping Zookeeper...")
    run_cmd(f"{KAFKA_HOME}/bin/zookeeper-server-stop.sh")
    time.sleep(2)

    for d in [RAMDISK_DIR, TMP_DIR]:
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

# ================= Single Producer Task =================
def producer_task(records, record_size):
    cmd = (
        f"{KAFKA_HOME}/bin/kafka-producer-perf-test.sh "
        f"--topic {TOPIC} "
        f"--num-records {records} "
        f"--record-size {record_size} "
        f"--throughput {THROUGHPUT} "
        f"--producer-props bootstrap.servers=localhost:9092 acks=0 compression.type=none"
    )
    return run_cmd(cmd)

# ================= Producer Test with Process Pool =================
def run_producer_test(num_records, record_size, num_threads):
    records_per_thread = num_records // num_threads
    futures = []
    with ProcessPoolExecutor(max_workers=num_threads) as executor:
        for _ in range(num_threads):
            futures.append(executor.submit(producer_task, records_per_thread, record_size))
        for future in as_completed(futures):
            result = future.result()
            if result != 0:
                print("[ERROR] A producer task failed!")

# ================= Benchmark Runner =================
def benchmark(num_records, record_size, num_threads, iters, warmup):
    if warmup:
        print("[INFO] Running warmup...")
        start_time = time.perf_counter()
        run_producer_test(num_records, record_size, num_threads)
        end_time = time.perf_counter()
    total_time = 0
    for i in range(1, iters + 1):
        print(f"[INFO] Iteration {i}/{iters}...")
        start_time = time.perf_counter()
        run_producer_test(num_records, record_size, num_threads)
        end_time = time.perf_counter()
        print(f"[RESULT] Iteration {i} finished in {end_time - start_time:.3f}s\n")
        total_time += end_time - start_time
    print(f"[RESULT] Average runtime: {total_time / iters:.3f}s\n")

# ================= Main Function =================
def main():
    parser = argparse.ArgumentParser(description="Kafka CPU Benchmark Script")
    parser.add_argument("--num-records", type=int, default=50000000, help="Number of records to produce")
    parser.add_argument("--record-size", type=int, default=100, help="Size of each record in bytes")
    parser.add_argument("--threads", type=int, default=1, help="Number of producer threads")
    parser.add_argument("--iters", type=int, default=3, help="Number of benchmark iterations")
    parser.add_argument("--warmup", action="store_true", help="Run a warmup iteration before benchmarking")

    args = parser.parse_args()

    print("=== Kafka CPU Benchmark Start ===")
    start_kafka()
    create_topic()
    benchmark(args.num_records, args.record_size, args.threads, args.iters, args.warmup)
    stop_kafka()
    print("=== Kafka CPU Benchmark Finished ===")

if __name__ == "__main__":
    main()
