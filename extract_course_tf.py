import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
COURSE_DIR = ROOT / "course_text"


def clean(text):
    text = text.replace("\ufeff", "").replace("\f", " ")
    replacements = {
        "ïƒ˜": "",
        "ï‚§": "",
        "ï±": "",
        "â€“": "-",
        "â€™": "'",
        "Ã—": "x",
        "„": '"',
        "”": '"',
        "“": '"',
        "’": "'",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"\b2/9/2026\b", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\bT\s+F\b", " ", text).strip()
    text = re.sub(r"\s+\d{1,2}$", "", text).strip()
    return text


def extract_file(path):
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    candidates = []
    block = None

    def append_lowercase_lookahead(current_idx):
        look = current_idx + 1
        while look < len(lines):
            next_text = lines[look].strip()
            if not next_text:
                look += 1
                continue
            if re.match(r"^(?:\d{1,2}|2/9/2026)(?:\s+\d{1,2})?$", next_text):
                look += 1
                continue
            break
        if look < len(lines):
            next_text = lines[look].strip()
            if (
                re.match(r"^[a-z]", next_text)
                and not re.match(r"^\s*(?:\d+\.|2/9/2026)\b", next_text)
            ):
                block["lines"].append(lines[look])
                return look
        return current_idx

    def flush():
        nonlocal block
        if not block:
            return
        raw = " ".join(block["lines"])
        if re.search(r"\bT\s+F\b", raw):
            q = clean(raw)
            q = re.sub(r"^\d+\.\s*", "", q).strip()
            if q:
                candidates.append(
                    {
                        "course": path.stem.replace("_unlocked", ""),
                        "source_file": f"cim courses/{path.stem}.pdf",
                        "source_text_file": str(path.relative_to(ROOT)).replace("\\", "/"),
                        "line": block["line"],
                        "question_number": block["num"],
                        "question": q,
                    }
                )
        block = None

    idx = 0
    while idx < len(lines):
        line = lines[idx]
        line_no = idx + 1
        start = re.match(r"^\s*(\d+)\.\s+(.*)", line)
        if start:
            flush()
            block = {"num": int(start.group(1)), "line": line_no, "lines": [line]}
            if re.search(r"\bT\s+F\b", line):
                idx = append_lowercase_lookahead(idx)
                flush()
            idx += 1
            continue
        if block:
            block["lines"].append(line)
            if re.search(r"\bT\s+F\b", line):
                idx = append_lowercase_lookahead(idx)
                flush()
                idx += 1
                continue
            if re.match(r"^\s*(?:\d{1,2}|2/9/2026)\s*$", line):
                pass
            elif line.strip():
                pass
            else:
                pass
        idx += 1
    flush()
    return candidates


def main():
    all_candidates = []
    for path in sorted(COURSE_DIR.glob("C*_unlocked.txt"), key=lambda p: int(re.search(r"C(\d+)", p.name).group(1))):
        all_candidates.extend(extract_file(path))
    (ROOT / "course_tf_candidates.json").write_text(
        json.dumps(all_candidates, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    with (ROOT / "course_tf_candidates.md").open("w", encoding="utf-8") as f:
        for item in all_candidates:
            f.write(
                f"- {item['course']} line {item['line']} q{item['question_number']}: "
                f"{item['question']}\n"
            )
    print(len(all_candidates))


if __name__ == "__main__":
    main()
