# O7 Full-stack live route 用户动作回执 - PRD

## 1. 产品问题

O7 已有本地 operator dropoff/browser、loopback relay、O6/O7 readback 等 software proof，但这些路径已消费并退役；
当前仍缺一个与真实上位机交互的用户动作 receipt。另一方面，Algorithm/Hardware owner 最近都在业务文件或命令前
runtime stall，继续从它们入口重派会重复消费 blocker。

本需求选择不同业务 owner 和不同证据类别：由 `full-stack-software-engineer` 直接复用 workstation 的既有核心
Nav2 execute proxy，让用户动作携带稳定 `task_id` 并获得 live/fail-closed 回执。不得新建 review/handoff/preflight
endpoint，也不得把 mock 测试输出当现场动作。

## 2. 用户故事

作为现场 operator，我在已看护、路线清空、物理范围受限且 CEO 已授权的条件下，希望通过 PC 固定入口只发起一次
指定路线目标；无论真实上位机执行、拒绝还是超时，我都能拿到带 task/run/route/action identity 的动作回执，并能
立即 stop。这样 Product 可以判断本轮是否真的出现 `user_action_delta`，而不是再次阅读“已准备执行”。

## 3. OKR 映射和方向判断

- O5 `85%`：暂停。provider/runtime blocker 已消费 `2/2`，本 sprint 不触达。
- O7 `93%`：继续并调整抓手到 live 用户动作 receipt；这是主 Objective。
- O6 `93%`：仅在同一 `task_id` 的 live receipt 可读时获得 supporting evidence，不新加 archive/readback wrapper。
- O1 `94%`：仅在同窗口出现真实 robot control/route/feedback/stop 事实时辅助评估，不由 Full-stack 声称 HIL。
- Mission Objective 0：planning 阶段仍暂停；只有 current-run user action 或更强 live delta 才重新评估。
- KR 历史归档：本阶段无完成 KR，不归档；证据留在本 sprint，最终由 Product 决定当前区/历史区变化。

## 4. 范围内需求

### R1 - 扩展既有 execute contract，不新增 endpoint

`POST /api/robot-control/nav2/goal/execute` 请求/响应增加安全字符串字段：`task_id`、`run_id`、
`route_intent_id`、`authorization_ref`、`action_id`。所有字段必须长度受限、去除控制字符，且不能改变 goal clamp、
base URL allowlist、危险 true field guard 或 remote fixed path。

响应增加 `user_action_receipt`，至少保留：schema、五个 identity、received time、fixed workstation/remote endpoint、
proxy status、remote HTTP status、request forwarded、robot control executed、terminal/result status 安全摘要、blocked reasons、
stop required，以及 fail-closed boundary。`execution_forwarded`、`execution_rejected`、`execution_failed` 三条路径都必须有
receipt；不得回显 credential、SSH host、绝对远端路径或完整 raw payload。

### R2 - exactly one live/fail-closed 用户动作

通过本地 workstation API 连接真实 `http://192.168.1.11:8787`，使用既有 28-pose route identity 与 fixed goal
`map (0.8, 0.25, 0)` 发送 exactly one request。保存：pre-action summary、request manifest、raw action receipt、
latest/terminal readback、base feedback readback、post-action summary 和 stop receipt。任何 live 失败都 no retry。

### R3 - stop 与诚实证明边界

动作完成、失败、超时或连接不确定后，最多调用一次既有 workstation base stop endpoint。Receipt 可以证明“用户已
发起动作且系统给出结果”，不能单独证明路线成功、HIL、safe-to-control 或 delivery。Mock 只用于单元测试与 hostile
matrix；live 失败后不得用 mock artifact 替换现场 artifact。

### R4 - 文档和留档

更新 `docs/product/pc_tools_workstation.md`，说明 identity/receipt/stop rule 与 proof boundary；Engineer 更新本 sprint
`tech-done.md`。Product 验收后才补 `side2side_check.md`、`final.md`，并按业务 delta 决定是否更新 OKR/progress log。

## 5. 非目标

- 不新增 route/readback/export/browser/handoff/preflight wrapper。
- 不修改上车 `upper_robot_api.py`、ROS2/Algorithm/Hardware/UART/launch/firmware。
- 不发送第二个 goal，不改目标，不发 manual/free-roam/direct `/cmd_vel`/`/initialpose`。
- 不把 `execution_forwarded` 自动等同于 `route_execution_success`，不把 goal succeeded 自动等同于 delivery。
- 不做 O5 provider/cloud、camera、localization bag、Algorithm/Hardware canary。

## 6. 验收口径

1. Contract tests 证明五个 identity 在 success/reject/timeout/unsafe response 中均稳定、受限且 fail closed；固定 remote path
   未改变，mock/fixture 固定标识为测试。
2. Workstation `npm run test && npm run build && npm run lint` 全部通过，新增技术注释全部为中文且修改范围注释比例
   `>20%`。
3. Live artifact 中 execute invocation count 必须为 `1`、task/run/route/auth/action identity 完整一致；mock fallback
   invocation count 必须为 `0`。
4. stop invocation count 必须 `<=1` 且记录结果；本地 API process cleanup clean。
5. 如果 live forwarded：保存 remote HTTP、terminal/latest、base feedback 与 post summary；只有源事实明确满足时才记录
   route/HIL 字段，否则保持 false/not proven。
6. 如果 live rejected/failed：保存精确 failure/blocked reason 与 fail-closed receipt，`robot_control_executed=false`（除非
   remote 明确返回 true 且 Product 单独审计）、route/delivery/HIL/safe-to-control 不得升级，且 no retry。

## 7. 风险与缺失证据

- 真实上位机 8787 runtime、当前 localization/Nav2/controller、轮速反馈和目标区域地图事实可能已变化；本 sprint 允许
  它们阻断并诚实收口，不允许补第二次动作。
- Full-stack receipt 不能替代 Hardware 对 vendor `T=1001` 的 HIL 判读，也不能替代 Algorithm 对 Nav2 terminal 的领域
  归因；Product 只消费上游明确字段。
- 既有 28-pose route 来自 2026-07-13，可能与当前 pose/map 不同。PC 仍会读取 current summary；若 operator 或 current
  WYSIWYG 认为不安全，stop rule 立即生效，动作不得重试。
