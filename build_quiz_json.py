import json
import re
import difflib
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent


COURSE_TF_ANSWERS = {
    ("C1", 158): "true",
    ("C1", 162): "true",
    ("C1", 165): "false",
    ("C1", 169): "false",
    ("C1", 256): "true",
    ("C1", 260): "true",
    ("C1", 262): "true",
    ("C1", 266): "false",
    ("C1", 270): "false",
    ("C1", 386): "false",
    ("C1", 388): "true",
    ("C1", 390): "true",
    ("C1", 392): "true",
    ("C1", 452): "true",
    ("C1", 456): "true",
    ("C1", 458): "false",
    ("C1", 461): "true",
    ("C1", 464): "true",
    ("C2", 176): "true",
    ("C2", 179): "false",
    ("C2", 181): "false",
    ("C2", 185): "true",
    ("C2", 390): "false",
    ("C2", 394): "true",
    ("C2", 397): "false",
    ("C2", 401): "false",
    ("C2", 404): "true",
    ("C3", 156): "false",
    ("C3", 160): "false",
    ("C3", 162): "true",
    ("C3", 167): "false",
    ("C3", 320): "false",
    ("C3", 322): "true",
    ("C3", 325): "true",
    ("C3", 329): "false",
    ("C3", 332): "true",
    ("C3", 601): "true",
    ("C3", 605): "false",
    ("C3", 608): "true",
    ("C3", 612): "true",
    ("C3", 614): "true",
    ("C4", 209): "false",
    ("C4", 213): "true",
    ("C4", 216): "false",
    ("C4", 220): "false",
    ("C4", 604): "true",
    ("C4", 608): "true",
    ("C4", 611): "true",
    ("C4", 615): "true",
    ("C4", 618): "true",
    ("C5", 499): "false",
    ("C5", 503): "true",
    ("C5", 505): "true",
    ("C5", 509): "false",
    ("C5", 513): "false",
    ("C6", 114): "false",
    ("C6", 118): "true",
    ("C6", 121): "true",
    ("C6", 125): "true",
    ("C6", 129): "false",
    ("C6", 600): "false",
    ("C6", 604): "true",
    ("C6", 607): "false",
    ("C6", 611): "true",
    ("C6", 613): "true",
    ("C7", 143): "true",
    ("C7", 147): "true",
    ("C7", 149): "true",
    ("C7", 151): "true",
    ("C7", 227): "false",
    ("C7", 231): "false",
    ("C7", 233): "false",
    ("C7", 235): "true",
    ("C7", 239): "true",
    ("C8", 191): "true",
    ("C8", 195): "false",
    ("C8", 199): "true",
    ("C8", 203): "true",
    ("C8", 207): "true",
    ("C8", 458): "true",
    ("C8", 462): "true",
    ("C8", 466): "true",
    ("C8", 470): "true",
    ("C8", 474): "true",
    ("C9", 381): "true",
    ("C9", 383): "true",
    ("C9", 387): "true",
    ("C9", 390): "true",
    ("C9", 394): "true",
    ("C9", 662): "true",
    ("C9", 664): "true",
    ("C9", 668): "false",
    ("C9", 672): "false",
    ("C9", 676): "false",
    ("C10", 296): "true",
    ("C10", 299): "true",
    ("C10", 303): "true",
    ("C10", 306): "true",
    ("C10", 309): "false",
    ("C10", 487): "true",
    ("C10", 491): "true",
    ("C10", 495): "true",
    ("C10", 499): "false",
    ("C10", 503): "false",
    ("C11", 86): "false",
    ("C11", 90): "false",
    ("C11", 92): "true",
    ("C11", 96): "true",
    ("C11", 100): "true",
    ("C11", 157): "false",
    ("C11", 159): "true",
    ("C11", 162): "true",
    ("C11", 166): "true",
    ("C11", 170): "false",
    ("C11", 256): "true",
    ("C11", 258): "true",
    ("C11", 260): "false",
    ("C11", 264): "true",
    ("C11", 267): "false",
    ("C11", 494): "false",
    ("C11", 497): "true",
    ("C11", 500): "false",
    ("C11", 504): "false",
    ("C11", 507): "true",
    ("C12", 71): "true",
    ("C12", 75): "false",
    ("C12", 79): "true",
    ("C12", 83): "false",
    ("C12", 87): "false",
    ("C12", 166): "false",
    ("C12", 171): "true",
    ("C12", 173): "true",
    ("C12", 177): "true",
    ("C12", 180): "false",
    ("C12", 290): "true",
    ("C12", 293): "false",
    ("C12", 295): "true",
    ("C12", 299): "true",
    ("C12", 302): "true",
    ("C12", 421): "true",
    ("C12", 423): "true",
    ("C12", 425): "true",
    ("C12", 427): "false",
    ("C12", 430): "true",
}

