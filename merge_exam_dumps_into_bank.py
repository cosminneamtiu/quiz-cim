import json
import re
import shutil
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DUMP_DIR = ROOT / "exam questions dumps"
BANK_PATH = ROOT / "quiz_questions.json"
SITE_DATA_PATH = ROOT / "quiz_site" / "quiz-data.js"


def normalize(text):
    text = str(text or "").lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def dump_label(path):
    stem = path.stem.replace("quiz_questions_", "").replace("_", " ")
    return f"Exam Dump {stem.title()}"


def item_courses(item):
    courses = []
    for source in item.get("answer_sources", []):
        course = source.get("course")
        if course and course not in courses:
            courses.append(course)
    return courses


def convert_dump_item(path, index, item):
    options_map = item.get("options") or {}
    options = list(options_map.values())

    merged = {
        "id": f"exam_dump_{path.stem}_{index:03d}",
        "source_file": f"exam questions dumps/{path.name}",
        "quiz": dump_label(path),
        "question_number": index,
        "question": item["question"],
        "options": options,
        "correct_answers": item.get("correct_answers", []),
        "correct_option_keys": item.get("correct_option_keys", []),
        "answer_status": item.get("answer_status", "confirmed"),
        "answer_sources": item.get("answer_sources", []),
    }

    if item.get("answer_notes"):
        merged["answer_notes"] = item["answer_notes"]

    courses = item_courses(item)
    if len(courses) == 1:
        merged["course"] = courses[0]
    elif courses:
        merged["courses"] = courses

    return merged


def regenerate_site_data(bank):
    SITE_DATA_PATH.write_text(
        "window.QUIZ_DATA = "
        + json.dumps(bank, ensure_ascii=False, indent=2)
        + ";\n",
        encoding="utf-8",
    )


def main():
    if not BANK_PATH.exists():
        raise FileNotFoundError(BANK_PATH)
    if not SITE_DATA_PATH.exists():
        raise FileNotFoundError(SITE_DATA_PATH)

    bank = json.loads(BANK_PATH.read_text(encoding="utf-8-sig"))
    questions = bank.get("questions")
    if not isinstance(questions, list):
        raise ValueError("quiz_questions.json must contain a questions array")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = DUMP_DIR / "backups" / f"main_merge_{timestamp}"
    backup_dir.mkdir(parents=True, exist_ok=False)
    shutil.copy2(BANK_PATH, backup_dir / BANK_PATH.name)
    shutil.copy2(SITE_DATA_PATH, backup_dir / SITE_DATA_PATH.name)

    existing_questions = {normalize(item.get("question")) for item in questions}
    seen_dump_questions = set()
    appended = []
    skipped_existing = []
    skipped_dump_duplicate = []
    skipped_needs_review = []

    dump_files = [
        path
        for path in sorted(DUMP_DIR.glob("quiz_questions*.json"))
        if path.name != "answer_audit_report.json"
    ]

    for path in dump_files:
        items = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(items, list):
            raise ValueError(f"{path.name} must contain a JSON array")

        generated_from = f"exam questions dumps/{path.name}"
        if generated_from not in bank["generated_from"]:
            bank["generated_from"].append(generated_from)

        for index, item in enumerate(items, start=1):
            qkey = normalize(item.get("question"))
            location = {"file": path.name, "index": index, "question": item.get("question")}

            if qkey in existing_questions:
                skipped_existing.append(location)
                continue
            if qkey in seen_dump_questions:
                skipped_dump_duplicate.append(location)
                continue
            seen_dump_questions.add(qkey)

            if item.get("answer_status") != "confirmed":
                location["answer_notes"] = item.get("answer_notes")
                skipped_needs_review.append(location)
                continue
            if not item.get("correct_answers"):
                location["answer_notes"] = "Confirmed item has no correct_answers."
                skipped_needs_review.append(location)
                continue

            merged = convert_dump_item(path, index, item)
            questions.append(merged)
            appended.append(
                {
                    "id": merged["id"],
                    "file": path.name,
                    "index": index,
                    "question": item.get("question"),
                }
            )
            existing_questions.add(qkey)

    bank["question_count"] = len(questions)

    BANK_PATH.write_text(json.dumps(bank, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    regenerate_site_data(bank)

    report = {
        "generated_at": timestamp,
        "backup_dir": str(backup_dir.relative_to(ROOT)).replace("\\", "/"),
        "starting_question_count": len(questions) - len(appended),
        "final_question_count": len(questions),
        "appended_count": len(appended),
        "skipped_existing_count": len(skipped_existing),
        "skipped_dump_duplicate_count": len(skipped_dump_duplicate),
        "skipped_needs_review_count": len(skipped_needs_review),
        "appended": appended,
        "skipped_existing": skipped_existing,
        "skipped_dump_duplicate": skipped_dump_duplicate,
        "skipped_needs_review": skipped_needs_review,
    }
    report_path = DUMP_DIR / "exam_dump_merge_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Appended {len(appended)} questions")
    print(f"Final question count: {len(questions)}")
    print(f"Skipped existing duplicates: {len(skipped_existing)}")
    print(f"Skipped dump duplicates: {len(skipped_dump_duplicate)}")
    print(f"Skipped needs_review: {len(skipped_needs_review)}")
    print(f"Backup: {backup_dir}")


if __name__ == "__main__":
    main()
