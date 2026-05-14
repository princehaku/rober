# Sprint 2026.05.14_14-15 Mobile Field Trial Retest Execution Gate - PRD

sprint_type: epic

## 用户价值

上轮 verdict 已经能指出缺失材料和下一步 retest/material request，但现场支持人员仍缺一个手机端结果页来记录“复测是否执行、材料是否收到、哪些项仍缺、下一轮动作是什么”。本轮把复测请求推进到复测执行结果包，减少 Product/Support 在聊天和散落截图里人工对账。

## OKR 映射

- 主目标：Objective 4 手机用户体验与低成本量产边界。
- 背景目标：Objective 5 仍最低约 68%，但当前没有真实外部云/4G/OSS/CDN/DB/queue 材料，不能继续本地 O5 metadata depth。
- 非目标：Objective 1/2/3 的硬件、Nav2/fixed-route、真实 delivery 或 HIL。

## 功能需求

1. 手机首屏新增“现场复测执行结果”panel。
2. Panel 能从 `mobile_real_device_field_trial_evidence_verdict*` 的 `retest_request` / `material_request` 派生，或消费后端提供的同名 family。
3. 新增 family：
   - `mobile_real_device_field_trial_retest_execution`
   - `mobile_real_device_field_trial_retest_execution_summary`
   - `mobile_real_device_field_trial_retest_execution_copy`
4. Summary 至少包含：
   - `retest_status`
   - `material_status`
   - `still_missing_evidence`
   - `next_action`
   - `safe_to_control=false`
   - `ack_semantics=accepted_processing_only_not_delivery_success`
   - `evidence_boundary=software_proof_docker_mobile_real_device_field_trial_retest_execution_gate`
   - `not_proven`
5. Copy package 必须 whitelist-only，不包含 token、Authorization、OSS AK/SK、DB/queue URL、credential-bearing URL、raw ROS topic、`/cmd_vel`、serial/UART、baudrate、WAVE ROVER、local path、traceback、checksum、完整 artifact、raw robot response、raw verdict payload 或机器人内部字段。
6. Robot 侧必须证明该 family 是 metadata-only：不能触发 collect/dropoff/cancel command、ACK POST、cursor advance/persistence、terminal ACK、production readiness、HIL、dropoff/cancel completion 或 delivery success。

## 验收标准

- Full-stack static smoke 能看到新 panel、schema、boundary、copy package、fail-closed 文案和 whitelist copy。
- Robot compatibility fence 能证明 `mobile_real_device_field_trial_retest_execution*` family 是 metadata-only。
- `docs/product/mobile_user_flow.md`、`mobile/README.md`、`docs/interfaces/ros_contracts.md` 同步说明边界。
- Sprint closeout 更新 `OKR.md` 和 `docs/process/okr_progress_log.md`，不把本轮软件证明冒充真实手机或 O5 外部 proof。

## 非目标

- 不接入真实 iPhone/Android device behavior。
- 不声明 production app readiness。
- 不声明真实 PWA install prompt / user choice。
- 不改 `/api/collect`、`/api/dropoff/confirm`、`/api/cancel` 控制语义。
- 不改硬件、Nav2/fixed-route、cloud production runtime、DB/queue、OSS/CDN 或真实 HIL。
