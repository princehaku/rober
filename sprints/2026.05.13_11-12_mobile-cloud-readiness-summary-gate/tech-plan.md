# Sprint 2026.05.13_11-12 Mobile Cloud Readiness Summary Gate - Tech Plan

## 目标

建立 `software_proof_docker_mobile_cloud_readiness_summary_gate`：手机首屏消费 cloud/preflight/DB/queue readiness 的 phone-safe 摘要，展示普通用户能理解的云中转状态、阻塞原因和恢复建议；robot-side compatibility fence 证明这些字段是 metadata-only，不改变 `trashbot.remote.v1` command/status/ack envelope，不触发机器人动作。

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 最低可推进 Objective 是 Objective 4：手机用户体验与低成本量产边界，约 62%。
2. Objective 5 约 63%，最新 sprint `2026.05.13_10-11_cloud-db-queue-config-gate/final.md` 已完成 cloud DB/queue config gate，但明确仍不是真实 production DB/queue 或真实云证据。
3. Objective 1/2/3 约 75%/77%/77%，主要缺真实 WAVE ROVER、真实串口、真实 Nav2/fixed-route、同一 `evidence_ref` 任务复盘、HIL 和真实送达；当前主机没有真实硬件，只有 Docker。
4. 本 sprint 直接针对 Objective 4。理由是 O4 当前低于 O5，且可在 Docker/local 条件下通过手机 cloud readiness summary 继续推进用户触点功能。
5. 不选择 Objective 1：真实 `hil_pass`、真实串口日志、`T=1001` feedback、`/odom`、`/imu/data`、`/battery` 实机样本仍不可得。
6. 不选择 Objective 2：真实 Nav2/fixed-route 运行、任务复盘、真实送达和失败恢复实测仍不可得。
7. 不选择 Objective 3：真实路线采集、Nav2 waypoint/fixed-route 实跑、关键帧实景证据与上车复账仍不可得。
8. 不选择 Objective 5：它刚在 10-11 sprint 上调到约 63%；本轮复用 O5 证据作为 O4 手机可解释性输入，不继续堆后端深度。

## 技术方案

### Task A：full-stack-software-engineer

文件范围：

- `mobile/web/index.html`
- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/test_mobile_web_entrypoint.py`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/README.md`
- `docs/product/mobile_user_flow.md`

实现要求：

- 在 mobile/web 首屏新增“云中转状态”摘要区域。
- 消费 `phone_cloud_readiness_summary`、`mobile_cloud_readiness_summary`、`phone_readiness.cloud_readiness` 或等价 phone-safe 字段；缺失时显示等待摘要，不启用任何控制动作。
- fixture 增加 schema，例如 `trashbot.phone_cloud_readiness_summary.v1`，并覆盖 `software_proof_docker_cloud_db_queue_config_gate` / `production_ready=false` / blocked recovery 语义。
- static smoke 覆盖面板可见、字段消费、ACK 文案、forbidden secret/raw/hardware 字段检查。
- 更新 `mobile/README.md` 与 `docs/product/mobile_user_flow.md`。
- 代码技术注释使用中文，重点解释为什么该摘要只读、为什么不能把 cloud/preflight blocked 写成机器人可动或 delivery success。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py
git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/test_mobile_web_entrypoint.py mobile/fixtures/mobile_web_status.fixture.json mobile/README.md docs/product/mobile_user_flow.md
```

### Task B：robot-software-engineer

文件范围：

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`

实现要求：

- 增加 `phone_cloud_readiness_summary` / `mobile_cloud_readiness_summary` / `cloud_readiness_summary` metadata-only compatibility fence。
- 验证 metadata-only response 不触发 backend action。
- 验证不 POST ACK。
- 验证不推进或持久化 cursor。
- 验证 protocol normalization 剥离 command envelope 外 metadata，不把 production-ready、credential、cloud URL 或 delivery-success 语义带入 command/status/ack。
- 更新接口文档，明确该 metadata 属于 phone-safe support/readiness summary，不属于 `trashbot.remote.v1` command/status/ack envelope。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
git diff --check -- onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md
```

### Task C：product-okr-owner

文件范围：

- `sprints/2026.05.13_11-12_mobile-cloud-readiness-summary-gate/tech-done.md`
- `sprints/2026.05.13_11-12_mobile-cloud-readiness-summary-gate/side2side_check.md`
- `sprints/2026.05.13_11-12_mobile-cloud-readiness-summary-gate/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

收口要求：

- 等 Task A、Task B 都完成后再汇总实际改动和验证输出。
- 检查引用文档路径真实存在。
- 保守更新 Objective 4 进度；Objective 1/2/3/5 除非有新证据不调整。
- 明确 evidence boundary：`software_proof_docker_mobile_cloud_readiness_summary_gate`。
- 明确不声明真实手机设备/browser、production app、真实云/4G、OSS/CDN live traffic、production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

验收命令：

```bash
test -f OKR.md && test -f docs/process/okr_progress_log.md && test -f docs/product/mobile_user_flow.md && test -f docs/interfaces/ros_contracts.md
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.13_11-12_mobile-cloud-readiness-summary-gate
```

## 接口影响

- 新增或消费 phone-safe metadata：`phone_cloud_readiness_summary`、`mobile_cloud_readiness_summary` 或 `cloud_readiness_summary`。
- 不改变 ROS2 topic、service、action、`/cmd_vel`、WAVE ROVER、UART、launch 参数或硬件配置。
- 不改变 `trashbot.remote.v1` command/status/ack envelope。
- 旧客户端可忽略新增 summary 字段。

## 安全与隐私边界

Cloud readiness summary、fixture、文档和 phone-safe status 不得包含：

- bearer token、Authorization header、OSS AK/SK、root password。
- DB URL、queue URL、credential-bearing URL、production secret。
- raw ROS topic、`/cmd_vel`、serial device、baudrate、WAVE ROVER 参数。
- local filesystem path、traceback、checksum、完整 artifact。
- 任何能把 accepted/processing、preflight present、config gate present 误读为 delivery success、real cloud ready、production DB/queue ready、HIL pass 或真实送达的文案。

## 验证计划

后续执行阶段必须至少运行围栏验证：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/test_mobile_web_entrypoint.py mobile/fixtures/mobile_web_status.fixture.json mobile/README.md docs/product/mobile_user_flow.md onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md
```

本 planning 阶段验收命令：

```bash
test -f sprints/2026.05.13_11-12_mobile-cloud-readiness-summary-gate/pre_start.md && test -f sprints/2026.05.13_11-12_mobile-cloud-readiness-summary-gate/prd.md && test -f sprints/2026.05.13_11-12_mobile-cloud-readiness-summary-gate/tech-plan.md
git diff --check -- sprints/2026.05.13_11-12_mobile-cloud-readiness-summary-gate
```

## 风险与回滚

- 如果文案把 cloud DB/queue config gate 写成真实 production DB/queue ready，Task A 或 Task C 必须先修文案再收口。
- 如果 robot fence 发现 metadata-only 字段进入 action path，Task B 必须补 normalization 或负例，不能用文档绕过。
- 如果只完成 mobile/static proof，Objective 4 只能保守小幅推进；真实手机、真实云、真实硬件与真实送达仍留作后续。
- 回滚方式是移除本 sprint 的 mobile cloud readiness summary 增量和对应文档增量；不得回滚无关 sprint 或其他 worker 改动。
