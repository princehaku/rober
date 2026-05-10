# Sprint 2026.05.10 16-17 Route Debug Status Panel - Final

## 状态

- 阶段：final completed。
- 时间：2026-05-10 16:50 Asia/Shanghai。
- Product Owner：`product-okr-owner`。
- 实现主责：`autonomy-engineer`。

## 本轮收口结论

本轮目标成立并完成：fixed-route debug web 已从 raw JSON 页面推进为可读状态面板。现场调试固定路线时，可以直接看到 route state、checkpoint、current target、visual gate、keyframe preflight、failure reason、last nav result 和 recent task/task record 引用，同时保留 raw JSON 作为工程排查兜底。

这次不把 debug 页面当成真实上车闭环。本轮没有真实 Nav2 行驶、没有真实 camera/keyframe match、没有 Docker/Humble colcon build，也没有浏览器截图验收。

## OKR 进度更新

| Objective | 本轮前 | 本轮后 | 更新理由 |
| --- | --- | --- | --- |
| Objective 1 硬件协议可信底盘 | 约 70% | 约 70% | 本轮未改硬件协议、UART、底盘桥或上车验证 |
| Objective 2 可恢复送垃圾任务闭环 | 约 74% | 约 74% | 本轮未改行为状态机或 action，只增强 fixed-route 复盘可观测性 |
| Objective 3 可验证导航与固定路线 | 约 68% | 约 71% | KR5 的关键帧/路线 debug 页面从 raw JSON 升级为可读 panel，并有自动化验证 |
| Objective 4 感知模块产品化 | 约 68% | 约 68% | 本轮未改 vision manifest、detector 或样本链路 |
| Objective 5 手机体验与量产边界 | 约 74% | 约 74% | 本轮是工程 debug 页面，不直接提升普通手机 operator 流程 |

## 实际改动

- `src/ros2_trashbot_nav/ros2_trashbot_nav/route_debug_web.py`：新增 dependency-free HTML/CSS/JS debug panel，保留 `/api/status` 和 raw JSON。
- `src/ros2_trashbot_nav/test/test_route_debug_web.py`：新增页面 contract 和 `/api/status` 缺失、损坏、正常透传测试。
- `sprints/2026.05.10_16-17_route-debug-status-panel/`：补齐 pre-start、PRD、tech-plan、tech-done、side2side check 和 final。
- `OKR.md`：更新当前进度快照和第 26 轮进度记录。

## 验证结果

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_nav/test -p 'test_route_debug_web.py'`：4 tests OK。
- `python3 -m py_compile src/ros2_trashbot_nav/ros2_trashbot_nav/route_debug_web.py`：通过。
- `git diff --check -- src/ros2_trashbot_nav/ros2_trashbot_nav/route_debug_web.py src/ros2_trashbot_nav/test/test_route_debug_web.py sprints/2026.05.10_16-17_route-debug-status-panel/tech-done.md`：通过。
- `PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh`：通过，interfaces 6、hardware 14、nav 31、bringup 9、behavior 111、vision 13 tests OK。

## 剩余风险

- 未做真实浏览器/手机截图，页面布局只通过 CSS contract 和静态测试约束。
- 未跑真实 fixed-route/Nav2 行驶。
- 未验证真实 camera frame 与 keyframe live matching。
- 未跑 Docker/Humble colcon build；当前 WSL/Docker 集成缺口仍沿用前几轮风险。

## 下一步

- 用真实 route/keyframe 样例跑一次 `waiting_visual_gate -> passed -> checkpoint advance`，把状态文件和 debug 页面截图纳入验收证据。
- 继续补真实 Nav2 waypoint/fixed-route 上车验证。
- 在 Docker/Humble 可用后补一次 `colcon build --symlink-install`。
