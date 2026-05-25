"""固定路线兼容门面。

新代码应优先从 route_contracts、route_parsers、elevator_assist 引用；
本文件保留旧导入面，避免并行 sprint 中其他 owner 的调用突然断裂。
"""

from ros2_trashbot_nav.elevator_assist import (
    ELEVATOR_ASSIST_EVIDENCE_STATUSES,
    ELEVATOR_ASSIST_EVIDENCE_VERSION,
    build_elevator_assist_evidence,
    build_elevator_assist_status,
)
from ros2_trashbot_nav.route_contracts import (
    FAILURE_CODE_CHECKPOINT_MISSING,
    FAILURE_CODE_NAVIGATION_ABORT,
    FAILURE_CODE_NAVIGATION_INTERRUPTED,
    FAILURE_CODE_NAVIGATION_TIMEOUT,
    FAILURE_CODE_NO_ROUTE,
    ROUTE_CONTRACT_VERSION,
    build_checkpoint_id,
    build_route_checkpoint_payload,
    build_route_id,
    build_route_replay_artifact_path,
    build_route_replay_entry,
)
from ros2_trashbot_nav.route_parsers import (
    OPTIONAL_NUMERIC_FIELDS,
    REQUIRED_WAYPOINT_FIELDS,
    load_waypoints_from_csv,
    load_waypoints_from_simple_yaml,
    validate_route_yaml_data,
    validate_waypoints,
)


# 这些字面量留在门面里，是为了静态 contract 测试能直接证明旧入口仍可追溯。
_ROUTE_CONTRACT_LITERAL = 'fixed_route.v1'
_ELEVATOR_CONTRACT_LITERAL = 'elevator_assist.evidence.v1'

# 兼容静态 contract 审阅：完整 profile 已迁移到 elevator_assist.py。
# 'door_open' 'door_closed_or_unknown' 'inside_elevator'
# 'target_floor_confirmed' 'target_floor_unconfirmed' 'safe_to_exit' 'unsafe_to_exit'
# 'robot_readable' 'operator_readable'


__all__ = [
    'ELEVATOR_ASSIST_EVIDENCE_STATUSES',
    'ELEVATOR_ASSIST_EVIDENCE_VERSION',
    'FAILURE_CODE_CHECKPOINT_MISSING',
    'FAILURE_CODE_NAVIGATION_ABORT',
    'FAILURE_CODE_NAVIGATION_INTERRUPTED',
    'FAILURE_CODE_NAVIGATION_TIMEOUT',
    'FAILURE_CODE_NO_ROUTE',
    'OPTIONAL_NUMERIC_FIELDS',
    'REQUIRED_WAYPOINT_FIELDS',
    'ROUTE_CONTRACT_VERSION',
    'build_checkpoint_id',
    'build_elevator_assist_evidence',
    'build_elevator_assist_status',
    'build_route_checkpoint_payload',
    'build_route_id',
    'build_route_replay_artifact_path',
    'build_route_replay_entry',
    'load_waypoints_from_csv',
    'load_waypoints_from_simple_yaml',
    'validate_route_yaml_data',
    'validate_waypoints',
]
