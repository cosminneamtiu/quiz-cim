import json
import re
import shutil
from collections import Counter
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
BANK_PATH = ROOT / "quiz_questions.json"
SITE_DATA_PATH = ROOT / "quiz_site" / "quiz-data.js"
REPORT_PATH = ROOT / "explanation_audit_report.json"
BACKUP_ROOT = ROOT / "exam questions dumps" / "backups"
COURSE_TEXT_DIR = ROOT / "course_text"


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "can",
    "for",
    "from",
    "if",
    "in",
    "into",
    "is",
    "it",
    "its",
    "of",
    "on",
    "or",
    "the",
    "to",
    "what",
    "when",
    "where",
    "which",
    "with",
}


SPECIAL_EXPLANATIONS = {
    "course_c10_line309": "False. The earliest due date rule gives highest priority to the part or job with the earliest due date, because that is the one closest to being late. A part with the latest due date has lower urgency, not highest priority.",
    "quizzes_english_q2_5": "Use the learning-curve formula Tn = T1 x n^m. Here T1 = 100 minutes and 100^m = 0.35, so T100 = 100 x 0.35 = 35 minutes.",
    "quizes_english_2025_015": "Use the learning-curve formula Tn = T1 x n^m. Here T1 = 10 minutes and 10^m = 0.59, so T10 = 10 x 0.59 = 5.9 minutes.",
    "exam_dump_quiz_questions_part7_003": "Use the learning-curve formula Tn = T1 x n^m. Here T1 = 4 minutes and 200^m = 0.3, so T200 = 4 x 0.3 = 1.2 minutes.",
    "quizzes_english_q5_3": "AS/RS capacity per aisle is 2 x compartments along the length x vertical compartments. For one aisle, capacity = 2 x 10 x 10 = 200 storage compartments.",
    "quizes_english_2025_page13_asrs_capacity": "AS/RS capacity per aisle is 2 x compartments along the length x vertical compartments. With two aisles, total capacity = 2 aisles x 2 x 10 x 10 = 400 storage compartments.",
    "exam_dump_quiz_questions_and_options_001": "Each aisle has two sides, so total capacity is aisles x 2 x horizontal compartments x vertical levels. The equation is 120 = 2 x 2 x 10 x levels, so levels = 120 / 40 = 3.",
    "exam_dump_quiz_questions_and_options_002": "The course AS/RS width formula is W = 3 x (x + a) for one aisle. With x = 1 m and a = 0.1 m, one aisle is 3 x 1.1 = 3.3 m; for three aisles, total width is 3 x 3.3 = 9.9 m.",
    "quizzes_english_q6_3": "In a monocode structure, each digit represents one level in the code hierarchy. A 4-digit monocode therefore requires 4 levels.",
    "exam_dump_quiz_questions_part4_003": "Ending inventory balance is previous balance plus monthly production minus sales. For December: 3.60 + 9.60 - 11.60 = 1.60.",
    "exam_dump_quiz_questions_part8_002": "Because January is the first production month, the previous inventory balance is 0. Ending inventory is 0 + 5.50 - 6.60 = -1.10.",
    "exam_dump_quiz_questions_part5_001": "Utilization is actual output divided by production capacity. Capacity is 80 hours x 10 parts/hour = 800 parts; 320 / 800 = 0.40, or 40%.",
    "exam_dump_quiz_questions_part6_001": "Total output is the sum over all models: 4 TV models x 300 each = 1200, and 3 laptop models x 600 each = 1800. Total = 1200 + 1800 = 3000 products.",
    "exam_dump_quiz_questions_part6_008": "Parts and materials are 50% of manufacturing cost, and manufacturing cost is 40% of selling price. Therefore parts and materials are 0.50 x 0.40 = 0.20, or 20% of selling price.",
    "exam_dump_quiz_questions_part6_010": "Availability is (MTBF - MTTR) / MTBF. With MTBF = 100 days and MTTR = 2 days, availability = (100 - 2) / 100 = 0.98, or 98%.",
    "exam_dump_quiz_questions_part7_002": "Use the MPS available-balance rule: Available_i = Available_(i-1) + MPS_i - Forecast_i. Following the table and keeping safety stock at least 10, the next batch should be ready on day 5.",
    "exam_dump_quiz_questions_part7_007": "Use Available_i = Available_(i-1) + MPS_i - Forecast_i. Day 5 is 3 + 0 - 2 = 1; day 6 is 1 + 0 - 1 = 0; day 7 is 0 + 10 - 5 = 5.",
    "exam_dump_quiz_questions_part9_012": "PSM is the percentage of in-sequence moves. Using the workflow counts from the course example, the in-sequence share is 70.37%.",
    "exam_dump_quiz_questions_part4_002": "Explode the bill of materials for one P1 product through the shown product structure. The required child quantities multiply through the levels, giving 30 units of M6.",
    "quizzes_english_q9_1": "Explode the product structure for the full batch, multiplying the required M5 quantity per P1 through the bill-of-material levels and then by 10 finished P1 products; this gives 40 units of M5.",
    "exam_dump_quiz_questions_part4_001": "The observed input/output pairs do not define one consistent maximum production-rate conclusion from the provided answer choices, so the accepted choice is none of the above.",
    "quizes_english_2025_032": "The false statement is that material handling costs should be as large as possible. The course/quiz answer states those costs should be as small as possible, so the opposite wording is the option to choose.",
}


SPECIAL_SOURCE_HINTS = {
    "quizzes_english_q2_5": {"course": "C2", "source_text_file": "course_text/C2_unlocked.txt", "line": 380, "note": "learning curve"},
    "quizes_english_2025_015": {"course": "C2", "source_text_file": "course_text/C2_unlocked.txt", "line": 380, "note": "learning curve"},
    "quizes_english_2025_page13_asrs_capacity": {"course": "C5", "source_text_file": "course_text/C5_unlocked.txt", "line": 188, "note": "AS/RS capacity formula"},
    "quizzes_english_q5_3": {"course": "C5", "source_text_file": "course_text/C5_unlocked.txt", "line": 188, "note": "AS/RS capacity formula"},
    "quizzes_english_q6_3": {"source_file": "quizzes_english.pdf", "note": "local quiz answer key"},
    "quizes_english_2025_032": {"source_file": "Quizes_English_2025.pdf", "source_page": 10, "note": "local quiz answer key and C4 cost statement"},
}


