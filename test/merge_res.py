#!/usr/bin/env python3
import os
import csv
import re
from collections import defaultdict

INPUT_DIR = "res"
OUTPUT_FILE = "merged_results.csv"

def extract_tag(filename):
    """
    Extracts a short tag from filename.
    Example: results_p2_2025-10-22_17-33-26.csv -> 'p2'
    """
    match = re.search(r"results_([^_]+)_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.csv", filename)
    if match:
        return match.group(1)
    return os.path.splitext(filename)[0]

def read_csv(filepath):
    """
    Reads a CSV file and returns a list of (benchmark_name, workload_name, elapsed_time)
    """
    rows = []
    with open(filepath, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            benchmark = row.get("benchmark_name", "").strip()
            workload = row.get("workload_name", "").strip()
            time = row.get("elapsed_time(s)", "").strip()
            if benchmark and workload:
                rows.append((benchmark, workload, time))
    return rows

def natural_key(tag):
    """
    Returns a key for natural sorting, e.g. p, p2, p10 -> p, p2, p10
    Splits string into parts of digits and non-digits.
    """
    parts = re.split(r'(\d+)', tag)
    return [int(p) if p.isdigit() else p for p in parts]

def main():
    files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".csv")]
    if not files:
        print("No CSV files found in 'res/' directory.")
        return

    merged_data = defaultdict(dict)
    tags = []

    for filename in files:
        tag = extract_tag(filename)
        tags.append(tag)
        filepath = os.path.join(INPUT_DIR, filename)
        rows = read_csv(filepath)
        for benchmark, workload, time in rows:
            merged_data[(benchmark, workload)][tag] = time

    # Sort tags in natural (human) order, e.g. p, p2, p3, p23
    tags = sorted(set(tags), key=natural_key)

    with open(OUTPUT_FILE, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        header = ["benchmark_name", "workload_name"] + tags
        writer.writerow(header)

        for (benchmark, workload), results in merged_data.items():
            row = [benchmark, workload]
            for tag in tags:
                row.append(results.get(tag, ""))
            writer.writerow(row)

    print(f"Merged results written to '{OUTPUT_FILE}' with columns sorted as: {', '.join(tags)}")

if __name__ == "__main__":
    main()
