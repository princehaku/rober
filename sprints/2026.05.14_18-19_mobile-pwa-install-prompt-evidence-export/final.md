# Sprint 2026.05.14_18-19 Mobile PWA Install Prompt Evidence Export - Final

sprint_type: epic

## 收口结论

本 sprint 完成 `software_proof_docker_mobile_pwa_install_prompt_evidence_export_gate`。手机端已把 PWA install prompt 事件/证据链推进到可复制、可下载、phone-safe、whitelist-only 的现场验收材料导出；Robot 侧已补 metadata-only compatibility fence，证明该材料 family 不会触发控制、ACK、cursor、readiness、HIL 或 delivery result。

Objective 4 从约 94% 谨慎上调到约 95%。Objective 5 保持约 68%，因为本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或其他真实外部 O5 证据。

## 实际改动

Task A `full-stack-software-engineer`：

- `mobile/web/app.js`
- `mobile/web/index.html`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/test_mobile_web_entrypoint.py`
- `mobile/README.md`
- `docs/product/mobile_user_flow.md`
- `sprints/2026.05.14_18-19_mobile-pwa-install-prompt-evidence-export/evidence/task_a_mobile_pwa_install_prompt_evidence_export.md`

Task B `robot-software-engineer`：

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`

Task C `product-okr-owner`：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.14_18-19_mobile-pwa-install-prompt-evidence-export/tech-done.md`
- `sprints/2026.05.14_18-19_mobile-pwa-install-prompt-evidence-export/side2side_check.md`
- `sprints/2026.05.14_18-19_mobile-pwa-install-prompt-evidence-export/final.md`

## 验证结果

- Task A：`mobile.test_mobile_web_entrypoint` Ran 35 tests OK；`py_compile` OK；`node --check mobile/web/app.js` OK；required `rg` OK；scoped `git diff --check` OK。
- Task B：targeted remote bridge/protocol unittest Ran 191 tests OK；`py_compile` OK；required `rg` OK；scoped `git diff --check` OK。
- Task C：required `rg` 与 scoped `git diff --check` 已执行，输出见最终聊天汇总。

## 阶段验收

通过。P0 验收项均满足：

- export/copy/download material 保持 whitelist-only。
- `safe_to_control=false`、`accepted_processing_only_not_delivery_success`、`not_proven` 均保留。
- Start Delivery、Confirm Dropoff、Cancel 继续 fail closed。
- Robot fence 证明 export metadata-only 不触发 robot control 或 delivery result。
- `docs/product/mobile_user_flow.md` 和 `docs/interfaces/ros_contracts.md` 已由对应 worker 同步。

## OKR 与风险

本轮直接服务 Objective 4 KR5/KR7：普通用户和现场验收人员不需要开发者工具即可获得可复测的手机端验收材料，同时不会把材料导出误写成真实验收通过或控制授权。

Objective 5 仍是数字最低 Objective，但本轮 stop rule 继续成立：缺真实外部材料时，不再堆 O5 local metadata。下一轮若拿不到真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration 证据，应继续转向 Objective 4 的真实手机设备/production app/真实 PWA prompt 现场验收，而不是上调 Objective 5。

剩余风险：

- 真实 iPhone/Android device behavior、production app、真实 PWA prompt/userChoice 仍未现场验证。
- Objective 5 external proof 仍缺。
- Nav2/fixed-route、WAVE ROVER、HIL、dropoff/cancel completion、delivery success 仍未完成。
