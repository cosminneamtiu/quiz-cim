import json
import re
import shutil
from collections import defaultdict
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DUMP_DIR = ROOT / "exam questions dumps"
CANONICAL_BANK = ROOT / "quiz_questions.json"


def normalize(text):
    text = str(text or "").lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def src(course, line, note=None):
    item = {
        "course": course,
        "source_text_file": f"course_text/{course}_unlocked.txt",
        "line": line,
    }
    if note:
        item["note"] = note
    return item


def bank_src(item):
    source = {
        "source": "quiz_questions.json",
        "matched_id": item.get("id"),
        "source_file": item.get("source_file"),
    }
    for key in ("quiz", "question_number", "course", "source_page", "source_line"):
        if item.get(key) is not None:
            source[key] = item[key]
    return source


def spec(keys=None, sources=None, status="confirmed", notes=None, answers=None):
    return {
        "correct_option_keys": keys or [],
        "answer_sources": sources or [],
        "answer_status": status,
        "answer_notes": notes,
        "answer_texts": answers or [],
    }


SOURCES = {
    "asrs": [src("C5", 188, "AS/RS capacity and dimensions formulas")],
    "polycode": [src("C6", 124, "coding structures"), src("C6", 142, "monocode tree structure"), src("C6", 163, "polycode code table")],
    "gt": [src("C6", 30, "group technology"), src("C6", 75, "methods to group parts into families")],
    "pfa": [src("C6", 187, "production flow analysis"), src("C6", 200, "part-machine incidence matrix")],
    "flexibility": [src("C7", 37, "requirements for flexible manufacturing systems"), src("C7", 645, "flexibility capabilities")],
    "fms_types": [src("C7", 37, "FMS definition"), src("C7", 72, "FMS benefits"), src("C7", 106, "types of flexibility")],
    "jit": [src("C10", 383, "JIT principles"), src("C10", 400, "Kanban cards")],
    "lean": [src("C11", 164, "lean manufacturing removes waste")],
    "planning": [src("C9", 23, "production planning scope"), src("C9", 37, "aggregate/MPS/MRP/capacity definitions")],
    "mps": [src("C9", 304, "MPS available balance formula"), src("C9", 283, "MPS is medium range")],
    "capacity": [src("C3", 251, "production capacity"), src("C9", 601, "capacity planning")],
    "ops": [src("C3", 50, "processing operation"), src("C3", 64, "assembly operation")],
    "util_avail": [src("C3", 315, "utilization formula"), src("C3", 350, "availability formula")],
    "lead_time": [src("C3", 385, "manufacturing lead time"), src("C3", 420, "batch lead time example")],
    "cost": [src("C3", 315, "utilization and capacity"), src("C8", 213, "make-or-buy example")],
    "material": [src("C4", 67, "material handling design factors"), src("C4", 156, "vehicle guidance technologies")],
    "storage": [src("C5", 86, "storage system measures"), src("C5", 113, "storage strategies")],
    "sustain": [src("C11", 33, "sustainable manufacturing"), src("C11", 105, "green products"), src("C11", 269, "sustainable operations")],
    "industry4": [src("C12", 192, "IIoT"), src("C12", 288, "Industry 4.0"), src("C12", 325, "Industry 4.0 features")],
    "romania": [src("C12", 381, "Romania advantages for Industry 4.0")],
    "design": [src("C8", 259, "concurrent engineering elements"), src("C8", 315, "design for quality"), src("C8", 338, "design for life cycle")],
    "routing": [src("C7", 264, "routing process definitions"), src("C7", 288, "operation frequency")],
    "investment": [src("C8", 392, "investment project management steps")],
    "mrpii": [src("C10", 355, "MRP II definition"), src("C10", 370, "MRP II benefits")],
    "product_structure": [src("C9", 400, "P1 product structure")],
    "workflow": [src("C6", 527, "workflow PIM/PBM formulas"), src("C6", 553, "workflow example calculation")],
}


