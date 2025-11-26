#!/usr/bin/env python3
import argparse
import os
import random
import textwrap

WORDS = [
    "lorem", "ipsum", "dolor", "sit", "amet", "consectetur", "adipiscing",
    "elit", "sed", "do", "eiusmod", "tempor", "incididunt", "ut", "labore",
    "et", "dolore", "magna", "aliqua"
]

def random_sentence(min_words=5, max_words=15):
    return " ".join(random.choices(WORDS, k=random.randint(min_words, max_words))).capitalize() + "."

def random_paragraph(sentences=5):
    return " ".join(random_sentence() for _ in range(sentences))

def random_list(n=5):
    return "\n".join(f"- {random_sentence(3,8)}" for _ in range(n))

def random_table(rows=4, cols=3):
    header = "| " + " | ".join(f"H{c}" for c in range(cols)) + " |"
    sep = "| " + " | ".join("---" for _ in range(cols)) + " |"
    body = "\n".join("| " + " | ".join(random.choice(WORDS) for _ in range(cols)) + " |" for _ in range(rows))
    return "\n".join([header, sep, body])

def random_codeblock():
    code = "\n".join(f"print('{random.choice(WORDS)}')" for _ in range(random.randint(3,8)))
    return f"```python\n{code}\n```"

def generate_markdown_file(index, output_dir, min_size, max_size):
    filename = os.path.join(output_dir, f"doc_{index}.md")
    parts = []

    parts.append(f"# Document {index}\n\n")

    while True:
        section_type = random.choice(["paragraph", "list", "table", "code"])
        if section_type == "paragraph":
            parts.append(textwrap.fill(random_paragraph(random.randint(3,7)), width=80) + "\n\n")
        elif section_type == "list":
            parts.append("## List Example\n" + random_list(random.randint(3,6)) + "\n\n")
        elif section_type == "table":
            parts.append("## Table Example\n" + random_table(random.randint(3,6), random.randint(3,5)) + "\n\n")
        elif section_type == "code":
            parts.append("## Code Example\n" + random_codeblock() + "\n\n")

        content = "".join(parts)
        size = len(content.encode("utf-8"))

        if size >= min_size:
            if size <= max_size or min_size == max_size:
                break

    with open(filename, "w") as f:
        f.write(content)

    return filename, size

def clean_output_dir(output_dir):
    """Remove previously generated markdown files matching doc_*.md."""
    removed = 0
    if os.path.isdir(output_dir):
        for name in os.listdir(output_dir):
            if name.startswith("doc_") and name.endswith(".md"):
                path = os.path.join(output_dir, name)
                try:
                    os.remove(path)
                    removed += 1
                except OSError:
                    pass
    return removed

def main():
    parser = argparse.ArgumentParser(description="Generate random Markdown files for benchmark testing")
    parser.add_argument("--size", type=int, default=1000, help="Number of markdown files to generate")
    parser.add_argument("--output", type=str, default="./data/markdown", help="Output directory")
    parser.add_argument("--min-size", type=int, default=20480, help="Minimum file size in bytes")
    parser.add_argument("--max-size", type=int, default=40960, help="Maximum file size in bytes")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducible generation")
    args = parser.parse_args()

    if args.min_size > args.max_size:
        parser.error("--min-size cannot be greater than --max-size")

    os.makedirs(args.output, exist_ok=True)

    # Set random seed for reproducibility
    random.seed(args.seed)

    # Clean old generated files
    removed = clean_output_dir(args.output)
    if removed:
        print(f"[INFO] Cleaned {removed} old markdown files in {args.output}")
    else:
        print(f"[INFO] No previous markdown files to clean in {args.output}")

    for i in range(1, args.size + 1):
        filename, size = generate_markdown_file(i, args.output, args.min_size, args.max_size)

    print(f"[INFO] Done. Generated {args.size} markdown files in {args.output} using seed {args.seed}")

if __name__ == "__main__":
    main()
