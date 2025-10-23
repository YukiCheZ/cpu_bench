#!/usr/bin/env python3
import os
import random

def generate_common_header(path, total_funcs):
    with open(path, "w") as f:
        f.write("#pragma once\n")
        f.write("#include <math.h>\n#include <stdio.h>\n\n")
        f.write("// Common macros\n")
        f.write("#define SCALE(x) ((x) * 1.000001 + sqrt(fabs(x)))\n\n")
        f.write("// Function declarations\n")
        for i in range(total_funcs):
            f.write(f"double func_{i}(double x);\n")
        f.write("\n")

def generate_c_file(path, file_id, num_funcs=50, func_size=200, total_funcs=250, num_files=5):
    with open(path, "w") as f:
        f.write('#include "common.h"\n\n')
        for i in range(num_funcs):
            fid = file_id * num_funcs + i
            f.write(f"double func_{fid}(double x) {{\n")
            for j in range(func_size):
                f.write(f"    x += sin(x) * cos({j});\n")
                f.write("    x = SCALE(x);\n")
            num_calls = random.randint(2, 6)  
            for _ in range(num_calls):
                target = random.randint(0, total_funcs-1)
                if target != fid:  
                    divisor = random.randint(1, 5)
                    f.write(f"    x += func_{target}(x / {divisor}.0);\n")
            f.write("    return x;\n}\n\n")

def generate_main(path, num_files, num_funcs_per_file):
    with open(path, "w") as f:
        f.write('#include "common.h"\n\n')
        f.write("int main() {\n")
        f.write("    double r = 0;\n")
        total_funcs = num_files * num_funcs_per_file
        for fid in range(total_funcs):
            f.write(f"    r += func_{fid}({fid}.0);\n")
        f.write('    printf("Result: %f\\n", r);\n')
        f.write("    return 0;\n}\n")

if __name__ == "__main__":
    import argparse
    import glob

    parser = argparse.ArgumentParser()
    parser.add_argument("--num_files", type=int, default=30, help="Number of .c files to generate")
    parser.add_argument("--num_funcs", type=int, default=300, help="Number of functions per file")
    parser.add_argument("--func_size", type=int, default=500, help="Number of lines per function")
    args = parser.parse_args()

    src_dir = "./data/src"
    if os.path.exists(src_dir):
        for f in glob.glob(os.path.join(src_dir, "*.c")) + glob.glob(os.path.join(src_dir, "*.h")):
            os.remove(f)
    else:
        os.makedirs(src_dir)

    total_funcs = args.num_files * args.num_funcs

    print(f"[INFO] Generating {args.num_files} C files with {args.num_funcs} functions each (total {total_funcs} functions)...")

    generate_common_header(os.path.join(src_dir, "common.h"), total_funcs)

    for i in range(args.num_files):
        generate_c_file(
            os.path.join(src_dir, f"file_{i}.c"),
            i,
            num_funcs=args.num_funcs,
            func_size=args.func_size,
            total_funcs=total_funcs,
            num_files=args.num_files
        )

    generate_main(os.path.join(src_dir, "main.c"), args.num_files, args.num_funcs)

    print("[DATA] Generation complete.")

