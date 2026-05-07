import csv


def load_waypoints_from_csv(input_csv: str, fallback_frame_id: str = 'map'):
    waypoints = []
    with open(input_csv, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            waypoints.append({
                'frame_id': row.get('frame_id', fallback_frame_id),
                'x': float(row.get('x', 0.0)),
                'y': float(row.get('y', 0.0)),
                'z': float(row.get('z', 0.0)),
                'qx': float(row.get('qx', 0.0)),
                'qy': float(row.get('qy', 0.0)),
                'qz': float(row.get('qz', 0.0)),
                'qw': float(row.get('qw', 1.0)),
            })
    return waypoints