def clean_text(text):
    text = str(text or "").replace("\ufeff", "").replace("\f", " ")
    replacements = {
        "Ã—": "x",
        "âˆ’": "-",
        "â€“": "-",
        "â€”": "-",
        "ï‚§": "",
        "ï±": "",
        "â€œ": '"',
        "â€": '"',
        "â€ž": '"',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return re.sub(r"\s+", " ", text).strip()


def normalize(text):
    text = clean_text(text).lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def answer_list(answers):
    answers = [str(answer) for answer in answers if str(answer).strip()]
    if not answers:
        return "the accepted answer"
    if len(answers) == 1:
        return f'"{answers[0]}"'
    return ", ".join(f'"{answer}"' for answer in answers[:-1]) + f', and "{answers[-1]}"'


def is_true_false(question):
    options = [normalize(option) for option in question.get("options", [])]
    answers = [normalize(answer) for answer in question.get("correct_answers", [])]
    return len(options) == 2 and set(options) == {"true", "false"} and len(answers) == 1 and answers[0] in {"true", "false"}


def is_calculation(question):
    text = normalize(question.get("question", ""))
    if not question.get("options"):
        return True
    if any(word in text for word in ["calculate", "calculates", "calculation"]):
        return True
    answers_text = " ".join(question.get("correct_answers", []))
    has_numeric_answer = bool(re.search(r"\d", answers_text))
    return has_numeric_answer and any(word in text for word in ["availability", "utilization", "capacity", "rate", "time", "stock"])


def question_text(question):
    return " ".join(
        [
            str(question.get("question", "")),
            " ".join(question.get("options", [])),
            " ".join(question.get("correct_answers", [])),
        ]
    )


def contains_any(text, *needles):
    return any(needle in text for needle in needles)


def concept_explanation(question):
    raw = question_text(question)
    text = normalize(raw)
    answers = question.get("correct_answers", [])
    accepted = answer_list(answers)
    answer_norm = normalize(" ".join(answers))
    is_false = is_true_false(question) and normalize(answers[0]) == "false"
    is_true = is_true_false(question) and normalize(answers[0]) == "true"

    if "earliest due date" in text:
        return "False. The earliest due date rule gives highest priority to the part or job with the earliest due date. The statement says latest due date, which reverses the rule."

    if contains_any(text, "shortest processing time", "shortest operation next"):
        return f"The correct answer is {accepted}. This dispatching rule gives priority to the job with the shortest next processing time, so it tends to reduce waiting time in the queue."

    if "first come first served" in text:
        return f"The correct answer is {accepted}. First-come-first-served keeps the arrival order: the job that enters the queue first receives priority first."

    if "critical ratio" in text:
        return f"The correct answer is {accepted}. Critical ratio compares the time remaining until due date with the work remaining; it is used to identify jobs most at risk of being late."

    if "order slack time" in text or "slack time" in text:
        return f"The correct answer is {accepted}. Slack-based priority uses the remaining time allowance after accounting for processing time; lower slack means higher urgency."

    if "learning curve" in text or "learning rate" in text:
        return f"The correct answer is {accepted}. A learning curve means the operation time decreases as repetitions increase, so later units take less time than the first unit."

    if "external challenge" in text or "internal challenge" in text or "traditional competition" in text or "global economy" in text:
        return f"The correct answer is {accepted}. Competition, partnerships, alliances, and the global economy are external pressures on a company, while internal challenges come from the company's own capabilities and organization."

    if "results of a production process" in text:
        return f"The correct answer is {accepted}. A production process can produce more than finished products; it also creates information, waste, scrap, emissions, or other outputs that must be controlled."

    if "early detection of faults" in text:
        if "increase" in text and is_false:
            return "The statement is false. Early fault detection normally reduces production cost because problems are found before they create scrap, rework, or downstream failures."
        return f"The correct answer is {accepted}. Detecting faults early reduces production cost by preventing defects from moving further through the process."

    if "batch size reduction" in text:
        if "classical" in text:
            return f"The correct answer is {accepted}. In classical production, reducing batch size can increase costs because more changeovers and setups are needed."
        return f"The correct answer is {accepted}. In CIM and modern flexible systems, batch-size reduction is supported by automation and quick changeover, so it should not be treated as automatically increasing cost."

    if "variety and quantity" in text:
        return f"The correct answer is {accepted}. Product variety and production quantity usually have an inverse relationship: high variety tends to mean lower quantities, while high quantity tends to mean lower variety."

    if "quality assessment" in text or "quality control" in text or "modern quality" in text or "traditional quality" in text or "house of quality" in text or "durability" in text or "quality can" in text or "quality standards" in text or "dimensions of the quality" in text:
        if "during the production" in answer_norm:
            return f"The correct answer is {accepted}. Quality is more effective when checked during production because defects can be detected and corrected before the end of the process."
        if "house of quality" in text:
            return f"The correct answer is {accepted}. The House of Quality translates customer requirements into measurable product or engineering characteristics."
        if "traditional quality" in text:
            return f"The correct answer is {accepted}. Traditional QC is inspection-centered and often belongs to the inspection department, while modern quality control emphasizes prevention during the process."
        if "durability" in text:
            return f"The correct answer is {accepted}. Durability concerns useful product life, not simply the time until the first failure."
        return f"The correct answer is {accepted}. Quality is judged by customer satisfaction and dimensions such as performance, reliability, conformance, durability, serviceability, features, and appearance."

    if "processing operation" in text or "transformation of the raw material" in text:
        return f"The correct answer is {accepted}. A processing operation transforms material from one state of completion to a more advanced state closer to the final part or product."

    if "assembly operation" in text or "pure assembly plant" in text or "dedicated manufacturer of assemblies" in text or "vertically integrated plant" in text or "assembling method" in text:
        if "pure assembly" in text:
            return f"The correct answer is {accepted}. A pure assembly plant does not produce parts; it joins already-made parts or components into assemblies."
        if "dedicated manufacturer" in text:
            return f"The correct answer is {accepted}. A dedicated assembly manufacturer focuses on assembly; it does not necessarily produce the components itself."
        if "vertically integrated" in text:
            return f"The correct answer is {accepted}. A vertically integrated plant performs more of the production chain itself, so it does not only assemble products."
        if "assembling method" in text:
            return f"The correct answer is {accepted}. The assembly method depends on expected throughput because production volume affects whether manual, automated, or specialized assembly methods are justified."
        return f"The correct answer is {accepted}. An assembly operation joins two or more components to create a new assembled entity."

    if "vehicle guidance" in text or "guidance technology" in text or "paint stripes" in text or "painted strips" in text or "self guidance" in text:
        if "sensor fusion" in answer_norm or "self guidance" in answer_norm:
            return f"The correct answer is {accepted}. Sensor-fusion-based self-guidance is the most modern option because the vehicle uses onboard sensing instead of only following a fixed physical guide path."
        if "paint stripes" in answer_norm:
            return f"The correct answer is {accepted}. Painted stripes are the cheapest vehicle-guidance method because they are simple physical path markings."
        if "painted strips" in text and is_false:
            return f"The correct answer is {accepted}. Painted strips are simple and cheap, but they are not the most advanced or most indicated guidance technology in every case."
        return f"The correct answer is {accepted}. Vehicle guidance technologies range from simple painted paths to embedded wires and modern self-guided systems."

    if "conveyor" in text or "fixed path" in text:
        if "conveyor systems" in answer_norm:
            return f"The correct answer is {accepted}. Conveyor systems are used to move relatively large quantities between specific locations over a fixed path."
        if is_false and "most efficient" in text:
            return "The statement is false. Recirculating conveyors are useful in some layouts, but the course does not treat them as the most efficient transport system in general."
        return f"The correct answer is {accepted}. Conveyor-based transport follows a defined path and works best when product flow is regular and evenly distributed."

    if "flow diagram" in text:
        return f"The correct answer is {accepted}. A flow diagram is a graphical charting method for analyzing material movement and transportation paths."

    if "vehicle based transport" in text or "transport systems based on vehicles" in text or "number of vehicles" in text or "cycle time for delivery" in text:
        if "delivery cycle time" in text or "cycle time" in text:
            return f"The correct answer is {accepted}. Vehicle delivery cycle time depends on travel time, loading time, unloading time, and related delays such as vehicle speed and distance."
        return f"The correct answer is {accepted}. The number of required vehicles depends on delivery-cycle time, workload, availability, and the required delivery rate."

    if "large and heavy components" in text or "large and heavy" in text:
        return f"The correct answer is {accepted}. Large and heavy items are typically moved with cranes and hoists; AGVs are more appropriate for pallet loads or flexible guided movement."

    if "part variety test" in text or "new part test" in text or "error recovery test" in text:
        if "part variety" in text:
            return f"The correct answer is {accepted}. The part variety test asks whether the system can process different part styles without batching them into one rigid sequence."
        if "new part" in text:
            return f"The correct answer is {accepted}. The new part test checks whether new part designs can be introduced into the existing product mix with relative ease."
        return f"The correct answer is {accepted}. A flexible manufacturing system should pass part-variety, schedule-change, error-recovery, and new-part tests."

    if "shop floor control" in text or ("order release" in text and "order scheduling" in text and "order progress" in text):
        if "b c a" in answer_norm:
            return f"The correct answer is {accepted}. A typical shop-floor-control flow is order release first, then order scheduling, then order progress monitoring."
        return f"The correct answer is {accepted}. Order release provides production documentation, order scheduling assigns orders to work centers, and order progress monitors order status."

    if "order release module" in text or "order scheduling module" in text or "order progress module" in text or "factory data collection" in text or "restore stocks" in text or "operations planning" in text:
        if "order release" in text:
            return f"The correct answer is {accepted}. Order release authorizes work and provides the documents/material information needed to start and process a production order."
        if "order scheduling" in text:
            return f"The correct answer is {accepted}. Order scheduling assigns orders and priorities to work centers so operations can be executed in the proper sequence."
        if "order progress" in text:
            return f"The correct answer is {accepted}. Order progress tracks order status and produces progress information for production control."
        if "factory data collection" in text:
            return f"The correct answer is {accepted}. Factory data collection feeds shop-floor status information back to the control system."
        if "restore stocks" in text:
            return f"The correct answer is {accepted}. Replenishing stock requires knowing both when to order and how much quantity to order."
        return f"The correct answer is {accepted}. Operations planning is part of manufacturing resource planning because it coordinates operations, resources, and schedules."

    if "manufacturing space ratio" in text or "space manufacturing ratio" in text:
        return f"The correct answer is {accepted}. Efficiency improves when more of the available space is used for value-adding manufacturing; this is why a larger manufacturing-space ratio, or equivalently a smaller space-manufacturing ratio, is better."

    if "complexity of a product" in text:
        return f"The correct answer is {accepted}. Product complexity is measured by the number of components for assemblies and by the number of operations needed for manufactured parts."

    if "capacity adjustments" in text or "capacity adjustment" in text or "increase or decrease production capacity" in text:
        if "long term" in text:
            return f"The correct answer is {accepted}. Long-term capacity changes involve structural decisions such as new equipment, new work centers, technology improvements, or plant expansion."
        return f"The correct answer is {accepted}. Short-term capacity changes are made with shifts, labor hours, temporary workers, overtime, or other scheduling/labor changes."

    if "cim system" in text:
        return f"The correct answer is {accepted}. CIM integrates design, planning, production, and control, so it improves process control, lowers inventories and batch sizes, and helps increase delivered quality."

    if "capacity planning" in text:
        return f"The correct answer is {accepted}. Capacity planning decides what equipment, labor, and resource capacity are needed to accomplish the production plan."

    if "production capacity increases" in text or "production rate increases" in text:
        return f"The correct answer is {accepted}. Production capacity is tied to production rate, so increasing the production rate increases the maximum output possible in a period."

    if "production is smaller" in text and "availability is larger" in text:
        return f"The correct answer is {accepted}. Higher machine availability means more usable operating time, so production should increase or stay higher, not become smaller."

    if "bottleneck" in text or "highest workload" in text:
        return f"The correct answer is {accepted}. The bottleneck is the station that limits the system because it has the highest workload, highest utilization, or lowest effective capacity."

    if "part machine incidence matrix" in text or "incidence matrix" in text:
        return f"The correct answer is {accepted}. In a part-machine incidence matrix, efficient machine grouping appears as dense blocks of 1s along the main diagonal."

    if "pim" in text or "pbm" in text or "work flow in the cell" in text or "workflow in the cell" in text:
        return f"The correct answer is {accepted}. Good cell layout has high in-sequence movement (PIM/PSM) and low backtracking movement (PBM)."

    if "chase production" in text or "level production" in text:
        if "chase" in text:
            return f"The correct answer is {accepted}. Chase production varies workforce or working hours so production follows demand period by period, often avoiding excess inventory."
        return f"The correct answer is {accepted}. Level production keeps workforce or hours steady, so inventory may rise when production exceeds demand."

    if "constant production" in text or "variable production" in text or "independent demand" in text or "exclusive use of a production strategy" in text:
        if "constant production" in text:
            return f"The correct answer is {accepted}. Constant or level production often creates larger stocks because output stays steady while demand varies."
        if "variable production" in text:
            return f"The correct answer is {accepted}. Variable production can keep labor demand stable if the number of working hours is adjusted instead of changing headcount."
        if "independent demand" in text:
            return f"The correct answer is {accepted}. Independent demand is demand for an end item that does not depend directly on demand for another product."
        return f"The correct answer is {accepted}. Production planning can use chase, level, or mixed strategies; it is not restricted to one exclusive strategy."

    if "inventory turns" in text or "residence time" in text or "inventory levels" in text or "cycle stock" in text:
        return f"The correct answer is {accepted}. Inventory level falls when residence time decreases and inventory turns increase; cycle stock is tied to normal production/consumption cycles, not simply sales exceeding production."

    if "human resource" in text:
        return f"The correct answer is {accepted}. Human resources remain part of production systems, but their role changes with automation level and manufacturing strategy."

    if "production control" in text and "inventory control" in text:
        return f"The correct answer is {accepted}. Production control includes inventory control because material availability and stock levels affect whether production orders can be executed."

    if "databases" in text and "binding" in text:
        return f"The correct answer is {accepted}. Databases connect departments in CIM because they let design, planning, production, quality, and control share consistent information."

    if "product classification" in text or "design features" in text:
        return f"The correct answer is {accepted}. Product classification can use design attributes, manufacturing attributes, or both."

    if "parts can be classified" in text:
        return f"The correct answer is {accepted}. Parts can be classified by design attributes, manufacturing attributes, or a combination of both."

    if "visual inspection" in text or "isual inspection" in text:
        return f"The correct answer is {accepted}. Visual inspection is the simplest and cheapest classification method, although it is less automated than coded or computerized approaches."

    if "process planning" in text or "processes planning" in text or "planning processes" in text or "pp requires" in text or "manufacturing research" in text:
        if "always" in text and ("manual" in text or "automatic" in text):
            return f"The correct answer is {accepted}. Process planning can be manual, computer-aided, retrieval-based, or generative; it is not always only manual or only automatic."
        if "existing tools" in text or "fasteners" in text:
            return f"The correct answer is {accepted}. Process planning needs information about available tools, fixtures/fasteners, machines, materials, and manufacturing constraints."
        if "decreases the time" in text or "computer" in text:
            return f"The correct answer is {accepted}. Computer-aided process planning reduces the time needed to develop consistent process plans."
        if "manufacturing research" in text:
            return f"The correct answer is {accepted}. Manufacturing research includes improving and optimizing production processes."
        return f"The correct answer is {accepted}. Process planning is needed for both produced parts and assemblies because it defines how manufacturing or assembly will be carried out."

    if "mass production systems" in text:
        return f"The correct answer is {accepted}. Mass production is associated with simple, standardized, low-cost products and simple drawings because high volume depends on repeatability."

    if "tqm" in text or "total quality management" in text:
        return f"The correct answer is {accepted}. TQM improves quality continuously across the organization, increasing customer satisfaction, service/product quality, and productivity."

    if "production capacity" in text and "quantity produced" in text and "meaning" in text:
        return f"The correct answer is {accepted}. The meaningful utilization ratio is quantity produced divided by production capacity; reversing it as capacity divided by quantity produced is not the standard performance measure."

    if "availability" in text and ("mtbf" in text or "mean time" in text):
        return f"The correct answer is {accepted}. Availability is computed from reliability data as (MTBF - MTTR) / MTBF, then expressed as a percentage."

    if "utilization" in text:
        return f"The correct answer is {accepted}. Utilization compares actual output or operating time with the available capacity for the same period."

    if contains_any(text, "asrs", "as rs", "automatic storage and retrieval", "storage and retrieval"):
        if "capacity" in text:
            return f"The correct answer is {accepted}. AS/RS storage capacity is based on aisles, both sides of each aisle, horizontal compartments, and vertical levels."
        if "width" in text:
            return f"The correct answer is {accepted}. AS/RS width is calculated from the aisle-width formula using the unit-load dimension plus the allowance, then multiplied by the number of aisles when total width is requested."
        if "throughput" in text:
            return f"The correct answer is {accepted}. AS/RS throughput increases when storage and retrieval can be combined efficiently, such as in dual-command cycles."
        return f"The correct answer is {accepted}. AS/RS questions are about automated storage/retrieval capacity, dimensions, throughput, or storage rules; the accepted option matches that AS/RS concept."

    if "storage" in text:
        if "random" in text or "randomized" in text:
            return f"The correct answer is {accepted}. Randomized storage reduces total required space because items can use any available location instead of reserving fixed locations."
        if "dedicated" in text:
            return f"The correct answer is {accepted}. Dedicated storage fixes locations for items, which can improve access/throughput for known high-activity items but usually requires more space."
        if "activity" in text or "space" in text:
            return f"The correct answer is {accepted}. Activity-based storage places high-activity items or high activity-to-space-ratio items where they can be accessed more efficiently."
        return f"The correct answer is {accepted}. Storage-system performance is judged by capacity, density, accessibility, throughput, utilization, and reliability."

    if "material handling" in text or "handling of materials" in text:
        if "cost" in text or "costs" in text:
            return f"The correct answer is {accepted}. Material handling is a support activity, so its cost should be minimized while still moving materials safely and effectively."
        if "paint stripes" in text or "guidance" in text:
            return f"The correct answer is {accepted}. Painted stripes are a simple low-cost AGV guidance method; more advanced self-guidance is more flexible but more expensive."
        if "large and heavy" in text or "heavy components" in text:
            return f"The correct answer is {accepted}. Large and heavy items are typically associated with cranes and hoists, while AGVs are more commonly used for pallet loads or flexible routing."
        return f"The correct answer is {accepted}. A material handling system is designed around material characteristics, flow rate, routing/scheduling, plant layout, budget, safety, and efficiency."

    if contains_any(text, "monocode", "polycode", "hybrid", "classification and coding", "tree coded", "chain type", "chain-type"):
        if "monocode" in text and ("highest" in text or "tree" in text or "number of digits" in text):
            return f"The correct answer is {accepted}. Monocode is hierarchical/tree-coded: each successive symbol depends on previous symbols, so the number of digits defines levels in the tree."
        if "polycode" in text or "lowest information density" in text:
            return f"The correct answer is {accepted}. Polycode uses independent symbols, so each symbol keeps the same meaning and the structure is not hierarchical/tree-coded."
        if "chain type" in text or "chain-type" in text:
            return f"The correct answer is {accepted}. Chain-type coding is not hierarchical, so its number of digits is not determined by tree levels the way monocode is."
        return f"The correct answer is {accepted}. Coding-structure questions distinguish monocode as hierarchical, polycode as independent-symbol coding, and hybrid as a mixed form."

    if contains_any(text, "cad", "cae", "cam", "caq", "capp", "cap "):
        if "cae" in text:
            return f"The correct answer is {accepted}. CAE is used for engineering analysis and simulation, such as stress, kinematics, and process simulations."
        if "cad" in text:
            return f"The correct answer is {accepted}. CAD supports product design and drawing/model creation; it is not the same as planning, manufacturing control, or quality assurance."
        if "cam" in text:
            return f"The correct answer is {accepted}. CAM connects computer support to manufacturing operations and machine/process execution."
        if "caq" in text:
            return f"The correct answer is {accepted}. CAQ is related to computer-aided quality activities, inspection, and quality assurance."
        if "capp" in text or "retrieval capp" in text:
            return f"The correct answer is {accepted}. CAPP creates or retrieves process plans; retrieval/variant CAPP reuses plans for similar part families."
        return f"The correct answer is {accepted}. CIM subsystem questions separate design, engineering analysis, manufacturing, quality, and process planning functions."

    if contains_any(text, "mrp", "mps", "master production", "aggregate production", "production planning", "enterprise resource", "erp"):
        if "aggregate" in text and "master" in text:
            return f"The correct answer is {accepted}. Aggregate planning is broader and comes before master production planning; MPS converts the aggregate plan into specific end-item schedules."
        if "material requirement" in text or "mrp" in text:
            return f"The correct answer is {accepted}. MRP translates the master production schedule for end products into requirements for materials, components, and parts."
        if "master production" in text or "mps" in text:
            return f"The correct answer is {accepted}. The MPS specifies what end items will be produced, in what quantities, and when they are scheduled."
        if "enterprise resource" in text or "erp" in text:
            return f"The correct answer is {accepted}. ERP integrates company-wide planning and resource information, so it supports CIM rather than being inefficient in CIM."
        if "chase" in text or "level" in text or "mixed" in text:
            return f"The correct answer is {accepted}. Chase, level, and mixed are aggregate production strategies for matching production with demand over time."
        return f"The correct answer is {accepted}. Production planning decides what products to make, how many to make, and when they should be completed."

    if contains_any(text, "mps", "available", "forecast", "on hand", "safety stock"):
        return f"The correct answer is {accepted}. In an MPS record, available balance is updated period by period from beginning inventory, scheduled production, and forecast demand while respecting safety stock."

    if contains_any(text, "make to stock", "make to order", "assemble to order", "engineer to order", "mto", "mts", "ato", "eto"):
        if "engineer to order" in answer_norm or "eto" in answer_norm:
            return f"The correct answer is {accepted}. Engineer-to-order is used when design/engineering work is driven by a specific customer order before production."
        if "assemble to order" in answer_norm or "ato" in answer_norm:
            return f"The correct answer is {accepted}. Assemble-to-order uses stocked subassemblies/components and assembles the final variant after the customer order."
        if "make to order" in answer_norm or "mto" in answer_norm:
            return f"The correct answer is {accepted}. Make-to-order starts production after the customer order, so it fits customized demand without finished-goods stock."
        if "make to stock" in answer_norm or "mts" in answer_norm:
            return f"The correct answer is {accepted}. Make-to-stock produces finished goods for inventory when demand can be forecast and the product configuration is stable."
        return f"The correct answer is {accepted}. Production-strategy questions separate stock production, order-triggered production, assembly from stocked modules, and engineering-to-order work."

    if contains_any(text, "project", "job shop", "repetitive", "line", "continuous", "classical manufacturing", "modern manufacturing"):
        if "project" in answer_norm:
            return f"The correct answer is {accepted}. Project production fits unique, large, site-specific products such as buildings or refineries, usually with long lead times."
        if "job shop" in answer_norm:
            return f"The correct answer is {accepted}. Job shops are suited to low-volume, high-variety work with variable routings through general-purpose work centers."
        if "line" in answer_norm:
            return f"The correct answer is {accepted}. Line production uses a fixed sequence of operations and is efficient for high-volume standardized products."
        if "continuous" in answer_norm:
            return f"The correct answer is {accepted}. Continuous production is used for very high-volume process industries with continuous flow, such as petroleum or chemicals."
        if "repetitive" in answer_norm:
            return f"The correct answer is {accepted}. Repetitive production repeatedly makes similar products, usually between job-shop variety and line/continuous volume."
        if "classical manufacturing" in answer_norm:
            return f"The correct answer is {accepted}. Large batches suit classical/traditional manufacturing because efficiency comes from repetition and reduced changeovers."
        if "modern manufacturing" in answer_norm:
            return f"The correct answer is {accepted}. Modern manufacturing emphasizes flexibility, responsiveness, and smaller batches compared with classical mass production."
        return f"The correct answer is {accepted}. Manufacturing-system type depends on product variety, production volume, routing, layout, and lead-time characteristics."

    if contains_any(text, "flexible manufacturing", "to be flexible", " fms ", "fms ", " fms", "flexibility"):
        if is_false:
            return "The statement is false. FMS means flexible manufacturing with automated workstations, computer control, and flexible routing/product mix; the statement contradicts that definition."
        if is_true:
            return "The statement is true. FMS is designed to improve flexibility and responsiveness while reducing direct labor and work-in-process compared with less flexible systems."
        return f"The correct answer is {accepted}. FMS combines automated workstations, material handling, and computer control so the system can handle product variety and routing changes."

    if contains_any(text, "group technology", "part family", "machine cell", "production flow analysis", "pfa"):
        return f"The correct answer is {accepted}. Group technology groups similar parts into part families and assigns them to machine groups or cells to reduce handling, setup, and lead time."

    if contains_any(text, "dfma", "design for manufacturing", "design for assembly", "concurrent engineering", "design for life cycle", "design for cost", "design for quality"):
        if "life cycle" in text:
            return f"The correct answer is {accepted}. Design for life cycle considers the product beyond manufacturing, including delivery, use, service, and disposal."
        if "cost" in text:
            return f"The correct answer is {accepted}. Design for cost aims to reduce cost through product and process design decisions."
        if "quality" in text:
            return f"The correct answer is {accepted}. Design for quality builds quality considerations into the design instead of relying only on later inspection."
        return f"The correct answer is {accepted}. DFMA and concurrent engineering improve manufacturability/assembly by simplifying parts, using standard components, and considering manufacturing early."

    if contains_any(text, "lean", "jit", "just in time", "kanban", "over production", "overproduction"):
        if "kanban" in text:
            return f"The correct answer is {accepted}. Kanban is a pull-control signal used in JIT/lean systems to authorize production or movement only when needed."
        if "over production" in text or "overproduction" in text:
            return f"The correct answer is {accepted}. Lean treats overproduction as waste, so removing overproduction supports lean manufacturing."
        return f"The correct answer is {accepted}. JIT and lean aim to reduce waste, inventories, WIP, lead time, and unnecessary handling while relying on reliable equipment and smooth flow."

    if contains_any(text, "industry 4 0", "cyber physical", "cyberphysical", "industrial internet", "iiot", "iot", "cloud computing", "digital factory", "smart manufacturing", "smart factories", "embedded system", "big data", "predictive manufacturing", "traditional factory", "traditional manufacturing system", "intelligent manufacturing"):
        if "cloud computing" in text and "physical location" in text:
            return f"The correct answer is {accepted}. Cloud-service users do not need to know the physical location or exact configuration of the equipment providing the service."
        if "digital factory" in text:
            return f"The correct answer is {accepted}. A digital factory uses information technology throughout its activities to model, plan, monitor, and control manufacturing."
        if "predictive manufacturing" in text:
            return f"The correct answer is {accepted}. Predictive manufacturing uses large amounts of sensor data to predict problems and keep production from being interrupted by equipment failure."
        if "iot" in text and "interconnected" in text:
            return f"The correct answer is {accepted}. In IoT, products/devices are connected through the Internet so they can exchange data and support smart services."
        if "traditional factory" in text or "traditional manufacturing system" in text:
            return f"The correct answer is {accepted}. Traditional factories usually use hierarchical control, fixed locations, and a more monolithic system structure."
        if "intelligent manufacturing" in text or "smart factories" in text or "context aware" in text:
            return f"The correct answer is {accepted}. Intelligent/smart manufacturing uses modular structures and context-aware or distributed decisions."
        if "third industrial revolution" in text and is_false:
            return "The statement is false. Cyber-physical systems are associated with Industry 4.0, the fourth industrial revolution, not the third."
        if "embedded systems encapsulate" in text and is_false:
            return "The statement is false. Cyber-physical systems extend and connect embedded systems; embedded systems do not encapsulate the whole cyber-physical system concept."
        return f"The correct answer is {accepted}. Industry 4.0/smart manufacturing relies on cyber-physical systems, connectivity, data, interoperability, virtualization, and modular/distributed decision making."

    if contains_any(text, "sustainable manufacturing", "sustainable development", "sustainability", "green product", "environment", "environmental impact", "environmentally friendly", "renewable", "pollution", "obsolete", "recycled", "reusable", "packaging", "donating equipment"):
        if "sustainability assurance" in text:
            return f"The correct answer is {accepted}. Sustainability assurance is a continuing journey because improvement, monitoring, and accountability must continue over time."
        if "green product" in text:
            return f"The correct answer is {accepted}. A green product is designed to reduce environmental impact; it usually cannot eliminate that impact completely."
        if "next generation" in text:
            return f"The correct answer is {accepted}. Sustainable development must protect resources for future generations rather than compromising them."
        if "management team" in text:
            return f"The correct answer is {accepted}. Sustainability is not only management's responsibility; it requires participation across the whole company."
        if "people" in answer_norm and "profit" in answer_norm:
            return f"The correct answer is {accepted}. Sustainability balances people, environment, and profitability rather than optimizing only one of them."
        return f"The correct answer is {accepted}. Sustainable manufacturing reduces environmental impact by minimizing waste, pollution, non-renewable resource use, and inefficient material/energy consumption."

    if contains_any(text, "setup time", "manufacturing lead time", "lead time", "work in process", "work-in-process"):
        if "setup" in text:
            return f"The correct answer is {accepted}. Setup time affects operation cycle time and lead time; reducing setup generally reduces lead time and work-in-process."
        return f"The correct answer is {accepted}. Manufacturing lead time is the time needed to process a product through the plant; reducing delays, setup, and WIP shortens it."

    if contains_any(text, "routing", "workstations", "processing time", "execution time", "frequency of operation"):
        return f"The correct answer is {accepted}. A routing defines the sequence of operations, the assigned workstations, and the processing/execution information for each part."

    if "two station manufacturing system" in text or "two-station manufacturing system" in text:
        return f"The correct answer is {accepted}. In a two-station manufacturing system, parts can follow either fixed routes or variable routes depending on how operations are assigned."

    if contains_any(text, "product structure", "possible structure", "bill of materials", "bom", "m5", "m6"):
        return f"The correct answer is {accepted}. Bill-of-materials questions require multiplying the required component quantities through each level of the product structure."

    if contains_any(text, "parts and materials", "manufacturing cost", "selling price"):
        return f"The correct answer is {accepted}. Relate parts/materials cost to manufacturing cost first, then relate manufacturing cost to selling price; multiply the percentages when both relationships apply."

    return None


def course_from_file(path_text):
    match = re.search(r"(C\d+)_unlocked", str(path_text or ""))
    return match.group(1) if match else None


def load_course_lines():
    course_lines = {}
    all_lines = []
    for path in sorted(COURSE_TEXT_DIR.glob("C*_unlocked.txt")):
        rel = path.relative_to(ROOT).as_posix()
        lines = path.read_text(encoding="utf-8", errors="replace").split("\n")
        course_lines[rel] = lines
        course = course_from_file(rel)
        for index, line in enumerate(lines, start=1):
            cleaned = clean_text(line)
            if len(cleaned) < 12:
                continue
            all_lines.append(
                {
                    "course": course,
                    "source_text_file": rel,
                    "line": index,
                    "text": cleaned,
                    "norm": normalize(cleaned),
                    "tokens": token_set(cleaned),
                }
            )
    return course_lines, all_lines


def token_set(text):
    return {
        token
        for token in normalize(text).split()
        if len(token) > 2 and token not in STOPWORDS and not token.isdigit()
    }


def source_key(source):
    return (
        source.get("course"),
        source.get("source_text_file"),
        source.get("line"),
        source.get("source_file"),
        source.get("source_page"),
        source.get("note"),
    )


def copy_source(source):
    allowed = ["course", "source_text_file", "line", "source_file", "source_page", "note"]
    return {key: source[key] for key in allowed if source.get(key) is not None}


def dedupe_sources(sources):
    deduped = []
    seen = set()
    for source in sources:
        copied = copy_source(source)
        key = source_key(copied)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(copied)
    return deduped


def source_context(source, course_lines, radius=2):
    rel = source.get("source_text_file")
    line_no = source.get("line")
    if not rel or not line_no or rel not in course_lines:
        return ""

    lines = course_lines[rel]
    start = max(1, int(line_no) - radius)
    end = min(len(lines), int(line_no) + radius)
    chunks = [clean_text(lines[index - 1]) for index in range(start, end + 1)]
    chunks = [chunk for chunk in chunks if chunk and not re.match(r"^\d{1,2}/\d{1,2}/\d{4}", chunk)]
    text = " ".join(chunks)
    return re.sub(r"\s+", " ", text).strip()[:280]


def best_course_match(question, all_course_lines):
    question_tokens = token_set(question.get("question", ""))
    answer_tokens = token_set(" ".join(question.get("correct_answers", [])))
    option_tokens = token_set(" ".join(question.get("options", [])))
    query_tokens = question_tokens | answer_tokens
    if not query_tokens:
        return None

    best = None
    for line in all_course_lines:
        common = query_tokens & line["tokens"]
        if not common:
            continue
        score = len(common)
        score += 2 * len(answer_tokens & line["tokens"])
        score += 1 if len(option_tokens & line["tokens"]) else 0
        answer_exact = False
        for answer in question.get("correct_answers", []):
            answer_norm = normalize(answer)
            if answer_norm in {"true", "false"}:
                continue
            if answer_norm and len(answer_norm) > 3 and answer_norm in line["norm"]:
                answer_exact = True
                score += 6
        if best is None or score > best["score"]:
            best = {**line, "score": score, "answer_exact": answer_exact}

    if not best:
        return None
    # Keep the threshold conservative so weak matches become needs_review.
    answer_overlap = len(answer_tokens & best["tokens"])
    needed_answer_overlap = min(2, len(answer_tokens))
    if best["score"] < 12 and not best["answer_exact"]:
        return None
    if answer_tokens and not best["answer_exact"] and answer_overlap < needed_answer_overlap:
        return None
    return {
        "course": best["course"],
        "source_text_file": best["source_text_file"],
        "line": best["line"],
        "note": "automatic course-text match",
    }


def quiz_source(question):
    source = {"source_file": question.get("source_file"), "note": "local quiz answer key"}
    if question.get("source_page") is not None:
        source["source_page"] = question.get("source_page")
    return copy_source(source)


def collect_sources(question, course_lines, all_course_lines):
    sources = []
    status = "needs_review"

    if question.get("answer_sources"):
        sources.extend(question["answer_sources"])
        status = "confirmed"

    if question.get("source_text_file") and question.get("source_line"):
        sources.append(
            {
                "course": question.get("course") or course_from_file(question.get("source_text_file")),
                "source_text_file": question.get("source_text_file"),
                "line": question.get("source_line"),
                "note": "course self-assessment item",
            }
        )
        status = "confirmed"

    if question.get("id") in SPECIAL_SOURCE_HINTS:
        sources.append(SPECIAL_SOURCE_HINTS[question["id"]])
        if SPECIAL_SOURCE_HINTS[question["id"]].get("source_text_file"):
            status = "confirmed"

    matched = None if status == "confirmed" else best_course_match(question, all_course_lines)
    if matched:
        sources.append(matched)
        status = "confirmed"

    if question.get("source_file"):
        sources.append(quiz_source(question))

    return dedupe_sources(sources), status


def evidence_sentence(question, sources, course_lines):
    for source in sources:
        context = source_context(source, course_lines)
        if context:
            return f"The supporting source says: {context}"

    notes = [source.get("note") for source in sources if source.get("note") and source.get("note") != "local quiz answer key"]
    if notes:
        return f"The relevant source topic is {notes[0]}."

    if question.get("source_file"):
        return "The local quiz answer key marks this option as accepted."

    return "No stronger course-text evidence was matched automatically."


def generic_explanation(question, sources, status, course_lines):
    specific = concept_explanation(question)
    if specific:
        return specific

    answers = question.get("correct_answers", [])
    accepted = answer_list(answers)

    if is_true_false(question):
        value = normalize(answers[0])
        if value == "true":
            return "The statement is true. It matches the accepted course answer for this concept, so choose true and reject the opposite statement."
        return "The statement is false. It contradicts the accepted course answer for this concept, so choose false rather than treating the statement as correct."

    if is_calculation(question):
        return f"The expected calculated result is {accepted}. Use the formula or table relationships in the question, then compare the computed value with the listed answers."

    if len(answers) > 1:
        return f"The accepted set is {accepted}. Select all of these and no extra options, because the unlisted options are distractors for this question."

    return f"The correct answer is {accepted}. It is the option that matches the concept asked in the question; the other options describe different concepts or distractors."


def draft_question(question, course_lines, all_course_lines):
    sources, status = collect_sources(question, course_lines, all_course_lines)
    if question.get("id") in SPECIAL_EXPLANATIONS:
        explanation = SPECIAL_EXPLANATIONS[question["id"]]
    else:
        explanation = generic_explanation(question, sources, status, course_lines)

    question["answer_explanation"] = explanation.strip()
    question["explanation_status"] = status
    question["explanation_sources"] = sources
    return status


def validate_bank(bank):
    questions = bank.get("questions")
    if not isinstance(questions, list):
        raise ValueError("quiz_questions.json must contain a questions array")

    for index, question in enumerate(questions, start=1):
        if not question.get("question"):
            raise ValueError(f"Question {index} is missing question text")
        if not isinstance(question.get("options"), list):
            raise ValueError(f"Question {index} options must be a list")
        answers = question.get("correct_answers")
        if not isinstance(answers, list) or not answers:
            raise ValueError(f"Question {index} must have at least one correct answer")
        if question.get("options"):
            option_norms = {normalize(option) for option in question["options"]}
            for answer in answers:
                if normalize(answer) not in option_norms:
                    raise ValueError(f"Question {index} answer does not match an option: {answer!r}")
        if not question.get("answer_explanation"):
            raise ValueError(f"Question {index} has an empty answer_explanation")


def regenerate_site_data(bank):
    SITE_DATA_PATH.write_text(
        "window.QUIZ_DATA = " + json.dumps(bank, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8",
    )


def main():
    bank = json.loads(BANK_PATH.read_text(encoding="utf-8-sig"))
    questions = bank.get("questions")
    if not isinstance(questions, list):
        raise ValueError("quiz_questions.json must contain a questions array")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = BACKUP_ROOT / f"explanations_{timestamp}"
    backup_dir.mkdir(parents=True, exist_ok=False)
    shutil.copy2(BANK_PATH, backup_dir / BANK_PATH.name)
    shutil.copy2(SITE_DATA_PATH, backup_dir / SITE_DATA_PATH.name)

    course_lines, all_course_lines = load_course_lines()
    statuses = Counter()
    needs_review = []
    courses = Counter()

    for question in questions:
        status = draft_question(question, course_lines, all_course_lines)
        statuses[status] += 1
        for source in question.get("explanation_sources", []):
            if source.get("course"):
                courses[source["course"]] += 1
        if status == "needs_review":
            needs_review.append(
                {
                    "id": question.get("id"),
                    "source_file": question.get("source_file"),
                    "source_page": question.get("source_page"),
                    "question": question.get("question"),
                    "correct_answers": question.get("correct_answers"),
                }
            )

    bank["question_count"] = len(questions)
    validate_bank(bank)

    BANK_PATH.write_text(json.dumps(bank, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    regenerate_site_data(bank)

    report = {
        "generated_at": timestamp,
        "backup_dir": backup_dir.relative_to(ROOT).as_posix(),
        "question_count": len(questions),
        "status_counts": dict(statuses),
        "course_source_counts": dict(sorted(courses.items())),
        "needs_review_count": len(needs_review),
        "needs_review": needs_review,
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Added explanations to {len(questions)} questions")
    print(f"Confirmed: {statuses['confirmed']}")
    print(f"Needs review: {statuses['needs_review']}")
    print(f"Backup: {backup_dir}")
    print(f"Report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
