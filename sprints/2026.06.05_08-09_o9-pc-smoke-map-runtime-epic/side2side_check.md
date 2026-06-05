# Side2Side Check: O9 PC Smoke + Map Runtime Epic

## sprint_type

sprint_type: epic

## Product 对照结论

2026-06-05 08-09 closeout 只按 `tech-done.md` 已记录证据收口。本轮目标是 O9 最低 Objective 的两个真实材料断点：PC same-origin scan-proof live smoke，以及 no-motion SLAM `/map` lifecycle proof。

验收结论：部分通过。

- Full-stack 侧通过：`TMPDIR=/tmp` 启动 8788，`npm run build` pass，`npm test -- --run test/App.test.ts` 30 pass，8788 same-origin `POST /api/o7/direct-upper/radar/scan-proof/refresh` 与 `GET /api/o7/direct-upper/radar/scan-proof/latest` 均 HTTP 200 JSON。
- PC live proof 关键字段可验收：`proof_status=scan_once_hz_raw_packet_tf_observed`，hz `241.753`，TF true，`runtime_summary_fallback_used=true`，`continuous_scan_status=not_proven`。
- 安全边界可验收：`safe_to_control=false`，`robot_control_executed=false`，未发布 `/cmd_vel`，未调用 `/api/base/manual`。
- Robot Software/Algorithm 侧只通过软件抓手：新增并部署 `POST /api/map/proof/refresh` 与 `o3_map_lifecycle_proof.py` helper，本地 `compileall`、`unittest`、`git diff --check` pass。
- O3 map/SLAM 侧未通过：没有 `/map` once，没有 map artifact，没有 metadata，没有 `runtime/map_lifecycle_latest.json` 可用材料。

## OKR 对照

| Objective | Product 判定 | 理由 |
| --- | --- | --- |
| O1 | 不涨 | 本轮没有 HIL、`/api/base/manual`、WAVE ROVER ACK、ROS feedback topics 或 `safe_to_control=true`。 |
| O2 | 不涨 | 本轮没有真实/受控电梯图片、OpenCV field eval、楼层/电梯 runtime 或送达材料。 |
| O3 | 不涨 | `/api/map/proof/refresh` route/helper 是软件抓手，但 no `/map` once、no map artifact、no metadata；`slam_toolbox` missing/interrupted install，continuous `/scan`/`/map` 不存在。 |
| O5 | 不涨 | 本轮没有 production cloud、4G/公网、DB/queue、OSS/CDN、真实 phone/browser 或生产 robot command/status material。 |
| O6 | 不涨 | 本轮没有真实 archive/query/inference/OSS/上车数据材料。 |
| O7 | 小涨 | 8788 same-origin refresh/latest live smoke 通过，证明 PC operator 入口能消费 live fresh scan proof；仍不证明 PC WASD、建图定位控制或完整 operator workflow。 |
| O8 | 小涨 | Epic closeout 保留证据边界，明确 root cause，避免把 map blocker 写成 O3 进度。 |
| O9 | 小涨 | O9 最低 Objective 获得 PC same-origin runtime material，但 continuous radar、SLAM `/map`、电梯图片和 HIL 仍 blocked。 |

本轮 OKR percentage 决策：O7 `91% -> 92%`，O8 `47% -> 48%`，O9 `18% -> 19%`；O1/O2/O3/O5/O6 保持不变。

## Blocker 与下一步

O3/O9 map lifecycle root cause 已收敛到具体层：

- 远端默认 `zsh` 不能直接 source ROS bash setup，后续命令必须使用 `bash -lc`，且 source 前不能启用 `set -u`。
- `slam_toolbox` missing，且安装被中断；后续需要先恢复 package manager 状态，再安装并复验。
- 现场无 continuous `/scan`/`/map`，`runtime/maps` 和 latest JSON missing。
- 当前没有可验收 `/map` artifact，不得写成 SLAM/map ready。

下一轮优先级：先修远端 ROS source/package/runtime 前置条件并重跑 no-motion SLAM `/map` proof；Full-stack 只把已通过的 API smoke 推到浏览器按钮级验收，不扩 UI 面。
