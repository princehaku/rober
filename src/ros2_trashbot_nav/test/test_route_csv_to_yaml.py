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


def test_load_waypoints_from_csv_ignores_image_frame_column_for_pose_frame_id():
    csv_content = (
        "index,sec,nanosec,x,y,z,qx,qy,qz,qw,frame\n"
        "0,1,2,1.25,2.5,0.0,0.0,0.0,0.1,0.99,000.jpg\n"
    )
    with tempfile.TemporaryDirectory() as td:
        csv_path = Path(td) / "route.csv"
        csv_path.write_text(csv_content, encoding="utf-8")
        waypoints = load_waypoints_from_csv(str(csv_path), "map")

    assert waypoints[0]["frame_id"] == "map"


def test_load_waypoints_from_csv_uses_explicit_frame_id_column():
    csv_content = (
        "index,sec,nanosec,frame_id,x,y,z,qx,qy,qz,qw,frame\n"
        "0,1,2,odom,1.25,2.5,0.0,0.0,0.0,0.1,0.99,000.jpg\n"
    )
    with tempfile.TemporaryDirectory() as td:
        csv_path = Path(td) / "route.csv"
        csv_path.write_text(csv_content, encoding="utf-8")
        waypoints = load_waypoints_from_csv(str(csv_path), "map")

    assert waypoints[0]["frame_id"] == "odom"


def test_load_waypoints_from_csv_falls_back_when_frame_id_is_blank():
    csv_content = (
        "index,sec,nanosec,frame_id,x,y,z,qx,qy,qz,qw,frame\n"
        "0,1,2,   ,1.25,2.5,0.0,0.0,0.0,0.1,0.99,000.jpg\n"
    )
    with tempfile.TemporaryDirectory() as td:
        csv_path = Path(td) / "route.csv"
        csv_path.write_text(csv_content, encoding="utf-8")
        waypoints = load_waypoints_from_csv(str(csv_path), "map")

    assert waypoints[0]["frame_id"] == "map"


def test_load_waypoints_from_csv_rejects_bad_numeric_values():
    csv_content = (
        "index,sec,nanosec,x,y,z,qx,qy,qz,qw,frame\n"
        "0,1,2,not-a-number,2.5,0.0,0.0,0.0,0.1,0.99,000.jpg\n"
    )
    with tempfile.TemporaryDirectory() as td:
        csv_path = Path(td) / "route.csv"
        csv_path.write_text(csv_content, encoding="utf-8")
        try:
            load_waypoints_from_csv(str(csv_path), "map")
        except ValueError as exc:
            assert "line 2" in str(exc)
        else:
            raise AssertionError("Expected invalid numeric CSV value to raise ValueError")
