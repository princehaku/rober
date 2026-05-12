from pathlib import Path

try:
    import yaml
except ModuleNotFoundError:
    yaml = None


def _load_simple_waypoint_yaml(text: str):
    waypoints = []
    current = None
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped == "waypoints:":
            continue
        if stripped.startswith("- "):
            if current is not None:
                waypoints.append(current)
            current = {}
            stripped = stripped[2:].strip()
            if not stripped:
                continue
        if ":" not in stripped or current is None:
            continue
        key, value = stripped.split(":", 1)
        value = value.strip().strip('"').strip("'")
        if value.replace(".", "", 1).replace("-", "", 1).isdigit():
            if "." in value:
                current[key.strip()] = float(value)
            else:
                current[key.strip()] = int(value)
        else:
            current[key.strip()] = value
    if current is not None:
        waypoints.append(current)
    return {"waypoints": waypoints}


def load_waypoint_file(path):
    waypoint_path = Path(path).expanduser()
    text = waypoint_path.read_text(encoding="utf-8")
    if yaml is not None:
        data = yaml.safe_load(text) or {}
    else:
        data = _load_simple_waypoint_yaml(text)
    if not isinstance(data.get("waypoints"), list):
        raise ValueError(f'waypoint file {waypoint_path} must contain a "waypoints" list')
    return data


def find_waypoint_pose(data, target_name: str):
    waypoints = data.get("waypoints") or []
    target_name = (target_name or "").strip()

    if target_name:
        selected = next((wp for wp in waypoints if wp.get("name") == target_name), None)
    else:
        selected = next((wp for wp in waypoints if int(wp.get("type", 0)) == 2), None)

    if selected is None:
        raise ValueError(f"delivery target not found: {target_name or 'first type=2 waypoint'}")

    return {
        "name": selected.get("name", ""),
        "frame_id": selected.get("frame_id") or "map",
        "x": float(selected.get("x") or 0.0),
        "y": float(selected.get("y") or 0.0),
        "z": float(selected.get("z") or 0.0),
        "qx": float(selected.get("orientation_x") or selected.get("qx") or 0.0),
        "qy": float(selected.get("orientation_y") or selected.get("qy") or 0.0),
        "qz": float(selected.get("orientation_z") or selected.get("qz") or 0.0),
        "qw": float(selected.get("orientation_w") or selected.get("qw") or 1.0),
    }
