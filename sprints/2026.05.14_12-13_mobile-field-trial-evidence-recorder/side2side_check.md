# Sprint 2026.05.14_12-13 Mobile Field Trial Evidence Recorder - Side2Side Check

sprint_type: epic

## 验收结论

本轮 Product 验收通过，证据边界必须保持为 `software_proof_docker_mobile_real_device_field_trial_evidence_record_gate`。

用户价值和产品北极星：现场人员现在可以在 `mobile/web` 首屏填写、展示、复制、归档“现场证据记录”，把 real device、production app、PWA install prompt、user choice、offline、touch、visual、material redaction、operator note、support note 变成结构化 phone-safe material。北极星仍是让普通手机用户链路逐步接近真实验收，但所有本轮产物都不能越界成控制放行或 delivery success。

## OKR 映射和 KR 判断

- Objective 4：本轮直接推进 O4 KR5/KR7，从“现场试跑执行清单”推进到可填写、可展示、可复制、可归档的现场证据记录入口。Product 判断可从约 88% 谨慎上调到约 89%。
- Objective 5：仍是最低约 68%，但没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或其他真实外部材料，不上调。
- Objective 1/2/3：本轮未改 WAVE ROVER、HIL、Nav2/fixed-route、`task_orchestrator` 或真实送达证据，不调整。

## Side-by-Side 核对

| 计划要求 | 实际结果 | Product 判断 |
| --- | --- | --- |
| 首屏“现场证据记录”入口 | Task A 新增并覆盖 `mobile_real_device_field_trial_evidence_record*` record/summary/copy/archive | 通过 |
| 字段覆盖现场材料 | 覆盖 real device、production app、PWA install prompt、user choice、offline、touch、visual、material redaction、operator note、support note | 通过 |
| whitelist-only copy/archive | 固定 `safe_to_control=false`、`accepted_processing_only_not_delivery_success`、`not_proven`，过滤敏感和内部字段 | 通过 |
| 不改变控制语义 | 未改变 `/api/collect`、`/api/dropoff/confirm`、`/api/cancel` 控制语义 | 通过 |
| Robot metadata-only fence | Task B 证明 `_record`、`_summary`、`_copy`、`_archive` 不触发 command、ACK、cursor、terminal、production readiness、HIL 或 delivery success | 通过 |
| mixed valid-command | 只执行 `trashbot.remote.v1` envelope，metadata 不改变 action、target、idempotency、ACK 或 cursor | 通过 |
| 文档同步 | `mobile/README.md`、`docs/product/mobile_user_flow.md`、`docs/interfaces/ros_contracts.md` 已由 A/B worker 更新；本次同步 OKR 和 progress log | 通过 |

## 验收证据

Task A Full-stack：

```text
python3 -m unittest mobile.test_mobile_web_entrypoint
Ran 32 tests in 0.042s
OK
py_compile pass
node --check mobile/web/app.js pass
required rg pass
scoped git diff --check pass
```

Task B Robot：

```text
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_bridge onboard.src.ros2_trashbot_behavior.test.test_remote_bridge_protocol
Ran 169 tests in 86.466s
OK
注：有一个既有 ResourceWarning。
py_compile pass
required rg pass
scoped git diff --check pass
```

## 不算完成的事项

本轮不是以下证据：真实手机验收、production app 验收、真实 PWA prompt/user choice、公网 TLS/4G/OSS/CDN/DB/queue、WAVE ROVER、HIL、dropoff/cancel completion 或 delivery success。ACK、HTTP accepted、copy package、archive package 和 evidence record 仍只是 accepted/processing/support metadata。

## 责任 Engineer

- User Touchpoint Full-Stack Engineer：Task A 已完成。
- Robot Platform Engineer：Task B 已完成。
- Product Manager / OKR Owner：完成本次阶段验收、OKR 口径和 sprint closeout。
