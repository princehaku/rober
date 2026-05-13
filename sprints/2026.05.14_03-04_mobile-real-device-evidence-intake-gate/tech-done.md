# Sprint 2026.05.14_03-04 Mobile Real Device Evidence Intake Gate - Tech Done

## Task B - Robot

### 实际改动

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
  - 新增 `mobile_real_device_evidence_intake`、`mobile_real_device_evidence_intake_summary`、`mobile_real_device_evidence_package` 的 metadata-only response fence。
  - 覆盖无 command envelope 时不得触发 collect、confirm_dropoff、cancel、ACK POST、cursor advance、cursor persistence、`last_terminal_ack_id`、delivery success、dropoff success、cancel completed、production readiness、HIL 或真实设备控制语义。
  - 新增 valid command mixed metadata fence，证明有效 `confirm_dropoff` command 只执行 command envelope；ACK/status/cursor 不吸收 intake metadata、evidence boundary 或成功语义。
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
  - 新增 validate/normalization fence，证明 command 外侧的 intake metadata 会被忽略，normalized command 不包含 intake metadata、evidence boundary、control hint、cursor override、delivery/dropoff/cancel success、production/HIL/real-device/PWA proof 或敏感字段。
  - 新增 protocol client metadata-only response fence，证明 intake metadata-only response 不会生成 command id 或 terminal ACK。
- `docs/interfaces/ros_contracts.md`
  - 记录 intake 三字段是 phone/support/acceptance metadata-only。
  - 明确它不是 command/status/ACK/cursor/production readiness/HIL/real device proof/control enablement/delivery success，也不能写入 robot status、ACK、backend action result、normalized command payload 或 cursor state。

### 验证结果

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
```

结果：`Ran 133 tests in 67.780s`，`OK`。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
```

结果：通过，无输出。

```bash
rg -n "mobile_real_device_evidence_intake|software_proof_docker_mobile_real_device_evidence_intake_gate|metadata-only|delivery success|PWA install prompt|production app|真实手机设备" docs/interfaces/ros_contracts.md onboard/src/ros2_trashbot_behavior/test
```

结果：通过，命中新 intake 测试与 `docs/interfaces/ros_contracts.md` 中的 metadata-only contract。

### 失败定位与修复

首轮 unittest 失败 1 项：`test_mobile_real_device_evidence_intake_metadata_is_ignored_by_valid_command_envelope` 对有效 `confirm_dropoff` command 的状态断言沿用了 collect 路径的 `loaded_and_ready`。实际 command envelope 正确执行后状态为 `returning`。已修正断言为 `returning`，并保留 metadata/evidence boundary 不进入 ACK/status/cursor 的检查；第二轮 targeted unittest 通过。

### 剩余风险

- 本 Task B 只证明 robot remote bridge/protocol 对 intake metadata 的软件围栏，不证明真实手机设备、真实 iPhone/Android 行为、production app、真实 PWA install prompt/user choice、真实 delivery、Nav2/fixed-route、WAVE ROVER 或 HIL。
- 本轮未改硬件、launch、ROS2 action/service/topic 契约或云端生产配置；无需 Hardware / Autonomy 协同。
- 需要 Full-stack Task A 提供手机/PWA intake surface，Product closeout 后续再更新 `OKR.md`、`side2side_check.md` 和 `final.md`。

## Task A - Full-stack

### 用户旅程变化和触点收益

- `mobile/web` 首屏新增“真实设备验收材料”panel，放在现有手机设备证据、真实手机验收交接、PWA 安装提示证据之后，浏览器验收包之前。
- 用户或支持人员现在可以粘贴真实 iPhone/Android、production app、PWA install prompt/user choice、截图摘要、URL 摘要和 observer note 的 JSON 摘要；页面会重新生成 redacted phone-safe package。
- 没有真实材料时，页面可以用当前本地浏览器 metadata 生成 blocked-by-design package，明确 `not_proven`、ACK 语义和 `software_proof_docker_mobile_real_device_evidence_intake_gate` 边界。
- 本 gate 不启用 Start Delivery、Confirm Dropoff 或 Cancel；动作仍由既有 command safety、cloud/device/browser readiness、handoff session、operation log 和 action feedback gates fail closed。

### 实际改动

- `mobile/web/index.html`
  - 新增“真实设备验收材料”panel、JSON 文本框、导入按钮、本地 blocked package 生成按钮、redacted package 复制入口和字段展示区。
- `mobile/web/app.js`
  - 新增 `trashbot.mobile_real_device_evidence_intake.v1`、`trashbot.mobile_real_device_evidence_intake_summary.v1`、`trashbot.mobile_real_device_evidence_package.v1` 的读取、归一化、脱敏、渲染和复制逻辑。
  - 支持顶层、`phone_readiness`、`/api/diagnostics` 嵌套字段，以及本地 JSON 导入。
  - 新增敏感字段过滤：token、Authorization、OSS AK/SK、root password、DB/queue URL、ROS topic、`/cmd_vel`、serial、baudrate、WAVE ROVER、本地路径、traceback、checksum、artifact、raw robot response 等命中后拒绝原文。
- `mobile/web/styles.css`
  - 新增 intake panel、textarea 和 responsive grid 样式。