MANUAL_BY_LOCATION = {
    "quiz_questions_and_options.json": {
        1: spec(["B"], SOURCES["asrs"], notes="120 / (2 aisles * 2 sides * 10 compartments per level) = 3 levels."),
        2: spec(["A"], SOURCES["asrs"], notes="Total width = 3 aisles * 3 * (1 + 0.1) = 9.9 m."),
        3: spec(["B"], SOURCES["polycode"]),
        4: spec(["B"], SOURCES["gt"]),
        5: spec(["B"], SOURCES["pfa"]),
        6: spec(["A", "B", "C", "D"], SOURCES["flexibility"]),
        7: spec(["B"], SOURCES["jit"]),
        8: spec(["A", "D"], SOURCES["lean"]),
        9: spec(["B"], SOURCES["mps"]),
        10: spec(["A", "D"], [src("C12", 281, "traditional factory control"), src("C7", 37, "distributed computer control in FMS")]),
        11: spec(
            status="needs_review",
            sources=SOURCES["investment"],
            notes="Course order is d, e, b, g, c, a, f, h after omitting vendor-progress monitoring; no provided option matches that order.",
        ),
        12: spec(["D"], SOURCES["fms_types"]),
    },
    "quiz_questions_part2.json": {
        1: spec(["D"], [src("C8", 213, "make-or-buy cost comparison")], notes="In-house cost exceeds the 35 euro purchase price."),
        2: spec(["C"], SOURCES["sustain"]),
        3: spec(["A", "B", "C", "D"], [src("C12", 86, "digital factory activities")]),
        4: spec(["A", "C", "D", "E"], SOURCES["industry4"]),
        5: spec(["B", "C", "E"], [src("C1", 92, "CIM benefits"), src("C12", 325, "Industry 4.0 modularity")]),
        6: spec(["B"], [src("C1", 92, "CIM reduces lot sizes")]),
        7: spec(["B", "C", "D"], SOURCES["mrpii"]),
        8: spec(["C", "D"], SOURCES["design"]),
        9: spec(["A"], SOURCES["pfa"]),
        10: spec(["C"], SOURCES["material"]),
        11: spec(["A"], SOURCES["planning"]),
        12: spec(["B", "C"], SOURCES["sustain"]),
        13: spec(["A", "B"], SOURCES["industry4"]),
    },
    "quiz_questions_part3.json": {
        1: spec(["A", "B"], [src("C1", 83, "external challenges")]),
        2: spec(["D"], SOURCES["capacity"]),
        3: spec(["A", "B", "C", "D"], [src("C1", 257, "CIM subsystems")]),
        4: spec(["A"], SOURCES["gt"]),
        5: spec(["B", "D"], [src("C3", 536, "assemble-to-order conditions")]),
        6: spec(["A", "B", "C"], SOURCES["planning"]),
        7: spec(["D"], SOURCES["ops"]),
        8: spec(["A", "B", "C", "D"], SOURCES["fms_types"]),
        9: spec(["A"], [src("C9", 263, "MPS end-item demand")]),
        10: spec(["B"], [src("C1", 92, "CIM reduces production lots")]),
        11: spec(["A"], [src("C1", 243, "inventory stock statements")]),
        12: spec(["A"], SOURCES["gt"]),
        13: spec(["B"], SOURCES["material"]),
        14: spec(["B"], SOURCES["lead_time"]),
        15: spec(["A", "B"], [src("C3", 119, "product complexity")]),
        16: spec(["B"], SOURCES["storage"]),
    },
    "quiz_questions_part4.json": {
        1: spec(["E"], SOURCES["capacity"], notes="Maximum observed output is 340, but no scenario has 340 in and 340 out."),
        2: spec(["B"], SOURCES["product_structure"], notes="1 P1 * 2 S2/P1 * 3 C6/S2 * 5 M6/C6 = 30 M6."),
        3: spec(sources=SOURCES["mps"], answers=["1.60"], notes="Inventory balance = 3.60 + 9.60 - 11.60 = 1.60."),
        4: spec(["A", "C"], SOURCES["sustain"]),
        5: spec(["A"], SOURCES["capacity"]),
        6: spec(["C"], SOURCES["design"]),
        7: spec(["B"], SOURCES["lean"]),
        8: spec(["C"], SOURCES["mps"], notes="December inventory = 1.32 + 21.89 - 22.20 = 1.01, below the 1.3 safety stock."),
    },
    "quiz_questions_part5.json": {
        1: spec(["A"], SOURCES["util_avail"], notes="320 / (80 hours * 10 parts/hour) = 40%."),
        2: spec(
            status="needs_review",
            sources=SOURCES["workflow"],
            notes="The workflow diagram needed for PBM is not present in this dump text, and the course example gives 11.11%, which is not among the provided options.",
        ),
        3: spec(["A"], [src("C8", 97, "retrieval/variant CAPP")]),
        4: spec(["B"], SOURCES["util_avail"]),
        5: spec(["F"], [src("C1", 83, "internal challenge")]),
    },
    "quiz_questions_part6.json": {
        1: spec(["B"], [src("C2", 254, "amount of products by models")], notes="4 * 300 + 3 * 600 = 3000 products."),
        2: spec(["A", "C"], SOURCES["polycode"]),
        3: spec(["C"], [src("C10", 101, "first-come first-served dispatching")], notes="Arrival order: C3 day 115, C1 day 116, C2 day 117."),
        4: spec(["A", "B", "D"], SOURCES["romania"]),
        5: spec(["A", "C", "D"], SOURCES["polycode"]),
        6: spec(["B"], [src("C2", 60, "job shop manufacturing")]),
        7: spec(["D"], [src("C3", 550, "make-to-stock for mature forecastable products")]),
        8: spec(["E"], [src("C3", 471, "manufacturing cost and selling price")], notes="Selling price = 200 / 0.40 = 500; parts/materials = 100; 100 / 500 = 20%."),
        9: spec(["B", "C"], SOURCES["storage"]),
        10: spec(["A"], SOURCES["util_avail"], notes="Availability = 100 / (100 + 2) = 98.04%."),
        11: spec(
            status="needs_review",
            sources=SOURCES["capacity"],
            notes="Using the course formula gives 8 * 5 * 8 * 10 * 0.90 = 2880 products/week, which is not among the provided options.",
        ),
    },
    "quiz_questions_part7.json": {
        1: spec(["A"], SOURCES["routing"]),
        2: spec(["D"], SOURCES["mps"], notes="Without a new lot, available stock falls below 10 on day 5."),
        3: spec(["A"], [src("C2", 380, "learning curve")], notes="4 * 0.3 = 1.2 minutes."),
        4: spec(["A", "B", "E"], [src("C12", 255, "traditional factory characteristics")]),
        5: spec(["A"], SOURCES["design"]),
        6: spec(["B", "C", "E"], [src("C1", 92, "CIM benefits"), src("C12", 325, "Industry 4.0 modularity")]),
        7: spec(["D"], SOURCES["mps"], notes="Days 5, 6, 7 balances are 1, 0, and 5."),
        8: spec(["B", "D"], SOURCES["lead_time"]),
        9: spec(["B", "D"], [src("C12", 306, "modular smart factory"), src("C12", 281, "context-aware decisions")]),
        10: spec(["B"], [src("C9", 647, "level production workforce/hours statement")]),
        11: spec(["C"], SOURCES["routing"]),
    },
    "quiz_questions_part8.json": {
        1: spec(["A"], SOURCES["lead_time"], notes="15 setup minutes + 5 * (200 / 100) processing minutes = 25 minutes."),
        2: spec(sources=SOURCES["mps"], answers=["-1.10"], notes="Starting inventory is zero, so January balance = 0 + 5.50 - 6.60 = -1.10."),
        3: spec(["A"], SOURCES["industry4"]),
    },
    "quiz_questions_part9.json": {
        1: spec(["C"], SOURCES["fms_types"]),
        2: spec(["A", "B", "C"], SOURCES["gt"]),
        3: spec(["B", "D", "E"], SOURCES["planning"]),
        4: spec(["A", "C"], [src("C2", 390, "two-workstation routing statement")]),
        5: spec(["A", "C"], [src("C9", 626, "long-term capacity adjustments")]),
        6: spec(["F"], SOURCES["fms_types"]),
        7: spec(["A", "B", "C"], SOURCES["routing"]),
        8: spec(["B", "C"], SOURCES["fms_types"]),
        9: spec(["B"], SOURCES["fms_types"]),
        10: spec(["B"], [src("C3", 572, "J.T. Black parts/materials percentage")]),
        11: spec(["A", "B", "C"], SOURCES["planning"]),
        12: spec(["D"], SOURCES["workflow"], notes="Course workflow example gives PIM/PSM = 95 / 135 * 100 = 70.37%."),
        13: spec(["C"], SOURCES["jit"]),
    },
    "quiz_questions_part10.json": {
        1: spec(["B"], SOURCES["ops"]),
        2: spec(["B"], [src("C8", 429, "CAPP self-assessment")]),
        3: spec(["A"], SOURCES["fms_types"]),
        4: spec(["B"], [src("C7", 355, "maximum production rate/bottleneck")]),
        5: spec(["B"], SOURCES["material"]),
        6: spec(["A"], SOURCES["planning"]),
        7: spec(["B"], SOURCES["industry4"]),
    },
    "quiz_questions_part11.json": {
        1: spec(["B"], SOURCES["ops"]),
        2: spec(["B"], [src("C8", 429, "CAPP self-assessment")]),
        3: spec(["A"], SOURCES["fms_types"]),
        4: spec(["B"], [src("C7", 355, "maximum production rate/bottleneck")]),
        5: spec(["B"], SOURCES["material"]),
        6: spec(["A"], SOURCES["planning"]),
        7: spec(["B"], SOURCES["industry4"]),
    },
    "quiz_questions_part12.json": {
        1: spec(["A", "C", "D"], SOURCES["gt"]),
        2: spec(["A", "B", "C", "D"], SOURCES["design"]),
        3: spec(["A", "B"], SOURCES["design"]),
        4: spec(["A", "C", "D"], SOURCES["fms_types"]),
        5: spec(["B"], SOURCES["storage"]),
        6: spec(["A", "B", "D"], SOURCES["jit"]),
        7: spec(["B"], SOURCES["storage"]),
        8: spec(["B"], SOURCES["fms_types"]),
        9: spec(["A"], SOURCES["planning"]),
        10: spec(["A", "B"], SOURCES["fms_types"]),
        11: spec(["A", "C"], [src("C4", 274, "AGV available time formula")]),
        12: spec(["A"], SOURCES["fms_types"]),
        13: spec(["B"], [src("C1", 181, "manufacturing-space ratio standard")], notes="Production-area/total-area ratio = (2 * 1) / 8 = 25%, below the 50% standard."),
    },
}


