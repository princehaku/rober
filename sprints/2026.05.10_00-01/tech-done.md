# Sprint 2026.05.10_00-01 Tech Done

## 文档阶段门禁

- 前置文档：`pre_start.md`、`prd.md`、`tech-plan.md` 已完成。
- 当前阶段：DEV/TEST DONE。
- 本阶段完成条件：记录实际改动、验证结果、偏差和剩余风险。

## 实际改动

| Owner | 改动 | 路径 | OKR 映射 |
| --- | --- | --- | --- |
| `Autonomy Algorithm Engineer` | fixed-route dry-run 不再因 `dry_run=true` 绕过 visual gate；只有 `enable_visual_gate=false` 才直接通过 | `src/ros2_trashbot_nav/ros2_trashbot_nav/fixed_route_autonomy.py` | Objective 3 KR3/KR5 |
| `Autonomy Algorithm Engineer` | status JSON 增加 `visual_gate_status`、`visual_gate_detail`、`visual_gate_checkpoint`，并对 missing keyframe / waiting camera / no descriptors / insufficient matches 写出可解释原因 | `src/ros2_trashbot_nav/ros2_trashbot_nav/fixed_route_autonomy.py` | Objective 3 KR5 |
| `Autonomy Algorithm Engineer` | 修改离线 dry-run 测试：开启 visual gate 且缺 keyframe/缺 camera 时进入 `waiting_visual_gate`，匹配通过时才 completed，关闭 visual gate 时仍可 completed | `src/ros2_trashbot_nav/test/test_fixed_route_dry_run_offline.py` | Objective 3 KR3 |
| `Autonomy Algorithm Engineer` | 补 status 静态契约，防止视觉门控字段从 debug JSON 中回退 | `src/ros2_trashbot_nav/test/test_fixed_route_status_static.py` | Objective 3 KR5 |
| `Product Manager / OKR Owner` | 更新 OKR 当前进度快照，明确本轮 Objective 3 进展和剩余缺口 | `OKR.md` | OKR 进度同步 |

## 验证记录

| 命令 | 结果 | 摘要 |
| --- | --- | --- |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_nav/test -p "test_fixed_route_dry_run_offline.py"` | passed | 6 tests OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_nav/test -p "test*.py"` | passed | 20 tests OK |
| `git diff --check -- src/ros2_trashbot_nav/ros2_trashbot_nav/fixed_route_autonomy.py src/ros2_trashbot_nav/test/test_fixed_route_dry_run_offline.py OKR.md sprints/2026.05.10_00-01` | passed | 无 whitespace error |
| `PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh` | passed | interfaces 4 + hardware 14 + nav 20 + bringup 7 + behavior 91 + vision 1 tests OK |

## 偏差与定位

- 交接中的 “patrol 硬编码 5 waypoint/sleep” 在当前主 `task_orchestrator` 已不存在；团队复查确认主 patrol 已读 waypoint 文件并调用 Nav2。
- 仍存在两个独立遗留：`use_saved_map=false` 学习阶段仍是模拟完成口径；legacy `trash_collection_server.py` 仍保留 sleep demo。它们未纳入本轮，避免扩大 Objective 3 主线。
- Docker/Humble 与 HIL 未在本轮执行，不能声明 ROS2 容器构建或上车通过。

## 完成前反思

- 本轮没有修改硬件协议、串口、速度映射或 vendor 假设。
- 未触碰已有未提交的 `.codex/agents/*.toml` 改动。
- `enable_visual_gate=true` 的 dry-run 现在会暴露 keyframe/camera 准入缺口；若只想做路线解析 dry-run，需要显式关闭 visual gate。
