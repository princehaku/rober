# Sprint 2026.05.14_11-12 Mobile Field Trial Runbook Execution Gate - Side2Side Check

## 验收对照

| 验收项 | 结果 | 证据 |
| --- | --- | --- |
| 首屏新增“现场试跑执行清单”panel | 通过 | `mobile/web/index.html` 包含 panel、readiness、open items、checklist、copy 区域。 |
| 新 family 完全一致 | 通过 | A/B/C 文档与测试均使用 `mobile_real_device_field_trial_runbook_execution`、`mobile_real_device_field_trial_runbook_execution_summary`、`mobile_real_device_field_trial_runbook_execution_copy`。 |
| evidence boundary 完全一致 | 通过 | 统一使用 `software_proof_docker_mobile_real_device_field_trial_runbook_execution_gate`。 |
| Copy package whitelist-only | 通过 | Task A 静态围栏覆盖 `safe_to_control=false`、`accepted_processing_only_not_delivery_success`、`not_proven` 和敏感字段禁止项。 |
| Robot metadata-only fence | 通过 | Task B targeted tests 覆盖 metadata-only response 与 mixed valid-command；runbook execution metadata 不触发 command、ACK、cursor、terminal ACK、production readiness、HIL、dropoff/cancel completion 或 delivery success。 |
| docs 同步 | 通过 | `mobile/README.md`、`docs/product/mobile_user_flow.md`、`docs/interfaces/ros_contracts.md` 已更新。 |
| OKR 口径 | 通过 | Objective 4 谨慎上调到约 88%；Objective 5 保持约 68%；Objective 1/2/3 不调整。 |

## 用户价值核对

本轮把上一轮“现场试跑证据复核”推进为“现场试跑执行清单”：现场人员可以按 real device、production app、PWA install prompt、user choice、offline、touch、visual、material redaction 八项执行和记录，而不是只复核已有材料。该清单仍是 phone-safe support metadata，不能被解释为真实验收通过或控制放行。

## 边界核对

- `safe_to_control=false` 保留。
- ACK 语义保持 `accepted_processing_only_not_delivery_success`。
- `not_proven` 保留真实手机、production app、真实 PWA install prompt/user choice、真实云/4G、OSS/CDN live traffic、production DB/queue、WAVE ROVER、HIL、dropoff/cancel completion 和 delivery success。
- Start Delivery、Confirm Dropoff、Cancel 仍由既有 command safety、readiness、operation log、action feedback 等 gate 控制；runbook execution package 不新增控制权限。

## 结论

本 sprint 验收通过，证据边界是 Docker/local mobile software proof + robot metadata-only fence。它推动 Objective 4 的现场试跑准备质量，但不提升 Objective 5，也不证明真实硬件、真实云、真实手机或真实送达。
