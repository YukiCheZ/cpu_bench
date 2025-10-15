#!/usr/bin/env python3
"""
Go Code Generator (Revised Version)
Usage example:
    python generate_go_code.py --out generated --pkgs 50 --files 5 --structs 8 --funcs 40 --complex 200

Fixes:
- Only one `types.go` is generated per package (contains Container) to avoid re-declaration.
- Avoid using `tmp := ...` to prevent variable shadowing and type mismatch errors.
- Use `_ = StructLiteral` to increase AST complexity without variable name collisions.
"""

import argparse
import os
import textwrap
import shutil

def generate_struct(pkg_idx, file_idx, struct_idx, complexity):
    """Generate a struct definition with multiple fields to increase AST size"""
    struct_name = f"S_{pkg_idx}_{file_idx}_{struct_idx}"
    fields = complexity // 10 + 5
    field_lines = [f"\tF{i} int" for i in range(fields)]
    arr_size = complexity // 5 + 10
    field_lines.append(f"\tBigArr [{arr_size}]int")
    return f"type {struct_name} struct {{\n" + "\n".join(field_lines) + "\n}\n\n"

def generate_function(pkg_idx, file_idx, func_idx, structs_per_file, complexity):
    """Generate a generic function that creates a lot of AST nodes and arithmetic operations"""
    func_name = f"Func_{pkg_idx}_{file_idx}_{func_idx}"
    lines = [f"func {func_name}[T any](c Container[T], n int) int {{",
             "\tvar acc int"]

    # Heavy arithmetic and struct literals to bloat the AST
    for r in range(complexity):
        lines.append(f"\tacc += n + {((r*17+3)%97)}")
        if r % 25 == 0:
            sidx = r % structs_per_file
            struct_name = f"S_{pkg_idx}_{file_idx}_{sidx}"
            lines.append(f"\t_ = {struct_name}{{F0: {r}, F1: {r+1}, F2: {r+2}}}")

    # Add a switch statement to make control flow more complex
    lines.append("\tswitch n % 5 {")
    for c in range(5):
        lines.append(f"\tcase {c}:")
        lines.append(f"\t\tacc += {c*3+1}")
    lines.append("\t}")
    lines.append("\treturn acc")
    lines.append("}\n")
    return "\n".join(lines)

def generate_types_file(pkg_idx):
    """Generate types.go for each package, containing only Container (declared once)"""
    pkg_name = f"pkg{pkg_idx:03d}"
    content = [f"package {pkg_name}", "", "// package-wide types", ""]
    content.append("type Container[T any] struct { Val T }\n")
    return "\n".join(content)

def generate_file(pkg_idx, file_idx, structs_per_file, funcs_per_file, complexity):
    """Generate a single .go file (no Container redeclaration)"""
    pkg_name = f"pkg{pkg_idx:03d}"
    content = [f"package {pkg_name}", "", "import (\"fmt\")", ""]
    # Structs
    for s in range(structs_per_file):
        content.append(generate_struct(pkg_idx, file_idx, s, complexity))
    # Functions
    for f in range(funcs_per_file):
        content.append(generate_function(pkg_idx, file_idx, f, structs_per_file, complexity))
    # init function — instantiate some generics to increase compile load
    content.append("func init() {")
    for c in range(min(funcs_per_file, 20)):
        func_name = f"Func_{pkg_idx}_{file_idx}_{c}"
        content.append(f"\t_ = {func_name}[int](Container[int]{{Val:{c}}}, {c+1})")
    content.append(f"\tfmt.Sprintf(\"init {pkg_name} file {file_idx}\")")
    content.append("}\n")
    return "\n".join(content)

def generate_main(pkgs, module_name):
    """Generate main.go at the module root to import all packages"""
    imports = "\n".join([f'\t_ "{module_name}/pkg{p:03d}"' for p in range(pkgs)])
    return textwrap.dedent(f"""\
        package main

        import (
        {imports}
        )

        func main() {{}}
    """)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="data", help="Output directory")
    parser.add_argument("--pkgs", type=int, default=100, help="Number of packages to generate")
    parser.add_argument("--files", type=int, default=5, help="Number of files per package")
    parser.add_argument("--structs", type=int, default=20, help="Number of structs per file")
    parser.add_argument("--funcs", type=int, default=50, help="Number of functions per file")
    parser.add_argument("--complex", type=int, default=200, help="Function complexity (larger = heavier build)")
    parser.add_argument("--module", default="data", help="Module name used in go.mod")
    args = parser.parse_args()

    out_dir = args.out

    if os.path.exists(out_dir):
        print(f"[INFO] Cleaning existing output directory: {out_dir}")
        shutil.rmtree(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    print(f"[INFO] Generating Go code: pkgs={args.pkgs}, files/pkg={args.files}, structs/file={args.structs}, funcs/file={args.funcs}, complexity={args.complex}, module={args.module}")

    # Generate packages and files
    for p in range(args.pkgs):
        pkg_dir = os.path.join(out_dir, f"pkg{p:03d}")
        os.makedirs(pkg_dir, exist_ok=True)

        # types.go (Container only, once per package)
        types_path = os.path.join(pkg_dir, "types.go")
        with open(types_path, "w") as tf:
            tf.write(generate_types_file(p))

        # Other .go files
        for fidx in range(args.files):
            file_path = os.path.join(pkg_dir, f"file_{fidx:03d}.go")
            content = generate_file(p, fidx, args.structs, args.funcs, args.complex)
            with open(file_path, "w") as fw:
                fw.write(content)

    # main.go at module root
    main_go = generate_main(args.pkgs, args.module)
    with open(os.path.join(out_dir, "main.go"), "w") as mg:
        mg.write(main_go)

    # go.mod at module root
    go_mod_path = os.path.join(out_dir, "go.mod")
    if not os.path.exists(go_mod_path):
        with open(go_mod_path, "w") as gm:
            gm.write(f"module {args.module}\n\ngo 1.24\n")

    print(f"[INFO] Code generation completed: {out_dir}")
    print(f"[INFO] To build and benchmark: cd {out_dir} && go build -a -o /dev/null ./...")
    print(f"[INFO] (or from parent dir: go build -C {out_dir} -a -o /dev/null ./...)")

if __name__ == "__main__":
    main()
