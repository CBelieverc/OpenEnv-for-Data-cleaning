"""Task 2 (Medium): Normalize formats — names, phones, emails, dates, addresses."""

# Dirty dataset: 10 records with format inconsistencies
TASK2_DIRTY = [
    {"id": "1", "name": "john DOE", "phone": "(555) 123-4567", "email": " JOHN@gmail.com ", "date": "Jan 5, 2024", "address": "123 Main St."},
    {"id": "2", "name": "JANE smith", "phone": "555.987.6543", "email": "Jane@Yahoo.COM", "date": "05/01/2024", "address": "456 OAK AVENUE"},
    {"id": "3", "name": "bob  JONES", "phone": "+1-555-246-8135", "email": "Bob@Hotmail.com", "date": "2024-03-15", "address": "789 Elm St"},
    {"id": "4", "name": "ALICE williams", "phone": "555 369 2580", "email": "alice@GMAIL.COM  ", "date": "Mar 20, 2024", "address": "321 Pine Avenue"},
    {"id": "5", "name": "charlie BROWN", "phone": "(555)864-2097", "email": "Charlie.Brown@outlook.com", "date": "04/15/2024", "address": "654 BIRCH ROAD"},
    {"id": "6", "name": "DIANA  davis", "phone": "555-753-1590", "email": "DIANA.DAVIS@gmail.COM", "date": "2024/05/10", "address": "987 Cedar Blvd."},
    {"id": "7", "name": "eve miller", "phone": "+1 (555) 159-7530", "email": "Eve@company.org", "date": "Jun 1, 2024", "address": "147 MAPLE STREET"},
    {"id": "8", "name": "FRANK Wilson", "phone": "555 753 4860", "email": " frank@tech.io ", "date": "06/15/2024", "address": "258 Oak Lane"},
    {"id": "9", "name": "grace  TAYLOR", "phone": "(555)951-3570", "email": "Grace.Taylor@COMPANY.COM", "date": "Jul 4, 2024", "address": "369 Walnut Court"},
    {"id": "10", "name": "HENRY anderson", "phone": "555.357.9510", "email": "Henry@Gmail.Com", "date": "07/20/2024", "address": "480 SPRUCE DRIVE"},
]

# Expected clean dataset
TASK2_EXPECTED = [
    {"id": "1", "name": "John Doe", "phone": "5551234567", "email": "john@gmail.com", "date": "2024-01-05", "address": "123 Main Street"},
    {"id": "2", "name": "Jane Smith", "phone": "5559876543", "email": "jane@yahoo.com", "date": "2024-05-01", "address": "456 Oak Avenue"},
    {"id": "3", "name": "Bob Jones", "phone": "5552468135", "email": "bob@hotmail.com", "date": "2024-03-15", "address": "789 Elm Street"},
    {"id": "4", "name": "Alice Williams", "phone": "5553692580", "email": "alice@gmail.com", "date": "2024-03-20", "address": "321 Pine Avenue"},
    {"id": "5", "name": "Charlie Brown", "phone": "5558642097", "email": "charlie.brown@outlook.com", "date": "2024-04-15", "address": "654 Birch Road"},
    {"id": "6", "name": "Diana Davis", "phone": "5557531590", "email": "diana.davis@gmail.com", "date": "2024-05-10", "address": "987 Cedar Boulevard"},
    {"id": "7", "name": "Eve Miller", "phone": "5551597530", "email": "eve@company.org", "date": "2024-06-01", "address": "147 Maple Street"},
    {"id": "8", "name": "Frank Wilson", "phone": "5557534860", "email": "frank@tech.io", "date": "2024-06-15", "address": "258 Oak Lane"},
    {"id": "9", "name": "Grace Taylor", "phone": "5559513570", "email": "grace.taylor@company.com", "date": "2024-07-04", "address": "369 Walnut Court"},
    {"id": "10", "name": "Henry Anderson", "phone": "5553579510", "email": "henry@gmail.com", "date": "2024-07-20", "address": "480 Spruce Drive"},
]

