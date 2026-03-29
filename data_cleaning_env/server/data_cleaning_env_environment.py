"""Data Cleaning Environment Implementation."""

import copy
from typing import Any, Optional
from uuid import uuid4

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

try:
    from ..models import CleanAction, CleaningObservation, CleaningState
    from .tasks import get_task
except ImportError:
    from models import CleanAction, CleaningObservation, CleaningState
    from server.tasks import get_task


class DataCleaningEnvironment(Environment):
    """OpenEnv environment for data cleaning tasks."""

    SUPPORTS_CONCURRENT_SESSIONS = True

    def __init__(self):
        super().__init__()
        self._state = CleaningState()
        self._dirty_data = []
        self._current_data = []
        self._expected_data = []
        self._issues = []
        self._fixed_issues = set()
        self._duplicate_groups = {}
        self._record_index = {}
        self._task_id = ""
        self._max_steps = 50
        self._step_count = 0
        self._total_issues = 0
        self._previous_score = 0.0

    def reset(
        self,
        seed: Optional[int] = None,
        episode_id: Optional[str] = None,
        **kwargs: Any,
    ) -> CleaningObservation:
        """Reset the environment with a new task."""
        task_id = kwargs.get("task_id", "easy")
        task = get_task(task_id)

        self._task_id = task_id
        self._dirty_data = copy.deepcopy(task["dirty_data"])
        self._current_data = copy.deepcopy(task["dirty_data"])
        self._expected_data = copy.deepcopy(task["expected_data"])
        self._issues = copy.deepcopy(task["issues"])
        self._fixed_issues = set()
        self._duplicate_groups = {}
        self._record_index = {r["id"]: r for r in self._current_data}
        self._max_steps = task["max_steps"]
        self._step_count = 0
        self._total_issues = len(self._issues)
        self._previous_score = 0.0

        self._state = CleaningState(
            episode_id=episode_id or str(uuid4()),
            step_count=0,
            task_id=task_id,
            current_data=self._current_data,
            expected_data=self._expected_data,
            original_data=self._dirty_data,
            issues=self._issues,
            fixed_issues=[],
            duplicate_groups={},
        )

        grade_fn = task["grade"]
        if task_id == "hard":
            initial_score = grade_fn(self._current_data, self._expected_data, duplicate_groups={})
        else:
            initial_score = grade_fn(self._current_data, self._expected_data)
        self._previous_score = initial_score

        remaining = self._get_remaining_issues()

        return CleaningObservation(
            done=False,
            reward=0.0,
            data=self._current_data,
            remaining_issues=remaining,
            total_issues=self._total_issues,
            issues_fixed=0,
            issues_remaining=len(remaining),
            task_id=task_id,
            step_count=0,
            max_steps=self._max_steps,
            last_action_result="success",
            message=f"Task '{task_id}' loaded. {self._total_issues} issues to fix. "
                    f"{len(self._current_data)} records. Max steps: {self._max_steps}.",
        )

    def step(
        self,
        action: CleanAction,
        timeout_s: Optional[float] = None,
        **kwargs: Any,
    ) -> CleaningObservation:
        """Execute a cleaning action."""
        self._step_count += 1
        self._state.step_count = self._step_count

        result = self._execute_action(action)

        current_score = self._compute_score()
        reward = self._calculate_reward(current_score)
        self._previous_score = current_score

        done = self._step_count >= self._max_steps or current_score >= 1.0
        if current_score >= 1.0 and not done:
            done = True

        remaining = self._get_remaining_issues()
        issues_fixed = self._total_issues - len(remaining)

        return CleaningObservation(
            done=done,
            reward=reward,
            data=self._current_data,
            remaining_issues=remaining if not done else [],
            total_issues=self._total_issues,
            issues_fixed=issues_fixed,
            issues_remaining=len(remaining),
            task_id=self._task_id,
            step_count=self._step_count,
            max_steps=self._max_steps,
            last_action_result=result["status"],
            message=result["message"],
            metadata={
                "score": current_score,
                "reward": reward,
                "duplicate_groups": self._duplicate_groups,
            },
        )

    @property
    def state(self) -> CleaningState:
        """Get current environment state."""
        self._state.current_data = self._current_data
        self._state.fixed_issues = list(self._fixed_issues)
        self._state.duplicate_groups = self._duplicate_groups
        return self._state

    def _execute_action(self, action: CleanAction) -> dict:
        """Execute the cleaning action and return result."""
        op = action.operation

        if op == "noop":
            return {"status": "no_effect", "message": "No operation performed."}

        if op == "set_field":
            return self._action_set_field(action)
        elif op == "set_field_bulk":
            return self._action_set_field_bulk(action)
        elif op == "mark_duplicate":
            return self._action_mark_duplicate(action)
        elif op == "merge":
            return self._action_merge(action)
        elif op == "delete_record":
            return self._action_delete_record(action)
        else:
            return {"status": "invalid", "message": f"Unknown operation: {op}"}

    def _action_set_field(self, action: CleanAction) -> dict:
        """Set a field value in a record."""
        if not action.record_id or not action.field_name:
            return {"status": "invalid", "message": "set_field requires record_id and field_name"}

        record = self._find_record(action.record_id)
        if record is None:
            return {"status": "error", "message": f"Record {action.record_id} not found"}

        old_value = record.get(action.field_name)
        record[action.field_name] = action.new_value
        self._update_current_data(action.record_id, record)

        issue_id = f"{action.record_id}:{action.field_name}"
        if issue_id in {i.get("issue_id") for i in self._issues}:
            self._fixed_issues.add(issue_id)

        return {
            "status": "success",
            "message": f"Set {action.record_id}.{action.field_name}: {old_value} -> {action.new_value}",
        }

    def _action_set_field_bulk(self, action: CleanAction) -> dict:
        """Set multiple fields in a record at once. Use field_choices as {field: value}."""
        if not action.record_id:
            return {"status": "invalid", "message": "set_field_bulk requires record_id"}

        field_updates = action.field_choices or {}
        if not field_updates:
            return {"status": "invalid", "message": "set_field_bulk requires field_choices as {field: value}"}

        record = self._find_record(action.record_id)
        if record is None:
            return {"status": "error", "message": f"Record {action.record_id} not found"}

        updated_fields = []
        for field_name, new_value in field_updates.items():
            old_value = record.get(field_name)
            record[field_name] = new_value
            updated_fields.append(f"{field_name}: {old_value} -> {new_value}")

            issue_id = f"{action.record_id}:{field_name}"
            if issue_id in {i.get("issue_id") for i in self._issues}:
                self._fixed_issues.add(issue_id)

        self._update_current_data(action.record_id, record)

        return {
            "status": "success",
            "message": f"Bulk updated record {action.record_id}: {'; '.join(updated_fields)}",
        }

    def _action_mark_duplicate(self, action: CleanAction) -> dict:
        """Mark a record as duplicate of master."""
        if not action.record_id or not action.master_id:
            return {"status": "invalid", "message": "mark_duplicate requires record_id and master_id"}

        if action.record_id == action.master_id:
            return {"status": "invalid", "message": "Cannot mark record as duplicate of itself"}

        self._duplicate_groups[action.record_id] = action.master_id

        dup_issue_id = None
        for issue in self._issues:
            if issue.get("type") == "duplicate":
                ids = issue.get("record_ids", [])
                if action.record_id in ids and action.master_id in ids:
                    dup_issue_id = issue.get("issue_id")
                    break
        if dup_issue_id:
            self._fixed_issues.add(dup_issue_id)

        return {
            "status": "success",
            "message": f"Marked {action.record_id} as duplicate of {action.master_id}",
        }

    def _action_merge(self, action: CleanAction) -> dict:
        """Merge a duplicate record into master."""
        if not action.record_id or not action.master_id:
            return {"status": "invalid", "message": "merge requires record_id and master_id"}

        dup_record = self._find_record(action.record_id)
        master_record = self._find_record(action.master_id)

        if dup_record is None:
            return {"status": "error", "message": f"Record {action.record_id} not found"}
        if master_record is None:
            return {"status": "error", "message": f"Master record {action.master_id} not found"}

        field_choices = action.field_choices or {}
        for field, value in dup_record.items():
            if field == "id":
                continue
            choice = field_choices.get(field, "keep_master")
            if choice == "keep_duplicate":
                master_record[field] = value

        self._update_current_data(action.master_id, master_record)
        self._remove_record(action.record_id)

        # Reassign any duplicates of the merged record to the new master
        for dup_id, master_id in list(self._duplicate_groups.items()):
            if master_id == action.record_id:
                self._duplicate_groups[dup_id] = action.master_id

        self._duplicate_groups[action.record_id] = action.master_id

        return {
            "status": "success",
            "message": f"Merged {action.record_id} into {action.master_id}",
        }

    def _action_delete_record(self, action: CleanAction) -> dict:
        """Delete a record from the dataset."""
        if not action.record_id:
            return {"status": "invalid", "message": "delete_record requires record_id"}

        if action.record_id not in self._record_index:
            return {"status": "error", "message": f"Record {action.record_id} not found"}

        self._remove_record(action.record_id)
        return {"status": "success", "message": f"Deleted record {action.record_id}"}

    def _find_record(self, record_id: str) -> dict:
        """Find a record by ID."""
        return self._record_index.get(record_id)

    def _update_current_data(self, record_id: str, updated_record: dict):
        """Update a record in current_data."""
        for i, record in enumerate(self._current_data):
            if record.get("id") == record_id:
                self._current_data[i] = updated_record
                self._record_index[record_id] = updated_record
                break

    def _remove_record(self, record_id: str):
        """Remove a record from current_data and the index."""
        self._current_data = [r for r in self._current_data if r.get("id") != record_id]
        self._record_index.pop(record_id, None)

    def _compute_score(self) -> float:
        """Compute current score using task grader."""
        task = get_task(self._task_id)
        grade_fn = task["grade"]
        if self._task_id == "hard":
            return grade_fn(self._current_data, self._expected_data, duplicate_groups=self._duplicate_groups)
        return grade_fn(self._current_data, self._expected_data)

    def _calculate_reward(self, current_score: float) -> float:
        """Calculate reward based on score improvement with efficiency and quality bonuses.

        Reward breakdown:
        - Score improvement: (current - previous) * 10.0
        - Completion bonus: +2.0 when score reaches 1.0
        - Efficiency bonus: +0.5 * (1 - step/max_steps) for finishing early
        - Quality bonus: +0.1 per batch operation (set_field_bulk)
        - Stagnation penalty: -0.05 when no improvement
        - Regression penalty: -0.3 when score decreases (destructive action)
        """
        improvement = current_score - self._previous_score

        # Base reward: score improvement
        reward = improvement * 10.0

        # Completion bonus
        if current_score >= 1.0:
            reward += 2.0
            # Efficiency bonus for finishing early
            if self._max_steps > 0:
                efficiency = 1.0 - (self._step_count / self._max_steps)
                reward += efficiency * 0.5

        # Stagnation / regression penalties
        if improvement < 0 and self._step_count > 1:
            reward -= 0.3  # Destructive action penalty
        elif improvement == 0 and self._step_count > 1:
            reward -= 0.05  # Stagnation penalty

        return round(reward, 4)

    def _get_remaining_issues(self) -> list:
        """Get list of issues not yet fixed."""
        return [i for i in self._issues if i.get("issue_id") not in self._fixed_issues]
