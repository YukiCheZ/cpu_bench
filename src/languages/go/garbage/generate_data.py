#!/usr/bin/env python3
import argparse
import os
import random
import string

def random_identifier(length=8):
    return ''.join(random.choices(string.ascii_letters, k=length))

def generate_func():
    fname = random_identifier()
    ret_type = random.choice(["int", "float64", "string", "bool"])
    body_line_count = random.randint(1, 5)
    body_lines = []
    for _ in range(body_line_count):
        var_name = random_identifier()
        value = random.randint(0, 100)
        body_lines.append(f"    {var_name} := {value}")
    body_lines.append(f"    return {random.randint(0,100)}")
    body = "\n".join(body_lines)
    return f"func {fname}() {ret_type} {{\n{body}\n}}\n"

def generate_file(num_lines):
    header = "package main\n\n"
    funcs = []
    for _ in range(num_lines):
        funcs.append(generate_func())
    return header + "\n".join(funcs)

def main():
    parser = argparse.ArgumentParser(description="Generate Go source file for garbage benchmark")
    parser.add_argument("--size", type=int, default=100000, help="approximate number of functions (controls file size)")
    parser.add_argument("--output", type=str, default="./data/input.go", help="output file path")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    random.seed(42)

    content = generate_file(args.size)
    with open(args.output, "w") as f:
        f.write(content)

    print(f"Generated {args.output}, approx {len(content)/1024:.2f} KB")

if __name__ == "__main__":
    main()
