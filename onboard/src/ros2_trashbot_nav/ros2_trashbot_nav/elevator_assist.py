"""电梯 assisted delivery 的离线 evidence schema。

这里不做门状态或楼层 OCR 推断，只定义行为层可以消费的保守证据形状。
"""


ELEVATOR_ASSIST_EVIDENCE_VERSION = 'elevator_assist.evidence.v1'
ELEVATOR_ASSIST_EVIDENCE_STATUSES = (
    'door_open',
    'door_closed_or_unknown',
    'inside_elevator',
    'target_floor_confirmed',
    'target_floor_unconfirmed',
    'safe_to_exit',
    'unsafe_to_exit',
)

_ELEVATOR_EVIDENCE_PROFILES = {
    'door_open': {
        'robot_readable': 'elevator door is open',
        'operator_readable': '电梯门已打开。',
        'reliable': True,
        'allows_entry': True,
        'confirms_target_floor': False,
        'allows_exit': False,
        'requires_operator': False,
    },
    'door_closed_or_unknown': {
        'robot_readable': 'elevator door is closed or unknown',
        'operator_readable': '电梯门未打开或状态未知。',
        'reliable': False,
        'allows_entry': False,
        'confirms_target_floor': False,
        'allows_exit': False,
        'requires_operator': True,
    },
    'inside_elevator': {
        'robot_readable': 'robot is stopped inside elevator',
        'operator_readable': '小车已进入电梯并停车等待。',
        'reliable': True,
        'allows_entry': False,
        'confirms_target_floor': False,
        'allows_exit': False,
        'requires_operator': False,
    },
    'target_floor_confirmed': {
        'robot_readable': 'target floor evidence is confirmed',
        'operator_readable': '已确认到达目标楼层。',
        'reliable': True,
        'allows_entry': False,
        'confirms_target_floor': True,
        'allows_exit': False,
        'requires_operator': False,
    },
    'target_floor_unconfirmed': {
        'robot_readable': 'target floor evidence is not confirmed',
        'operator_readable': '未确认目标楼层。',
        'reliable': False,
        'allows_entry': False,
        'confirms_target_floor': False,
        'allows_exit': False,
        'requires_operator': True,
    },
    'safe_to_exit': {
        'robot_readable': 'target floor and exit path evidence allow exit',
        'operator_readable': '目标楼层和驶出条件已满足。',
        'reliable': True,
        'allows_entry': False,
        'confirms_target_floor': True,
        'allows_exit': True,
        'requires_operator': False,
    },
    'unsafe_to_exit': {
        'robot_readable': 'exit condition is unsafe or unknown',
        'operator_readable': '驶出条件不安全或未知。',
        'reliable': False,
        'allows_entry': False,
        'confirms_target_floor': False,
        'allows_exit': False,
        'requires_operator': True,
    },
}


def build_elevator_assist_evidence(
    status: str,
    *,
    source: str = 'dry_run',
    confidence: float = 0.0,
    detail: str = '',
    checkpoint=None,
    observed_at=None,
    metadata=None,
):
    """归一化电梯证据，避免视觉 proof 被误写成真实楼层确认。"""
    normalized_status = str(status or '').strip()
    if normalized_status not in _ELEVATOR_EVIDENCE_PROFILES:
        raise ValueError(f'unsupported elevator assist evidence status: {status!r}')
    try:
        normalized_confidence = float(confidence)
    except (TypeError, ValueError) as exc:
        raise ValueError(f'elevator assist evidence confidence must be numeric: {confidence!r}') from exc
    normalized_confidence = max(0.0, min(1.0, normalized_confidence))

    # profile 是当前 schema 的事实表，后续 OCR/门检测只能填 evidence，不能改含义。
    profile = _ELEVATOR_EVIDENCE_PROFILES[normalized_status]
    return {
        'schema_version': ELEVATOR_ASSIST_EVIDENCE_VERSION,
        'status': normalized_status,
        'source': str(source or 'dry_run'),
        'confidence': normalized_confidence,
        'detail': str(detail or profile['robot_readable']),
        'checkpoint': checkpoint,
        'observed_at': observed_at,
        'robot_readable': profile['robot_readable'],
        'operator_readable': profile['operator_readable'],
        'reliable': profile['reliable'],
        'allows_entry': profile['allows_entry'],
        'confirms_target_floor': profile['confirms_target_floor'],
        'allows_exit': profile['allows_exit'],
        'requires_operator': profile['requires_operator'],
        'metadata': dict(metadata or {}),
    }


def build_elevator_assist_status(
    evidence=None,
    *,
    enabled: bool = False,
    mode: str = 'dry_run',
):
    """把 evidence 包装到稳定 elevator_assist 节点，供状态文件直接落盘。"""
    normalized_evidence = evidence or build_elevator_assist_evidence(
        'door_closed_or_unknown',
        source='offline_schema',
        detail='elevator assist dry-run evidence is not supplied',
    )
    return {
        'enabled': bool(enabled),
        'mode': str(mode or 'dry_run'),
        'evidence_schema_version': ELEVATOR_ASSIST_EVIDENCE_VERSION,
        'supported_evidence': list(ELEVATOR_ASSIST_EVIDENCE_STATUSES),
        'evidence': normalized_evidence,
    }
