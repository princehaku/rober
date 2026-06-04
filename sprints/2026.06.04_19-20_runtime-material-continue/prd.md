# PRD: Runtime Material Continue

## 用户价值

普通用户不关心 SSH、ROS2 topic 或串口细节，只关心小车是否能安全地接收任务、看见环境、建图定位、处理电梯辅助流程，并在异常时停住且给出可理解的原因。本轮 PRD 的核心是继续把“软件入口可用”升级成“真实/受控材料可复盘”。

## 目标

1. O3：让上位机非运动 ROS2 runtime 产生 fresh `/scan` 或明确 driver/supervisor root cause，并为后续 `/map`、AMCL、Nav2 留出可执行 command hook。
2. O2：找到或生成真实/受控电梯图片 manifest；若没有图片，输出可直接执行的采集模板和 blocker，不用 fixture 冒充。
3. O7：PC operator workflow 能展示上一轮 operator report 同源 evidence ref，并保持 `safe_to_control=false`、`robot_control_executed=false` 等边界。
4. O1：按 vendor 来源和现场安全条件判断是否允许 stop-first HIL；不满足就只做非运动证据和升级 blocker。
5. O8：继续用 Epic 链路、evidence type 和 owner health 防止虚假涨分。

## 非目标

- 不推进 O5/O6 production cloud、4G、DB/queue、OSS/CDN 或 token 配置。
- 不在无现场看护、净空和急停时执行底盘 forward/back/left/right motion pulse。
- 不把 OpenCV fixture、UI mock、dry-run stub 或 stale artifact 写成真实完成。

## 验收口径

- O3 可涨分候选：fresh `/scan` once/hz、fresh `/lidar/raw_packet`、`/map` 或 map artifact、TF/AMCL/Nav2 lifecycle 中至少一项进入 `robot_runtime_material`，并写清缺失项。
- O2 可涨分候选：`trashbot.elevator_image_manifest.v1` 真实/受控图片 manifest + OpenCV eval artifact + false positive/negative + 不可判定策略。
- O7 可涨分候选：PC operator flow 消费真实 8787/PC 同源 evidence ref，并能展示 operator report、stop/HIL 缺口和 not_proven 边界。
- O1 可涨分候选：现场安全前提成立后的 stop-first low-speed pulse；否则不涨分，只记录 blocker。
