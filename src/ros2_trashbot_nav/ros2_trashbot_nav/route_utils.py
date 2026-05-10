import csv


ROUTE_CONTRACT_VERSION = 'fixed_route.v1'
ELEVATOR_ASSIST_EVIDENCE_VERSION = 'elevator_assist.evidence.v1'
REQUIRED_WAYPOINT_FIELDS = ('x', 'y', 'qw')
OPTIONAL_NUMERIC_FIELDS = ('z', 'qx', 'qy', 'qz')

FAILURE_CODE_NO_ROUTE = 'NO_ROUTE'
FAILURE_CODE_CHECKPOINT_MISSING = 'CHECKPOINT_MISSING'
FAILURE_CODE_NAVIGATION_ABORT = 'NAVIGATION_ABORT'
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


def _coerce_float(value, field_name: str, source: str, index: int) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f'{source} waypoint {index} field "{field_name}" must be numeric: {value!r}'
        ) from exc


def validate_waypoints(waypoints, source: str = 'route'):
    """Validate and normalize fixed-route waypoints without ROS dependencies."""
    if not isinstance(waypoints, list):
        raise ValueError(f'{source} field "waypoints" must be a list')
    if not waypoints:
        raise ValueError(f'{source} route must not be empty')

    normalized = []
    for index, waypoint in enumerate(waypoints):
        if not isinstance(waypoint, dict):
            raise ValueError(
                f'{source} waypoint {index} must be a mapping, got {type(waypoint).__name__}'
            )
        for field_name in REQUIRED_WAYPOINT_FIELDS:
            if field_name not in waypoint or waypoint.get(field_name) in (None, ''):
                raise ValueError(f'{source} waypoint {index} missing required field "{field_name}"')

        frame_id = str(waypoint.get('frame_id') or 'map').strip() or 'map'
        item = {'frame_id': frame_id}
        for field_name in REQUIRED_WAYPOINT_FIELDS:
            item[field_name] = _coerce_float(waypoint.get(field_name), field_name, source, index)
        for field_name in OPTIONAL_NUMERIC_FIELDS:
            item[field_name] = _coerce_float(
                waypoint.get(field_name, 0.0), field_name, source, index
            )

        normalized.append({
            'frame_id': item['frame_id'],
            'x': item['x'],
            'y': item['y'],
            'z': item['z'],
            'qx': item['qx'],
            'qy': item['qy'],
            'qz': item['qz'],
            'qw': item['qw'],
        })
    return normalized


def validate_route_yaml_data(data, source: str = 'route'):
    if data is None:
        raise ValueError(f'{source} YAML is empty')
    if not isinstance(data, dict):
        raise ValueError(f'{source} YAML root must be a mapping')
    return validate_waypoints(data.get('waypoints'), source)


def load_waypoints_from_simple_yaml(input_yaml: str):
    """Parse the route YAML subset used by offline tests when PyYAML is absent."""
    waypoints = []
    current = None
    with open(input_yaml, 'r', encoding='utf-8') as f:
        for line_number, raw_line in enumerate(f, start=1):
            line = raw_line.split('#', 1)[0].rstrip()
            stripped = line.strip()
            if not stripped or stripped == 'waypoints:':
                continue
            if stripped.startswith('- '):
                if current is not None:
                    waypoints.append(current)
                current = {}
                stripped = stripped[2:].strip()
                if not stripped:
                    continue
            if ':' not in stripped:
                raise ValueError(
                    f'Invalid simple route YAML line {line_number} in {input_yaml}: {raw_line.rstrip()}'
                )
            if current is None:
                raise ValueError(
                    f'Unexpected field before waypoint at line {line_number} in {input_yaml}'
                )
            key, value = stripped.split(':', 1)
            current[key.strip()] = value.strip().strip('"\'')
    if current is not None:
        waypoints.append(current)
    return validate_waypoints(waypoints, input_yaml)


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
    """Normalize elevator dry-run evidence for robot and operator consumers.

    The schema is deliberately perception-agnostic: this sprint only records the
    evidence shape, so later visual gates, route markers, OCR, or manual dry-run
    events can replace the source without changing task-record or diagnostics
    consumers.
    """
    normalized_status = str(status or '').strip()
    if normalized_status not in _ELEVATOR_EVIDENCE_PROFILES:
        raise ValueError(f'unsupported elevator assist evidence status: {status!r}')
    try:
        normalized_confidence = float(confidence)
    except (TypeError, ValueError) as exc:
        raise ValueError(f'elevator assist evidence confidence must be numeric: {confidence!r}') from exc
    normalized_confidence = max(0.0, min(1.0, normalized_confidence))

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
    """Wrap normalized evidence under the stable elevator_assist status key."""
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


def load_waypoints_from_csv(input_csv: str, fallback_frame_id: str = 'map'):
    waypoints = []
    with open(input_csv, 'r', encoding='utf-8') as f:
        for line_number, row in enumerate(csv.DictReader(f), start=2):
            frame_id = (row.get('frame_id') or '').strip() or fallback_frame_id.strip() or 'map'
            for field_name in REQUIRED_WAYPOINT_FIELDS:
                if field_name not in row or row.get(field_name) in (None, ''):
                    raise ValueError(
                        f'Missing required field "{field_name}" in {input_csv} line {line_number}: {row}'
                    )
            try:
                waypoint = {
                    'frame_id': frame_id,
                    'x': float(row.get('x')),
                    'y': float(row.get('y')),
                    'z': float(row.get('z') or 0.0),
                    'qx': float(row.get('qx') or 0.0),
                    'qy': float(row.get('qy') or 0.0),
                    'qz': float(row.get('qz') or 0.0),
                    'qw': float(row.get('qw')),
                }
            except ValueError as exc:
                raise ValueError(f'Invalid numeric value in {input_csv} line {line_number}: {row}') from exc
            waypoints.append(waypoint)
    return validate_waypoints(waypoints, input_csv)

