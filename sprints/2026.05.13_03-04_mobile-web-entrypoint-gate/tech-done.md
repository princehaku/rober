# Sprint 2026.05.13_03-04 Mobile Web Entrypoint Gate - Tech Done

## Sprint Type

- sprint_type: epic
- Evidence boundary target: `software_proof_docker_mobile_web_entrypoint_gate`

## Full-stack Worker Result

实际改动：

- 新增 `mobile/web/index.html`、`styles.css`、`app.js`、`manifest.webmanifest`、`service-worker.js`、`offline.html`、`icon-192.svg`、`icon-512.svg`。
- 新增 `mobile/fixtures/mobile_web_status.fixture.json`，显式标注为 static smoke fixture，不是真实机器人状态。
- 新增 `mobile/test_mobile_web_entrypoint.py`，检查静态入口文件、phone-safe schema 消费、按钮 fail-closed、service worker 绕行动态控制流量、offline shell 禁用主操作、fixture 安全边界。
- 更新 `mobile/README.md`、`docs/product/mobile_user_flow.md`、`docs/interfaces/ros_contracts.md`，同步 mobile web entrypoint、PWA/offline 边界、按钮启用契约和 evidence boundary。

用户旅程变化：

- 手机用户有了独立 `mobile/web/` 静态入口，不再只依赖 onboard fallback 大字符串。
- 首屏显示 readiness、下一步、恢复提示、任务流程、操作安全、离线恢复、Diagnostics 和 Support Handoff。
- Start Delivery、Confirm Dropoff、Cancel 默认禁用，只有后端 `command_safety` 与旧 action permission 同时允许时才启用。
- blocked/offline/pending ACK/manual takeover 时主操作保持禁用，Diagnostics 和 Support Handoff 仍可达。

接口影响：

- 不改变 `/api/status`、`/api/diagnostics` schema。
- 不改变 ROS2 action/service/topic contract。
- 不改变 `trashbot.remote.v1` commands/status/ack envelope。
- `mobile/web/` 只作为 consumer 消费 `phone_readiness`、`command_safety`、`phone_offline_resume_readiness`，兼容 `phone_task_flow_readiness`、`phone_support_bundle`、`voice_prompt_readiness`。

验证结果：

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_static.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - `Ran 94 tests in 22.892s`
  - `OK`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_static.py`
  - 退出码 0，无输出。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint`
  - 第一轮失败定位：`app.js` 未显式消费 `voice_prompt_readiness`；service-worker smoke 的 `SHELL_URLS` 正则写错。
  - 修复后重跑：`Ran 5 tests in 0.001s`，`OK`。
- `git diff --check -- <full-stack-touched-files>`
  - 退出码 0，无输出。

浏览器/ROS2 联调结果：

- 本轮未接真实 operator gateway、真实手机浏览器、真实云或 ROS2 runtime；联调边界保持在 `/api/status`、`/api/diagnostics` phone-safe consumer contract 和静态 smoke。
- Browser plugin / local Chromium 未在当前运行时可用；`node` 检查显示 `playwright missing`，本 worker 未做真实浏览器截图验收。

剩余风险：

- 未证明真实手机设备、真实 iPhone/Android 浏览器、真实 PWA 安装提示、production app、真实云、公网 HTTPS/TLS、真实 4G/SIM、OSS/CDN 实流量、Nav2/fixed-route delivery、WAVE ROVER motion、HIL 或 delivery success。
- `mobile/web/` 当前是 dependency-free 静态入口；真实云部署路径和生产账号体系仍未实现。

## Robot Worker Result

实际改动：

- 更新 `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`，新增 `mobile_web_entrypoint`、`mobile_web_entrypoint_readiness`、`pwa_entrypoint` metadata-only response 兼容围栏。
- 更新 `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`，确认合法 robot command envelope 解析时剥离 mobile web / PWA metadata 字段。
- 更新 `docs/product/remote_4g_mvp.md` 与 `docs/interfaces/ros_contracts.md`，同步 mobile web entrypoint 只是 consumer，不改变 `trashbot.remote.v1` command/status/ack 语义。
- 未修改 `remote_bridge.py` 或 `remote_bridge_protocol.py` runtime 代码；本轮只加 compatibility fences。

兼容性证明：

- `mobile_web_entrypoint`、`mobile_web_entrypoint_readiness`、`pwa_entrypoint` metadata-only responses 不启动 `/trashbot/collect_trash`、dropoff confirm、cancel 或其他 robot action。
- metadata-only responses 不 POST ACK、不推进内存 cursor、不持久化 cursor。
- status post 不回写 mobile metadata、`trigger_robot_action`、`cursor_override`、`delivery_success` 或 `/cmd_vel`。
- valid command 旁路 metadata 会从 parsed robot command envelope 中剥离，不改变 `id`、`type`、`payload` 的既有命令语义。

验证结果：

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
  - `Ran 60 tests in 30.370s`
  - `OK`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py`
  - 退出码 0，无输出。
- `git diff --check -- <robot-touched-files>`
  - 退出码 0，无输出。

剩余风险：

- 本轮没有真实云、真实 4G/SIM、production DB/queue、多实例一致性、真实手机浏览器/设备、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。
- ACK 仍只代表 accepted/processing evidence，不代表 delivery success。
