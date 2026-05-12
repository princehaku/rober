# Sprint 2026.05.12_15-16 Phone Browser Acceptance Gate - Tech Done

## 状态

- 阶段：tech-done
- 主责：`full-stack-software-engineer`
- 证据边界：`software_proof_docker_phone_browser_acceptance_gate`
- 当前结论：通过本地真实浏览器 acceptance gate；证据边界为 `software_proof_docker_phone_browser_acceptance_gate`

## 实际改动

- 新增 `scripts/phone_browser_acceptance_gate.py`，用本地 operator fixture server 和真实 Chromium-family browser 生成 `390x844`、`768x900` viewport 的布局证据。
- 调整本地 operator 页面，将 raw status JSON 支持快照默认隐藏，普通手机首屏只展示 readiness、command safety、ACK 语义、recovery hint 和 Diagnostics 入口。
- 收紧手机 CSS：长 evidence boundary 可换行，次级 proof 明细在窄屏首屏隐藏，步骤栏保持横向紧凑，保证四个主按钮在 `390x844` 首屏可见。
- 修正 Diagnostics 点击流程：`/api/diagnostics` payload 不再覆盖首屏 status/command safety，避免支持入口把 ACK 文案回退成默认 copy。
- 更新 HTTP/static focused tests，固定 raw status 隐藏、Diagnostics 不覆盖 status、当前 command safety boundary 的静态围栏。
- 更新 `docs/product/mobile_user_flow.md`，记录本地 phone browser acceptance gate 的命令、验收点和证据边界。

## 验收结果

### Browser acceptance

```text
viewport=390x844 hit_area_status=passed overlap_status=passed overflow_status=passed ack_copy_visible=true diagnostics_accessible=true primary_actions_disabled=true first_screen_buttons_visible=true phone_safe_status=passed evidence_boundary=software_proof_docker_phone_browser_acceptance_gate evidence_json=sprints/2026.05.12_15-16_phone-browser-acceptance-gate/evidence/phone_browser_390x844.json screenshot=sprints/2026.05.12_15-16_phone-browser-acceptance-gate/evidence/phone_browser_390x844.png
viewport=768x900 hit_area_status=passed overlap_status=passed overflow_status=passed ack_copy_visible=true diagnostics_accessible=true primary_actions_disabled=true first_screen_buttons_visible=true phone_safe_status=passed evidence_boundary=software_proof_docker_phone_browser_acceptance_gate evidence_json=sprints/2026.05.12_15-16_phone-browser-acceptance-gate/evidence/phone_browser_768x900.json screenshot=sprints/2026.05.12_15-16_phone-browser-acceptance-gate/evidence/phone_browser_768x900.png
summary=sprints/2026.05.12_15-16_phone-browser-acceptance-gate/evidence/phone_browser_acceptance_summary.json ok=true evidence_boundary=software_proof_docker_phone_browser_acceptance_gate
```

Evidence files:

- `sprints/2026.05.12_15-16_phone-browser-acceptance-gate/evidence/phone_browser_390x844.json`
- `sprints/2026.05.12_15-16_phone-browser-acceptance-gate/evidence/phone_browser_390x844.png`
- `sprints/2026.05.12_15-16_phone-browser-acceptance-gate/evidence/phone_browser_768x900.json`
- `sprints/2026.05.12_15-16_phone-browser-acceptance-gate/evidence/phone_browser_768x900.png`
- `sprints/2026.05.12_15-16_phone-browser-acceptance-gate/evidence/phone_browser_acceptance_summary.json`

### Targeted unittest

```bash
python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py src/ros2_trashbot_behavior/test/test_operator_gateway_static.py
```

```text
Ran 73 tests in 17.910s

OK
```

### Compile fence

```bash
python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
```

Result: exit code `0`.

### Scoped diff check

```bash
git diff --check -- src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py src/ros2_trashbot_behavior/test/test_operator_gateway_static.py scripts/phone_browser_acceptance_gate.py docs/product/mobile_user_flow.md docs/interfaces/ros_contracts.md sprints/2026.05.12_15-16_phone-browser-acceptance-gate/tech-done.md
```

Result: exit code `0`.

## 失败定位与修复

- 首次 browser gate 运行时，两个 viewport 均显示 `ack_copy_visible=false`；hit area、overlap、Diagnostics 和 primary disabled 已通过。
- 根因：Diagnostics 点击复用通用 `api()`，把 `/api/diagnostics` payload 当成 status 渲染，导致 `commandSafetyAck` 回退到默认文案。
- 修复：`api(path, options, updateStatus = true)` 支持 Diagnostics 请求不刷新 status；`diagnostics()` 改为 `api('/api/diagnostics', {}, false)` 后再 `showDiagnostics(payload)`。
- 视觉复核发现 `390x844` 下长 boundary 文案横向裁切，且主按钮不在首屏；修复移动 CSS，并把 gate 加严到 `overflow_status=passed` 与 `first_screen_buttons_visible=true`。
- 复跑 browser gate 后两个 viewport 均输出 `ack_copy_visible=true`、`overflow_status=passed`、`first_screen_buttons_visible=true`。

## 剩余风险

- 本轮只证明 Docker/local browser software proof，不证明真实手机设备、正式 app、真实云/4G、OSS/CDN 实流量、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。
