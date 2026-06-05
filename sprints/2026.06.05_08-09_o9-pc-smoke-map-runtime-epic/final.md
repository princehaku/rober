# Final: O9 PC Smoke + Map Runtime Epic

## sprint_type

sprint_type: epic

## 收口时间

- 2026-06-05T09:50:00+08:00
- 对应 OKR 快照：2026-06-05 08-09 CST

## 最终结论

本轮 O9 Epic 窄口径达成：PC same-origin scan-proof live smoke 成立，no-motion SLAM `/map` lifecycle 取得 `/scan` once、`/map` once、map metadata、PGM/YAML 落盘和 latest/readback clean success；剩余风险是 latest JSON 实际路径与原计划路径不一致。

可计入 O7/O9 的 PC 证据：

- Full-stack 已用 `TMPDIR=/tmp PORT=8788 ROBER_UPPER_API_BASE_URL=http://192.168.1.11:8787 npm run api` 启动 8788，解除上一轮 `tsx_ipc_pipe_enotsup` runtime blocker。
- `npm run build` pass。
- `npm test -- --run test/App.test.ts` pass，30 tests passed。
- 8788 same-origin `POST /api/o7/direct-upper/radar/scan-proof/refresh` HTTP 200 JSON。
- 8788 same-origin `GET /api/o7/direct-upper/radar/scan-proof/latest` HTTP 200 JSON。
- 关键字段：`artifact_status=loaded`、`proof_status=scan_once_hz_raw_packet_tf_observed`，hz `241.753`，TF true，`runtime_summary_fallback_used=true`，`continuous_scan_status=not_proven`。

可计入 O3/O9 的 no-motion map 证据：

- Robot Software/Algorithm 已安装 `slam_toolbox`，`ros2 pkg prefix slam_toolbox` 返回 `/opt/ros/humble`。
- `POST /api/map/proof/refresh` 已部署且不再 405，helper 短窗口 runtime topic list 包含 `/lidar/raw_packet`、`/scan`、`/map`、`/map_metadata`、`/tf`、`/tf_static`、`/slam_toolbox/*`。
- `/scan` once 成立，frame_id `laser_frame`。
- `/map` once 成立，frame_id `map`，metadata `resolution=0.05`、`width=6`、`height=116`。
- `/trashbot/save_map` 返回 `success=True, message='Map saved to runtime/maps/trashbot_map.pgm'`。
- 远端确认存在 `/root/rober/onboard/runtime/maps/trashbot_map.pgm` 和 `/root/rober/onboard/runtime/maps/trashbot_map.yaml`。
- 短复跑 `POST /api/map/proof/refresh` 后 latest/readback 返回 `latest_result.proof.status=map_once_artifact_metadata_observed`、`evidence_type=robot_runtime_material`、`root_causes=[]`、`map_once_observed=true`、`map_file_observed=true`。
- `GET /api/map/proof/latest` 能读到 latest，但 JSON 实际在 `/root/rober/runtime/map_lifecycle_latest.json`，不是原计划 `/root/rober/onboard/runtime/map_lifecycle_latest.json`；原因是 upper API service cwd 是 `/root/rober`。

本地护栏：

- `python3 -m unittest onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py` pass，12 tests passed。
- `python3 -m compileall -q onboard/scripts onboard/src` pass。
- `python3 -m unittest discover -s onboard/scripts -p 'test_*.py'` pass，`Ran 83 tests`，`OK (skipped=3)`。
- 本轮 Product 收口阶段 `git diff --check` pass。

## 安全边界

- 安全字段保持 `safe_to_control=false`、`sends_base_motion_commands=false`、`robot_control_executed=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`hil_pass=false`。
- 本轮没有发布 `/cmd_vel`，没有调用 `/api/base/manual`，没有 WAVE ROVER 底盘 UART，没有 HIL。
- 本轮不证明 continuous radar ready、AMCL、Nav2 lifecycle、路径生成、地图质量可导航、fixed-route、PC WASD、WAVE ROVER ACK、HIL pass 或真实送达闭环。

## OKR 更新

已更新 `OKR.md` section 4 和 4.1：

| Objective | 本轮决定 |
| --- | --- |
| O1 | 保持约 95.5%，没有 HIL/ACK/feedback topic。 |
| O2 | 保持约 72%，没有电梯图片或 field eval。 |
| O3 | 约 75% -> 约 76%，no-motion `/map` once、metadata、PGM/YAML 落盘和 latest/readback clean success 成立；latest JSON 路径口径仍需修正或文档化。 |
| O5 | 保持约 84%，没有 production live material。 |
| O6 | 保持约 82%，没有真实 archive/query/inference/OSS material。 |
| O7 | 约 91% -> 约 92%，PC same-origin runtime proof 成立。 |
| O8 | 约 47% -> 约 48%，Epic closeout/root-cause/false-negative 边界归档成立。 |
| O9 | 约 18% -> 约 20%，最低 Objective 获得 PC same-origin runtime material 与 no-motion map lifecycle `robot_runtime_material`。 |

## 剩余风险

- `continuous_scan_status=not_proven` 仍成立，不能把 once scan/map proof 写成 continuous radar ready。
- latest/readback 已 clean success，但 latest JSON 实际位于 `/root/rober/runtime/map_lifecycle_latest.json`，不是原计划 `/root/rober/onboard/runtime/map_lifecycle_latest.json`；下一轮需要修正或锁定这一路径契约。
- PC 8788 API smoke 不能外推为浏览器按钮级验收、PC WASD、WAVE ROVER ACK、HIL 或 `safe_to_control=true`。
- O3 只进入 no-motion map material 阶段，不证明 AMCL/Nav2、路线质量、地图可导航或 fixed-route 可跑。

## 下一轮最高优先级

1. Robot Software + Algorithm 先修正或锁定 `map_lifecycle_latest.json` 路径契约，随后推进 AMCL/Nav2 lifecycle 和路径生成边界。
2. Full-stack 把 8788 same-origin API smoke 推到浏览器按钮级验收和 PC 建图控制 readback，不扩 UI 面。
3. Product 继续守住 evidence type：O3 看 map/latest/AMCL/Nav2，O7 看 operator workflow，O9 只看新的 runtime/HIL/field material。
