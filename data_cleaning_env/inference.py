"""
Data Cleaning Environment — Baseline Inference Script

MANDATORY environment variables:
    API_BASE_URL  — LLM API endpoint (e.g., https://router.huggingface.co/v1)
    MODEL_NAME    — Model identifier for inference
    HF_TOKEN      — Hugging Face / API key

Usage:
    export API_BASE_URL="https://router.huggingface.co/v1"
    export MODEL_NAME="meta-llama/Llama-3.1-8B-Instruct"
    export HF_TOKEN="hf_..."
    python inference.py
"""

import json
import os
import re
import sys
import textwrap

from openai import OpenAI

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server.data_cleaning_env_environment import DataCleaningEnvironment
from models import CleanAction

API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
API_KEY = os.getenv("HF_TOKEN") or os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "meta-llama/Llama-3.1-8B-Instruct")
MAX_STEPS = 50
TEMPERATURE = 0.1
MAX_TOKENS = 300
FALLBACK_ACTION = {"operation": "noop"}

SYSTEM_PROMPT = textwrap.dedent("""
You are a data cleaning expert. You receive a dirty dataset and must clean it by issuing actions.

RESPONSE FORMAT:
Reply with exactly ONE JSON object on a single line, no other text:
{"operation": "set_field", "record_id": "1", "field_name": "age", "new_value": 25}
{"operation": "mark_duplicate", "record_id": "2", "master_id": "1"}
{"operation": "merge", "record_id": "2", "master_id": "1", "field_choices": {"email": "keep_duplicate"}}
{"operation": "noop"}

RULES:
- Use "set_field" to fix individual values (type conversion, format normalization)
- Use "mark_duplicate" to identify duplicate records
- Use "merge" to combine duplicate records into one
- Use "noop" when no action is needed
- For set_field, new_value must be the correct Python type (int, float, bool, str, or null)
- Fix issues one at a time
- Do NOT include any text outside the JSON object
""").strip()


def parse_action(response_text: str) -> dict:
    """Parse model response into action dict."""
    if not response_text:
        return FALLBACK_ACTION

    response_text = response_text.strip()

    # Try to find JSON object in response
    try:
        # Direct parse
        action = json.loads(response_text)
        if isinstance(action, dict) and "operation" in action:
            return action
    except json.JSONDecodeError:
        pass

    # Try regex extraction
    json_match = re.search(r'\{[^{}]+\}', response_text)
    if json_match:
        try:
            action = json.loads(json_match.group())
            if isinstance(action, dict) and "operation" in action:
                return action
        except json.JSONDecodeError:
            pass

    return FALLBACK_ACTION


def build_user_prompt(observation, step: int) -> str:
    """Build user prompt from observation."""
    data_json = json.dumps(observation.data, indent=2)
    issues_json = json.dumps(observation.remaining_issues[:10], indent=2)

    prompt = f"""Step {step}/{observation.max_steps} | Task: {observation.task_id}
Issues fixed: {observation.issues_fixed}/{observation.total_issues} | Score: {observation.metadata.get('score', 0):.3f}

Current dataset:
{data_json}

Remaining issues (first 10):
{issues_json}

Last action result: {observation.last_action_result}
{observation.message}

What cleaning action should you take next? Reply with ONE JSON action object."""

    return prompt


def run_episode(env: DataCleaningEnvironment, task_id: str, client: OpenAI) -> float:
    """Run one episode of data cleaning."""
    result = env.reset(task_id=task_id)
    observation = result

    print(f"\n{'='*60}")
    print(f"Task: {task_id} | Issues: {observation.total_issues} | Max steps: {observation.max_steps}")
    print(f"{'='*60}")

    for step in range(1, observation.max_steps + 1):
        if observation.done:
            print(f"Episode complete at step {step-1}")
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
            print(f"  Model request failed ({exc}). Using fallback.")
            response_text = json.dumps(FALLBACK_ACTION)

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

        score = observation.metadata.get("score", 0) if hasattr(observation, 'metadata') and observation.metadata else 0
        print(f"  Step {step}: {action.operation} "
              f"({action.record_id or ''}.{action.field_name or ''}) "
              f"-> reward={observation.reward:+.4f} score={score:.3f} "
              f"| {observation.last_action_result}")

        if observation.done:
            final_score = observation.metadata.get("score", 0) if hasattr(observation, 'metadata') and observation.metadata else 0
            print(f"  DONE! Final score: {final_score:.3f}")
            break

    final_score = observation.metadata.get("score", 0) if hasattr(observation, 'metadata') and observation.metadata else 0
    return final_score


def main():
    """Run baseline inference on all 3 tasks."""
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    env = DataCleaningEnvironment()

    scores = {}
    for task_id in ["easy", "medium", "hard"]:
        score = run_episode(env, task_id, client)
        scores[task_id] = score

    env.close()

    print(f"\n{'='*60}")
    print("BASELINE SCORES")
    print(f"{'='*60}")
    for task_id, score in scores.items():
        print(f"  {task_id:8s}: {score:.3f}")
    mean_score = sum(scores.values()) / len(scores)
    print(f"  {'mean':8s}: {mean_score:.3f}")


if __name__ == "__main__":
    main()
