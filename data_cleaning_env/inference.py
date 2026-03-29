"""
Data Cleaning Environment — Baseline Inference Script

Reads API credentials from environment variables:
    API_BASE_URL  — LLM API endpoint (e.g., https://router.huggingface.co/v1)
    MODEL_NAME    — Model identifier for inference
    HF_TOKEN      — Hugging Face / API key
    OPENAI_API_KEY — Alternative API key

If no API credentials are set, runs a deterministic rule-based baseline agent.
This ensures the script always produces reproducible scores.

Usage:
    # With LLM:
    export API_BASE_URL="https://router.huggingface.co/v1"
    export MODEL_NAME="meta-llama/Llama-3.1-8B-Instruct"
    export HF_TOKEN="hf_..."
    python inference.py

    # Without LLM (deterministic baseline):
    python inference.py
"""

import json
import os
import re
import sys
import textwrap

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server.data_cleaning_env_environment import DataCleaningEnvironment
from models import CleanAction

API_BASE_URL = os.getenv("API_BASE_URL")
API_KEY = os.getenv("HF_TOKEN") or os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")
MAX_STEPS = 50
TEMPERATURE = 0.1
MAX_TOKENS = 300

SYSTEM_PROMPT = textwrap.dedent("""
You are a data cleaning expert. You receive a dirty dataset with detected issues and must clean it by issuing actions.

RESPONSE FORMAT:
Reply with exactly ONE JSON object on a single line, no other text:
{"operation": "set_field", "record_id": "1", "field_name": "age", "new_value": 25}
{"operation": "set_field_bulk", "record_id": "1", "field_choices": {"age": 25, "active": true}}
{"operation": "mark_duplicate", "record_id": "2", "master_id": "1"}
{"operation": "delete_record", "record_id": "3"}
{"operation": "noop"}

AVAILABLE OPERATIONS:
- "set_field": Fix one field value (type conversion, format normalization)
- "set_field_bulk": Fix multiple fields in one record at once (more efficient)
- "mark_duplicate": Identify a record as duplicate of another
- "delete_record": Remove a record entirely
- "noop": Do nothing (only when all issues are fixed)

STRATEGY:
1. Look at the "remaining issues" list — each has a hint explaining what to fix
2. For type issues: convert the value to the correct type (int, float, bool, null)
3. For format issues: normalize the value (ISO dates, digits-only phones, Title Case names)
4. For duplicate issues: mark_duplicate, then delete_record on the duplicate
5. Use set_field_bulk when a record has multiple issues
6. When fixing booleans: use true/false (not "true"/"false")
7. When fixing numbers: use actual numbers (not strings)
8. When fixing dates: use ISO format YYYY-MM-DD
9. When fixing phones: use digits only
10. When fixing emails: lowercase and trim
""").strip()


def parse_action(response_text: str) -> dict:
    """Parse model response into action dict."""
    if not response_text:
        return {"operation": "noop"}

    response_text = response_text.strip()

    try:
        action = json.loads(response_text)
        if isinstance(action, dict) and "operation" in action:
            return action
    except json.JSONDecodeError:
        pass

    # Find JSON object with balanced braces (handles nested structures)
    brace_count = 0
    start_idx = None
    for i, char in enumerate(response_text):
        if char == '{':
            if brace_count == 0:
                start_idx = i
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0 and start_idx is not None:
                try:
                    action = json.loads(response_text[start_idx : i + 1])
                    if isinstance(action, dict) and "operation" in action:
                        return action
                except json.JSONDecodeError:
                    pass
                start_idx = None

    return {"operation": "noop"}


def deterministic_agent(observation) -> dict:
    """Rule-based agent that uses issue hints to determine actions."""
    if not observation.remaining_issues:
        return {"operation": "noop"}

    issue = observation.remaining_issues[0]
    issue_type = issue.get("type", "")
    hint = issue.get("hint", "")

    if issue_type == "duplicate":
        record_ids = issue.get("record_ids", [])
        if len(record_ids) >= 2:
            return {"operation": "mark_duplicate", "record_id": record_ids[1], "master_id": record_ids[0]}
        return {"operation": "noop"}

    record_id = issue.get("record_id", "")
    field = issue.get("field", "")

    if not record_id or not field:
        return {"operation": "noop"}

    # Parse hint to determine correct value
    hint_lower = hint.lower()
    new_value = None

    if "boolean" in hint_lower:
        if "true" in hint_lower and "false" not in hint_lower:
            new_value = True
        elif "false" in hint_lower:
            new_value = False
    elif "integer" in hint_lower or "int" in hint_lower:
        match = re.search(r'integer\s+(\d+)', hint_lower)
        if match:
            new_value = int(match.group(1))
    elif "float" in hint_lower:
        match = re.search(r'float\s+([\d.]+)', hint_lower)
        if match:
            new_value = float(match.group(1))
    elif "null" in hint_lower or "none" in hint_lower:
        new_value = None
    elif "iso format" in hint_lower or "iso" in hint_lower or "convert" in hint_lower:
        match = re.search(r"['\"](\d{4}-\d{2}-\d{2})['\"]", hint)
        if match:
            new_value = match.group(1)
    elif "digits only" in hint_lower or "extract digits" in hint_lower:
        match = re.search(r"['\"]?(\d{10,})['\"]?", hint)
        if match:
            new_value = match.group(1)

    # Fallback: extract the last single-quoted string as the expected value
    if new_value is None:
        quoted = re.findall(r"'([^']*)'", hint)
        if quoted:
            new_value = quoted[-1]

    if new_value is not None:
        return {"operation": "set_field", "record_id": record_id, "field_name": field, "new_value": new_value}

    return {"operation": "noop"}


