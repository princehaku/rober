# Sprint 2026.05.10_00-01 Side To Side Check

## 文档阶段门禁

- 前置文档：`tech-done.md`。
- 当前阶段：SIDE TO SIDE CHECK。
- 本阶段完成条件：对照 PRD、OKR、接口、验证证据和风险边界。

## PRD vs 实现

| PRD 项 | 实现状态 | 证据 | 结论 |
| --- | --- | --- | --- |
| 缺 keyframe 且 `enable_visual_gate=true` 不能 completed | implemented | `test_dry_run_waits_for_visual_gate_when_no_camera_or_keyframes_exist` | closed |
| keyframe 存在但缺 camera frame 不能 completed | implemented | `test_dry_run_waits_for_camera_frame_when_keyframe_exists` | closed |
| visual gate 通过后 dry-run 才推进 checkpoint | implemented | `test_dry_run_advances_after_visual_gate_passes` | closed |
| `enable_visual_gate=false` 保持路线解析 dry-run 可 completed | preserved | `test_dry_run_does_not_create_basic_navigator_and_writes_contract_status` | closed |
| status JSON 输出 checkpoint 和失败原因 | implemented | `visual_gate_status/detail/checkpoint` 字段测试 | closed |

## OKR/KR 对照

| OKR | 本轮检查点 | 状态 |
| --- | --- | --- |
| Objective 1 | 本轮未改硬件协议，不新增硬件结论 | unchanged |
| Objective 2 | fixed-route 未满足 visual gate 时不再误报送达完成 | improved |
| Objective 3 | fixed-route dry-run 视觉门控进入可验证闭环 | improved |
| Objective 4 | 摄像头继续作为送达任务辅助准入，不作为拾取成功前提 | unchanged |
| Objective 5 | 调试状态更适合手机/远程诊断透出失败原因 | improved |

## 接口与记录契约

| 字段 | Producer | Consumer | 语义 |
| --- | --- | --- | --- |
| `visual_gate_status` | `fixed_route_autonomy` | debug web / behavior / 远程诊断 | `disabled`、`missing_keyframe`、`waiting_camera_frame`、`no_live_descriptors`、`insufficient_matches`、`passed` |
| `visual_gate_detail` | `fixed_route_autonomy` | debug web / 维护者 | 人可读原因 |
| `visual_gate_checkpoint` | `fixed_route_autonomy` | debug web / behavior | 当前检查的 route checkpoint |

## 验证证据

| 命令 | 状态 | 摘要 |
| --- | --- | --- |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_nav/test -p 'test_fixed_route_dry_run_offline.py'` | passed | 6 tests OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_nav/test -p 'test*.py'` | passed | 20 tests OK |
| `PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh` | passed | interfaces 4、hardware 14、nav 20、bringup 7、behavior 91、vision 1 |
| `git diff --check -- src/ros2_trashbot_nav/ros2_trashbot_nav/fixed_route_autonomy.py src/ros2_trashbot_nav/test/test_fixed_route_dry_run_offline.py src/ros2_trashbot_nav/test/test_fixed_route_status_static.py` | passed | 无 whitespace error |

## 风险边界

- Docker/Humble build 本轮未跑；当前机器此前记录为 `docker` command not found。
- HIL、真实摄像头、真实 keyframe 图像匹配未跑，不声明上车通过。
- 本轮不涉及 WAVE ROVER、ESP32、Orange Pi、UART、波特率、引脚、电压或机械尺寸变更。

## 本阶段结论

本轮 PRD 的软件 dry-run 验收已 closed。可进入 `final.md`，但整体项目仍保留 Docker/HIL/实机视觉验证缺口。