- `mobile/fixtures/mobile_web_status.fixture.json`
  - 新增顶层和 `phone_readiness` 嵌套 intake / summary / package fixture，保持 `overall_status=blocked`、`safe_to_control=false`、`redaction_status=passed`。
- `mobile/test_mobile_web_entrypoint.py`
  - 增加 intake panel、schema、copy path、redaction filter、非控制放行和 fixture contract 的 targeted unittest 覆盖。
- `docs/product/mobile_user_flow.md`
  - 补充真实设备材料 intake 的 schema、字段、redaction 规则和非控制放行边界。
- `mobile/README.md`
  - 补充当前 sprint 增量、消费字段、intake 规则和路线图条目。

### 前后端 / ROS2 联调结果

- 前端新增字段只消费 phone-safe metadata：`mobile_real_device_evidence_intake`、`mobile_real_device_evidence_intake_summary`、`mobile_real_device_evidence_package`，并兼容 `phone_readiness` 与 diagnostics 嵌套来源。
- Task A 未改 ROS2 后端、cloud relay 或 robot bridge；Robot Task B 已在同一 sprint 中证明这些 metadata-only response 不触发 collect、confirm_dropoff、cancel、ACK POST、cursor advance/persistence 或 success 语义。

### 验证结果

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
```

结果：`Ran 24 tests in 0.014s`，`OK`。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py
```

结果：通过，无输出。

```bash
node --check mobile/web/app.js
```

结果：通过，无输出。

```bash
rg -n "software_proof_docker_mobile_real_device_evidence_intake_gate|mobile_real_device_evidence_intake|真实手机设备|production app|PWA install prompt|not_proven|redaction" mobile docs/product/mobile_user_flow.md
```

结果：通过，命中 `mobile/web`、fixture、unittest、`mobile/README.md` 和 `docs/product/mobile_user_flow.md` 中的新 intake schema、边界、`not_proven` 与 redaction 说明。

```bash
git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/fixtures/mobile_web_status.fixture.json mobile/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md mobile/README.md sprints/2026.05.14_03-04_mobile-real-device-evidence-intake-gate/tech-done.md
```

结果：通过，无输出。

### 失败定位

- Task A 实现和最终验收命令未出现失败。

### 剩余风险

- 本 Task A 是 `software_proof_docker_mobile_real_device_evidence_intake_gate`，只证明本地/static PWA 可以导入、过滤、展示和复制 redacted phone-safe package。
- 仍不证明真实手机设备、真实 iPhone/Android device behavior、production app、真实 PWA install prompt/user choice、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL 或真实 delivery。
- 后续若要提升 Objective 4/5 真实验收，需要拿到真实设备/browser 或 production app 的外部材料，并由 Product closeout 独立更新 OKR 与最终边界。

## Task C - Product Closeout

### 用户价值和产品北极星

本轮把真实设备验收材料从“散落截图/聊天说明”推进为手机/PWA 首屏可导入、可脱敏、可复制、可由 robot 侧忽略控制语义的统一 intake gate。北极星仍是普通手机用户不需要理解 ROS2、串口、云端内部配置或 raw JSON，也能把真实 iPhone/Android、production app、PWA install prompt/user choice 的验收材料交给产品和工程团队判断下一步。

### OKR 映射与 KR 拆解

- Objective 4 KR5：真实手机验收材料有了 schema、redaction、`not_proven` 和 phone-safe package 入口，后续可用于真实设备验收收口。
- Objective 4 KR7：首屏继续围绕 iPhone/Android、production app、PWA install prompt/user choice、viewport、display-mode 和 touch/browser evidence 组织材料，但本轮只证明 intake 软件入口。
- Objective 5：保持约 68%，因为本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration。

### 验收口径与责任 Engineer

- Full-stack 责任范围已完成：`mobile/web` 首屏真实设备验收材料 panel、JSON 导入、本地 blocked package 生成、redacted phone-safe package 复制、fixture/test/docs。
- Robot 责任范围已完成：`mobile_real_device_evidence_intake` / summary / package metadata-only compatibility fence，证明不会触发 Start Delivery、Confirm Dropoff、Cancel、ACK POST、cursor、persistence、production readiness、HIL 或 delivery success。
- Product 责任范围已完成：本 closeout 追加、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md` 更新。

### OKR 调整

Objective 4 从约 79% 谨慎上调到约 80%。理由是本轮在已有 handoff、install prompt evidence、current PWA local Chromium proof 之上，新增真实设备材料 intake 和 robot metadata-only fence，缩短了真实手机验收材料从现场到产品判定的路径。

Objective 5 保持约 68%。本轮没有真实外部 O5 材料，不能把 Docker/local software proof 写成云中转、4G、OSS/CDN、production DB/queue 或 production app 进度。

Objective 1/2/3 不调整。本轮未改硬件、Nav2/fixed-route、delivery action、真实 dropoff/cancel 或 HIL。

### 剩余风险

仍缺真实手机设备、真实 iPhone/Android device behavior、production app、真实 PWA install prompt/user choice、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration、Nav2/fixed-route、WAVE ROVER、HIL、真实 dropoff/cancel completion 和真实 delivery。ACK、HTTP accepted、receipt、intake package、handoff session、browser proof 和 install prompt evidence 仍只是 accepted/processing/support metadata，不是 delivery success。
