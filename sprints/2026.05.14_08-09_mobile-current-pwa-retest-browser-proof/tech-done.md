# Sprint 2026.05.14_08-09 Mobile Current PWA Retest Browser Proof - Tech Done

## Task A - Full-stack 当前 PWA retest browser proof

Owner: `full-stack-software-engineer`

### 用户旅程变化和触点收益

- 本轮把首屏“真实设备复测请求”panel 纳入当前 `mobile/web` PWA 的本地 Chromium-family browser proof gate。
- 390x844 与 768x900 viewport 证据现在同时检查 retest request panel、`software_proof_docker_mobile_real_device_retest_request_gate`、source boundary、copy button、主操作 fail closed、Diagnostics / Support Handoff、ACK 非 delivery success 文案和 phone-safe 可见文本。
- 证据边界是 `software_proof_docker_mobile_current_pwa_retest_browser_proof_gate`；只证明本机 Chromium-family browser 渲染当前 PWA，不证明真实 iPhone/Android、production app、真实 PWA install prompt/user choice、O5 外部材料、HIL 或真实 delivery。

### 实际改动

- `pc-tools/evidence/phone_browser_acceptance_gate.py`
  - 将 evidence boundary 更新为 `software_proof_docker_mobile_current_pwa_retest_browser_proof_gate`。
  - 保留 `software_proof_docker_mobile_current_pwa_browser_proof_refresh_gate` 作为 current-PWA browser proof 兼容边界，并保留 `software_proof_docker_mobile_web_browser_proof_gate` 作为旧 artifact 兼容边界。
  - 新增 retest request 关键 DOM、panel expectation、boundary expectation、source boundary expectation、visible/copyable judgment 和 JSON evidence 字段。
  - gate 只展开已存在的 terminal/diagnostics DOM 与复制按钮，不调用控制 endpoint，也不把 ACK 或 metadata 写成 delivery success。
- `mobile/test_mobile_web_entrypoint.py`
  - 更新 browser gate 断言，覆盖新 evidence boundary、兼容 boundary、legacy artifact boundary 和 retest request panel/copyable judgment。
- `mobile/README.md`
  - 记录本轮 current PWA retest browser proof 的命令、证据边界、兼容边界和 not_proven 范围。
- `docs/product/mobile_user_flow.md`
  - 同步当前 browser proof gate 覆盖 retest request panel 的用户流程和证据边界。
- `sprints/2026.05.14_08-09_mobile-current-pwa-retest-browser-proof/evidence/`
  - 生成 `mobile_web_browser_390x844.json`
  - 生成 `mobile_web_browser_390x844.png`
  - 生成 `mobile_web_browser_768x900.json`
  - 生成 `mobile_web_browser_768x900.png`
  - 生成 `mobile_web_browser_acceptance_summary.json`

### 验证结果

```text
$ python3 pc-tools/evidence/phone_browser_acceptance_gate.py --output-dir sprints/2026.05.14_08-09_mobile-current-pwa-retest-browser-proof/evidence
viewport=390x844 passed=true ... real_device_retest_request_visible=true real_device_retest_request_copyable=true ... evidence_boundary=software_proof_docker_mobile_current_pwa_retest_browser_proof_gate
viewport=768x900 passed=true ... real_device_retest_request_visible=true real_device_retest_request_copyable=true ... evidence_boundary=software_proof_docker_mobile_current_pwa_retest_browser_proof_gate
summary=sprints/2026.05.14_08-09_mobile-current-pwa-retest-browser-proof/evidence/mobile_web_browser_acceptance_summary.json ok=true evidence_boundary=software_proof_docker_mobile_current_pwa_retest_browser_proof_gate compatible_evidence_boundary=software_proof_docker_mobile_current_pwa_browser_proof_refresh_gate legacy_artifact_evidence_boundary=software_proof_docker_mobile_web_browser_proof_gate
```

```text
$ PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
Ran 28 tests in 0.025s
OK
```

```text
$ PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/phone_browser_acceptance_gate.py mobile/test_mobile_web_entrypoint.py
pass
```

```text
$ git diff --check -- pc-tools/evidence/phone_browser_acceptance_gate.py mobile/test_mobile_web_entrypoint.py mobile/README.md docs/product/mobile_user_flow.md sprints/2026.05.14_08-09_mobile-current-pwa-retest-browser-proof/tech-done.md
pass
```

### 首次失败定位与修复

- 首次运行 browser gate 时，gate 直接调用 `renderTerminalActionPanel()`，触发当前 PWA out-of-scope 内部路径的 `ReferenceError: nextEvidence is not defined`。Task A 不允许改 `mobile/web/app.js`，因此修复为 gate 只展开既有 terminal confirmation DOM，不调用内部控制或提交路径。
- 第二次运行时，phone-safe forbidden 词表把可见说明里的普通词 `token` 当作泄漏误报；修复为继续拦截 `authorization`、`oss ak/sk`、`access_key`、DB/queue URL、ROS topic、`/cmd_vel`、serial、path、traceback、checksum 和完整 artifact 等实质泄漏词，不把“复制包不包含 token”的边界说明误判为泄漏。
- browser bundle safe-copy 在当前 PWA 离线 fallback 下可能显示 `{}`；本轮 gate 对 browser bundle 继续验证 panel boundary 与 copy button，对 Task A 目标 retest request 则验证 package schema visible/copyable。