COURSE_PARAPHRASE_DUPLICATES = {
    ("C1", 169),  # OCR-prefixed duplicate of the setup/productivity statement
    ("C3", 322),  # setup time is considered/must be considered
    ("C3", 608),  # 50% from/of the selling price
}

COURSE_QUESTION_OVERRIDES = {
    ("C4", 618): "In the case of a conveyor-type transport system, the products should be distributed evenly.",
    ("C10", 296): "The order release module may contain the list of necessary raw materials.",
    ("C10", 487): "The order progress module generates progress reports.",
    ("C12", 71): "The ultra modern manufacturing involves the use of cyber-physical systems.",
    ("C12", 87): "The cyber-physical systems are related to the third industrial revolution.",
    ("C12", 180): "The embedded systems encapsulate the cyber-physical systems.",
}


def normalize_question(text):
    text = clean_text(text).lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def clean_text(text):
    text = text.replace("\ufeff", "").replace("\f", " ")
    text = text.replace("â€¢", "o")
    text = text.replace("•", "o")
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"^[✓vV/\\'\s]+", "", text).strip()
    text = re.sub(r"^[xX]\s+", "", text).strip()
    text = re.sub(r"^(?:o|0|O|CI|Cl|C1|IZI|I3I|rn|☐|☑)\s+", "", text).strip()
    text = re.sub(r"^(?:o|0|O|CI|Cl|C1|IZI|I3I|rn)(?=[A-Z0-9])", "", text).strip()
    text = re.sub(r"\s+[01]/1$", "", text).strip()
    text = text.replace("systerns", "systems")
    text = text.replace("prcduction", "production")
    text = text.replace("prcductivity", "productivity")
    text = text.replace("rn0vement", "movement")
    text = text.replace("CMIpany", "company")
    text = text.replace("Balch", "Batch")
    text = text.replace("COnformanæ", "conformance")
    text = text.replace("proæss", "process")
    text = text.replace("(nntrol", "control")
    text = text.replace("prcKåuct", "product")
    text = text.replace("serviæs", "services")
    text = text.replace("souræs", "sources")
    text = text.replace("cmnpany", "company")
    text = text.replace("0vement stock", "movement stock")
    text = text.replace("tums", "turns")
    text = text.replace("Rr server", "per server")
    text = text.replace("proeuction", "production")
    text = text.replace("Just-in-Timeo", "Just-in-Time")
    text = text.replace("�", '"')
    text = text.replace("Apure", "A pure")
    text = text.replace("relative v/ ease", "relative ease")
    text = text.replace("•", "")
    return text.strip(" -")


def parse_answer_lines(lines):
    useful = [line for line in lines if line.strip()]
    bullet_mode = any(re.match(r"\s*(?:o|•|â€¢)\s+", line) for line in useful)
    answers = []
    current = None

    continuation_endings = (
        " the", " a", " an", " and", " or", " of", " in", " into", " from",
        " with", " without", " to", " for", " on", " is", " are", " dual",
        " single", " depend on", " depends on"
    )

    for raw in useful:
        bullet = re.match(r"\s*(?:o|•|â€¢)\s+(.*)", raw)
        if bullet:
            if current:
                answers.append(clean_text(current))
            current = bullet.group(1).strip()
            continue

        line = clean_text(raw)
        if not line:
            continue
        if bullet_mode and current:
            current += " " + line
        elif bullet_mode:
            current = line
        else:
            if current is None:
                current = line
            elif re.match(r"^[a-z]", line) or current.lower().endswith(continuation_endings):
                current += " " + line
            else:
                answers.append(clean_text(current))
                current = line

    if current:
        answers.append(clean_text(current))
    return [a for a in answers if a]


