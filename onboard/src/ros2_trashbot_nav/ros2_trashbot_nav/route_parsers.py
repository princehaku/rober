"""固定路线 CSV/YAML 解析与校验。

解析逻辑保持 ROS-free，目的是让路线格式错误可以在笔记本、CI 或 dry-run
阶段被提前发现，而不是等到 Nav2 runtime 才失败。
"""

import csv


REQUIRED_WAYPOINT_FIELDS = ('x', 'y', 'qw')
OPTIONAL_NUMERIC_FIELDS = ('z', 'qx', 'qy', 'qz')


def _coerce_float(value, field_name: str, source: str, index: int) -> float:
    """把输入转成 float；错误消息带 source/index 方便现场定位坏行。"""
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f'{source} waypoint {index} field "{field_name}" must be numeric: {value!r}'
        ) from exc


def validate_waypoints(waypoints, source: str = 'route'):
    """校验并归一化 waypoint 列表，输出固定 JSON 友好结构。"""
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

        # frame_id 允许缺省为 map，避免 recorder 旧 CSV 的 frame 图片列被误用成坐标系。
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
    """校验固定路线 YAML 根对象，只接受 waypoints contract。"""
    if data is None:
        raise ValueError(f'{source} YAML is empty')
    if not isinstance(data, dict):
        raise ValueError(f'{source} YAML root must be a mapping')
    return validate_waypoints(data.get('waypoints'), source)


def load_waypoints_from_simple_yaml(input_yaml: str):
    """无 PyYAML 时的最小 YAML 解析器，仅服务当前固定路线子集。"""
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


def load_waypoints_from_csv(input_csv: str, fallback_frame_id: str = 'map'):
    """读取 recorder CSV 并输出固定路线 YAML 可直接使用的 waypoint 列表。"""
    waypoints = []
    with open(input_csv, 'r', encoding='utf-8') as f:
        for line_number, row in enumerate(csv.DictReader(f), start=2):
            # recorder 里 frame 通常是图片名，只有显式 frame_id 才作为 pose frame。
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
