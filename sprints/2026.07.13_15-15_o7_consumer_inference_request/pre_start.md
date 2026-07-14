# Pre Start - O7 Consumer Inference Request

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_15-15_o7_consumer_inference_request/`
- Created at: 2026-07-13 15:15 CST
- Product owner: `product-okr-owner`
- Implementation owner: `full-stack-software-engineer`
- Planning status: ready for implementation dispatch

## User Value And Product North Star

用户价值：PC operator 在选中一个 O6/O7 consumer task 后，可以从同一任务详情发起一次本地/模拟模型推理请求，让 `evidence_ref`、`input_id` 和 `requested_outputs` 进入 O6 archive 的 `model_inference.*` event timeline，并立刻拿到可读、安全、不可外推的 receipt。这样 operator 不再只看已有材料，也能在本机回环链路内完成一次 `request -> O6 write -> receipt/readback boundary` 的软件闭环。

产品北极星仍是普通用户送垃圾闭环，但本轮只推进 PC 运营调试和数据训练平台上的任务证据消费能力：让 O7 能驱动 O6-KR5 local/mock inference write path，而不是重复展示 query/readback wrapper。

## Recent Evidence And Blocker Scan

- O5 当前仍是最低 Objective，约 `85%`。上一轮 `sprints/2026.07.13_13-13_o5_cdn_tls_external_evidence_probe/` 已关闭在 `blocked_http_status_not_success_class`，没有 success-class endpoint 或更强 production evidence 时，继续做 CDN/TLS/support-only wrapper 会重复消费同一 blocker。
- O1/O3 最近已经完成 stop path readiness、mock stop HIL gate、controlled route execution gate 和 bounded route command plan；没有 explicit operator approval、current live HIL/stop path、同窗口 LiDAR localization TF readiness 与 Nav2 controller result 时，不能再包装 readiness 或 no-motion plan。
- O6/O7 约 `93%`，刚完成 label filters、archive task filters 和 O7 consumer query filters。下一步如果继续 O7，必须是新的 action/write path，而不是 query/readback-only wrapper。

## Direction Decision

- OKR 方向判断：继续 O6-KR5 / O7 用户触点方向，但本轮不调整主百分比。
- 不直接推进 O5 的理由：O5 最低但当前可行动作依赖成功 HTTP class 或更强 production/cloud evidence；本轮没有新 endpoint 成功证据，重复 O5 会产生同类 blocked wrapper。
- 本轮核心抓手：在 O7 PC consumer-read primary path 增加 `consumer inference` local/mock request action，调用 O6 `POST /api/o6/archive/inference`。
- KR 归档判断：本轮 planning 阶段和后续实现即使通过，也只证明 local/mock software proof；KR `不归档`。

## Scope Guardrails

本 sprint 只允许 planning 阶段创建：

- `sprints/2026.07.13_15-15_o7_consumer_inference_request/pre_start.md`
- `sprints/2026.07.13_15-15_o7_consumer_inference_request/prd.md`
- `sprints/2026.07.13_15-15_o7_consumer_inference_request/tech-plan.md`

后续 implementation 由 `full-stack-software-engineer` 单线闭环。Product planning 阶段不修改产品代码、测试代码、`OKR.md`、`docs/process/okr_progress_log.md`、历史 sprint、硬件/ROS2/nav 文件，也不生成 closeout docs。

## Required Evidence Chain

后续实现验收必须证明：

- O7 UI/API 可以基于 selected task 组装安全 inference request。
- PC adapter 只允许本机回环 `baseUrl`，并 fail-closed 拒绝危险字段、未知字段、credential、URL/path/raw-like content 和危险 true claim。
- O7 调用 O6 `POST /api/o6/archive/inference` 后，O6 response schema 是 `trashbot.o6.model_inference.v1`，source 是 `local_mock_inference`，且 archive event written。
- O7 返回 `trashbot.pc_tools_workstation.o7_consumer_inference_request_result.v1` 或等价安全 receipt，包含 selected task、inference id、input ids、requested outputs、created/updated/duplicate summary、proof boundary 和 fixed false fields。
- 固定边界：`safe_to_control=false`、`delivery_success=false`、`robot_control_executed=false`、`primary_actions_enabled=false`、`connects_cloud_production=false`。

## Risks

- 这不证明真实模型、真实 GPU、真实外部推理 API、真实电梯门识别、真实楼层识别、production cloud、route execution、delivery、HIL 或 safe-to-control。
- 如果 O6 task 不存在、task unauthorized、input 时间窗不合法或 payload unsafe，O7 必须返回 fail-closed receipt，不得写入 O6 store。
- 需要同步更新 O7 interface 和 PC product docs，避免 UI 行为超过 local/mock 证据边界。
