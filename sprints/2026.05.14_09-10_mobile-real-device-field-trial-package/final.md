# Sprint 2026.05.14_09-10 Mobile Real Device Field Trial Package - Final

## 收口结论

- sprint_type: epic
- 本轮完成：`software_proof_docker_mobile_real_device_field_trial_package_gate`
- OKR 调整：Objective 4 从约 85% 保守上调到约 86%；Objective 5 保持约 68%；Objective 1/2/3 不调整。

## 用户价值和产品北极星

手机仍是普通用户唯一入口。本轮把真实设备验收材料链从“复测请求 / browser proof”推进到“真实设备现场试跑包”：现场人员可以在 `mobile/web` 首屏记录 runtime metadata 和人工 observation fields，并复制一份 phone-safe package 给支持/验收链路。

这不是愿景交付，也不是 happy path 完成；它只补齐真实 iPhone/Android 或 production app 现场试跑前的材料收集入口，避免把 ACK、HTTP accepted、package copy 或 metadata-only response 写成真实送达。

## Task A/B 结果

- Task A Full-stack：更新 `mobile/web/index.html`、`mobile/web/app.js`、`mobile/web/styles.css`、`mobile/test_mobile_web_entrypoint.py`、`mobile/README.md`、`docs/product/mobile_user_flow.md`；新增“真实设备现场试跑包”panel，采集 phone-safe runtime metadata 和人工 observation fields，生成/复制 `mobile_real_device_field_trial_package*`。验证 `mobile.test_mobile_web_entrypoint` 29 tests OK；`py_compile`、`node --check mobile/web/app.js`、boundary/schema/copy/ACK/not_proven/中文标题 `rg` 与 scoped diff check 均通过。
- Task B Robot：更新 `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`、`onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`、`docs/interfaces/ros_contracts.md`；新增 `mobile_real_device_field_trial_package*` protocol normalization fences、worker metadata-only fences 与 mixed valid-command coverage。验证 `Ran 157 tests in 80.820s OK`；`py_compile`、`rg` 与 scoped diff check 均通过。

## 首次失败和修复

- Task A/B closeout 报告未留下需要 Product 继续追踪的未修复失败；两条执行链路的最终验证均通过。
- 本轮 Product closeout 不修改工程代码或测试，只同步 sprint closeout、OKR 快照和 OKR progress log。

## OKR 最低优先级回顾

Objective 5 仍是当前最低 Objective（约 68%）。本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或其他真实外部 O5 材料；当前 Docker-only host 也无法提供这些真实外部材料。因此继续 O5 本地 metadata depth 不能提升 completion，按 stop rule 本轮转向 Objective 4 的真实设备现场试跑材料入口，并保持 Objective 5 不调整。

## 证据边界和剩余风险

- `software_proof_docker_mobile_real_device_field_trial_package_gate` 只证明 Docker/local `mobile/web` 可以生成 phone-safe field trial package，且 Robot metadata-only fence 不把该 metadata 当成 command、ACK、cursor、terminal result、production readiness、HIL 或 delivery proof。
- `not_proven` 仍包括真实手机设备、真实 iPhone/Android device behavior、production app、真实 PWA install prompt/user choice、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration、Nav2/fixed-route、WAVE ROVER、HIL、真实 dropoff/cancel completion 和真实 delivery。
- 真实设备现场试跑包、browser proof、ACK、HTTP accepted、receipt、intake package、acceptance decision package、review handoff package、review execution package、retest request package、handoff session 和 install prompt evidence 仍只是 accepted/processing/support metadata，不是 delivery success。

## 下一步

下一轮优先按 `OKR.md` 4.1 重新排序。若仍拿不到 Objective 5 的真实外部材料，继续推进 Objective 4 的真实 iPhone/Android device behavior、production app、真实 PWA install prompt/user choice 或主路径真实移动设备验收；若拿到 O5 外部材料，再回到公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration evidence。