ANSWER_FIELDS = {
    "correct_option_keys",
    "correct_answers",
    "answer_status",
    "answer_sources",
    "answer_notes",
}


def load_answer_bank():
    if not CANONICAL_BANK.exists():
        return {}

    data = json.loads(CANONICAL_BANK.read_text(encoding="utf-8-sig"))
    bank = {}
    for item in data.get("questions", []):
        question_key = normalize(item.get("question"))
        if not question_key or not item.get("correct_answers"):
            continue
        bank.setdefault(question_key, item)
    return bank


def option_matches_answer(option, answer):
    opt = normalize(option)
    ans = normalize(answer)
    if not opt or not ans:
        return False
    return ans == opt or ans.startswith(f"{opt} ") or opt.startswith(f"{ans} ")


def bank_spec_for(item, bank):
    match = bank.get(normalize(item.get("question")))
    if not match:
        return None

    options = item.get("options") or {}
    keys = []
    for key, option in options.items():
        if any(option_matches_answer(option, answer) for answer in match.get("correct_answers", [])):
            keys.append(key)
    if not keys:
        return None

    return spec(keys=keys, sources=[bank_src(match)], notes="Matched from existing answered quiz bank.")


def apply_spec(item, answer_spec):
    options = item.get("options") or {}
    keys = list(answer_spec["correct_option_keys"])
    answers = [options[key] for key in keys if key in options]
    answers.extend(answer_spec.get("answer_texts", []))

    for field in ANSWER_FIELDS:
        item.pop(field, None)

    item["correct_option_keys"] = keys
    item["correct_answers"] = answers
    item["answer_status"] = answer_spec["answer_status"]
    item["answer_sources"] = answer_spec["answer_sources"]
    if answer_spec.get("answer_notes"):
        item["answer_notes"] = answer_spec["answer_notes"]


