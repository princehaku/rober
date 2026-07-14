# PRD - O3 Map Server LoadMap Return Code Probe

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_17-55_o3_map_server_loadmap_return_code_probe/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Target objective: O3/O1 strict no-motion field lane
- Product status: ready for implementation

## 1. 用户价值和产品北极星

用户最终只关心小车能否可靠沿固定路线送垃圾。要进入这条用户价值链，真实上位机必须先完成 `/map_server` lifecycle clean/active，之后才有 `/map`、AMCL、dynamic TF、planner-only path generation、Nav2 route execution、delivery/operator acceptance 的证据链。

本 PRD 的产品目标不是再写一个 blocker 标签，而是把 16:55 的 `map_server_on_configure_return_false_after_valid_map_io_deferred_completion` 推进到可修复的 return code / call path，或直接修到 `/map_server active`。

## 2. OKR 映射和方向判断

方向判断：继续 O3/O1 strict no-motion field lane，暂停 O5 support-only。

- O5 约 `85%`：最低进度项，但当前缺真实 external production evidence。没有 HTTPS/TLS、公网入口、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser evidence 时，继续 O5 support-only 不计主进度。
- O1 约 `93%`：仍缺 current same-run path generation success 与 Nav2 route execution success。本轮解除 `/map_server` lifecycle blocker，是 O1 当前缺口的上游工作。
- O3 现场验证 lane：本轮只作为 strict no-motion supporting evidence，不恢复已归档 KR，不声明路线能力完成。
- O6/O7 约 `93%`：等待 live route execution、delivery/operator 或 production readback，本轮不推进。

本轮不调整 OKR 百分比，不归档 KR。只有出现 `/map_server active` 并推进到同 run path/route evidence，后续 Product closeout 才能评估是否形成 OKR 增量。

## 3. KR 拆解、更新或历史归档

当前 KR 处理：

- 不归档任何 KR。
- 不把 O3 临时现场验证 lane 恢复为已完成 Objective。
- 不把 fail-closed proof、readback、wrapper、status panel 或 review 当成 KR 完成。

本轮可新增的证据类别：

- `/map_server active=true` 的 strict no-motion live proof；或
- `loadMapResponseFromYaml` return code / error string / response status proof；或
- 比 `map_server_on_configure_return_false_after_valid_map_io_deferred_completion` 更窄的 `on_configure` return path、参数、异常、executor/log ordering 或 lifecycle manager ChangeState response handling root cause。

## 4. Problem Statement

16:55 sprint 已接受的事实是：

- `/map_server` configure callback 已进入。
- managed map YAML/PGM readable，`map_input_validation.valid_for_map_server=true`。
- 没有 map_server-scoped exception。
- 没有 service/RPC timeout。
- lifecycle manager 收到 ChangeState failure/false 后，map IO completion log 才出现。
- `/map_server active=false`。

这仍不足以让 Algorithm 介入路径生成，因为 blocker 仍停在 lifecycle 上游。下一步必须回答：`loadMapResponseFromYaml` 的具体返回码或错误是什么，`on_configure` 哪条 return path 触发了 failure，以及 lifecycle manager 的 ChangeState response 是否真实反映 callback 结果。

## 5. In Scope

- 读取并分析 Nav2 map_server configure/runtime log。
- 检查 helper/proof/parser 是否能提取 `loadMapResponseFromYaml` return code、error string、response status 或 equivalent evidence。
- 对 `on_configure` return path、callback exception、parameter validation、map response assembly、executor/log ordering 和 lifecycle manager ChangeState response handling 建立更窄分类。
- 在 strict no-motion 条件下修复或证明 `/map_server active`。
- 更新相关 helper/proof/parser/tests/docs 和 sprint `tech-done.md`。

## 6. Out of Scope

- O5 production readiness、cloud cutover、real browser/mobile external evidence。
- `/cmd_vel`、`/api/base/manual`、NavigateToPose、WAVE ROVER UART。
- Algorithm path generation、route execution、SLAM、keyframe、rosbag、route.csv，除非 `/map_server` lifecycle 已 clean/active。
- Hardware serial/runtime/wiring 修改；只有 LiDAR serial/runtime/wiring 成为 primary root cause 时才另开 Hardware 工作，并先读 `docs/vendor/VENDOR_INDEX.md`。
- UI/API surface、handoff、review-only、status panel。

## 7. Acceptance Criteria

P0 验收必须满足以下之一：

- 成功证明 `/map_server active=true`，并保持 strict no-motion；或
- 若仍 blocked，输出比 16:55 更窄的 primary root cause，至少落到 `loadMapResponseFromYaml` return code / error string / response status、`on_configure` return path、参数、异常、executor/log ordering 或 lifecycle manager ChangeState response handling 之一。

硬性失败条件：

- 只重复 `map_server_on_configure_return_false_after_valid_map_io_deferred_completion`，没有新增字段、返回码、代码路径、参数、异常或时序解释。
- 没有 true-board 或同等 strict no-motion artifact，也没有明确说明真实板不可达原因。
- 发布 `/cmd_vel`、调用 `/api/base/manual`、发送 NavigateToPose 或打开 WAVE ROVER UART。
- 把 support-only proof 包装成 route execution、delivery、HIL、safe-to-control 或 production evidence。

## 8. Priority and Owner

- Priority: P0
- Owner: `robot-software-engineer`
- Consult only if needed: `robot-algorithm-engineer` after `/map_server active`; `rober-hardware-engineer` only if LiDAR serial/runtime/wiring becomes primary and vendor docs are read.

## 9. Risks, Blockers, Evidence Chain

主要风险：

- Nav2 map_server 源码或 runtime instrumentation 不直接暴露 `loadMapResponseFromYaml` return code，需要先扩展 proof 字段或解析日志。
- map IO completion log 可能晚于 lifecycle failure，必须区分真实 failure 和日志排序问题。
- runtime log 可能混有 LiDAR serial/runtime 背景噪声，但本轮不能在未成为 primary root cause 前转硬件。
- 如果只加分类不加修复，Product 只接受“比 16:55 更窄”的 root cause，不接受同名 blocker 重复消费。

仍缺证据链：

- `/map_server active`
- `/map` sample
- AMCL active and pose observed
- dynamic `map->odom`
- planner-only path generation
- same-run route execution
- delivery/operator acceptance
- current live HIL
- production external evidence

## 10. Required Sprint Documents

当前必须创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

工程完成后必须补：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
