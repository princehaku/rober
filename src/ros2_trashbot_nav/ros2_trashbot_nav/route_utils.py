import csv


def load_waypoints_from_csv(input_csv: str, fallback_frame_id: str = 'map'):
    waypoints = []
    with open(input_csv, 'r', encoding='utf-8') as f:
        for line_number, row in enumerate(csv.DictReader(f), start=2):
            frame_id = (row.get('frame_id') or fallback_frame_id).strip()
            try:
                waypoint = {
                    'frame_id': frame_id,
                    'x': float(row.get('x') or 0.0),
                    'y': float(row.get('y') or 0.0),
                    'z': float(row.get('z') or 0.0),
                    'qx': float(row.get('qx') or 0.0),
                    'qy': float(row.get('qy') or 0.0),
                    'qz': float(row.get('qz') or 0.0),
                    'qw': float(row.get('qw') or 1.0),
                }
            except ValueError as exc:
                raise ValueError(f'Invalid numeric value in {input_csv} line {line_number}: {row}') from exc
            waypoints.append(waypoint)
    return waypoints