def validate_file(path, items):
    errors = []
    for index, item in enumerate(items, start=1):
        options = item.get("options")
        if not isinstance(options, dict):
            errors.append(f"{path.name} item {index}: options must be an object")
            continue

        status = item.get("answer_status")
        keys = item.get("correct_option_keys")
        answers = item.get("correct_answers")
        sources = item.get("answer_sources")
        if status not in {"confirmed", "needs_review"}:
            errors.append(f"{path.name} item {index}: invalid answer_status {status!r}")
        if not isinstance(keys, list):
            errors.append(f"{path.name} item {index}: correct_option_keys must be a list")
            keys = []
        if not isinstance(answers, list):
            errors.append(f"{path.name} item {index}: correct_answers must be a list")
            answers = []
        if not isinstance(sources, list):
            errors.append(f"{path.name} item {index}: answer_sources must be a list")
            sources = []

        for key in keys:
            if key not in options:
                errors.append(f"{path.name} item {index}: unknown option key {key!r}")

        keyed_answers = [options[key] for key in keys if key in options]
        if answers[: len(keyed_answers)] != keyed_answers:
            errors.append(f"{path.name} item {index}: answers do not match selected option text")

        if status == "confirmed" and not answers:
            errors.append(f"{path.name} item {index}: confirmed item has no answers")
        if status == "confirmed" and not sources:
            errors.append(f"{path.name} item {index}: confirmed item has no sources")
        if status == "needs_review" and not item.get("answer_notes"):
            errors.append(f"{path.name} item {index}: needs_review item must explain why")
    return errors


