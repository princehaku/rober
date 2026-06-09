# No-Motion Map Route Evidence Side2Side Check

## 验收对照

| 验收项 | 结果 | 证据 |
| --- | --- | --- |
| 本地 py_compile | 通过 | `learn.launch.py`、`route_data_recorder.py` 编译通过 |
| 本地单测 | 通过 | `test_launch_contract_static.py` + `test_route_data_recorder_static.py` 共 `19` tests OK |
| Docker/Humble build | 通过 | `Summary: 6 packages finished [54.8s]` |
| 板上 build | 通过 | `Summary: 2 packages finished [8.41s]` |
| `learn.launch.py --show-args` | 通过 | `artifacts/board_no_motion_capture_20260610/learn_show_args_after_sync.txt` |
| no-motion `route.csv` | 通过 | `route_output/route.csv` 共 `75` 行 |
| keyframe + manifest | 通过 | `route_output/keyframes/` 与 `route_output/manifest.json` |
| `map.yaml` | 通过 | `map_output/trashbot_no_motion_map.yaml` 与 `.pgm` |
| 清场后 `/scan` sample | 通过 | `no_motion_learn_capture_clean.md` 记录 `frame_id=laser_frame`，有有效 ranges/intensities |
| 清场后 camera ownership | 通过 | `no_motion_learn_capture_clean.md` 记录 `/camera/image_raw` 为 `640x480 bgr8`，清场前设备占用已解除 |
| 清场后 `/tf_static` | 通过 | `base_link -> laser_frame` smoke TF 可采样 |
| 清场后 `/odom` | 通过 | synthetic zero `/odom` 可采样，`frame_id=odom`、`child_frame_id=base_link` |

## 结论

本轮从“只有 sensor-only topic/keyframe fallback，缺 map/route”推进到“真实上位机 no-motion 产出 map、route.csv、keyframes、manifest，并在清场后干净采到 `/scan`、camera、`/tf_static`、synthetic `/odom`”。这满足 O7/O6 可消费的真实 no-motion route/map artifact 入口，但仍不是真实路线运动或 HIL。

清场复跑已证明上一轮不通过项主要来自残留进程和设备占用，而不是传感器硬件坏。剩余边界是：`route.csv` 仍是 synthetic `/odom` 零位样本，`map.yaml` 是 no-motion smoke 地图，不能当作可导航地图或真实运动路线。