def build_user_prompt(observation, step: int) -> str:
    """Build user prompt from observation."""
    data_json = json.dumps(observation.data, indent=2)
    issues_json = json.dumps(observation.remaining_issues[:10], indent=2)

    score = 0
    if hasattr(observation, 'metadata') and observation.metadata:
        score = observation.metadata.get('score', 0)

    prompt = f"""Step {step}/{observation.max_steps} | Task: {observation.task_id}
Issues fixed: {observation.issues_fixed}/{observation.total_issues} | Score: {score:.3f}

Current dataset:
{data_json}

Remaining issues (first 10):
{issues_json}

Last action result: {observation.last_action_result}
{observation.message}

What cleaning action should you take next? Reply with ONE JSON action object."""

    return prompt


def run_episode_llm(env, task_id: str, client) -> float:
    """Run one episode using LLM agent."""
    import openai
    observation = env.reset(task_id=task_id)

    for step in range(1, MAX_STEPS + 1):
        if observation.done:
            break

        user_prompt = build_user_prompt(observation, step)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        try:
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
                stream=False,
            )
            response_text = completion.choices[0].message.content or ""
        except Exception as exc:
            print(f"  LLM error ({exc}). Using fallback.")
            action_dict = deterministic_agent(observation)
            response_text = json.dumps(action_dict)

        action_dict = parse_action(response_text)
        action = CleanAction(
            operation=action_dict.get("operation", "noop"),
            record_id=action_dict.get("record_id"),
            field_name=action_dict.get("field_name"),
            new_value=action_dict.get("new_value"),
            master_id=action_dict.get("master_id"),
            field_choices=action_dict.get("field_choices"),
        )
        observation = env.step(action)

    score = 0
    if hasattr(observation, 'metadata') and observation.metadata:
        score = observation.metadata.get('score', 0)
    return score


def run_episode_deterministic(env, task_id: str) -> float:
    """Run one episode using deterministic rule-based agent."""
    observation = env.reset(task_id=task_id)

    for step in range(1, MAX_STEPS + 1):
        if observation.done:
            break

        action_dict = deterministic_agent(observation)
        action = CleanAction(
            operation=action_dict.get("operation", "noop"),
            record_id=action_dict.get("record_id"),
            field_name=action_dict.get("field_name"),
            new_value=action_dict.get("new_value"),
            master_id=action_dict.get("master_id"),
            field_choices=action_dict.get("field_choices"),
        )
        observation = env.step(action)

    score = 0
    if hasattr(observation, 'metadata') and observation.metadata:
        score = observation.metadata.get('score', 0)
    return score


def main():
    """Run baseline inference on all 3 tasks."""
    env = DataCleaningEnvironment()

    use_llm = bool(API_BASE_URL and API_KEY and MODEL_NAME)

    if use_llm:
        from openai import OpenAI
        client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
        print(f"Using LLM: {MODEL_NAME} at {API_BASE_URL}")
        run_fn = lambda tid: run_episode_llm(env, tid, client)
    else:
        print("No API credentials found. Using deterministic rule-based baseline agent.")
        run_fn = lambda tid: run_episode_deterministic(env, tid)

    scores = {}
    for task_id in ["easy", "medium", "hard"]:
        print(f"\nRunning {task_id}...")
        score = run_fn(task_id)
        scores[task_id] = score
        print(f"  {task_id}: {score:.3f}")

    print(f"\n{'='*60}")
    print("BASELINE SCORES")
    print(f"{'='*60}")
    for task_id, score in scores.items():
        print(f"  {task_id:8s}: {score:.3f}")
    mean_score = sum(scores.values()) / len(scores)
    print(f"  {'mean':8s}: {mean_score:.3f}")


if __name__ == "__main__":
    main()
