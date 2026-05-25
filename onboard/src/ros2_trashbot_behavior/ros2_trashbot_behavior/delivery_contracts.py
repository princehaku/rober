from dataclasses import dataclass, field
from enum import Enum


class RobotState(Enum):
    IDLE = 0
    LEARNING = 1
    PATROLLING = 2
    COLLECTING = 3
    DELIVERING = 4
    RETURNING = 5
    ERROR = 6
    LOADED = 7
    DROPOFF = 8


@dataclass
class NavigationResult:
    success: bool
    result_code: str
    message: str
    elapsed_sec: float
    evidence: dict = field(default_factory=dict)


# fixed-route runner 与 task_record 共用这组字段，集中定义可以避免后续新增字段时
# 只改 orchestrator 而忘记同步 record 归一化逻辑。
FIXED_ROUTE_PROGRESS_FIELDS = (
    "source",
    "route_contract_version",
    "route_file",
    "route_id",
    "route_file_basename",
    "checkpoint",
    "checkpoint_id",
    "current_index",
    "target",
    "current_target",
    "total",
    "total_checkpoints",
    "evidence_ref",
    "failure_code",
)
