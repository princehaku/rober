# Sprint 2026.05.10_00-01 Final

## 收口结论

本轮围绕 Objective 3 fixed-route dry-run 视觉门控推进，软件侧已收口。

`fixed_route_autonomy` 现在不会因为 dry-run 就绕过 visual gate：启用视觉门控时，缺 keyframe、缺 camera frame、缺 descriptor 或匹配不足都会停在 `waiting_visual_gate` 并写出可读、可机器消费的状态字段；只有 visual gate 通过后 dry-run 才推进 checkpoint。

## 本轮 OKR 进度

| Objective | 当前状态 | 说明 |
| --- | --- | --- |
| Objective 1 硬件控制层 | 软件侧较稳，HIL 未完成 | 本轮未改硬件；仍需 Docker/Humble 和真机串口/运动证据。 |
| Objective 2 送垃圾任务闭环 | 中高进度 | action result、task record、timeout/cancel/failure 逐步可判定；仍有 patrol 硬编码 5 waypoint 占位债务。 |
| Objective 3 导航与固定路线 | 本轮明显推进 | dry-run 已覆盖路线读取、visual gate 等待、camera frame 等待、匹配通过后推进和 debug status 输出。 |
| Objective 4 感知模块 | 低到中进度 | 本轮把视觉作为固定路线准入状态透出，但还没有样本沉淀/模型评估闭环。 |
| Objective 5 手机用户体验/量产边界 | 中进度 | 诊断字段更适合手机/远程展示；完整手机 UX、语音提示和量产硬件表仍未实现。 |

## 验证结果

| 命令 | 结果 |
| --- | --- |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_nav/test -p 'test_fixed_route_dry_run_offline.py'` | 6 tests OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_nav/test -p 'test*.py'` | 20 tests OK |
| `PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh` | interfaces 4 + hardware 14 + nav 20 + bringup 7 + behavior 91 + vision 1 tests OK |
| `git diff --check -- ...fixed_route...` | passed |

## 剩余事项

1. Objective 3：补 route-wide keyframe coverage 预检，让路线启动前一次性暴露缺失 keyframe。
2. Objective 2：处理 patrol 仍存在的 `waypoints_total = 5` 模拟成功债务。
3. Objective 1：恢复 Docker/Humble build gate，并补 HIL 实机证据。
4. Objective 4/5：把 visual gate 状态接入 debug 页面/手机端展示，再推进样本沉淀和用户提示词。

## 采用资料

- `AGENTS.md`
- `OKR.md`
- `sprints/2026.05.10_00-01/pre_start.md`
- `sprints/2026.05.10_00-01/prd.md`
- `sprints/2026.05.10_00-01/tech-plan.md`