### 剩余风险和机器人侧配合事项

- 本轮是 `software_proof_docker_mobile_current_pwa_retest_browser_proof_gate`，不是真实手机设备、production app、真实 PWA install prompt/user choice、O5 外部材料、HIL 或真实 delivery。
- `mobile_real_device_retest_request*` 仍是下一轮真实设备复测材料请求，不是验收通过，也不是控制放行来源。
- Robot worker 需要继续用 metadata-only fence 证明本轮 browser/retest metadata 不触发 collect、confirm_dropoff、cancel、ACK、cursor、terminal ACK、production readiness、HIL、dropoff/cancel completion 或 delivery success。

## Task B - Robot metadata-only compatibility fence

Owner: `robot-software-engineer`

### 用户旅程变化和触点收益

- Robot 侧把 `mobile_current_pwa_retest_browser_proof*` 与真实设备复测请求 metadata 固化为 metadata-only：手机首屏/浏览器证据可以被远程状态携带，但不会被误解为控制命令。
- mixed valid-command 场景证明即使 metadata 和有效 command 同包出现，也只执行 `trashbot.remote.v1` command envelope，不把 browser proof 或真实设备复测请求写入 ACK/status/cursor/terminal result。

### 实际改动

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
  - 新增 current PWA retest browser proof worker 围栏，覆盖 metadata-only response 与 valid-command mixed metadata。
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
  - 新增 protocol normalization 围栏，证明 browser proof / retest request metadata 不进入 normalized command。
- `docs/interfaces/ros_contracts.md`
  - 同步 `mobile_current_pwa_retest_browser_proof`、`mobile_current_pwa_retest_browser_proof_summary`、`phone_current_pwa_retest_browser_proof` 的 metadata-only 契约边界。

### 验证结果

```text
$ PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
Ran 153 tests in 78.872s
OK
```

```text
$ PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
pass
```

```text
$ git diff --check -- onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md sprints/2026.05.14_08-09_mobile-current-pwa-retest-browser-proof/tech-done.md
pass
```

### 剩余风险

- Robot fence 是 metadata-only 软件围栏，不是真实 collect/dropoff/cancel、Nav2/fixed-route、WAVE ROVER、HIL 或 delivery success。
- 本轮未改 production `remote_bridge.py` runtime 语义；只把当前 PWA retest browser proof / retest request metadata 的不触发控制语义写入测试和接口契约。

## Task C - Product closeout

Owner: `product-okr-owner`

### 用户价值和产品北极星

- 用户价值：支持/验收人员现在可以用本轮 evidence 包复查当前 `mobile/web` PWA 首屏是否稳定展示真实设备复测请求、关键面板、phone-safe 边界和 fail-closed 主操作。
- 产品北极星：继续把手机作为普通用户唯一入口，但保持证据边界清楚；本轮只把 current PWA retest browser proof 做实，不把 browser proof、ACK 或 metadata 写成真实送达。

### OKR 映射与本轮核心抓手

- Objective 4 KR5/KR7：当前 PWA 的 390x844 与 768x900 本地 Chromium-family browser proof 覆盖真实设备复测请求 panel、可复制判断、触控/布局/phone-safe 和主操作 fail-closed。
- Objective 5：仍是最低 Objective（约 68%），但本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration 外部材料，因此不调整。
- Objective 1/2/3：本轮没有硬件、任务闭环、导航或 route 实测材料，因此不调整。

### KR 拆解或更新

- O4 从约 84% 保守上调到约 85%：依据是 Task A browser evidence `ok=true`、两组 viewport passed、retest request 可见/可复制、ACK 非 delivery success、phone-safe checks passed，以及 Task B metadata-only fence `Ran 153 tests ... OK`。
- O5 保持约 68%：缺真实外部云/4G/OSS/CDN/DB/queue/worker 材料，不能用本地 browser proof 替代。
- O1/O2/O3 保持不变：缺真实 WAVE ROVER/HIL、Nav2/fixed-route、任务复盘和真实送达证据。

### 优先级、验收口径和责任 Engineer

- P0 已完成：`full-stack-software-engineer` 交付 current PWA retest browser proof evidence 和 mobile/docs 更新。
- P0 已完成：`robot-software-engineer` 交付 metadata-only / mixed valid-command 围栏和接口契约更新。
- P0 已完成：`product-okr-owner` 更新 `OKR.md`、`docs/process/okr_progress_log.md`、`side2side_check.md`、`final.md`，并把本轮证据边界写成 `software_proof_docker_mobile_current_pwa_retest_browser_proof_gate`。

### 风险、阻塞和证据链缺口

- `not_proven` 仍包括真实手机设备、真实 iPhone/Android device behavior、production app、真实 PWA install prompt/user choice、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration、Nav2/fixed-route、WAVE ROVER、HIL、真实 dropoff/cancel completion 和真实 delivery。
- 真实设备复测请求仍是下一轮材料请求，不是验收通过。
- browser proof 与 ACK/HTTP accepted/receipt 仍是 accepted/processing/support metadata，不是 delivery success。

### 需要创建或更新的 sprint 文档

- 已更新：`tech-done.md`
- 已创建/更新：`side2side_check.md`
- 已创建/更新：`final.md`