# Detected issues
TASK2_ISSUES = [
    # Record 1
    {"issue_id": "1:name", "record_id": "1", "field": "name", "issue_type": "format", "hint": "Normalize to Title Case: 'John Doe'"},
    {"issue_id": "1:phone", "record_id": "1", "field": "phone", "issue_type": "format", "hint": "Extract digits only: '5551234567'"},
    {"issue_id": "1:email", "record_id": "1", "field": "email", "issue_type": "format", "hint": "Lowercase and trim: 'john@gmail.com'"},
    {"issue_id": "1:date", "record_id": "1", "field": "date", "issue_type": "format", "hint": "Convert to ISO: '2024-01-05'"},
    {"issue_id": "1:address", "record_id": "1", "field": "address", "issue_type": "format", "hint": "Normalize abbreviation: 'St.' -> 'Street'"},
    # Record 2
    {"issue_id": "2:name", "record_id": "2", "field": "name", "issue_type": "format", "hint": "Normalize to Title Case: 'Jane Smith'"},
    {"issue_id": "2:phone", "record_id": "2", "field": "phone", "issue_type": "format", "hint": "Extract digits only: '5559876543'"},
    {"issue_id": "2:email", "record_id": "2", "field": "email", "issue_type": "format", "hint": "Lowercase: 'jane@yahoo.com'"},
    {"issue_id": "2:date", "record_id": "2", "field": "date", "issue_type": "format", "hint": "Convert MM/DD/YYYY to ISO: '2024-05-01'"},
    {"issue_id": "2:address", "record_id": "2", "field": "address", "issue_type": "format", "hint": "Title case and expand: '456 Oak Avenue'"},
    # Record 3
    {"issue_id": "3:name", "record_id": "3", "field": "name", "issue_type": "format", "hint": "Remove extra spaces, Title Case: 'Bob Jones'"},
    {"issue_id": "3:phone", "record_id": "3", "field": "phone", "issue_type": "format", "hint": "Remove country code and formatting: '5552468135'"},
    {"issue_id": "3:email", "record_id": "3", "field": "email", "issue_type": "format", "hint": "Lowercase: 'bob@hotmail.com'"},
    {"issue_id": "3:address", "record_id": "3", "field": "address", "issue_type": "format", "hint": "Expand abbreviation: '789 Elm Street'"},
    # Record 4
    {"issue_id": "4:name", "record_id": "4", "field": "name", "issue_type": "format", "hint": "Title Case: 'Alice Williams'"},
    {"issue_id": "4:phone", "record_id": "4", "field": "phone", "issue_type": "format", "hint": "Remove spaces, extract digits: '5553692580'"},
    {"issue_id": "4:email", "record_id": "4", "field": "email", "issue_type": "format", "hint": "Lowercase and trim: 'alice@gmail.com'"},
    {"issue_id": "4:date", "record_id": "4", "field": "date", "issue_type": "format", "hint": "Convert to ISO: '2024-03-20'"},
    # Record 5
    {"issue_id": "5:name", "record_id": "5", "field": "name", "issue_type": "format", "hint": "Title Case: 'Charlie Brown'"},
    {"issue_id": "5:phone", "record_id": "5", "field": "phone", "issue_type": "format", "hint": "Extract digits only: '5558642097'"},
    {"issue_id": "5:email", "record_id": "5", "field": "email", "issue_type": "format", "hint": "Lowercase: 'charlie.brown@outlook.com'"},
    {"issue_id": "5:date", "record_id": "5", "field": "date", "issue_type": "format", "hint": "Convert MM/DD/YYYY to ISO: '2024-04-15'"},
    {"issue_id": "5:address", "record_id": "5", "field": "address", "issue_type": "format", "hint": "Title case and expand: '654 Birch Road'"},
    # Record 6
    {"issue_id": "6:name", "record_id": "6", "field": "name", "issue_type": "format", "hint": "Remove extra spaces, Title Case: 'Diana Davis'"},
    {"issue_id": "6:phone", "record_id": "6", "field": "phone", "issue_type": "format", "hint": "Extract digits: '5557531590'"},
    {"issue_id": "6:email", "record_id": "6", "field": "email", "issue_type": "format", "hint": "Lowercase: 'diana.davis@gmail.com'"},
    {"issue_id": "6:date", "record_id": "6", "field": "date", "issue_type": "format", "hint": "Convert YYYY/MM/DD to ISO: '2024-05-10'"},
    {"issue_id": "6:address", "record_id": "6", "field": "address", "issue_type": "format", "hint": "Expand abbreviation: '987 Cedar Boulevard'"},
    # Record 7
    {"issue_id": "7:name", "record_id": "7", "field": "name", "issue_type": "format", "hint": "Title Case: 'Eve Miller'"},
    {"issue_id": "7:phone", "record_id": "7", "field": "phone", "issue_type": "format", "hint": "Remove country code, parens, spaces: '5551597530'"},
    {"issue_id": "7:date", "record_id": "7", "field": "date", "issue_type": "format", "hint": "Convert to ISO: '2024-06-01'"},
    {"issue_id": "7:address", "record_id": "7", "field": "address", "issue_type": "format", "hint": "Title case: '147 Maple Street'"},
    # Record 8
    {"issue_id": "8:name", "record_id": "8", "field": "name", "issue_type": "format", "hint": "Title Case: 'Frank Wilson'"},
    {"issue_id": "8:phone", "record_id": "8", "field": "phone", "issue_type": "format", "hint": "Remove spaces: '5557534860'"},
    {"issue_id": "8:email", "record_id": "8", "field": "email", "issue_type": "format", "hint": "Trim and lowercase: 'frank@tech.io'"},
    {"issue_id": "8:date", "record_id": "8", "field": "date", "issue_type": "format", "hint": "Convert MM/DD/YYYY to ISO: '2024-06-15'"},
    # Record 9
    {"issue_id": "9:name", "record_id": "9", "field": "name", "issue_type": "format", "hint": "Remove extra spaces, Title Case: 'Grace Taylor'"},
    {"issue_id": "9:phone", "record_id": "9", "field": "phone", "issue_type": "format", "hint": "Extract digits: '5559513570'"},
    {"issue_id": "9:email", "record_id": "9", "field": "email", "issue_type": "format", "hint": "Lowercase: 'grace.taylor@company.com'"},
    {"issue_id": "9:date", "record_id": "9", "field": "date", "issue_type": "format", "hint": "Convert to ISO: '2024-07-04'"},
    # Record 10
    {"issue_id": "10:name", "record_id": "10", "field": "name", "issue_type": "format", "hint": "Title Case: 'Henry Anderson'"},
    {"issue_id": "10:phone", "record_id": "10", "field": "phone", "issue_type": "format", "hint": "Extract digits: '5553579510'"},
    {"issue_id": "10:email", "record_id": "10", "field": "email", "issue_type": "format", "hint": "Lowercase: 'henry@gmail.com'"},
    {"issue_id": "10:date", "record_id": "10", "field": "date", "issue_type": "format", "hint": "Convert MM/DD/YYYY to ISO: '2024-07-20'"},
    {"issue_id": "10:address", "record_id": "10", "field": "address", "issue_type": "format", "hint": "Title case: '480 Spruce Drive'"},
]


def grade_task2(current_data: list, expected_data: list, **kwargs) -> float:
    """Grade Task 2 by comparing normalized field values."""
    total_fields = 0
    correct_fields = 0
    for current_record, expected_record in zip(current_data, expected_data):
        for field in expected_record:
            total_fields += 1
            if field not in current_record:
                continue
            curr_val = str(current_record[field]).strip()
            exp_val = str(expected_record[field]).strip()
            if curr_val.lower() == exp_val.lower():
                correct_fields += 1
    return correct_fields / total_fields if total_fields > 0 else 0.0