def parse_text_pdf():
    txt = (ROOT / "quizzes_english.txt").read_text(encoding="utf-8", errors="replace")
    txt = txt.replace("\f", "\n")
    lines = txt.splitlines()

    questions = []
    quiz = None
    block = []

    def flush_block():
        nonlocal block, quiz
        if not block or quiz is None:
            block = []
            return

        first = block[0]
        m = re.match(r"\s*(\d+)\.\s*(.*)", first)
        if not m:
            block = []
            return
        qnum = int(m.group(1))
        block[0] = m.group(2)

        answer_idx = None
        for i, line in enumerate(block):
            if re.match(r"\s*(?:Correct answer|Answer)\s*:", line, re.I):
                answer_idx = i
                break
        if answer_idx is None:
            block = []
            return

        stem_lines = block[:answer_idx]
        answer_label = block[answer_idx]
        answer_lines = []
        same_line = answer_label.split(":", 1)[1].strip()
        if same_line:
            answer_lines.append(same_line)
        answer_lines.extend(block[answer_idx + 1 :])

        q_lines = []
        options = []
        current_option = None
        for raw in stem_lines:
            line = raw.rstrip()
            if not line.strip():
                continue
            opt = re.match(r"\s*(?:o|•|â€¢)\s+(.*)", line)
            if opt:
                if current_option:
                    options.append(clean_text(current_option))
                current_option = opt.group(1).strip()
            elif current_option is not None and line.startswith(" " * 8):
                current_option += " " + line.strip()
            else:
                if current_option:
                    options.append(clean_text(current_option))
                    current_option = None
                q_lines.append(line.strip())
        if current_option:
            options.append(clean_text(current_option))

        answers = parse_answer_lines(answer_lines)
        questions.append(
            {
                "id": f"quizzes_english_q{quiz}_{qnum}",
                "source_file": "quizzes_english.pdf",
                "quiz": f"Quiz {quiz}",
                "question_number": qnum,
                "question": clean_text(" ".join(q_lines)),
                "options": options,
                "correct_answers": answers,
            }
        )
        block = []

    for line in lines:
        qm = re.match(r"\s*Quiz\s+(\d+)\s*$", line, re.I)
        start = re.match(r"\s*\d+\.\s+", line)
        if qm:
            flush_block()
            quiz = int(qm.group(1))
            continue
        if start and block:
            flush_block()
        if quiz is not None:
            block.append(line)
    flush_block()
    return questions


