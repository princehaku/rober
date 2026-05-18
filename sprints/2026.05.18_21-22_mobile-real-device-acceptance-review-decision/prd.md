# Sprint 2026.05.18_21-22 Mobile Real Device Acceptance Review Decision - PRD

## 1. 用户价值

普通用户最终需要真实手机入口可用，而不是桌面浏览器 proof。当前链路已经能生成真实设备现场验收会话，但缺少“验收会话之后怎么判定下一步”的 phone-safe review decision。这个缺口会让材料到了现场后仍停留在会话包，无法明确是补材料、交给 reviewer、还是继续阻塞。

本轮用户价值是把真实手机材料链路往前推进一格：让手机端和支持人员能看到 acceptance session 的评审结论、缺什么材料、谁接手、下一步补什么，同时保持主操作按钮不放行。

## 2. OKR 映射

- Objective 4 KR7：手机端 UI 可直接使用，真实设备验收材料链路继续前移。
- Objective 4 KR5：普通用户不接触命令行，也能知道失败时该怎么做。
- Objective 5 不推进：本轮不证明公网 HTTPS/TLS、4G/SIM、OSS/CDN、production DB/queue 或 external proof。

## 3. 功能需求

新增 `mobile_real_device_field_trial_acceptance_review_decision*`：

- 输入优先级：explicit review decision → `mobile_real_device_field_trial_acceptance_session*` → blocked-by-design fallback。
- 输出字段：review decision、session status、source priority、blocked items、next required evidence、owner handoff、safe evidence reference、safe copy、evidence boundary、`not_proven`。
- 决策枚举至少包括：
  - `blocked_missing_acceptance_session`
  - `blocked_missing_real_device_acceptance_materials`
  - `blocked_unsafe_or_unredacted_acceptance_materials`
  - `ready_for_manual_acceptance_review_not_control`
- 所有 copy/export 只能包含 phone-safe whitelist 字段。

## 4. 非目标

- 不新增真实手机证据。
- 不打开 Start Delivery、Confirm Dropoff 或 Cancel。
- 不把 ACK、HTTP accepted、会话包、review decision 写成 delivery success。
- 不修改 route/elevator、hardware、cloud 或 ROS2 behavior 逻辑。

## 5. 验收标准

- `mobile/web/app.js` 能渲染 review decision panel。
- fixture 包含 `mobile_real_device_field_trial_acceptance_review_decision*` 示例。
- targeted mobile unittest 覆盖新 panel 的边界文字、schema、`safe_to_control=false` 与 not-proven copy。
- 文档同步说明功能边界。
