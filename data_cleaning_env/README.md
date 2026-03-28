---
title: Data Cleaning Environment
emoji: 🧹
colorFrom: indigo
colorTo: green
sdk: docker
pinned: false
app_port: 8000
base_path: /web
tags:
  - openenv
---

# Data Cleaning Environment

A real-world OpenEnv environment that simulates data cleaning tasks. An AI agent receives dirty datasets and must clean them through typed actions.

## Why Data Cleaning?

Data cleaning is a universal, practical task performed by every data team. It requires type-aware reasoning, format normalization, deduplication, and conflict resolution — all with deterministic, objectively gradable outcomes.

## Tasks

| Task | Difficulty | Description | Records | Issues |
|------|-----------|-------------|---------|--------|
| `easy` | Simple | Fix data types: strings to numbers, booleans, ISO dates | 5 | ~19 |
| `medium` | Moderate | Normalize formats: names, phones, emails, dates, addresses | 10 | ~45 |
| `hard` | Complex | Deduplicate records and resolve conflicts | 15 | 5 groups |

## Action Space

```python
# Fix a single field value
CleanAction(operation="set_field", record_id="1", field_name="age", new_value=25)

# Fix multiple fields in one record (more efficient = higher score)
CleanAction(operation="set_field_bulk", record_id="1", field_choices={"age": 25, "active": True, "score": 89.5})

# Mark duplicate
CleanAction(operation="mark_duplicate", record_id="2", master_id="1")

# Merge duplicates
CleanAction(operation="merge", record_id="2", master_id="1", field_choices={"email": "keep_duplicate"})

# Delete a record
CleanAction(operation="delete_record", record_id="3")

# No operation
CleanAction(operation="noop")
```

## Observation Space

```python
CleaningObservation(
    data=[...],                    # Current dataset (list of dicts)
    remaining_issues=[...],        # Issues still to fix
    total_issues=19,               # Total at episode start
    issues_fixed=5,                # Fixed so far
    issues_remaining=14,           # Left to fix
    task_id="easy",                # Current task
    step_count=5,                  # Steps taken
    max_steps=30,                  # Max allowed
    last_action_result="success",  # success/no_effect/invalid/error
    message="...",                 # Human-readable feedback
    done=False,
    reward=0.3333,
)
```

## Reward Design

Multi-signal reward function with partial progress:

- **Score improvement**: `(new_score - old_score) * 10.0` — primary signal
- **Completion bonus**: `+2.0` when score reaches 1.0
- **Efficiency bonus**: `+0.5 * (1 - step/max_steps)` for finishing early
- **Stagnation penalty**: `-0.05` when no improvement
- **Regression penalty**: `-0.3` when score decreases (destructive action)

## Quick Start

### Using the Client

```python
from data_cleaning_env import DataCleaningEnv, CleanAction

with DataCleaningEnv(base_url="http://localhost:8000").sync() as env:
    result = env.reset(task_id="easy")
    print(result.observation.data)
    print(result.observation.remaining_issues)

    result = env.step(CleanAction(
        operation="set_field",
        record_id="1",
        field_name="age",
        new_value=25
    ))
    print(f"Reward: {result.reward}")
```

### Deploy to Hugging Face Spaces

```bash
openenv push --repo-id your-username/data-cleaning-env
```

## Grading

Each task has a deterministic grader that scores 0.0–1.0:

- **Easy**: Field-level exact match against expected values
- **Medium**: Format compliance + correctness (case-insensitive string comparison)
- **Hard**: 50% duplicate identification (F1) + 50% record removal accuracy

## Baseline Scores

Baseline scores from `python inference.py` (deterministic rule-based agent):

| Task | Score |
|------|-------|
| `easy` | 0.867 |
| `medium` | 0.617 |
| `hard` | 0.750 |
| **mean** | **0.744** |

Optimal scores achievable with perfect actions:

| Task | Score |
|------|-------|
| `easy` | 1.000 |
| `medium` | 1.000 |
| `hard` | 1.000 |

Graders are deterministic: running the same sequence of actions always produces the same score.

## Project Structure

```
data_cleaning_env/
├── __init__.py
├── models.py              # CleanAction, CleaningObservation, CleaningReward, CleaningState
├── client.py              # DataCleaningEnv client
├── inference.py           # Baseline inference script
├── openenv.yaml           # Environment manifest
├── pyproject.toml         # Package metadata
├── README.md
└── server/
    ├── __init__.py
    ├── app.py             # FastAPI server
    ├── Dockerfile
    ├── requirements.txt
    ├── data_cleaning_env_environment.py  # Environment logic
    └── tasks/
        ├── __init__.py
        ├── task1_type_fixes.py     # Easy task + grader
        ├── task2_normalization.py  # Medium task + grader
        └── task3_dedup.py          # Hard task + grader
```
