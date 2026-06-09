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
| `/scan` sample | 未通过 | `scan_once.txt` 为空，LiDAR driver 串口读空数据崩溃 |
| camera launch ownership | 部分通过 | sample/keyframes 存在，但本轮 launch 内 camera publisher 打开 `/dev/video1` 失败，可能由残留 publisher 供给 |

## 结论

本轮从“只有 sensor-only topic/keyframe fallback，缺 map/route”推进到“真实上位机 no-motion 产出 map、route.csv、keyframes 和 manifest”。这满足 O7/O6 可消费的真实 route/map artifact 入口，但仍不是真实路线运动或 HIL。

不通过项已收敛为现场进程清理和设备占用问题：`ttyacm0_diagnostics.txt` 显示重复节点、残留 `lidar_driver` 和 `/dev/ttyACM0` 占用。下一轮应先做远端 ROS 进程清场，再重跑 LiDAR/camera ownership smoke。
