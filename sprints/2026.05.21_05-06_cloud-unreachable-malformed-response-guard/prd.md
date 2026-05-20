# Cloud Unreachable Malformed Response Guard PRD

## 用户价值和产品北极星

产品北极星是普通手机用户把垃圾交给低成本 ROS2 小车后，可以通过手机理解任务状态、异常原因和下一步行动，而不接触 ROS2、SSH、串口、云服务日志或硬件调试。`cloud_unreachable_malformed_response_guard` 的用户价值是：当云端不可达或返回畸形响应时，Robot/API 与 `mobile/web` 明确禁用主操作、显示安全文案、保留诊断入口，避免把通信失败写成送达成功。

本 sprint 只做 Docker/local software proof。它不是真实 external cloud proof，不是真实手机/browser proof，不提升 Objective 5 百分比。

## OKR 映射

- Objective 5：当前最低，约 68%。本 sprint 针对 O5 的本地 fail-closed 缺口，但不提高百分比；O5 提升仍需真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或 true phone/browser 证据。
- Objective 1：约 81%。PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved/material pending，本 sprint 不消费该 blocker，也不新增硬件 wrapper。
- Objective 2/3/4：约 99%。本 sprint 不证明 route/elevator field pass、Nav2/fixed-route、真实手机验收、dropoff/cancel completion 或 delivery success。

## KR 拆解或更新

- KR-A：Robot/API 能把 `cloud_unreachable` 和 `malformed_response` 标准化为 fail-closed status/diagnostics summary，保留 `remote_ready=false`、`primary_actions_enabled=false`、`delivery_success=false`。
- KR-B：Robot/API summary 使用 `software_proof_docker_cloud_unreachable_malformed_response_guard`，并明确 ACK 语义为 communication failure / malformed response not delivery success。
- KR-C：`mobile/web` 能读取该 summary，显示中文安全文案、恢复建议和诊断入口，同时保持 Start Delivery、Confirm Dropoff、Cancel 禁用。
- KR-D：文档同步 `docs/product/mobile_user_flow.md` 与 `docs/product/remote_4g_mvp.md`，说明这两个状态不是 external proof、不是 phone proof、不是 delivery success。
- KR-E：验证围栏覆盖 Robot focused unittest、mobile focused unittest、fixture schema/redaction check、required `rg` 和 scoped `git diff --check`。

## 本轮核心抓手

核心抓手是把两个已被产品流程点名但未形成同级 guard 的通信失败状态补齐：

- `cloud_unreachable`：云端无法访问、超时或连接失败时，不能让手机继续发主操作，也不能把旧状态当完成。
- `malformed_response`：云端响应不是可消费的安全 JSON contract 时，不能猜测结果、不能自动重放、不能把解析失败写成 ACK 或送达成功。

## 需要做什么

1. Robot Platform Engineer 定义并实现 `cloud_unreachable_malformed_response_guard` 的 status/diagnostics safe summary。
2. Robot Platform Engineer 增加 focused unit tests，验证不可达和畸形响应都 fail closed，且不泄露 credentials、raw response、traceback、ROS topics、`/cmd_vel` 或硬件细节。
3. User Touchpoint Full-Stack Engineer 在 `mobile/web` 增加或扩展 cloud readiness rendering，展示两个状态的安全文案和 recovery hint。
4. User Touchpoint Full-Stack Engineer 更新 fixture/test，证明主操作禁用、诊断可见、不会自动重试/重放/请求 ACK/cursor。
5. Engineers 同步相关 `docs/product/` 文档；Product closeout 只在实现后补 `tech-done.md`、`side2side_check.md`、`final.md`，并保持 OKR 保守。

## 优先级和验收口径

Priority P0:

- `cloud_unreachable` 和 `malformed_response` 都必须显示为 not delivery success。
- Start Delivery、Confirm Dropoff、Cancel 必须 fail closed。
- Diagnostics / support handoff 可以保持可见，但不得触发 robot command、ACK、cursor、retry、resubmit 或 raw diagnostics fetch。
- Phone copy 必须中文优先，告诉用户云端暂不可用或响应格式异常，并建议刷新状态或联系支持，而不是继续发车。
- Safe summary 必须包含 `software_proof_docker_cloud_unreachable_malformed_response_guard`、`remote_ready=false`、`primary_actions_enabled=false`、`delivery_success=false`、`not_proven`。

验收口径：

- Robot 和 Full-Stack 的 scoped verification commands 通过。
- Required `rg` 能命中 `cloud_unreachable_malformed_response_guard`、`cloud_unreachable`、`malformed_response`、`software_proof_docker_cloud_unreachable_malformed_response_guard`、`delivery_success=false`、`primary_actions_enabled=false`。
- Product closeout 不提升 Objective 5，除非后续出现真实 external cloud/phone evidence。

## 对应责任 Engineer

- Robot Platform Engineer：Robot/API guard summary、diagnostics contract、focused Python tests、runtime contract docs。
- User Touchpoint Full-Stack Engineer：`mobile/web` rendering、fixture、focused mobile tests、phone user-flow docs。
- Product Manager / OKR Owner：planning docs now; implementation后验收证据、sprint closeout、保守 OKR 边界。

## 风险、阻塞和需要补齐的证据链

- O5 blocker：缺真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、true phone/browser proof。
- Cloud proof boundary：Docker/local unreachable/malformed fixture 只能证明 fail-closed software behavior，不证明公网、TLS、4G、云可用性或生产队列。
- Phone proof boundary：local `mobile/web` test 不是真实 iPhone/Android、production app、PWA prompt/userChoice 或 field acceptance。
- Delivery proof boundary：通信失败处理不证明 Nav2/fixed-route、WAVE ROVER/UART、HIL、dropoff/cancel completion、delivery result 或 delivery success。
- PR #5 boundary：`PRRT_kwDOSWB9286CJ3tX` 仍 unresolved/material pending，本 sprint 不处理、不消费、不关闭该线程。

## 需要创建或更新的 sprint 文档

- Created in planning: `pre_start.md`, `prd.md`, `tech-plan.md`.
- Required after implementation: `tech-done.md`, `side2side_check.md`, `final.md`.
