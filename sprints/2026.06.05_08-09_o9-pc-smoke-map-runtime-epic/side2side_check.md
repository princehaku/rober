# Side2Side Check: O9 PC Smoke + Map Runtime Epic

## sprint_type

sprint_type: epic

## Product 对照结论

2026-06-05 08-09 closeout 以 `tech-done.md` 最新事实收口。本轮目标是 O9 最低 Objective 的两个真实材料断点：PC same-origin scan-proof live smoke，以及 no-motion SLAM `/map` lifecycle proof。

验收结论：窄口径通过，但不能外推为 continuous radar、可导航地图、Nav2、PC WASD、HIL 或 `safe_to_control=true`。

- Full-stack 侧通过：`TMPDIR=/tmp` 启动 8788，`npm run build` pass，`npm test -- --run test/App.test.ts` 30/30 pass，8788 same-origin `POST /api/o7/direct-upper/radar/scan-proof/refresh` 与 `GET /api/o7/direct-upper/radar/scan-proof/latest` 均 HTTP 200 JSON。
- PC live proof 关键字段可验收：`proof_status=scan_once_hz_raw_packet_tf_observed`，hz `241.753`，TF true，`artifact_status=loaded`，`runtime_summary_fallback_used=true`，`continuous_scan_status=not_proven`。
- Robot Software/Algorithm 侧窄口径通过：`slam_toolbox` 已安装，`ros2 pkg prefix slam_toolbox` 返回 `/opt/ros/humble`；短窗口 runtime topic list 包含 `/scan`、`/map`、`/map_metadata`、`/tf`、`/tf_static`、`/slam_toolbox/*`。
- no-motion map lifecycle 可计证据：`/scan` once 成立，`/map` once 成立，metadata 为 `resolution=0.05`、`width=6`、`height=116`，`/trashbot/save_map` 返回 `success=True`，远端确认存在 `/root/rober/onboard/runtime/maps/trashbot_map.pgm` 和 `.yaml`。
- latest artifact 可验收：短复跑 `POST /api/map/proof/refresh` 后 latest/readback 返回 `latest_result.proof.status=map_once_artifact_metadata_observed`、`evidence_type=robot_runtime_material`、`root_causes=[]`、`map_once_observed=true`、`map_file_observed=true`。
- latest 路径边界：`GET /api/map/proof/latest` 能读到 latest，但 JSON 实际在 `/root/rober/runtime/map_lifecycle_latest.json`，不是原计划 `/root/rober/onboard/runtime/map_lifecycle_latest.json`；root cause 是 upper API service cwd 为 `/root/rober`。
- 安全边界可验收：`safe_to_control=false`，`sends_base_motion_commands=false`，`robot_control_executed=false`，未发布 `/cmd_vel`，未调用 `/api/base/manual`，无 WAVE ROVER 底盘 UART/HIL。

## OKR 对照

| Objective | Product 判定 | 理由 |
| --- | --- | --- |
| O1 | 不涨 | 本轮没有 HIL、`/api/base/manual`、WAVE ROVER ACK、ROS feedback topics 或 `safe_to_control=true`。 |
| O2 | 不涨 | 本轮没有真实/受控电梯图片、OpenCV field eval、楼层/电梯 runtime 或送达材料。 |
| O3 | 小涨 | no-motion `/scan` once、`/map` once、map metadata、PGM/YAML 落盘成立，latest/readback 已返回 `map_once_artifact_metadata_observed` 与 `root_causes=[]`；但路径漂移仍需后续修正，不证明地图可导航、AMCL/Nav2 ready 或 fixed-route。 |
| O5 | 不涨 | 本轮没有 production cloud、4G/公网、DB/queue、OSS/CDN、真实 phone/browser 或生产 robot command/status material。 |
| O6 | 不涨 | 本轮没有真实 archive/query/inference/OSS/上车数据材料。 |
| O7 | 小涨 | 8788 same-origin refresh/latest live smoke 通过，证明 PC operator 入口能消费 live fresh scan proof；仍不证明 PC WASD、建图定位按钮级验收或完整 operator workflow。 |
| O8 | 小涨 | Epic closeout 保留证据边界，纠正 stale Product 结论，明确 latest JSON 路径漂移，避免把治理、路径漂移或 once map proof 写成完整产品能力。 |
| O9 | 小涨 | O9 最低 Objective 同轮拿到 PC same-origin runtime material 和 no-motion map lifecycle material；仍缺 continuous radar、真实/受控电梯图片和 stop-first HIL。 |

本轮 OKR percentage 决策：O3 `75% -> 76%`，O7 `91% -> 92%`，O8 `47% -> 48%`，O9 `18% -> 20%`；O1/O2/O5/O6 保持不变。

## Blocker 与下一步

O3/O9 map lifecycle 已解除一批前置 blocker：

- 远端 source 口径：必须继续使用 `bash -lc` source ROS setup；直接 zsh source 仍是错误用法。
- `slam_toolbox_missing` 已解除，`ros2 pkg prefix slam_toolbox` 返回 `/opt/ros/humble`。
- `/map` once、map metadata、PGM/YAML 落盘已经成立。
- latest/readback 已返回 `map_once_artifact_metadata_observed`、`root_causes=[]`、`map_once_observed=true`、`map_file_observed=true`。
- 当前剩余缺口是 latest JSON path 漂移需要修正或文档化，以及 continuous `/scan`/`/map`、AMCL、Nav2、路线质量和 HIL 均未证明。

下一轮最高优先级：Robot Software + Algorithm 先修正或显式锁定 `map_lifecycle_latest.json` 的 `/root/rober` vs `/root/rober/onboard` 路径口径，再推进 AMCL/Nav2 lifecycle 与 PC 建图按钮级验收。Full-stack 只把已通过的 API smoke 推到浏览器按钮级验收，不扩 UI 面。
