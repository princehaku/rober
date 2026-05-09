import csv


ROUTE_CONTRACT_VERSION = 'fixed_route.v1'
REQUIRED_WAYPOINT_FIELDS = ('x', 'y', 'qw')
OPTIONAL_NUMERIC_FIELDS = ('z', 'qx', 'qy', 'qz')


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

