# Pre Start: O10 Delivery Readiness Path Contract Epic

## sprint_type

sprint_type: epic

## 启动时间

- 2026-06-05T12:06:18+08:00

## 本轮目标

本轮按 `OKR.md` 当前最高优先级启动 O10 受控送达 readiness chain，不再重复消费 scan/latest/status readback。最小功能抓手是先锁定 map proof latest JSON 路径契约：让 `POST /api/map/proof/refresh`、`GET /api/map/proof/latest`、PC readback 和文档都指向同一上位机 runtime 口径。

## 最近 2 轮 blocker scan

| Sprint | blocker / 风险 | 本轮处理 |
| --- | --- | --- |
| `2026.06.05_08-09_o9-pc-smoke-map-runtime-epic` | map proof latest 实际写到 `/root/rober/runtime/map_lifecycle_latest.json`，不是原计划 `/root/rober/onboard/runtime/map_lifecycle_latest.json`。 | 本轮 P0 修正或锁定路径契约，并用远端 refresh/latest/readback 验收。 |
| `2026.06.05_10-05_okr-six-sprint-breakthrough-rewrite` | O10 新增为 0%，要求下一轮跨 owner Epic，不能再用 Micro-only 或 latest/readback/status 消费主线。 | 本轮创建 Epic，并要求每个 owner 单 artifact / 单命令链 / 单 evidence type。 |

本轮不重复消费 Docker build、HIL 安全授权、电梯真实图片缺口；这些如果无法满足，只能记录为 `blocked_with_root_cause` 或 CEO 决策点。

## Owner 和边界

| Owner | 任务 | 文件边界 |
| --- | --- | --- |
| Robot Software Engineer | O10 Path Contract Lock：修正或锁定 map proof latest JSON 路径契约，部署/远端验证。 | `onboard/scripts/upper_robot_api.py`、`onboard/scripts/o3_map_lifecycle_proof.py`、`onboard/scripts/test_upper_robot_api.py`、`docs/navigation/nav2_map_quality_metrics.md`、本 sprint `owner_notes/robot-software-engineer.md` |
| Full-stack Software Engineer | 只读检查 PC same-origin map/scan proof 按钮契约是否能消费锁定后的 latest 路径；若需小修，只限 PC API/合同文件。 | `pc-tools/workstation/src/`、`docs/interfaces/o7_direct_upper_pc_api.md`、本 sprint `owner_notes/full-stack-software-engineer.md` |
| Robot Algorithm Engineer | 判断本轮能否进入 AMCL/Nav2 readiness 或电梯图片 eval；无真实/受控图片时不得伪造涨分。 | `docs/navigation/`、`docs/vision/`、本 sprint `owner_notes/robot-algorithm-engineer.md` |
| Hardware Infra Engineer | 复核本轮 map proof/path lock 不触碰底盘；stop-first HIL 缺现场前提时给 CEO blocker。 | `docs/hardware/`、本 sprint `owner_notes/robot-hardware-engineer.md` |
| Product Manager / OKR Owner | 收 delivery-readiness chain、更新 OKR 进度和最终边界。 | `OKR.md`、本 sprint 文档 |

## 安全边界

- 本轮 `map proof refresh` 只允许 no-motion LiDAR/SLAM proof。
- 不发布 `/cmd_vel`，不调用 `/api/base/manual`，不写 WAVE ROVER UART。
- 所有相关 payload 必须保持 `safe_to_control=false`、`sends_base_motion_commands=false`、`robot_control_executed=false`、`hil_pass=false`。
