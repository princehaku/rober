# Final: O9 PC Smoke + Map Runtime Epic

## sprint_type

sprint_type: epic

## 收口时间

- 2026-06-05T09:33:50+08:00
- 对应 OKR 快照：2026-06-05 08-09 CST

## 最终结论

本轮 O9 Epic 部分达成：PC same-origin scan-proof live smoke 成立，no-motion SLAM `/map` lifecycle proof 未成立。

可计入 O7/O9 的证据：

- Full-stack 已用 `TMPDIR=/tmp PORT=8788 ROBER_UPPER_API_BASE_URL=http://192.168.1.11:8787 npm run api` 启动 8788，解除上一轮 `tsx_ipc_pipe_enotsup` runtime blocker。
- `npm run build` pass。
- `npm test -- --run test/App.test.ts` pass，30 tests passed。
- 8788 same-origin `POST /api/o7/direct-upper/radar/scan-proof/refresh` HTTP 200 JSON。
- 8788 same-origin `GET /api/o7/direct-upper/radar/scan-proof/latest` HTTP 200 JSON。
- 关键字段：`proof_status=scan_once_hz_raw_packet_tf_observed`，hz `241.753`，TF true，`runtime_summary_fallback_used=true`，`continuous_scan_status=not_proven`。
- 安全字段：`safe_to_control=false`，`robot_control_executed=false`；本轮没有 `/cmd_vel`，没有 `/api/base/manual`，没有 HIL。

不可计入 O3 map/SLAM 的证据：

- Robot Software/Algorithm 新增并部署 `POST /api/map/proof/refresh` 与 `o3_map_lifecycle_proof.py` helper。
- 本地 `python3 -m compileall -q onboard/scripts onboard/src` pass。
- 本地 `python3 -m unittest discover -s onboard/scripts -p 'test_*.py'` pass，`Ran 83 tests`，`OK (skipped=3)`。
- 本地 `git diff --check` pass。
- 但没有 `/map` once，没有 map artifact，没有 metadata，没有 `runtime/map_lifecycle_latest.json` 成功 readback。

## Root Cause

O3/O9 map lifecycle 当前是 `blocked_with_root_cause`：

- remote shell/source：远端默认 `zsh` 直接 source `/opt/ros/humble/setup.bash` 会失败，必须使用 `bash -lc`，且不能在 source 前启用 `set -u`。
- SLAM dependency：`slam_toolbox` missing，`apt-get install -y ros-humble-slam-toolbox` 被中断，不能作为 SLAM 可用证据。
- ROS runtime：现场常驻 graph 没有 continuous `/scan` 或 `/map`，只有 `/parameter_events` 与 `/rosout`。
- map artifact：`runtime/maps` missing，`runtime/map_lifecycle_latest.json` missing，`/api/map/proof/latest` 无可验收 material。

## OKR 更新

已更新 `OKR.md` section 4 和 4.1：

| Objective | 本轮决定 |
| --- | --- |
| O1 | 保持约 95.5%，没有 HIL/ACK/feedback topic。 |
| O2 | 保持约 72%，没有电梯图片或 field eval。 |
| O3 | 保持约 75%，没有 SLAM `/map` artifact。 |
| O5 | 保持约 84%，没有 production live material。 |
| O6 | 保持约 82%，没有真实 archive/query/inference/OSS material。 |
| O7 | 约 91% -> 约 92%，PC same-origin runtime proof 成立。 |
| O8 | 约 47% -> 约 48%，Epic closeout/root-cause 归档成立。 |
| O9 | 约 18% -> 约 19%，最低 Objective 获得 PC live same-origin scan-proof workflow 小幅进展。 |

## 剩余风险

- 不能把 `scan_once_hz_raw_packet_tf_observed` 外推为 continuous radar ready；`continuous_scan_status=not_proven` 仍是当前边界。
- 不能把 `POST /api/map/proof/refresh` route/helper 外推为 O3 map/SLAM 成功；`/map`、map artifact、metadata 都还没有。
- 不能把 PC 8788 API smoke 外推为浏览器按钮级验收、PC WASD、WAVE ROVER ACK、HIL 或 `safe_to_control=true`。
- 后续若继续消费 same-origin refresh/latest 或 status readback，而没有 continuous radar、SLAM `/map`、电梯图片或 HIL material，不得继续上调 O9。

## 下一轮建议

1. Robot Software + Algorithm 优先修复远端 `slam_toolbox`/ROS source/runtime 前置条件，再重跑 no-motion SLAM `/map` lifecycle proof。
2. Full-stack 只把 8788 same-origin API smoke 推到浏览器按钮级验收，不扩 UI 面。
3. Product 继续守住 evidence type：O3 只看 `/map`/artifact/metadata，O7 只看 operator workflow，O9 只看新的 runtime/HIL/field material。
