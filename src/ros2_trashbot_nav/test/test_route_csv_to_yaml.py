import tempfile
from pathlib import Path

from ros2_trashbot_nav.route_utils import load_waypoints_from_csv


def test_load_waypoints_from_csv_parses_numeric_fields():
    csv_content = (
        "index,sec,nanosec,x,y,z,qx,qy,qz,qw,frame\n"
        "0,1,2,1.25,2.5,0.0,0.0,0.0,0.1,0.99,000.jpg\n"
    )
    with tempfile.TemporaryDirectory() as td:
        csv_path = Path(td) / "route.csv"
        csv_path.write_text(csv_content, encoding="utf-8")
        waypoints = load_waypoints_from_csv(str(csv_path), "map")

    assert len(waypoints) == 1
    wp = waypoints[0]
    assert wp["frame_id"] == "map"
    assert wp["x"] == 1.25
    assert wp["y"] == 2.5
    assert wp["qz"] == 0.1
    assert wp["qw"] == 0.99
