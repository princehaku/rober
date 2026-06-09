# No-Motion Map Route Evidence Final

## 收口状态

状态：部分完成，核心 no-motion map/route evidence 已落地，LiDAR/camera ownership 仍需下一轮清场复验。

本轮在真实上位机 `root@192.168.1.11:37878` 上完成了 no-motion `learn.launch.py` 采集闭环：`map.yaml`、`route.csv`、keyframes、manifest 均已产生。相比上一轮 `No map data received` 和 `ModuleNotFoundError: cv_bridge`，这轮已经把 O7/O6 可消费的真实路线材料入口打通。

## 关键证据

- Docker/Humble：`Summary: 6 packages finished [54.8s]`
- 板上增量构建：`Summary: 2 packages finished [8.41s]`
- `save_map`：`success=True`
- `route.csv`：`75` 行
- `keyframes/`：`148` 个文件
- `manifest.json`：`trashbot.vision_samples.v1`
- `map_output/trashbot_no_motion_map.yaml` 与 `.pgm`：已保存
- 远端清理：清理后 `ros2 node list` 为空，相关 `ps` 输出为空

## OKR 回顾

- 现场 O3 验证 lane：明显推进。首次拿到同一轮真实上位机 no-motion map + route + keyframe + manifest 材料，但仍不是运动路线。
- O7：推进。PC route replay / labeling 后续终于有真实 route/keyframe/manifest 输入，不再只能消费 fixture。
- O6：推进。archive/event/evidence consumer 后续可接入这份真实 artifact packet。
- O1：不提升。本轮未验证 ROS2 `/cmd_vel`、真实 `/odom`、HIL 或底盘运动闭环。

## 剩余风险

- `/scan` 本轮未采到，`lidar_driver` 因 `/dev/ttyACM0` 读空数据崩溃；现场存在重复节点和串口占用，需清场后重跑。
- `camera_publisher` 本轮 launch 内打开 `/dev/video1` 失败，但 topic/keyframe 数据由残留 camera publisher 供给；需清场后证明 launch ownership。
- `route.csv` 是 synthetic `/odom` 的 no-motion 零位样本，不能当作真实路线。
- `map.yaml` 是 no-motion 建图 smoke，不能当作可导航地图。
- 本轮未发布 `/cmd_vel`，不改变 `safe_to_control=false` 和 `primary_actions_enabled=false` 的产品安全边界。

## 下一步

1. 远端清理残留 ROS 进程后重跑 camera/LiDAR ownership smoke。
2. 在 LiDAR `/scan` 稳定后，用真实缓慢移动采集 route/map，并把 synthetic `/odom` 切回真实 `/odom`。
3. 将本轮 `route.csv`、keyframes、manifest 接入 O7 route replay / labeling queue 做消费验证。
