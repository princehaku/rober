# Sprint 2026.05.10 16-17 Route Debug Status Panel - Tech Done

## 状态

- 阶段：tech-done completed。
- 时间：2026-05-10 16:42 CST。
- Owner：`autonomy-engineer`。
- 本轮目标：推进 Objective 3 KR5，把 fixed-route debug 从 raw JSON 升级为可读、可复盘、可测试的状态面板。

## 实际改动文件

- `src/ros2_trashbot_nav/ros2_trashbot_nav/route_debug_web.py`
- `src/ros2_trashbot_nav/test/test_route_debug_web.py`
- `sprints/2026.05.10_16-17_route-debug-status-panel/tech-done.md`

## 自主能力目标和本轮抓手

- 目标：现场调试 fixed-route 时，不再要求工程同学从 raw JSON 里人工拼状态，而是能直接看到 route state、checkpoint、current target、visual gate、keyframe preflight、失败原因和最近任务引用。
- 抓手：只消费 `fixed_route_autonomy.py` 已经写出的 status JSON，不改导航逻辑、不改 ROS2 msg/srv/action、不改硬件参数。
- 能力边界：本轮是 debug 可观测能力和错误状态展示，不声明真实 Nav2、相机或 WAVE ROVER 上车闭环完成。

## 页面能力变化

- 首页新增 dependency-free fixed-route debug panel，保留 `/api/status` 和 raw JSON。
- 新增稳定 DOM id：
  - `routeStateBadge`
  - `routeSummary`
  - `routeProgress`
  - `routeTarget`
  - `visualGateStatus`
  - `keyframePreflight`
  - `routeFailureReason`
  - `recentTask`
  - `rawStatus`
- 新增 JS 映射函数：
  - `routeStateView(status)`
  - `visualGateView(status)`
  - `renderStatus(status)`
  - `renderKeyframePreflight(preflight)`
- 页面展示：
  - route state badge、mode、checkpoint progress、updated time、route file、keyframe dir、contract version。
  - current target 的 index、xyz 和 quaternion。
  - visual gate 的 enabled、status、checkpoint、detail。
  - keyframe preflight 的 enabled、route_visual_ready、total、loaded、missing、invalid。
  - failure reason、last error、last transition、last nav result。
  - recent task 引用，优先级为 `task_record_path` -> `last_task.task_record_path` -> `task.id` / `last_task.task_id`。
  - raw JSON 仍作为工程排查兜底。

## 接口影响

- 不改 `/api/status` 路径。
- 不改 fixed-route status JSON producer 和字段 shape。
- 不改 `fixed_route_autonomy.py`。
- 不改 ROS2 msg/srv/action。
- 不涉及 WAVE ROVER、ESP32、Orange Pi、UART、波特率、电压、引脚或硬件 launch 参数。

## 测试和验证结果

本次接手收尾后重新运行并通过：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_nav/test -p 'test_route_debug_web.py'
```

结果：

```text
Ran 4 tests in 1.088s
OK
```

```bash
python3 -m py_compile src/ros2_trashbot_nav/ros2_trashbot_nav/route_debug_web.py
```

结果：通过，无输出。

```bash
git diff --check -- src/ros2_trashbot_nav/ros2_trashbot_nav/route_debug_web.py src/ros2_trashbot_nav/test/test_route_debug_web.py sprints/2026.05.10_16-17_route-debug-status-panel/tech-done.md
```

结果：通过，无输出。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_nav/test
```

结果：

```text
Ran 31 tests in 2.446s
OK
```

```bash
PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh
```

结果：

```text
interfaces: Ran 6 tests in 0.101s OK
hardware: Ran 14 tests in 0.053s OK
nav: Ran 31 tests in 2.534s OK
bringup: Ran 9 tests in 0.056s OK
behavior: Ran 111 tests in 16.839s OK
vision: Ran 13 tests in 0.754s OK
```

## 失败定位

- 本轮实现和验证未出现需要修复的测试失败。
- 测试输出中出现 `HTTPServer` 默认 access log，这是单测内临时 HTTP server 的请求日志，不影响结果。

## 数据、样本或调试输出变化

- 未新增 route 数据、keyframe 样本或视觉检测样本。
- 调试输出变化集中在 route debug web 首页：同一份 status JSON 现在同时以可读面板和 raw JSON 展示。

## 剩余风险和下一步能力建设

- 仍未验证真实 Nav2 waypoint/fixed-route 行驶。
- 仍未验证真实 camera frame 与 keyframe live matching。
- 本轮未做浏览器像素级截图验收，手机窄屏只通过 CSS contract 和静态 HTML 测试约束。
- 下一步建议补真实 route/keyframe 样例，用 route debug panel 记录一次 waiting_visual_gate -> passed -> checkpoint advance 的实测证据。
