# Sprint 2026.05.10 16-17 Route Debug Status Panel - Side2Side Check

## 状态

- 阶段：side2side check completed。
- 时间：2026-05-10 16:50 Asia/Shanghai。
- Coordinator：Codex 主会话。
- 实现主责：`autonomy-engineer`。

## 对照验收

| 验收项 | 结果 | 证据 |
| --- | --- | --- |
| 首页不再只是 raw JSON | 通过 | `route_debug_web.py` 新增 route summary、checkpoint、current target、visual gate、keyframe preflight、failure reason、recent task 和 raw status 区域 |
| 保留 raw JSON | 通过 | 页面保留 `rawStatus`，测试断言 `Raw Status` 存在 |
| `/api/status` 路径不变 | 通过 | `make_handler()` 仍处理 `/api/status`；测试覆盖缺文件、坏 JSON、正常 JSON 透传 |
| 不改 fixed-route status payload shape | 通过 | 本轮没有修改 `fixed_route_autonomy.py`，页面只消费已有字段 |
| 页面字段稳定可测试 | 通过 | `test_route_debug_web.py` 断言关键 DOM id 和 JS 函数名存在 |
| 长路径/错误原因可换行 | 通过 | HTML/CSS 包含 `overflow-wrap: anywhere`，静态测试覆盖 |

## Coordinator 复跑验证

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_nav/test -p 'test_route_debug_web.py'
```

结果：4 tests OK。

```bash
python3 -m py_compile src/ros2_trashbot_nav/ros2_trashbot_nav/route_debug_web.py
```

结果：通过，无输出。

```bash
git diff --check -- src/ros2_trashbot_nav/ros2_trashbot_nav/route_debug_web.py src/ros2_trashbot_nav/test/test_route_debug_web.py sprints/2026.05.10_16-17_route-debug-status-panel/tech-done.md
```

结果：通过，无输出。

```bash
PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh
```

结果：通过，interfaces 6、hardware 14、nav 31、bringup 9、behavior 111、vision 13 tests OK。

## 未完成验收

- 未做真实浏览器截图或手机窄屏视觉验收。
- 未跑真实 Nav2/fixed-route 上车流程。
- 未验证真实 camera frame 与 keyframe live matching。
- 未跑 Docker/Humble colcon build。
