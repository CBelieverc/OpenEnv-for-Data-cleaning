"""Task datasets and graders for the Data Cleaning Environment."""

from .task1_type_fixes import TASK1_DIRTY, TASK1_EXPECTED, TASK1_ISSUES, grade_task1
from .task2_normalization import TASK2_DIRTY, TASK2_EXPECTED, TASK2_ISSUES, grade_task2
from .task3_dedup import TASK3_DIRTY, TASK3_ISSUES, grade_task3

TASKS = {
    "easy": {
        "dirty_data": TASK1_DIRTY,
        "expected_data": TASK1_EXPECTED,
        "issues": TASK1_ISSUES,
        "grade": grade_task1,
        "max_steps": 30,
        "description": "Fix data types: convert strings to numbers, booleans, and dates.",
    },
    "medium": {
        "dirty_data": TASK2_DIRTY,
        "expected_data": TASK2_EXPECTED,
        "issues": TASK2_ISSUES,
        "grade": grade_task2,
        "max_steps": 50,
        "description": "Normalize formats: names, phones, emails, dates, addresses.",
    },
    "hard": {
        "dirty_data": TASK3_DIRTY,
        "expected_data": TASK3_DIRTY,
        "issues": TASK3_ISSUES,
        "grade": grade_task3,
        "max_steps": 60,
        "description": "Deduplicate records and resolve conflicts.",
    },
}


def get_task(task_id: str) -> dict:
    """Get task configuration by ID."""
    if task_id not in TASKS:
        raise ValueError(f"Unknown task: {task_id}. Available: {list(TASKS.keys())}")
    return TASKS[task_id]
