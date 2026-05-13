# Sprint 2026.05.14_07-08 Mobile Real Device Retest Request Gate - Side2Side Check

## Sprint 类型

- sprint_type: epic
- 对照对象：`software_proof_docker_mobile_real_device_retest_request_gate`
- 验收结论：通过，证据边界为 Docker/local mobile software proof + Robot metadata-only fence。

## 用户价值和产品北极星

产品北极星仍是让普通手机用户完成低成本 trash delivery 主路径，而不是让用户理解 ROS2、命令行或硬件调试。本轮的实际用户价值是把上一轮 review execution 的 blocked reason、next evidence request、evidence readiness、operator/reviewer notes、redaction/source boundary 和 `not_proven`，转成下一轮真实设备复测可执行的 retest request package。

该 package 的价值是让验收人员知道下一轮真实手机/production app/PWA prompt/user choice 要补什么、谁负责、下一步动作是什么，以及哪些证据仍然 not_proven；它不是验收通过或 delivery success。

## OKR 映射

- Objective 4 KR5/KR7：通过 retest request checklist/package，让真实设备验收从 review execution 推进到可执行复测材料请求。
- Objective 4 当前从约 83% 谨慎上调到约 84%。
- Objective 5 当前仍是最低 Objective，约 68%，但本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration 外部材料，不能上调。
- Objective 1/2/3 本轮未获得硬件、导航、任务状态机、HIL、Nav2/fixed-route 或真实 delivery 证据，不调整。

## 验收对照

| 验收项 | 结果 | 证据 |
| --- | --- | --- |
| retest request panel/package 已从 review execution 派生 | 通过 | Task A 新增 `mobile_real_device_retest_request*`，覆盖 retest checklist、missing evidence、owner/next action、blocked/rejection reason、redaction/source boundary、ACK 和 `not_proven`。 |
| phone-safe copy whitelist | 通过 | Task A 明确 copy package 只含复测入口、材料摘要、owner、next action、blocked/rejected reason、redaction/source boundary、ACK semantics、evidence boundary 和 `not_proven` 等安全字段。 |
| Start/Confirm/Cancel fail closed | 通过 | Task A 保持缺真实设备材料、production app、真实 PWA install prompt/user choice 或 Objective 5 外部材料时主操作 fail closed。 |
| Robot metadata-only fence | 通过 | Task B 证明 `mobile_real_device_retest_request*` metadata-only response 不触发 collect/dropoff/cancel、ACK、cursor、terminal ACK、production readiness、HIL、dropoff/cancel completion 或 delivery success。 |
| Valid command mixed metadata fence | 通过 | Task B 证明 valid command mixed metadata 只执行 command envelope，retest request metadata 不进入 normalized command、ACK、status、cursor 或 terminal result。 |
| 文档同步 | 通过 | Task A 同步 `mobile/README.md`、`docs/product/mobile_user_flow.md`；Task B 同步 `docs/interfaces/ros_contracts.md`；Task C 同步 `OKR.md`、`docs/process/okr_progress_log.md` 和本 sprint closeout。 |

## Objective 5 最低但不选的回顾

本轮 `tech-plan.md` 的理由仍成立：Objective 5 约 68%，低于 Objective 4，但本机只有 Docker，没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或真实外部 O5 材料。继续做 O5 metadata depth 会重复消费同一外部证据 blocker，无法把 Objective 5 从约 68% 推到真实外部 proof。

因此本轮转向 Objective 4 的真实设备复测请求包是合理的：它不声称真实设备通过，只把已有 review execution 转成下一轮真实设备复测的材料请求和缺口清单。

## 未证明项

- 未证明真实手机设备或真实 iPhone/Android device behavior。
- 未证明 production app。
- 未证明真实 PWA install prompt/user choice。
- 未证明真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 production worker/migration。
- 未证明 Nav2/fixed-route、WAVE ROVER、真实串口、HIL、真实 dropoff/cancel completion 或真实 delivery。
- `retest request`、ACK、HTTP accepted、receipt、review execution package 和 retest request package 都只是 accepted/processing/support metadata，不是 delivery success。

## 验收结论

`software_proof_docker_mobile_real_device_retest_request_gate` 成立。Objective 4 可谨慎上调到约 84%；Objective 5 因缺真实外部材料保持约 68%；Objective 1/2/3 不调整。
