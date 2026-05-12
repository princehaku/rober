# Sprint 2026.05.13_03-04 Mobile Web Entrypoint Gate - Tech Plan

## Sprint Type

- sprint_type: epic
- Execution model: two parallel workers after this plan is accepted as complete.
- Evidence boundary target: `software_proof_docker_mobile_web_entrypoint_gate`
- Product rule: 本计划不更新 OKR 数字；最终 `final.md` 根据 worker 证据再保守评估。

## OKR 最低优先级核对

当前 `OKR.md` 4.1 按数字排序的最低 Objective 是：

- Objective 4：手机用户体验与低成本量产边界，当前约 54%。

相邻 Objective：

- Objective 5：云中转 + OSS/CDN 数据通路产品化，当前约 55%。
- Objective 1/2/3 当前约 75%/77%/77%，但本机没有真实硬件，真实 WAVE ROVER、串口、HIL、Nav2/fixed-route 和送达闭环仍不可在本轮直接证明。

本 sprint 正针对最低 Objective 4。选择理由基于 live 证据：

- 02-03 已完成 cloud-relay self-contained runtime，但手机端仍缺 production app 和真实设备验收。
- 01-02 只建立 `mobile/README.md` 脚手架，`mobile/web/` 还没有可运行入口。
- 00-01 已有 phone offline/resume gate，但仍是本地 fallback 证明。
- 因此本轮不继续加厚云中转 backend，而把 phone PWA entrypoint 从 onboard fallback 大字符串推进到 `mobile/web/`。

## 技术方案

### 1. Full-stack worker: `mobile/web/` PWA entrypoint

目标：新增 dependency-free phone PWA 静态入口，消费既有 phone-safe schema，不发明机器人状态。

允许改动文件范围：

