"""Task 1 (Easy): Fix data types — convert strings to correct types."""

# Dirty dataset: 5 records with type issues
TASK1_DIRTY = [
    {"id": "1", "name": "Alice", "age": "twenty-five", "date_joined": "03/15/2024", "active": "yes", "score": "89.5"},
    {"id": "2", "name": "Bob", "age": "30", "date_joined": "2024-01-20", "active": "no", "score": "72.0"},
    {"id": "3", "name": "Charlie", "age": "35", "date_joined": "Dec 25, 2023", "active": "1", "score": "95"},
    {"id": "4", "name": "Diana", "age": "28", "date_joined": "07/04/2024", "active": "0", "score": "N/A"},
    {"id": "5", "name": "Eve", "age": "thirty-two", "date_joined": "2024/02/14", "active": "true", "score": "81.3"},
]

# Expected clean dataset
TASK1_EXPECTED = [
    {"id": "1", "name": "Alice", "age": 25, "date_joined": "2024-03-15", "active": True, "score": 89.5},
    {"id": "2", "name": "Bob", "age": 30, "date_joined": "2024-01-20", "active": False, "score": 72.0},
    {"id": "3", "name": "Charlie", "age": 35, "date_joined": "2023-12-25", "active": True, "score": 95.0},
    {"id": "4", "name": "Diana", "age": 28, "date_joined": "2024-07-04", "active": False, "score": None},
    {"id": "5", "name": "Eve", "age": 32, "date_joined": "2024-02-14", "active": True, "score": 81.3},
]

# Detected issues (field-level)
TASK1_ISSUES = [
    {"issue_id": "1:age", "record_id": "1", "field": "age", "issue_type": "type_mismatch", "hint": "Convert 'twenty-five' to integer 25"},
    {"issue_id": "1:date_joined", "record_id": "1", "field": "date_joined", "issue_type": "format_mismatch", "hint": "Convert '03/15/2024' to ISO format '2024-03-15'"},
    {"issue_id": "1:active", "record_id": "1", "field": "active", "issue_type": "type_mismatch", "hint": "Convert 'yes' to boolean True"},
    {"issue_id": "1:score", "record_id": "1", "field": "score", "issue_type": "type_mismatch", "hint": "Convert '89.5' to float 89.5"},
    {"issue_id": "2:score", "record_id": "2", "field": "score", "issue_type": "type_mismatch", "hint": "Convert '72.0' to float 72.0"},
    {"issue_id": "2:active", "record_id": "2", "field": "active", "issue_type": "type_mismatch", "hint": "Convert 'no' to boolean False"},
    {"issue_id": "2:age", "record_id": "2", "field": "age", "issue_type": "type_mismatch", "hint": "Convert '30' to integer 30"},
    {"issue_id": "3:date_joined", "record_id": "3", "field": "date_joined", "issue_type": "format_mismatch", "hint": "Convert 'Dec 25, 2023' to ISO format '2023-12-25'"},
    {"issue_id": "3:active", "record_id": "3", "field": "active", "issue_type": "type_mismatch", "hint": "Convert '1' to boolean True"},
    {"issue_id": "3:score", "record_id": "3", "field": "score", "issue_type": "type_mismatch", "hint": "Convert '95' to float 95.0"},
    {"issue_id": "3:age", "record_id": "3", "field": "age", "issue_type": "type_mismatch", "hint": "Convert '35' to integer 35"},
    {"issue_id": "4:date_joined", "record_id": "4", "field": "date_joined", "issue_type": "format_mismatch", "hint": "Convert '07/04/2024' to ISO format '2024-07-04'"},
    {"issue_id": "4:active", "record_id": "4", "field": "active", "issue_type": "type_mismatch", "hint": "Convert '0' to boolean False"},
    {"issue_id": "4:score", "record_id": "4", "field": "score", "issue_type": "type_mismatch", "hint": "Convert 'N/A' to None/null"},
    {"issue_id": "4:age", "record_id": "4", "field": "age", "issue_type": "type_mismatch", "hint": "Convert '28' to integer 28"},
    {"issue_id": "5:age", "record_id": "5", "field": "age", "issue_type": "type_mismatch", "hint": "Convert 'thirty-two' to integer 32"},
    {"issue_id": "5:date_joined", "record_id": "5", "field": "date_joined", "issue_type": "format_mismatch", "hint": "Convert '2024/02/14' to ISO format '2024-02-14'"},
    {"issue_id": "5:active", "record_id": "5", "field": "active", "issue_type": "type_mismatch", "hint": "Convert 'true' to boolean True"},
    {"issue_id": "5:score", "record_id": "5", "field": "score", "issue_type": "type_mismatch", "hint": "Convert '81.3' to float 81.3"},
]


def grade_task1(current_data: list, expected_data: list, **kwargs) -> float:
    """Grade Task 1 by comparing field values to expected output."""
    total_fields = 0
    correct_fields = 0
    for current_record, expected_record in zip(current_data, expected_data):
        for field in expected_record:
            total_fields += 1
            curr_val = current_record.get(field)
            exp_val = expected_record[field]
            if _values_match(curr_val, exp_val):
                correct_fields += 1
    return correct_fields / total_fields if total_fields > 0 else 0.0


def _values_match(current, expected) -> bool:
    """Compare two values with type coercion for grading."""
    if current is None and expected is None:
        return True
    if current is None or expected is None:
        return False
    # Normalize for comparison
    if isinstance(expected, bool):
        return current == expected
    if isinstance(expected, int):
        try:
            return int(current) == expected
        except (ValueError, TypeError):
            return False
    if isinstance(expected, float):
        try:
            return abs(float(current) - expected) < 0.001
        except (ValueError, TypeError):
            return False
    return str(current).strip() == str(expected).strip()
