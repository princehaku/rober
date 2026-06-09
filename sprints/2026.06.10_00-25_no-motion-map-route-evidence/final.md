# No-Motion Map Route Evidence Final

## 收口状态

状态：部分完成，核心 no-motion map/route evidence 已落地，清场后 LiDAR/camera/TF/odom ownership 已复验通过。

本轮在真实上位机 `root@192.168.1.11:37878` 上完成了 no-motion `learn.launch.py` 采集闭环：`map.yaml`、`route.csv`、keyframes、manifest 均已产生。清场后复跑也证明 `/scan`、`/camera/image_raw`、`/tf_static`、synthetic `/odom` 可在同一轮干净采样。相比上一轮 `No map data received` 和 `ModuleNotFoundError: cv_bridge`，这轮已经把 O7/O6 可消费的真实 no-motion 路线材料入口打通。

## 关键证据

- Docker/Humble：`Summary: 6 packages finished [54.8s]`
- 板上增量构建：`Summary: 2 packages finished [8.41s]`
- `save_map`：`success=True`
- `route.csv`：`75` 行
- `keyframes/`：`148` 个文件
- `manifest.json`：`trashbot.vision_samples.v1`
- `map_output/trashbot_no_motion_map.yaml` 与 `.pgm`：已保存
- 远端清理：清理后 `ros2 node list` 为空，相关 `ps` 输出为空
- 清场后复跑：
  - `/scan`：成功，`frame_id=laser_frame`，有有效 ranges/intensities
  - `/camera/image_raw`：成功，`640x480`、`encoding=bgr8`
  - `/tf_static`：成功，`base_link -> laser_frame`
  - `/odom`：成功，synthetic zero odom，`frame_id=odom`、`child_frame_id=base_link`
  - `route.csv`、`manifest.json`、`keyframes/000.*`、`trashbot_map.yaml`、`trashbot_map.pgm`：均已拉回本地 clean artifact

## OKR 回顾

- 现场 O3 验证 lane：明显推进。首次拿到同一轮真实上位机 no-motion map + route + keyframe + manifest 材料，但仍不是运动路线。
- O7：推进。PC route replay / labeling 后续终于有真实 route/keyframe/manifest 输入，不再只能消费 fixture。
- O6：推进。archive/event/evidence consumer 后续可接入这份真实 artifact packet。
- O1：不提升。本轮未验证 ROS2 `/cmd_vel`、真实 `/odom`、HIL 或底盘运动闭环。

## 剩余风险

- `route.csv` 是 synthetic `/odom` 的 no-motion 零位样本，不能当作真实路线。
- `map.yaml` 是 no-motion 建图 smoke，不能当作可导航地图。
- `waypoint_manager` 在 no-motion 期间仍会写入 `auto_000x` 零位航点；后续 clean capture 应显式关闭该节点或把副作用隔离到临时 waypoint 文件。
- 多个 Python 节点在 `Ctrl-C` 收尾时会打印 `rcl_shutdown already called`，不影响本轮证据，但退出路径需要单独整理。
- 本轮未发布 `/cmd_vel`，不改变 `safe_to_control=false` 和 `primary_actions_enabled=false` 的产品安全边界。

## 下一步

1. 增加 `waypoint_manager_enabled` 或临时 waypoint 文件隔离，避免 no-motion clean capture 污染默认 waypoint 存储。
2. 在安全现场条件下，用真实缓慢移动采集 route/map，并把 synthetic `/odom` 切回真实 `/odom`。
3. 将本轮 `route.csv`、keyframes、manifest 接入 O7 route replay / labeling queue 做消费验证。
4. 单独整理 Python ROS2 节点退出路径，消除 `rcl_shutdown already called` 收尾噪声。
