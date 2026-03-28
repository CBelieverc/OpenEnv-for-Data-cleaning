"""Data Cleaning Environment Client."""

from typing import Any, Dict, List, Optional

from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State

from .models import CleanAction, CleaningObservation


class DataCleaningEnv(EnvClient[CleanAction, CleaningObservation, State]):
    """Client for the Data Cleaning Environment."""

    def _step_payload(self, action: CleanAction) -> Dict:
        """Convert CleanAction to JSON payload."""
        return {
            "operation": action.operation,
            "record_id": action.record_id,
            "field_name": action.field_name,
            "new_value": action.new_value,
            "master_id": action.master_id,
            "field_choices": action.field_choices,
        }

    def _parse_result(self, payload: Dict) -> StepResult[CleaningObservation]:
        """Parse server response into StepResult."""
        obs_data = payload.get("observation", {})
        observation = CleaningObservation(
            done=payload.get("done", False),
            reward=payload.get("reward"),
            data=obs_data.get("data", []),
            remaining_issues=obs_data.get("remaining_issues", []),
            total_issues=obs_data.get("total_issues", 0),
            issues_fixed=obs_data.get("issues_fixed", 0),
            issues_remaining=obs_data.get("issues_remaining", 0),
            task_id=obs_data.get("task_id", ""),
            step_count=obs_data.get("step_count", 0),
            max_steps=obs_data.get("max_steps", 50),
            last_action_result=obs_data.get("last_action_result", ""),
            message=obs_data.get("message", ""),
            metadata=obs_data.get("metadata", {}),
        )
        return StepResult(
            observation=observation,
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> State:
        """Parse server response into State."""
        return State(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
        )
