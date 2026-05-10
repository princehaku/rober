# Sprint 2026.05.10 16-17 Route Debug Status Panel - Tech Plan

## 状态

- 阶段：tech-plan completed，可进入 implementation。
- 时间：2026-05-10 16:15 Asia/Shanghai。
- 主责：Autonomy Algorithm Engineer。
- 执行方式：1 owner 单线闭环，必须由 `autonomy-engineer` 子 agent 实现、验证并更新 `tech-done.md`。Coordinator 不直接写产品代码或测试代码。

## 文件范围

Autonomy Engineer 可改：

- `src/ros2_trashbot_nav/ros2_trashbot_nav/route_debug_web.py`
- `src/ros2_trashbot_nav/test/test_route_debug_web.py`
- `sprints/2026.05.10_16-17_route-debug-status-panel/tech-done.md`

允许只读：

- `AGENTS.md`
- `OKR.md`
- `src/ros2_trashbot_nav/ros2_trashbot_nav/fixed_route_autonomy.py`
- `src/ros2_trashbot_nav/test/test_fixed_route_status_static.py`
- `src/ros2_trashbot_nav/test/test_fixed_route_dry_run_offline.py`
- `sprints/2026.05.10_16-17_route-debug-status-panel/pre_start.md`
- `sprints/2026.05.10_16-17_route-debug-status-panel/prd.md`

禁止改动：

- `OKR.md`
- `AGENTS.md`
- `.codex/agents/`
- `docs/vendor/`
- `src/ros2_trashbot_hardware/`
- `src/ros2_trashbot_behavior/`
- `src/ros2_trashbot_interfaces/`
- ROS2 msg/srv/action
- launch 硬件参数、UART、WAVE ROVER、ESP32、Orange Pi 相关配置

## 接口影响

- 不改 `/api/status` 路径。
- 不改 fixed-route status JSON 的生产者和字段 shape。
- 只在 HTML/JS 中消费现有字段：
  - `state`
  - `mode`
  - `route_contract_version`
  - `route_file`
  - `keyframe_dir`
  - `current_index`
  - `current_target`
  - `total`
  - `enable_visual_gate`
  - `keyframe_preflight`
  - `visual_gate_status`
  - `visual_gate_detail`
  - `visual_gate_checkpoint`
  - `last_error`
  - `failure_reason`
  - `last_transition`
  - `last_nav_result`
  - `updated_at`
  - 可选 `task_record_path`、`last_task`、`task`、`nav_results`

## 实施任务

### Task 1：新增 route debug web 测试

文件：

- `src/ros2_trashbot_nav/test/test_route_debug_web.py`

要求：

1. 使用标准库 `unittest`。
2. 导入 `route_debug_web.HTML` 和 `make_handler`，不需要启动真实 ROS2。
3. 静态断言首页 HTML 包含 PRD 要求的 DOM id 和 JS 函数名。
4. 用临时目录和 `HTTPServer` 或直接 handler 辅助测试 `/api/status`：
   - status 文件缺失时返回 `missing_status_file`。
   - status 文件坏 JSON 时返回 `invalid_status_file`。
   - status 文件正常时透传 JSON 字段。

### Task 2：改造 HTML 为可读 panel

文件：

- `src/ros2_trashbot_nav/ros2_trashbot_nav/route_debug_web.py`

要求：

1. 保留 dependency-free 单文件 HTML，不引入外部 CDN、前端框架或构建步骤。
2. 新增 CSS，让面板在手机宽度和桌面宽度都可读；路径和错误原因使用 `overflow-wrap:anywhere`。
3. 首页结构至少包含：
   - 顶部状态 badge 和 summary。
   - checkpoint progress。
   - current target 坐标。
   - visual gate 状态和 detail。
   - keyframe preflight 覆盖、missing、invalid。
   - failure reason / last error。
   - recent task/task record 引用。
   - raw JSON。
4. 不要删除 raw JSON；它仍是工程排查兜底。

### Task 3：实现字段到文案映射

文件：

- `src/ros2_trashbot_nav/ros2_trashbot_nav/route_debug_web.py`

要求：

1. `routeStateView(status)`：
   - `completed` -> Completed / ok。
   - `ready`、`running` -> Active / ok 或 warning。
   - `waiting_visual_gate` -> Waiting visual gate / warning。
   - `error`、`invalid_status_file` -> Error / error。
   - `missing_status_file` -> Missing status / muted。
   - 其他 -> Unknown / muted。
2. `visualGateView(status)`：
   - 显示 disabled、passed、waiting_camera_frame、keyframe_preflight_failed、insufficient_matches、no_live_descriptors、missing_keyframe 等常见状态。
3. `renderKeyframePreflight(preflight)`：
   - 展示 total、loaded 数量、missing 列表、invalid 列表和 `route_visual_ready`。
4. `renderStatus(status)`：
   - 统一更新 DOM，任何字段缺失时显示 `not provided` 或 `-`。
   - recent task 优先显示 `task_record_path`，其次显示 `last_task.task_record_path`，其次显示 `task.id` 或 `last_task.task_id`，否则显示 `not provided`。
   - `updated_at` 如果是 number，显示本地时间；否则原样显示或 `not provided`。

### Task 4：写 tech-done

文件：

- `sprints/2026.05.10_16-17_route-debug-status-panel/tech-done.md`

记录：

- 实际改动文件。
- 自主能力目标和本轮抓手。
- 页面能力变化。
- 接口影响。
- 验证命令和结果。
- 失败定位。
- 剩余风险。

## 验收命令

Autonomy Engineer 必须至少运行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_nav/test -p 'test_route_debug_web.py'
python3 -m py_compile src/ros2_trashbot_nav/ros2_trashbot_nav/route_debug_web.py
git diff --check -- src/ros2_trashbot_nav/ros2_trashbot_nav/route_debug_web.py src/ros2_trashbot_nav/test/test_route_debug_web.py sprints/2026.05.10_16-17_route-debug-status-panel/tech-done.md
```

如果改动影响 nav 包通用测试，还应运行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_nav/test
```

如果本地耗时可接受，继续运行完整护栏：

```bash
PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh
```

## 剩余风险边界

- 本轮不证明真实 Nav2 行驶、真实 camera frame、真实 keyframe/live-frame match。
- 本轮不证明手机浏览器像素级布局，只通过静态 contract 和 HTTP handler 测试防回退。
- Docker/Humble 和 WAVE ROVER HIL 仍不是本轮必达，但 Coordinator 收口时应如实记录。
