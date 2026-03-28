"""Data models for the Data Cleaning Environment."""

from typing import Any, Dict, List, Optional
from pydantic import Field
from openenv.core.env_server.types import Action, Observation, State


class CleanAction(Action):
    """Action for data cleaning operations."""
    operation: str = Field(..., description="Operation type: set_field, mark_duplicate, merge, delete_record, noop")
    record_id: Optional[str] = Field(None, description="Target record ID")
    field_name: Optional[str] = Field(None, description="Target field name")
    new_value: Optional[Any] = Field(None, description="New value for set_field")
    master_id: Optional[str] = Field(None, description="Master record ID for mark_duplicate/merge")
    field_choices: Optional[Dict[str, str]] = Field(None, description="Field merge strategy: keep_master or keep_duplicate")


class CleaningObservation(Observation):
    """Observation returned after each cleaning step."""
    data: List[Dict[str, Any]] = Field(default_factory=list, description="Current dataset state")
    remaining_issues: List[Dict[str, Any]] = Field(default_factory=list, description="Issues still to fix")
    total_issues: int = Field(0, description="Total issues at episode start")
    issues_fixed: int = Field(0, description="Issues fixed so far")
    issues_remaining: int = Field(0, description="Issues left to fix")
    task_id: str = Field("", description="Current task identifier")
    step_count: int = Field(0, description="Steps taken this episode")
    max_steps: int = Field(50, description="Maximum allowed steps")
    last_action_result: str = Field("", description="Result of last action: success, no_effect, invalid, error")
    message: str = Field("", description="Human-readable feedback")


class CleaningReward(Action):
    """Typed reward model for data cleaning — captures reward breakdown per step."""
    score: float = Field(0.0, description="Current grader score (0.0–1.0)")
    score_delta: float = Field(0.0, description="Score improvement this step")
    step_reward: float = Field(0.0, description="Reward for score improvement")
    completion_bonus: float = Field(0.0, description="Bonus for reaching score 1.0")
    stagnation_penalty: float = Field(0.0, description="Penalty for no improvement")
    cumulative_score: float = Field(0.0, description="Cumulative grader score across episode")


class CleaningState(State):
    """Episode state for data cleaning."""
    task_id: str = ""
    current_data: List[Dict[str, Any]] = Field(default_factory=list)
    expected_data: List[Dict[str, Any]] = Field(default_factory=list)
    original_data: List[Dict[str, Any]] = Field(default_factory=list)
    issues: List[Dict[str, Any]] = Field(default_factory=list)
    fixed_issues: List[str] = Field(default_factory=list)
    duplicate_groups: Dict[str, str] = Field(default_factory=dict)
