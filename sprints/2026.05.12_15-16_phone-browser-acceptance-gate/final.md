# Sprint 2026.05.12_15-16 Phone Browser Acceptance Gate - Final

## 状态

- 阶段：final
- Product Owner：`product-okr-owner`
- 主责 Engineer：`full-stack-software-engineer`
- 收口时间：2026-05-12 15:16 Asia/Shanghai
- 最终结论：O5 phone browser acceptance gate 已按 `software_proof_docker_phone_browser_acceptance_gate` 收口

## 用户价值和产品北极星

用户价值：普通 operator 用手机宽度浏览器访问本地 fallback 页面时，能在首屏看到当前状态、主操作按钮、ACK 语义和 Diagnostics 入口；阻断状态下主操作保持 disabled，降低误触发和误解 ACK 的风险。

产品北极星：手机是普通用户唯一入口。本轮没有把 fallback HTML 包装成正式 app，而是把它纳入真实浏览器验收，为后续真实手机设备、正式远程入口和普通用户验收打下可复查基础。

## OKR 映射和 KR 更新

- O5 KR1：手机端最小流程从 API/handler proof 推进到真实浏览器首屏 proof。
- O5 KR5：ACK copy、阻断原因和 Diagnostics 入口可被普通用户在首屏理解。
- O5 KR7：`390x844` 与 `768x900` viewport 均证明 44px hit area、首屏主按钮可见、无重叠、无溢出。
- O6 KR6：本轮只复用 phone-safe command/recovery 语义作为 UI 背景，不改变 O6 完成度。

OKR 更新：`OKR.md` 中 O5 从约 40% 保守上调到约 43%；O6 保持约 41%；O1-O4 不提升。

## 本轮核心抓手

核心抓手是用本地真实 Chrome 跑 browser acceptance gate，而不是只验证 HTML 字符串或 API payload。该 gate 产出了结构化 JSON、summary artifact 和两张 screenshot，使 Product 可以对照 KR7 做收口。

## 实际证据

Browser gate 两组 viewport 均通过：

```text
viewport=390x844 hit_area_status=passed overlap_status=passed overflow_status=passed ack_copy_visible=true diagnostics_accessible=true primary_actions_disabled=true first_screen_buttons_visible=true phone_safe_status=passed evidence_boundary=software_proof_docker_phone_browser_acceptance_gate
viewport=768x900 hit_area_status=passed overlap_status=passed overflow_status=passed ack_copy_visible=true diagnostics_accessible=true primary_actions_disabled=true first_screen_buttons_visible=true phone_safe_status=passed evidence_boundary=software_proof_docker_phone_browser_acceptance_gate
summary=sprints/2026.05.12_15-16_phone-browser-acceptance-gate/evidence/phone_browser_acceptance_summary.json ok=true
```

Evidence artifacts：

- `sprints/2026.05.12_15-16_phone-browser-acceptance-gate/evidence/phone_browser_acceptance_summary.json`
- `sprints/2026.05.12_15-16_phone-browser-acceptance-gate/evidence/phone_browser_390x844.png`
- `sprints/2026.05.12_15-16_phone-browser-acceptance-gate/evidence/phone_browser_390x844.json`
- `sprints/2026.05.12_15-16_phone-browser-acceptance-gate/evidence/phone_browser_768x900.png`
- `sprints/2026.05.12_15-16_phone-browser-acceptance-gate/evidence/phone_browser_768x900.json`

Full-stack 验证：

```text
Ran 73 tests in 17.910s
OK
py_compile: exit 0
scoped git diff --check: exit 0
```

## 失败定位和修复确认

首次 browser proof 暴露 Diagnostics 覆盖 status panel 并导致 ACK copy 回退；视觉复核还发现移动端长文案裁切和按钮不在首屏。Full-stack 已修复为 `/api/diagnostics` fetch 不刷新 status，并调整移动端 CSS。复跑后两组 viewport 的 ACK、overflow、first-screen button 和 disabled action 检查均通过。

## 责任 Engineer

- `full-stack-software-engineer`：完成实现、browser gate、targeted tests、py_compile、scoped diff check、`docs/product/mobile_user_flow.md` 和 `tech-done.md`。
- `product-okr-owner`：完成 Product acceptance、`side2side_check.md`、`final.md` 和 `OKR.md` 更新。

## 剩余风险

- 没有真实手机设备 Safari/Chrome、正式 app 或普通用户实机验收。
- 没有真实云/4G、HTTPS/TLS、公网入口、OSS/CDN 实流量、生产 DB/queue 或生产账号流程。
- 没有 Nav2/fixed-route 真实送达、WAVE ROVER、真实串口、HIL 或真实垃圾送达。
- 本轮证据仅可用于 O5 KR7 的本地 browser software proof，不能用于提升 O1-O4 或声明 O6 真实云完成。

## 下一步建议

O5 下一步应进入真实设备验收：使用至少一台 iPhone Safari 和一台 Android Chrome 对同一 acceptance checklist 做真机截图/录屏，并继续保持 ACK 不等于送达成功、Diagnostics 不解锁主操作的边界。
