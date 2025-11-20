#!/usr/bin/env python3
import subprocess
import time
import os
import socket
import shutil
from pathlib import Path
import argparse
import socket
from concurrent.futures import ProcessPoolExecutor, as_completed

# ================= Default Configuration =================
KAFKA_VERSION = "3.8.0"
SCALA_VERSION = "2.13"
KAFKA_HOME = f"./bin/kafka_{SCALA_VERSION}-{KAFKA_VERSION}"
TOPIC = "perf-test"
NUM_PARTITIONS = 64
THROUGHPUT = -1

RAMDISK_DIR = Path("/tmp/kafka_ramdisk")
TMP_DIR = Path("/tmp/kafka_tmp")
ZK_DATA_DIR = Path("/tmp/kafka_zk_data") 
KAFKA_LOG_DIR = Path(KAFKA_HOME + "/logs")

for d in [RAMDISK_DIR, TMP_DIR, ZK_DATA_DIR]:
    d.mkdir(parents=True, exist_ok=True)

os.environ["KAFKA_JVM_PERFORMANCE_OPTS"] = (
    "-server "
    "-XX:+UseSerialGC "
    f"-XX:ActiveProcessorCount=1 "
    f"-Djava.io.tmpdir={TMP_DIR}"
)

# ================= Helper Function =================
def run_cmd(cmd, ignore_output=True):
    if ignore_output:
        result = subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        return result.returncode
    else:
        result = subprocess.run(cmd, shell=True)
        return result.returncode

def wait_for_port(port, host='localhost', timeout=30):
    start_time = time.time()
    while time.time() - start_time < timeout:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            if result == 0:
                return True
        time.sleep(0.5)
    return False

def kill_process_by_pattern(pattern):
    subprocess.run(f"pkill -9 -f {pattern}", shell=True, stderr=subprocess.DEVNULL)

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
    print("[INFO] Configuring & Starting Zookeeper...")
    
    zk_props_file = Path(KAFKA_HOME) / "config/zookeeper.properties"
    zk_backup = zk_props_file.with_suffix(".properties.bak")
    
    if not zk_backup.exists():
        zk_props_file.rename(zk_backup)
    
    content = zk_backup.read_text()
    new_content = []
    for line in content.splitlines():
        if not line.strip().startswith("dataDir="):
            new_content.append(line)
    new_content.append(f"dataDir={ZK_DATA_DIR}")
    zk_props_file.write_text("\n".join(new_content))

    run_cmd(f"{KAFKA_HOME}/bin/zookeeper-server-start.sh -daemon {zk_props_file}")
    
    if not wait_for_port(2181):
        raise TimeoutError("Zookeeper failed to start on port 2181")
    print("[INFO] Zookeeper is ready.")

    print("[INFO] Configuring & Starting Kafka Broker...")
    server_properties = Path(KAFKA_HOME) / "config/server.properties"
    server_backup = server_properties.with_suffix(".properties.bak")
    
    if not server_backup.exists():
        server_properties.rename(server_backup)
    
    content = server_backup.read_text()
    content = content.replace("log.dirs=/tmp/kafka-logs", f"log.dirs={RAMDISK_DIR}")
    if "zookeeper.connect=localhost:2181" not in content:
         pass
    server_properties.write_text(content)

    run_cmd(f"{KAFKA_HOME}/bin/kafka-server-start.sh -daemon {server_properties}")

    print("[INFO] Waiting for Kafka to listen on 9092...")
    if not wait_for_port(9092):
        print("[ERROR] Kafka failed to start. Checking logs:")
        run_cmd(f"tail -n 20 {KAFKA_LOG_DIR}/server.log", ignore_output=False)
        raise TimeoutError("Kafka failed to start on port 9092")
    print("[INFO] Kafka is ready.")

def stop_kafka():
    print("[INFO] Stopping Kafka Broker & Zookeeper...")
    run_cmd(f"{KAFKA_HOME}/bin/kafka-server-stop.sh")
    run_cmd(f"{KAFKA_HOME}/bin/zookeeper-server-stop.sh")
    
    time.sleep(1) 

    print("[INFO] Force killing residual processes...")
    kill_process_by_pattern("kafka.Kafka") 
    kill_process_by_pattern("org.apache.zookeeper.server")

    print("[INFO] Cleaning up ALL data directories...")
    for d in [RAMDISK_DIR, TMP_DIR, KAFKA_LOG_DIR, ZK_DATA_DIR]:
        if d.exists():
            try:
                shutil.rmtree(d)
                d.mkdir(parents=True, exist_ok=True) 
            except Exception as e:
                print(f"[WARN] Failed to clean {d}: {e}")
    
    default_zk = Path("/tmp/zookeeper")
    if default_zk.exists():
        shutil.rmtree(default_zk, ignore_errors=True)

# ================= Topic Creation =================
def create_topic():
    cmd_list = f"{KAFKA_HOME}/bin/kafka-topics.sh --list --bootstrap-server localhost:9092"
    
    for i in range(10):
        result = subprocess.run(cmd_list, shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        if result.returncode == 0:
            break
        time.sleep(1)
    
    if TOPIC not in result.stdout:
        cmd_create = (
            f"{KAFKA_HOME}/bin/kafka-topics.sh --create "
            f"--bootstrap-server localhost:9092 "
            f"--replication-factor 1 "
            f"--partitions {NUM_PARTITIONS} "
            f"--topic {TOPIC}"
        )
        run_cmd(cmd_create)

# ================= Worker Process Task =================
def producer_worker(records, record_size, iters, core_id=None):
    cmd = (
        f"{KAFKA_HOME}/bin/kafka-producer-perf-test.sh "
        f"--topic {TOPIC} "
        f"--num-records {records} "
        f"--record-size {record_size} "
        f"--throughput {THROUGHPUT} "
        f"--producer-props bootstrap.servers=localhost:9092 acks=0 compression.type=zstd"
    )
    if core_id is not None:
        cmd = f"taskset -c {core_id} {cmd}"

    for i in range(iters):
        ret = run_cmd(cmd)
        if ret != 0:
            return 1
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
            if future.result() != 0:
                print("[ERROR] A producer task failed!")

# ================= Benchmark Runner =================
def benchmark(num_records, record_size, num_threads, iters, warmup):
    print(f"[INFO] Starting benchmark: {num_records} records, {record_size} bytes, {num_threads} threads")

    if warmup:
        print("[INFO] Running warmup...")
        run_producer_test(max(100000, num_records // 10), record_size, num_threads, 1)

    print("[INFO] Running main benchmark...")
    start_time = time.perf_counter()
    run_producer_test(num_records, record_size, num_threads, iters)
    end_time = time.perf_counter()
    print(f"[RESULT] Total elapsed time: {end_time - start_time:.4f} s")

# ================= Main Function =================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-records", type=int, default=1000000000)
    parser.add_argument("--record-size", type=int, default=1)
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--iters", type=int, default=1)
    parser.add_argument("--warmup", action="store_false")
    args = parser.parse_args()


    try:
        stop_kafka() 
    except:
        pass

    print("[INFO] Kafka CPU Benchmark Start")
    start_kafka()
    try:
        create_topic()
        benchmark(args.num_records, args.record_size, args.threads, args.iters, args.warmup)
    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        stop_kafka()
        print("[INFO] Kafka CPU Benchmark Finished")

if __name__ == "__main__":
    main()