- `mobile/web/`
- `mobile/fixtures/`（如需要静态 fixture）
- `mobile/README.md`
- `docs/product/mobile_user_flow.md`
- `docs/interfaces/ros_contracts.md`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_static.py`（仅当需要锁定 static contract 或 fixture helper）
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`（仅当需要锁定 `/api/status` consumer contract）
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`（仅当需要锁定 diagnostics consumer contract）
- Worker 自行新增的最小 mobile smoke script/test（路径应在 `mobile/` 或合适测试目录内）

实现要求：

- `mobile/web/index.html` 是手机入口首屏，依赖静态 CSS/JS，不引入构建链或 npm 依赖。
- JS 只消费 `/api/status`、`/api/diagnostics` 和已有 phone-safe 字段：`phone_readiness`、`command_safety`、`phone_offline_resume_readiness`，可兼容 `phone_task_flow_readiness`、`phone_support_bundle`、`voice_prompt_readiness`。
- 页面不得 hardcode 新机器人状态；fixture 只能用于 static/mobile smoke，并必须显式标注为 fixture。
- Start Delivery、Confirm Dropoff、Cancel 的 enabled state 必须来自 `command_safety` 和既有 action permissions；blocked/offline/pending ACK/manual takeover 状态保持 disabled。
- Diagnostics 和 Support Handoff 在 primary actions blocked 时仍可打开或显示入口。
- `service-worker.js` 只缓存静态 shell；必须 bypass `/api/*`、`/robots/*`、command routes、ACK routes、diagnostics 和所有非 GET 请求。
- Offline shell 不缓存、排队或重放控制请求；primary actions disabled。
- 文案中文优先，不暴露 raw JSON、ROS topic、`/cmd_vel`、serial device、baudrate、WAVE ROVER 参数、token、Authorization、OSS AK/SK、DB/queue URL、local path、checksum 或完整 artifact。
- 代码技术注释使用中文，并解释安全边界或状态消费原因。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_static.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
```

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_static.py
```

```bash
# Worker 选择一个小型 static/mobile smoke，例如：
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile <added-mobile-validation-script>
# 或：
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest <added-mobile-validation-test>
```

```bash
git diff --check -- <full-stack-touched-files>
```

输出必须包含：

1. 实际改动文件列表。
2. 上述验收命令输出摘要。
3. 若有失败，给出根因定位和重跑结果。
4. 剩余风险，尤其是真实手机设备/生产 app/真实云/4G/HIL 未证明项。

### 2. Robot worker: remote bridge / operator compatibility fence

目标：补 remote bridge/operator compatibility fence，确保 mobile web metadata 或 new static contract 不污染机器人 command/status/ack envelope。

允许改动文件范围：

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py`（仅当测试暴露兼容缺口）
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py`（仅当测试暴露兼容缺口）
- `docs/product/remote_4g_mvp.md`
- `docs/interfaces/ros_contracts.md`
- 本 sprint 文档中的 worker 结果段（实现后由收口补入 `tech-done.md`）

实现要求：

- 首选只加 compatibility fence；若现有生产代码已满足，不要为了形式修改 runtime。
- 覆盖 mobile metadata/static contract 下的 metadata-only response：
  - 不触发 `/trashbot/collect_trash`、dropoff confirm、cancel 或其他 robot action。
  - 不 POST ACK。
  - 不推进内存 cursor。
  - 不持久化 cursor。
  - 不改变 `trashbot.remote.v1` command/status/ack envelope。
  - 不把 ACK 文案升级为 delivery success。
- 如需新增文档说明，必须明确 mobile web entrypoint 是 consumer，不能改变 remote bridge delivery semantics。
- 代码技术注释使用中文，并解释兼容围栏的原因。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
```

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py
```

```bash
git diff --check -- <robot-touched-files>
```

输出必须包含：

1. 实际改动文件列表。
2. 上述验收命令输出摘要。
3. 若无需生产代码修改，明确说明测试围栏证明了什么。
4. 剩余风险，尤其是真实云/4G/HIL/真实送达未证明项。

## 并行启动要求

本 sprint 是 2 owner Epic，文件范围基本互不重叠，必须并行启动两个 worker：

- `full-stack-software-engineer` 负责 `mobile/web/` 和手机产品文档。
- `robot-software-engineer` 负责 remote bridge/operator compatibility fence。

主节点收到 worker 返回后只做结果验收、证据核对、补 `tech-done.md`、`side2side_check.md`、`final.md`，并在最终收口时决定是否更新 `OKR.md` 与 `docs/process/okr_progress_log.md`。

## 接口影响

- 新增 `mobile/web/` consumer 不应改变现有 `/api/status`、`/api/diagnostics` schema。
- 不改变 `trashbot.remote.v1` commands/status/ack envelope。
- 不改变 ROS2 action/service/topic contract。
- 不新增硬件、UART、WAVE ROVER、Orange Pi、机械或电气假设。

## 风险边界

- 本轮成功也只能支持 `software_proof_docker_mobile_web_entrypoint_gate`。
- 不证明 production app、真实手机浏览器/设备、真实 service worker install prompt、真实公网云、HTTPS/TLS、真实 4G/SIM、OSS/CDN 实流量、生产 DB/queue、多实例一致性、Nav2/fixed-route、WAVE ROVER、HIL 或 delivery success。
- 如果 service worker 缓存控制流量、fixture 被误当实时状态、或 ACK copy 被写成送达成功，必须阻断收口并要求对应 worker 修复。

## Product 计划任务只读检查

本 Product 计划任务只运行文件存在性和 sprint 文档 diff check：

```bash
test -f OKR.md && test -f mobile/README.md && test -f sprints/2026.05.13_02-03_cloud-relay-self-contained-gate/final.md
```

```bash
git diff --check -- sprints/2026.05.13_03-04_mobile-web-entrypoint-gate/pre_start.md sprints/2026.05.13_03-04_mobile-web-entrypoint-gate/prd.md sprints/2026.05.13_03-04_mobile-web-entrypoint-gate/tech-plan.md
```
