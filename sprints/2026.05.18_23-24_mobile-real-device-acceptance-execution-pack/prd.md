# Sprint 2026.05.18_23-24 Mobile Real Device Acceptance Execution Pack - PRD

## 1. 用户价值和产品北极星

产品北极星仍是：让普通手机用户不接触命令行、ROS2、串口、云凭证或硬件调试，也能把垃圾交给小车并理解任务状态、异常和下一步处理。

本轮用户价值不是证明真实手机验收通过，而是把上一轮“现场验收复核交接”进一步变成现场 owner 可执行的执行包。现场人员可以按 checklist 采集真实 iPhone/Android / production app / PWA prompt/user choice 材料，知道哪些内容要打码、如何复跑、哪些证据必须保持同一 safe `evidence_ref`，以及哪些结果仍然不能打开主操作。

## 2. OKR 映射

- Objective 4：本轮主目标。补齐真实手机验收执行包、手机只读展示、Robot diagnostics safe alias 和产品/接口文档，使 O4 真机材料链可以从 handoff 进入执行。
- Objective 5：不推进。当前缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover 和 external proof。
- Objective 1：不推进。当前缺真实 WAVE ROVER/UART/HIL、真实底盘反馈、真实 2D LiDAR / ToF 材料和 PR #5 要求的 vendor/source 证据。
- Objective 2 / Objective 3：不推进真实完成度。PR #4 route/elevator 后续需要真实现场材料，本轮手机执行包不证明真实电梯、真实 Nav2/fixed-route、投放或 delivery success。

## 3. KR 拆解

- KR-A：从 `mobile_real_device_field_trial_acceptance_review_handoff*` 生成 `mobile_real_device_field_trial_acceptance_execution_pack*` summary / copy / fixture，字段至少包括 owner checklist、evidence capture steps、redaction requirements、rerun commands、`next_required_evidence` 和 safe copy。
- KR-B：mobile/web 新增只读 execution pack panel，只展示现场执行材料和安全边界，不启用 Start Delivery、Confirm Dropoff、Cancel 或任何控制类主操作。
- KR-C：Robot diagnostics 新增 safe alias，向 operator / support 暴露相同的 execution pack 摘要，并保留 `source=software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。
- KR-D：产品文档和接口文档同步说明执行包字段、证据来源、打码要求、复跑命令和不证明事项。
- KR-E：Product closeout 在 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md` 中保守收口，若没有真实手机材料，不上调真实验收或 delivery success。

## 4. 本轮核心抓手

把“下一步要真实手机材料”从口头建议变成可执行包：

1. 现场 owner 打开手机 panel 或 diagnostics safe alias。
2. 按 checklist 完成真实设备、production app / PWA prompt、用户选择、截图/录屏和日志采集。
3. 按 redaction requirements 遮盖 token、公网域名敏感路径、用户隐私和设备标识。
4. 按 rerun commands 复跑同一 `evidence_ref` 的本地校验或后续 intake。
5. 由下一轮 review decision 判断是否进入真实验收材料回填，或继续 `not_proven`。

## 5. 范围边界

### In Scope

- `mobile_real_device_field_trial_acceptance_execution_pack*` fixture / summary / copy。
- mobile/web 只读 panel。
- Robot diagnostics safe alias。
- `docs/product/mobile_user_flow.md` 和 `docs/interfaces/ros_contracts.md` 同步。
- 当前 sprint 的实现、验收和收口文档。
- `OKR.md` 与 `docs/process/okr_progress_log.md` 的保守收口更新。

### Out of Scope

- 不新增真实硬件配置，不修改 WAVE ROVER、UART、传感器或 bringup 硬件参数。
- 不证明真实手机、真实 PWA prompt/user choice、production app 通过。
- 不证明真实 route/elevator field pass、Nav2/fixed-route、dropoff/cancel completion、delivery success 或 HIL。
- 不推进 O5 公网 HTTPS/TLS、4G/SIM、OSS/CDN、production DB/queue 或 worker/cutover。
- 不新增大测试堆，只跑围栏验证。

## 6. 优先级和验收口径

- P0：所有安全字段和文案必须 fail-closed，包含 `source=software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- P0：mobile/web 和 Robot diagnostics 展示的 execution pack 字段一致，且不暴露 raw JSON、ROS topic、串口、云密钥或控制入口。
- P1：现场 owner checklist、evidence capture steps、redaction requirements、rerun commands、`next_required_evidence` 可直接执行。
- P1：产品文档和接口文档同步更新，不让 docs 滞后于实现。
- P2：Product closeout 明确本轮验证范围和剩余风险，不把 local software proof 写成真实材料。

## 7. 对应责任 Engineer

- Full-stack 主责：mobile/web、fixture、前端测试、产品文档。
- Robot 主责：diagnostics safe alias、Robot 测试、接口文档。
- Product 主责：sprint closeout、OKR/progress log、证据边界。
- Hardware 只读补充：PR #5 2D LiDAR / ToF 材料缺口事实核对。

## 8. 风险、阻塞和证据链

- 证据链风险：执行包只能降低真实手机验收采集成本，不能替代真实现场材料。
- 安全风险：任何 copy 若暗示可控、已通过、已投放或 delivery success，都必须修正。
- PR #5 风险：2D LiDAR / ToF 的 SKU/source/receipt/installation/wiring/power/calibration/HIL-entry 仍缺，不能被手机执行包覆盖。
- PR #4 风险：电梯 assisted delivery 的真实 route/elevator materials 仍缺，不能被手机执行包覆盖。
- O5 风险：Docker-only 主机没有公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/cutover。

## 9. 需要创建或更新的 sprint 文档

- 已创建：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 实现后必须更新：`tech-done.md`。
- 验收后必须更新：`side2side_check.md`。
- 收口后必须更新：`final.md`。

