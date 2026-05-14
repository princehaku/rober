# Sprint 2026.05.14_09-10 Mobile Real Device Field Trial Package - Tech Done

## Task A - Full-stack 真实设备现场试跑包

Owner: `full-stack-software-engineer`

### 用户旅程变化和触点收益

- 本轮在 `mobile/web` 首屏新增“真实设备现场试跑包”panel，把真实 iPhone/Android 或 production app 现场试跑前的 runtime metadata 与人工 observation fields 做成可复制的 phone-safe package。
- package 固定 `safe_to_control=false`、`ack_semantics=accepted_processing_only_not_delivery_success`、`not_proven`，并使用 `software_proof_docker_mobile_real_device_field_trial_package_gate` 作为证据边界。
- 该能力只把现场试跑材料收集口径产品化，不证明真实手机设备、production app、真实 PWA install prompt/user choice、O5 外部 proof、HIL 或 delivery success。

### 实际改动

- `mobile/web/index.html`
  - 新增真实设备现场试跑包首屏 panel、人工 observation inputs 和 copy action。
- `mobile/web/app.js`
  - 新增/派生 `mobile_real_device_field_trial_package`、`mobile_real_device_field_trial_package_summary`、`mobile_real_device_field_trial_package_copy`。
  - 采集 phone-safe runtime metadata，并生成 whitelist-only copy package。
- `mobile/web/styles.css`
  - 补齐 field trial package panel、输入区和移动 viewport 触控/布局样式。
- `mobile/test_mobile_web_entrypoint.py`
  - 覆盖 package schema、safe fields、manual observation fields、敏感字段过滤、ACK 非 delivery success、primary actions fail closed。
- `mobile/README.md`
  - 同步真实设备现场试跑包的使用方式、验证命令和 not_proven 边界。
- `docs/product/mobile_user_flow.md`
  - 同步 field trial package 在手机用户流程中的产品边界。

### 验证结果

```text
$ PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
Ran 29 tests ... OK
```

```text
$ PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py
pass
```

```text
$ node --check mobile/web/app.js
pass
```

```text
$ rg -n "software_proof_docker_mobile_real_device_field_trial_package_gate|mobile_real_device_field_trial_package|accepted_processing_only_not_delivery_success|not_proven|safe_to_control=false|真实设备现场试跑包" mobile/web/index.html mobile/web/app.js mobile/test_mobile_web_entrypoint.py mobile/README.md docs/product/mobile_user_flow.md
pass
```

```text
$ git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/test_mobile_web_entrypoint.py mobile/README.md docs/product/mobile_user_flow.md sprints/2026.05.14_09-10_mobile-real-device-field-trial-package/tech-done.md
pass
```

### 剩余风险

- 本轮仍是 Docker/local mobile software proof only；不证明真实 iPhone/Android、production app、真实 PWA install prompt/user choice、Objective 5 外部 proof、HIL 或 delivery success。
- 现场人员后续仍需提供真实设备截图/录屏、真实浏览器或 production app 入口、PWA install prompt/user choice 和人工观察材料。

## Task B - Robot metadata-only compatibility fence

Owner: `robot-software-engineer`

### 用户旅程变化和触点收益

- Robot 侧把 `mobile_real_device_field_trial_package*` 固化为 metadata-only family：手机现场试跑包可以随远程状态或支持材料流转，但不会被误认为机器人控制命令。
- mixed valid-command 场景证明即使 field trial metadata 和合法 command 同包出现，也只执行 `trashbot.remote.v1` command envelope。

### 实际改动

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
  - 新增 `mobile_real_device_field_trial_package`、`mobile_real_device_field_trial_package_summary`、`mobile_real_device_field_trial_package_copy` worker metadata-only fences。
  - 新增 mixed valid-command coverage，证明 field trial package metadata 不触发 backend action。
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
  - 新增 protocol normalization fences，证明 field trial package metadata 不进入 normalized command、ACK、status、cursor 或 terminal result。
- `docs/interfaces/ros_contracts.md`
  - 同步 field trial package metadata 只服务 phone/support/product handoff，不是 robot command、ACK、cursor、terminal result、production readiness、HIL 或 delivery proof。

### 验证结果

```text
$ PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
Ran 157 tests in 80.820s
OK
```

```text
$ PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
pass
```

```text
$ rg -n "mobile_real_device_field_trial_package|metadata-only|delivery success|HIL|production readiness|cursor|ACK" onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md
pass
```

```text
$ git diff --check -- onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md sprints/2026.05.14_09-10_mobile-real-device-field-trial-package/tech-done.md
pass
```

### 剩余风险

- Robot-side 证据是 software/protocol fence only；不证明真实 phone device behavior、production app readiness、cloud/4G、Nav2/fixed-route、WAVE ROVER feedback、HIL、dropoff/cancel completion 或 delivery。
- 本轮没有修改 production robot runtime，只补 metadata-only compatibility fences 与接口合同。

## Task C - Product closeout

Owner: `product-okr-owner`

### 用户价值和产品北极星

- 用户价值：现场人员现在有一份统一、可复制、phone-safe 的真实设备现场试跑包口径，可记录 runtime metadata 与人工 observation fields，并避免把 ACK/package copy 误读成 delivery success。
- 产品北极星：手机仍是普通用户唯一入口；本轮推进真实设备验收材料链，但不把 software proof 写成真实手机验收或真实送达。

### OKR 映射与本轮核心抓手

- Objective 4 KR4/KR5/KR7：field trial package 让真实设备现场试跑材料进入可复制、可脱敏、可复盘的软件入口，支持 O4 从约 85% 保守上调到约 86%。
- Objective 5：仍是最低 Objective（约 68%），但本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration 外部材料，因此不调整。
- Objective 1/2/3：本轮没有硬件、任务闭环、导航或 route 实测材料，因此不调整。

### KR 拆解或更新

- O4 从约 85% 保守上调到约 86%：依据是 Task A mobile tests 29 OK、`node --check` pass、field trial package boundary/copy/ACK/not_proven 围栏通过，以及 Task B Robot metadata-only fence 157 tests OK。
- O5 保持约 68%：缺真实外部云/4G/OSS/CDN/DB/queue/worker 材料，不能用本地 field trial package metadata 替代。
- O1/O2/O3 保持不变：缺真实 WAVE ROVER/HIL、Nav2/fixed-route、任务复盘和真实送达证据。

### 优先级、验收口径和责任 Engineer

- P0 已完成：`full-stack-software-engineer` 交付真实设备现场试跑包 UI/logic/tests/docs。
- P0 已完成：`robot-software-engineer` 交付 metadata-only / mixed valid-command 围栏和接口契约更新。
- P0 已完成：`product-okr-owner` 更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`，并把本轮证据边界写成 `software_proof_docker_mobile_real_device_field_trial_package_gate`。

### 风险、阻塞和证据链缺口

- `not_proven` 仍包括真实手机设备、真实 iPhone/Android device behavior、production app、真实 PWA install prompt/user choice、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration、Nav2/fixed-route、WAVE ROVER、HIL、真实 dropoff/cancel completion 和真实 delivery。
- 真实设备现场试跑包只是 support/reproduction metadata，不是验收通过、控制放行、ACK、terminal result 或 delivery success。
- 下一步需要真实设备现场试跑截图/录屏/observations、production app 或真实浏览器入口 URL、真实 PWA install prompt/user choice；若回到 O5，还需要真实外部云/4G/OSS/CDN/DB/queue/worker evidence。

### 需要创建或更新的 sprint 文档

- 已创建/更新：`tech-done.md`
- 已创建/更新：`side2side_check.md`
- 已创建/更新：`final.md`
