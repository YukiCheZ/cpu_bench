#!/usr/bin/env python3
import os
import sys
import shutil
import argparse
import random

parser = argparse.ArgumentParser()
parser.add_argument("--lang", default="js", choices=["js", "ts"], help="Language: js or ts")
parser.add_argument("--size", type=int, default=500, help="Number of files to generate")
parser.add_argument("--complexity", type=int, default=2000, help="Complexity per file")
parser.add_argument("--out", default="./data/demo_js", help="Output directory")
parser.add_argument("--repeat-imports", type=int, default=10, help="Number of repeated imports per file")
parser.add_argument("--heavy-factor", type=int, default=50, help="Additional heavy factor per file")
args = parser.parse_args()

LANG = args.lang
SIZE = args.size
COMPLEXITY = args.complexity
OUT_DIR = args.out
REPEAT_IMPORTS = args.repeat_imports
HEAVY = args.heavy_factor
EXT = LANG

src_dir = os.path.join(OUT_DIR, "src")
if os.path.exists(OUT_DIR):
    shutil.rmtree(OUT_DIR)
os.makedirs(src_dir, exist_ok=True)

for f in range(1, SIZE + 1):
    file_path = os.path.join(src_dir, f"file_{f}.{EXT}")
    NEXT = (f % SIZE) + 1
    lines = [f"// Auto-generated {LANG} file {f}"]

    # === Repeated imports ===
    for r in range(REPEAT_IMPORTS):
        lines.append(f"import {{ func{NEXT} as func{NEXT}_{r} }} from './file_{NEXT}.{EXT}';")

    a, b = random.randint(0, 1<<16), random.randint(0, 1<<16)
    lines.append(f"const CONST_{f} = ((a, b) => ((a ** 5 + b ** 3) ^ (a << 2) | (b >>> 1)))({a}, {b});")

    # === Add some dummy classes (增加 class 定义让 AST 变大)
    for h in range(HEAVY):
        lines.append(f"class HeavyClass_{f}_{h} {{")
        for m in range(HEAVY):
            lines.append(f"  method{m}() {{ return {random.randint(0, 99999)} + {random.randint(0, 99999)}; }}")
        lines.append("}")

    # === Main exported function
    lines.append(f"export function func{f}() {{")
    for c in range(1, COMPLEXITY + 1):
        x1, x2 = random.randint(0, 1<<16), random.randint(0, 1<<16)
        lines.append(f"  const nested{c} = (x) => x * {x1} + {x2};")
        lines.append(f"  const outer{c} = () => {{")
        lines.append(f"    let total = 0;")
        lines.append(f"    for (let i = 0; i < {COMPLEXITY}; i++) {{")
        lines.append(f"      total += (i * CONST_{f}) ^ (i % 7);")
        lines.append(f"    }}")
        lines.append(f"    return total;")
        lines.append(f"  }};")

    # === Add heavy expression chain
    expr = " + ".join([f"nested{random.randint(1, COMPLEXITY)}({random.randint(0, 999)})" for _ in range(HEAVY * 20)])
    lines.append(f"  const superChain = {expr};")

    # === Dead code
    lines.append(f"  if (Math.random() < -1) {{ console.log('dead code {f}', outer1()); }}")
    lines.append(f"  return func{NEXT}_0 ? outer1() + superChain : 0;")
    lines.append("}")

    with open(file_path, "w") as f_handle:
        f_handle.write("\n".join(lines))

# === Entry file
entry_file = os.path.join(src_dir, f"entry.{EXT}")
with open(entry_file, "w") as f_handle:
    f_handle.write(f"// Entry file for {LANG}\n")
    for f in range(1, SIZE + 1):
        f_handle.write(f"import {{ func{f} }} from './file_{f}.{EXT}';\n")
    f_handle.write("console.log('Benchmark start');\n")
    f_handle.write("console.log(func1());\n")

print(f"[RESULT] Generated {SIZE} {LANG} files with complexity {COMPLEXITY} and heavy factor {HEAVY} in {src_dir} (entry.{EXT} created)")
