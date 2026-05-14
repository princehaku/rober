# Sprint 2026.05.14_12-13 Mobile Field Trial Evidence Recorder - Final

sprint_type: epic

## 收口结论

本 sprint 完成 Objective 4 的现场证据记录软件证明。`mobile/web` 已从“现场试跑执行清单”推进到可填写、展示、复制、归档的“现场证据记录”入口，并由 Robot metadata-only fence 证明该 family 不触发控制、ACK、cursor、terminal、production readiness、HIL、dropoff/cancel completion 或 delivery success。

证据边界严格为 `software_proof_docker_mobile_real_device_field_trial_evidence_record_gate`。这不是真实手机验收、production app、真实 PWA install prompt/user choice、公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、WAVE ROVER、HIL、dropoff/cancel completion 或 delivery success。

## 用户价值和产品北极星

用户价值：现场试跑人员可以把 real device、production app、PWA install prompt、user choice、offline、touch、visual、material redaction、operator note、support note 记录成 phone-safe package，减少材料遗漏和返工。

产品北极星：手机端继续靠近普通用户真实验收链路，但 Docker/local 和人工记录产物必须保持 `safe_to_control=false`、`ack_semantics=accepted_processing_only_not_delivery_success`、`not_proven`、whitelist-only copy/archive 和 Robot metadata-only 边界。

## OKR 映射和 KR 更新

- Objective 4：从约 88% 谨慎上调到约 89%。理由是本轮把现场试跑材料链从 checklist 推进到结构化 evidence record，并补齐 copy/archive 与 Robot metadata-only fence。
- Objective 5：保持约 68%，仍是最低 Objective。本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或其他真实外部材料，因此不上调。
- Objective 1/2/3：本轮没有真实硬件、导航、任务闭环或 HIL 新证据，不调整。

## 本轮核心抓手

统一 family：

- `mobile_real_device_field_trial_evidence_record`
- `mobile_real_device_field_trial_evidence_record_summary`
- `mobile_real_device_field_trial_evidence_record_copy`
- `mobile_real_device_field_trial_evidence_record_archive`

统一边界：

- `software_proof_docker_mobile_real_device_field_trial_evidence_record_gate`

## 实际改动

Task A Full-stack 改动：

- `mobile/web/index.html`
- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/test_mobile_web_entrypoint.py`
- `mobile/README.md`
- `docs/product/mobile_user_flow.md`

Task B Robot 改动：

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`

Product closeout 改动：

- `sprints/2026.05.14_12-13_mobile-field-trial-evidence-recorder/tech-done.md`
- `sprints/2026.05.14_12-13_mobile-field-trial-evidence-recorder/side2side_check.md`
- `sprints/2026.05.14_12-13_mobile-field-trial-evidence-recorder/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## 验收口径和验证结果

Full-stack 验证：

```text
python3 -m unittest mobile.test_mobile_web_entrypoint
Ran 32 tests in 0.042s
OK
py_compile pass
node --check mobile/web/app.js pass
required rg pass
scoped git diff --check pass
```

Robot 验证：

```text
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_bridge onboard.src.ros2_trashbot_behavior.test.test_remote_bridge_protocol
Ran 169 tests in 86.466s
OK
注：有一个既有 ResourceWarning。
py_compile pass
required rg pass
scoped git diff --check pass
```

Product closeout 验证结果记录在本轮最终回复中；验收范围仅覆盖指定 closeout 文件、OKR 口径、progress log 和 required rg/diff checks。

## 风险、阻塞和证据链

- Objective 5 仍是最低约 68%，但缺真实外部材料；继续 O5 本地 metadata 不应上调 O5。
- 本轮 evidence record 仍不能证明真实 iPhone/Android device behavior、production app、真实 PWA install prompt/user choice、公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、WAVE ROVER、HIL、dropoff/cancel completion 或 delivery success。
- ACK、HTTP accepted、copy/archive package、field observation 和 evidence record 只能作为 accepted/processing/support metadata。
- 下一步若仍无 O5 外部材料，应继续围绕 Objective 4 做真实手机/production app/PWA prompt/user choice 的实际材料采集；若拿到 O5 外部材料，再回到 Objective 5 completion。

## Sprint 文档状态

- `pre_start.md`、`prd.md`、`tech-plan.md` 已存在。
- `tech-done.md`、`side2side_check.md`、`final.md` 已补齐。
- `OKR.md` 与 `docs/process/okr_progress_log.md` 已同步本轮 closeout 口径。