def row_status(img, y):
    w, h = img.size
    y = int(max(0, min(h - 1, y)))
    step = max(1, w // 140)
    total = green = pink = 0
    for x in range(int(w * 0.10), int(w * 0.92), step):
        r, g, b = img.getpixel((x, y))[:3]
        total += 1
        if g > r + 5 and g > b + 2 and g > 215 and r > 200 and b > 200:
            green += 1
        if r > g + 8 and r > b + 8 and r > 230 and g > 190 and b > 190:
            pink += 1
    if total and green / total > 0.22:
        return "green"
    if total and pink / total > 0.22:
        return "pink"
    return "plain"


def is_score_text(text):
    text = text.strip()
    return bool(re.fullmatch(r"[01]/1", text)) or bool(re.search(r"\b[01]/1$", text))


def is_noise_line(text):
    t = text.strip()
    if not t:
        return True
    if re.fullmatch(r"[xXvV/'\\✓]+", t):
        return True
    if re.fullmatch(r"(?:points?|ints?|o)", t, re.I):
        return True
    if re.search(r"f\s*10", t, re.I):
        return True
    if re.fullmatch(r"(?:o+f0|0\s*of\s*0).*", t, re.I):
        return True
    if re.search(r"\d+\s+of\s+10\s+p(?:o?i?nts|ints)", t, re.I):
        return True
    if re.fullmatch(r"[01]/1", t):
        return True
    return False


def join_items(lines, gap_threshold):
    items = []
    current = []
    last_y = None
    for line in lines:
        text = clean_text(line["text"])
        if not text or text.lower() == "correct answer" or is_noise_line(text):
            continue
        if last_y is not None and line["y"] - last_y > gap_threshold and current:
            items.append(clean_text(" ".join(current)))
            current = []
        current.append(text)
        last_y = line["y"]
    if current:
        items.append(clean_text(" ".join(current)))
    return [i for i in items if i]


def card_question_and_options(card, gap_threshold):
    lines = [l for l in card if not is_noise_line(l["text"])]
    if not lines:
        return "", []

    # Split question stem from options at the first larger vertical gap after the stem.
    split_idx = None
    for i in range(1, len(lines)):
        if lines[i]["text"].strip().lower() == "correct answer":
            break
        if lines[i]["y"] - lines[i - 1]["y"] > gap_threshold:
            split_idx = i
            break
    if split_idx is None:
        split_idx = 1

    q_lines = []
    for line in lines[:split_idx]:
        t = clean_text(line["text"])
        if t and t.lower() != "correct answer":
            q_lines.append(t)

    pre_answer = []
    for line in lines[split_idx:]:
        if line["text"].strip().lower() == "correct answer":
            break
        pre_answer.append(line)
    return clean_text(" ".join(q_lines)), join_items(pre_answer, gap_threshold)


def parse_ocr_pages():
    pages = json.loads((ROOT / "ocr_lines.json").read_text(encoding="utf-8-sig"))
    questions = []
    page_quiz_index = 0
    question_index = 0

    for page_no, page in enumerate(pages, start=1):
        img = Image.open(page["path"]).convert("RGB")
        lines = []
        for raw in page["lines"]:
            line = dict(raw)
            line["status"] = row_status(img, line["y"] + line["height"] / 2)
            lines.append(line)
        lines.sort(key=lambda l: (l["y"], l["x"]))

        score_ys = []
        if page["file"].startswith("q2025"):
            for line in lines:
                if is_score_text(line["text"]):
                    score_ys.append(line["y"])
        else:
            # The standalone tall PNGs often mangle the score markers. Their cards
            # are separated by a consistent large vertical gap.
            content = [l for l in lines if not is_noise_line(l["text"])]
            for i, line in enumerate(content):
                if i == 0 or line["y"] - content[i - 1]["y"] > 70:
                    score_ys.append(line["y"])
        if not score_ys:
            content = [l for l in lines if not is_noise_line(l["text"])]
            for i, line in enumerate(content):
                if i == 0 or line["y"] - content[i - 1]["y"] > page["height"] * 0.075:
                    score_ys.append(line["y"])
        if page["file"].startswith("q2025"):
            content = [l for l in lines if not is_noise_line(l["text"])]
            for i, line in enumerate(content):
                if i == 0:
                    continue
                if clean_text(line["text"]).lower() == "correct answer":
                    continue
                if line["y"] - content[i - 1]["y"] > 150:
                    score_ys.append(line["y"])
        score_ys = sorted(set(round(y, 1) for y in score_ys))

        # A visible "x" line on the selected wrong row can also match score grouping;
        # keep only markers near the upper part of each card by enforcing distance.
        filtered = []
        for y in score_ys:
            if not filtered or y - filtered[-1] > page["height"] * 0.07:
                filtered.append(y)
        score_ys = filtered

        for idx, start_y in enumerate(score_ys):
            end_y = score_ys[idx + 1] if idx + 1 < len(score_ys) else page["height"] + 1
            card = [
                l for l in lines
                if start_y - page["height"] * 0.025 <= l["y"] < end_y - page["height"] * 0.015
                and not re.search(r"\d+\s+of\s+10\s+p(?:o?i?nts|ints)", l["text"], re.I)
            ]
            if not card:
                continue

            heights = sorted(l["height"] for l in card if l["height"] > 0)
            med_h = heights[len(heights) // 2] if heights else page["height"] / 100
            gap_threshold = max(med_h * 2.05, 24)

            q_text, options = card_question_and_options(card, gap_threshold)
            if not q_text:
                continue

            ca_idx = None
            for i, line in enumerate(card):
                if clean_text(line["text"]).lower() == "correct answer":
                    ca_idx = i
                    break

            if ca_idx is not None:
                correct_lines = [l for l in card[ca_idx + 1 :] if not is_noise_line(l["text"])]
                correct_answers = join_items(correct_lines, gap_threshold)
            else:
                correct_lines = [
                    l for l in card
                    if l["status"] == "green" and clean_text(l["text"]).lower() != "correct answer"
                ]
                # Remove question rows if a heading is mistakenly sampled as green.
                correct_lines = [l for l in correct_lines if l["y"] > min(x["y"] for x in card) + gap_threshold]
                correct_answers = join_items(correct_lines, gap_threshold)

            if correct_answers:
                question_index += 1
                questions.append(
                    {
                        "id": f"quizes_english_2025_{question_index:03d}",
                        "source_file": "Quizes_English_2025.pdf" if page["file"].startswith("q2025") else page["file"],
                        "source_page": page_no if page["file"].startswith("q2025") else None,
                        "quiz": None,
                        "question_number": None,
                        "question": q_text,
                        "options": options,
                        "correct_answers": correct_answers,
                    }
                )
    return questions


def manual_image_questions():
    raw = {
        "QUIZ 11.png": [
            (
                "Which of the following are dimensions of the quality?",
                ["reliability", "conformance", "serviceability", "cost", "aesthetic appeal"],
                ["reliability", "conformance", "serviceability", "aesthetic appeal"],
            ),
            (
                "What tests should pass a manufacturing system to be considered flexible?",
                ["productivity test", "costs test", "part variety test", "new part test", "error recovery test"],
                ["part variety test", "new part test", "error recovery test"],
            ),
            (
                "Modern Quality Control focuses on inspection of the products:",
                ["after they are produced", "only at the beginning of the production process", "during the production process"],
                ["during the production process"],
            ),
            (
                "In the case of level production strategy:",
                [
                    "the number of employees is constant.",
                    "the number of hours worked is constant.",
                    "the number of employees is variable.",
                    "the number of hours worked is variable.",
                ],
                ["the number of employees is constant.", "the number of hours worked is constant."],
            ),
            (
                "Which of the following are specific to traditional quality control (QC)?",
                [
                    "is the responsibility of the inspection department",
                    "is performed fully automated",
                    "is performed only after the product has been manufactured",
                    "is performed for each step of the production process",
                    "statistical quality control techniques are used",
                ],
                [
                    "is the responsibility of the inspection department",
                    "is performed only after the product has been manufactured",
                    "statistical quality control techniques are used",
                ],
            ),
            (
                "Quality can be defined as the degree of satisfaction of customer requirements.",
                ["false", "true"],
                ["true"],
            ),
            (
                "In CIM, manufacturing batch size reduction leads to increased production costs.",
                ["true", "false"],
                ["false"],
            ),
            (
                "What are the advantages of TQM?",
                [
                    "increasing consumer satisfaction",
                    "constantly improving the quality of products and services",
                    "increasing productivity",
                ],
                [
                    "increasing consumer satisfaction",
                    "constantly improving the quality of products and services",
                    "increasing productivity",
                ],
            ),
            (
                'In the case of "Just-in-Time" manufacturing systems, inventories represented by WIP are:',
                ["zero", "non-zero"],
                ["non-zero"],
            ),
            (
                "The durability of a product is defined as the life of the product until the first failure.",
                ["true", "false"],
                ["false"],
            ),
        ],
        "QUIZ 12.png": [
            (
                "Which of the following statements is / are true?",
                [
                    "There are no companies who by their activity have no impact on the environment.",
                    "There are companies who by their activity have no impact on the environment.",
                ],
                ["There are no companies who by their activity have no impact on the environment."],
            ),
            (
                "How can a green product be manufactured?",
                [
                    "increasing the number of materials",
                    "increasing the efficiency of production processes",
                    "using renewable materials",
                    "reducing the life cycle of the product",
                ],
                ["increasing the efficiency of production processes", "using renewable materials"],
            ),
            (
                "In sustainable manufacturing the focus is on:",
                [
                    "making products using more materials",
                    "avoid using risk materials",
                    "reducing waste in the manufacturing process",
                ],
                ["avoid using risk materials", "reducing waste in the manufacturing process"],
            ),
            (
                "Lean and clean manufacturing objectives are:",
                [
                    "to eliminate or reduce those activities that do not add value to a product.",
                    "to increase the number of material used",
                    "to increase the number of packages for a product.",
                    "to eliminate or reduce the environmental impact.",
                ],
                [
                    "to eliminate or reduce those activities that do not add value to a product.",
                    "to eliminate or reduce the environmental impact.",
                ],
            ),
            (
                "Which of the following is / are example(s) of clean technologies?",
                [
                    "solid waste management",
                    "wastewater treatment",
                    "recycling",
                    "the use of wind turbines",
                    "the use of asbestos panels",
                ],
                ["solid waste management", "wastewater treatment", "recycling", "the use of wind turbines"],
            ),
            (
                "Sustainability requires a balance between:",
                ["people", "environment", "profitability"],
                ["people", "environment", "profitability"],
            ),
            (
                "Sustainability assurance is:",
                ["a journey for any company.", "a destination for any company."],
                ["a journey for any company."],
            ),
            (
                "A green product is:",
                [
                    "a product designed to increase its environmental impact.",
                    "a product colored in brown",
                    "a product designed to reduce its environmental impact.",
                    "a product colored in green",
                ],
                ["a product designed to reduce its environmental impact."],
            ),
            (
                "Which of the following statements is / are true?",
                [
                    "Utilization of non-renewable materials must increase to reduce waste.",
                    "The energy consumed per unit of product, according to the principles of sustainability, can be increased if it comes from renewable sources.",
                    "Clean manufacturing ensures responsible use of energy.",
                    "In lean manufacturing there is overproduction.",
                ],
                ["Clean manufacturing ensures responsible use of energy."],
            ),
            (
                "The industrial ecology focuses on:",
                [
                    "reducing pollution",
                    "identifying inefficiencies and losses in manufacturing processes",
                    "preventing pollution",
                ],
                ["identifying inefficiencies and losses in manufacturing processes", "preventing pollution"],
            ),
        ],
    }
    out = []
    for source_file, items in raw.items():
        for i, (question, options, answers) in enumerate(items, start=1):
            out.append(
                {
                    "id": f"{source_file.lower().replace(' ', '_').replace('.png', '')}_{i:02d}",
                    "source_file": source_file,
                    "source_page": None,
                    "quiz": source_file.replace(".png", ""),
                    "question_number": i,
                    "question": question,
                    "options": options,
                    "correct_answers": answers,
                }
            )
    return out


def apply_ocr_corrections(questions):
    corrected = []
    inserted_page13 = False
    for q in questions:
        if q["source_file"] != "Quizes_English_2025.pdf":
            corrected.append(q)
            continue

        page = q.get("source_page")
        question = q["question"]

        if page == 1 and question.startswith("Which of the following is/are not component"):
            q["options"] = ["CAD", "CAN", "CAQ", "ERP"]

        if page == 6 and question.startswith("A project manufacturing system can be used if"):
            q["options"] = [
                "the design drawings are simple",
                "the customer is identified before production starts",
                "the total time for production is short",
                "products are complex",
            ]
            q["correct_answers"] = [
                "the customer is identified before production starts",
                "products are complex",
            ]

        if page == 13 and question.startswith("Which of the following statements"):
            if not inserted_page13:
                corrected.append(
                    {
                        "id": "quizes_english_2025_page13_asrs_capacity",
                        "source_file": "Quizes_English_2025.pdf",
                        "source_page": 13,
                        "quiz": None,
                        "question_number": None,
                        "question": (
                            "Each side of a two-aisle ASRS contains 10 storage compartments in the "
                            "length direction and 10 compartments vertically. All storage compartments "
                            "will be the same size to accommodate standard size pallets of dimensions: "
                            "x = 1 m, y = 1 m. The height of a unit load is z = 1 m. What is the "
                            "storage capacity of the ASRS?"
                        ),
                        "options": ["400", "100", "200", "10"],
                        "correct_answers": ["400"],
                    }
                )
                inserted_page13 = True
            q["correct_answers"] = [
                "Less total space is required in a storage system that uses randomized storage.",
                "Higher throughput can be achieved when a dedicated storage strategy is implemented.",
            ]

        if page == 15 and question.startswith("What changes can be made to increase or decrease production capacity over long term"):
            q["correct_answers"] = [
                "increase the production rate, by making improvements in methods or process technology",
                "increase the number of work centers in the shop",
            ]

        if page == 21 and question.startswith("A processing operation"):
            q["correct_answers"] = [
                "transforms a work material from one state of completion to a more advanced state that is closer to the final desired part or product"
            ]

        if page == 23 and question.startswith("Dedicated storage is used when"):
            q["correct_answers"] = [
                "items are stored in part number or product number sequence",
                "items are stored according to their activity-to-space ratios",
            ]

        if page == 25 and question.startswith("Bottleneck station is the station with"):
            q["options"] = [
                "the average workload per server",
                "the highest workload per server",
                "the lowest workload per server",
            ]
            q["correct_answers"] = ["the highest workload per server"]

        if page == 27 and question.startswith("9/ Which of the following statements"):
            q["question"] = "Which of the following statements is / are correct?"
            q["correct_answers"] = [
                "Order scheduling assigns the production orders to the various work centers in the plant.",
                "Order progress module monitors the status of the various orders in the plant.",
                "Order release provides the documentation needed to process a production order through the factory.",
            ]

        if page == 33 and question.startswith("Traditional quality control"):
            q["question"] = "Traditional quality control (QC):"
            q["correct_answers"] = [
                "is the responsibility of the inspection department",
                "involves the use of statistical quality control techniques",
            ]

        q["question"] = clean_text(q["question"])
        q["options"] = [clean_text(o) for o in q["options"] if clean_text(o)]
        q["correct_answers"] = [clean_text(a) for a in q["correct_answers"] if clean_text(a)]
        corrected.append(q)
    return corrected


def parse_course_tf_questions(existing_questions):
    candidate_path = ROOT / "course_tf_candidates.json"
    if not candidate_path.exists():
        return []

    candidates = json.loads(candidate_path.read_text(encoding="utf-8"))
    existing_norms = {normalize_question(q["question"]) for q in existing_questions}
    added_norms = set()
    added = []
    skipped = []

    base_for_fuzzy = [(normalize_question(q["question"]), q) for q in existing_questions]

    for item in candidates:
        key = (item["course"], int(item["line"]))
        if key not in COURSE_TF_ANSWERS:
            raise ValueError(f"Missing course answer for {key}")

        question = COURSE_QUESTION_OVERRIDES.get(key, item["question"])
        question = clean_text(question)
        qnorm = normalize_question(question)

        skip_reason = None
        if qnorm in existing_norms:
            skip_reason = "exact duplicate"
        elif qnorm in added_norms:
            skip_reason = "duplicate within course extraction"
        elif key in COURSE_PARAPHRASE_DUPLICATES:
            skip_reason = "paraphrase duplicate"

        if skip_reason:
            best = None
            if base_for_fuzzy:
                best = max(
                    ((difflib.SequenceMatcher(None, qnorm, n).ratio(), q) for n, q in base_for_fuzzy),
                    key=lambda pair: pair[0],
                )
            skipped.append(
                {
                    "course": item["course"],
                    "line": item["line"],
                    "question": question,
                    "reason": skip_reason,
                    "matched_existing_id": best[1]["id"] if best and best[0] > 0.85 else None,
                }
            )
            continue

        added_norms.add(qnorm)
        added.append(
            {
                "id": f"course_{item['course'].lower()}_line{item['line']}",
                "source_file": item["source_file"],
                "source_page": None,
                "source_text_file": item.get("source_text_file"),
                "source_line": item["line"],
                "course": item["course"],
                "quiz": f"{item['course']} Self Assessment",
                "question_number": item["question_number"],
                "question": question,
                "options": ["true", "false"],
                "correct_answers": [COURSE_TF_ANSWERS[key]],
            }
        )

    report = {
        "candidate_count": len(candidates),
        "added_count": len(added),
        "skipped_count": len(skipped),
        "skipped": skipped,
    }
    (ROOT / "course_import_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return added


def main():
    text_questions = parse_text_pdf()
    ocr_questions = apply_ocr_corrections([
        q for q in parse_ocr_pages()
        if q["source_file"] not in {"QUIZ 11.png", "QUIZ 12.png"}
    ])
    image_questions = manual_image_questions()
    base_questions = text_questions + ocr_questions + image_questions
    course_questions = parse_course_tf_questions(base_questions)
    data = {
        "schema_version": 1,
        "generated_from": [
            "quizzes_english.pdf",
            "Quizes_English_2025.pdf",
            "QUIZ 11.png",
            "QUIZ 12.png",
            "cim courses/C1_unlocked.pdf",
            "cim courses/C2_unlocked.pdf",
            "cim courses/C3_unlocked.pdf",
            "cim courses/C4_unlocked.pdf",
            "cim courses/C5_unlocked.pdf",
            "cim courses/C6_unlocked.pdf",
            "cim courses/C7_unlocked.pdf",
            "cim courses/C8_unlocked.pdf",
            "cim courses/C9_unlocked.pdf",
            "cim courses/C10_unlocked.pdf",
            "cim courses/C11_unlocked.pdf",
            "cim courses/C12_unlocked.pdf",
        ],
        "question_count": len(base_questions) + len(course_questions),
        "questions": base_questions + course_questions,
    }
    (ROOT / "quiz_questions.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"text_pdf={len(text_questions)} "
        f"scanned_pdf={len(ocr_questions)} "
        f"images={len(image_questions)} "
        f"courses={len(course_questions)} "
        f"total={data['question_count']}"
    )


if __name__ == "__main__":
    main()