def main():
    dump_files = sorted(DUMP_DIR.glob("*.json"))
    if not dump_files:
        raise SystemExit(f"No JSON files found in {DUMP_DIR}")

    bank = load_answer_bank()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = DUMP_DIR / "backups" / timestamp
    backup_dir.mkdir(parents=True, exist_ok=False)

    raw_by_file = {}
    for path in dump_files:
        if path.name == "answer_audit_report.json":
            continue
        items = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(items, list):
            raise ValueError(f"{path.name} must contain a JSON array")
        for index, item in enumerate(items, start=1):
            if not isinstance(item, dict) or "question" not in item or "options" not in item:
                raise ValueError(f"{path.name} item {index} must contain question and options")
        raw_by_file[path.name] = (path, items)

    manual_by_question = {}
    for file_name, specs in MANUAL_BY_LOCATION.items():
        if file_name not in raw_by_file:
            raise ValueError(f"Manual map references missing file {file_name}")
        _, items = raw_by_file[file_name]
        for index, answer_spec in specs.items():
            if index < 1 or index > len(items):
                raise ValueError(f"Manual map references missing item {file_name} #{index}")
            qkey = normalize(items[index - 1]["question"])
            prior = manual_by_question.get(qkey)
            comparable = (answer_spec["correct_option_keys"], answer_spec["answer_status"], answer_spec.get("answer_texts", []))
            if prior and prior["comparable"] != comparable:
                raise ValueError(f"Conflicting manual answers for normalized question: {items[index - 1]['question']}")
            manual_by_question[qkey] = {"spec": answer_spec, "comparable": comparable}

    audit = {
        "generated_at": timestamp,
        "backup_dir": str(backup_dir.relative_to(ROOT)).replace("\\", "/"),
        "files": {},
        "needs_review": [],
        "duplicate_groups": [],
    }

    duplicate_index = defaultdict(list)
    errors = []

    for file_name, (path, items) in raw_by_file.items():
        shutil.copy2(path, backup_dir / path.name)

        confirmed = 0
        needs_review = 0
        source_courses = set()

        for index, item in enumerate(items, start=1):
            qkey = normalize(item["question"])
            duplicate_index[qkey].append({"file": file_name, "index": index})

            chosen = bank_spec_for(item, bank)
            manual = manual_by_question.get(qkey)
            if manual:
                chosen = manual["spec"]
            if not chosen:
                chosen = spec(status="needs_review", notes="No course-backed answer was mapped for this item.")

            apply_spec(item, chosen)

            if item["answer_status"] == "confirmed":
                confirmed += 1
            else:
                needs_review += 1
                audit["needs_review"].append(
                    {
                        "file": file_name,
                        "index": index,
                        "question": item["question"],
                        "answer_notes": item.get("answer_notes"),
                    }
                )

            for source in item.get("answer_sources", []):
                if source.get("course"):
                    source_courses.add(source["course"])

        errors.extend(validate_file(path, items))
        audit["files"][file_name] = {
            "question_count": len(items),
            "confirmed_count": confirmed,
            "needs_review_count": needs_review,
            "source_courses": sorted(source_courses, key=lambda value: int(value[1:]) if value[1:].isdigit() else value),
        }

    for qkey, locations in duplicate_index.items():
        if len(locations) < 2:
            continue
        answer_sets = set()
        for location in locations:
            items = raw_by_file[location["file"]][1]
            item = items[location["index"] - 1]
            answer_sets.add(tuple(item.get("correct_option_keys", [])))
        if len(answer_sets) > 1:
            errors.append(f"Duplicate question has conflicting answers: {locations}")
        audit["duplicate_groups"].append({"locations": locations, "correct_option_keys": list(next(iter(answer_sets)))})

    if errors:
        raise ValueError("Validation failed:\n" + "\n".join(errors))

    for path, items in raw_by_file.values():
        path.write_text(json.dumps(items, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")

    audit_path = DUMP_DIR / "answer_audit_report.json"
    audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Updated {len(raw_by_file)} files")
    print(f"Backup: {backup_dir}")
    print(f"Needs review: {len(audit['needs_review'])}")


if __name__ == "__main__":
    main()
