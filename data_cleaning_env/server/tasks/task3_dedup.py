"""Task 3 (Hard): Deduplicate records and resolve conflicts.

Genuinely challenging because:
- Pair (1,2): Same phone, different names ("John Smith" vs "J. Smith"), different emails
- Pair (3,4): Same name + phone, different email formats (jane@ vs jane.doe@)
- Pair (5,6): Same email + phone, names differ ("Robert" vs "Bob" — nickname detection)
- Pair (8,9): Same phone + name, emails differ (charlie@ vs charles.davis@)
- Pair (12,13): Same phone + name, emails differ (frank@ vs frank.t@)
- Hints are intentionally vague to require reasoning, not just pattern matching
"""

# Dirty dataset: 15 records with 5 duplicate groups
TASK3_DIRTY = [
    {"id": "1", "name": "John Smith", "email": "john@work.com", "phone": "5551234567", "address": "123 Main St", "joined": "2024-01-15"},
    {"id": "2", "name": "J. Smith", "email": "john@personal.com", "phone": "5551234567", "address": "123 Main Street", "joined": "2024-02-20"},
    {"id": "3", "name": "Jane Doe", "email": "jane@company.com", "phone": "5559876543", "address": "456 Oak Ave", "joined": "2024-01-10"},
    {"id": "4", "name": "Jane Doe", "email": "jane.doe@company.com", "phone": "5559876543", "address": "456 Oak Avenue", "joined": "2024-03-05"},
    {"id": "5", "name": "Robert Brown", "email": "bob@email.com", "phone": "5552468135", "address": "789 Elm St", "joined": "2024-02-01"},
    {"id": "6", "name": "Bob Brown", "email": "bob@email.com", "phone": "5552468135", "address": "789 Elm Street", "joined": "2024-01-20"},
    {"id": "7", "name": "Alice Williams", "email": "alice@tech.io", "phone": "5553692580", "address": "321 Pine Ave", "joined": "2024-03-15"},
    {"id": "8", "name": "Charlie Davis", "email": "charlie@startup.co", "phone": "5558642097", "address": "654 Birch Rd", "joined": "2024-01-25"},
    {"id": "9", "name": "Charlie Davis", "email": "charles.davis@startup.co", "phone": "5558642097", "address": "654 Birch Road", "joined": "2024-02-10"},
    {"id": "10", "name": "Diana Miller", "email": "diana@org.net", "phone": "5557531590", "address": "987 Cedar Blvd", "joined": "2024-02-28"},
    {"id": "11", "name": "Eve Wilson", "email": "eve@design.co", "phone": "5551597530", "address": "147 Maple St", "joined": "2024-03-01"},
    {"id": "12", "name": "Frank Taylor", "email": "frank@finance.com", "phone": "5559513570", "address": "258 Oak Ln", "joined": "2024-01-30"},
    {"id": "13", "name": "Frank Taylor", "email": "frank.t@finance.com", "phone": "5559513570", "address": "258 Oak Lane", "joined": "2024-03-10"},
    {"id": "14", "name": "Grace Anderson", "email": "grace@health.org", "phone": "5553579510", "address": "369 Walnut Ct", "joined": "2024-02-15"},
    {"id": "15", "name": "Henry Lee", "email": "henry@edu.school", "phone": "5554682073", "address": "480 Spruce Dr", "joined": "2024-03-20"},
]

# Ground truth duplicate pairs
DUPLICATE_PAIRS = {
    ("1", "2"),   # Phone match, name fuzzy (John vs J.)
    ("3", "4"),   # Name + phone exact, email format differs
    ("5", "6"),   # Email + phone exact, name fuzzy (Robert vs Bob)
    ("8", "9"),   # Phone + name exact, email differs (charlie@ vs charles.davis@)
    ("12", "13"), # Phone + name exact, email differs (frank@ vs frank.t@)
}

# IDs that should be removed (the "duplicate" in each pair)
DUPLICATE_IDS_TO_REMOVE = {"2", "4", "6", "9", "13"}

# Master IDs that should be kept
MASTER_IDS = {"1", "3", "5", "7", "8", "10", "11", "12", "14", "15"}

# Detected issues — hints are intentionally vague to require reasoning
TASK3_ISSUES = [
    {
        "issue_id": "dup_1_2",
        "type": "duplicate",
        "record_ids": ["1", "2"],
        "hint": "These records may refer to the same person. Check phone, name similarity, and address overlap.",
    },
    {
        "issue_id": "dup_3_4",
        "type": "duplicate",
        "record_ids": ["3", "4"],
        "hint": "Same name and phone number. Different email format — likely the same person with multiple email addresses.",
    },
    {
        "issue_id": "dup_5_6",
        "type": "duplicate",
        "record_ids": ["5", "6"],
        "hint": "Same email and phone. Names differ — one may be a nickname or shortened form.",
    },
    {
        "issue_id": "dup_8_9",
        "type": "duplicate",
        "record_ids": ["8", "9"],
        "hint": "Same phone and name. Different email addresses — could be work vs personal email.",
    },
    {
        "issue_id": "dup_12_13",
        "type": "duplicate",
        "record_ids": ["12", "13"],
        "hint": "Same phone and name. Email addresses differ slightly — may be different accounts for the same person.",
    },
]


def grade_task3(current_data: list, expected_data: list, duplicate_groups: dict = None, **kwargs) -> float:
    """Grade Task 3 on duplicate identification (50%) and record removal (50%).

    Scoring breakdown:
    - 50%: Duplicate identification F1 (precision + recall on pairs)
    - 50%: Record removal accuracy (duplicates removed, masters kept)
    """
    if duplicate_groups is None:
        duplicate_groups = {}

    id_score = _grade_duplicate_identification(duplicate_groups)
    removal_score = _grade_record_removal(current_data)

    return (id_score * 0.5) + (removal_score * 0.5)


def _grade_duplicate_identification(identified_groups: dict) -> float:
    """Score duplicate identification using precision + recall (F1) on pairs.

    identified_groups is {duplicate_id: master_id} as stored by the environment.
    """
    gt_pairs = DUPLICATE_PAIRS

    # Convert {dup_id: master_id} entries to sorted pairs
    id_pairs = set()
    for dup_id, master_id in identified_groups.items():
        if dup_id != master_id:
            id_pairs.add(tuple(sorted([dup_id, master_id])))

    if not gt_pairs:
        return 1.0

    true_positives = len(gt_pairs & id_pairs)
    precision = true_positives / len(id_pairs) if id_pairs else 0.0
    recall = true_positives / len(gt_pairs) if gt_pairs else 0.0

    if precision + recall == 0:
        return 0.0
    f1 = 2 * (precision * recall) / (precision + recall)
    return f1


def _grade_record_removal(current_data: list) -> float:
    """Score whether correct records were removed and masters kept."""
    current_ids = {r["id"] for r in current_data}

    # Check duplicates were removed
    removed = DUPLICATE_IDS_TO_REMOVE - current_ids
    removal_rate = len(removed) / len(DUPLICATE_IDS_TO_REMOVE)

    # Check masters were kept
    kept = MASTER_IDS & current_ids
    keep_rate = len(kept) / len(MASTER_IDS)

    return (removal_rate + keep_rate) / 2.0
