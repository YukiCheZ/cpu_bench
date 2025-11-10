#!/usr/bin/env python3
import csv
import os
import re
from collections import defaultdict

# Input and output paths
RES_DIR = "res_lab1"
OUTPUT_FILE = "merged_results_lab1.csv"

# Match pattern: results_round_{n}_{timestamp}.csv
pattern = re.compile(r"results_round_(\d+)_.+\.csv$")

def main():
    # {(benchmark_name, workload_name): {round_n: elapsed_time}}
    results = defaultdict(dict)
    rounds = set()

    for fname in os.listdir(RES_DIR):
        match = pattern.match(fname)
        if not match:
            continue
        round_num = int(match.group(1))
        rounds.add(round_num)

        filepath = os.path.join(RES_DIR, fname)
        print(f"Reading {filepath}")
        with open(filepath, newline='') as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames or "benchmark_name" not in reader.fieldnames:
                print(f"Skipping invalid file: {fname}")
                continue

            for row in reader:
                # Skip empty rows or rows missing required fields
                if not row or not row.get("benchmark_name") or not row.get("workload_name"):
                    continue
                bench = row["benchmark_name"].strip()
                work = row["workload_name"].strip()
                elapsed = row.get("elapsed_time(s)", "").strip()

                if elapsed == "":
                    continue  # Skip rows without valid elapsed time
                results[(bench, work)][round_num] = elapsed

    if not results:
        print("No valid results found. Please check CSV file formats in 'res/' directory.")
        return

    sorted_rounds = sorted(rounds)

    with open(OUTPUT_FILE, "w", newline='') as f:
        writer = csv.writer(f)
        header = ["benchmark_name", "workload_name"] + [f"round_{r}" for r in sorted_rounds]
        writer.writerow(header)

        for (bench, work), data in sorted(results.items()):
            row = [bench, work]
            for r in sorted_rounds:
                row.append(data.get(r, ""))  # Leave empty if missing
            writer.writerow(row)

    print(f"\nMerging complete. Output written to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
