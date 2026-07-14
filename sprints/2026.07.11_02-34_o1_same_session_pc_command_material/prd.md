# O1 Same-Session PC Command Material PRD

## 用户价值

用户最终需要一台普通手机用户也能信任的垃圾投递机器人。O1 的底盘控制层必须能解释“PC 端是否真的发起过同会话低速点动、上位机是否记录过同会话轮速材料、后续 base status 是否还能读到反馈”，而不是只给出孤立 artifact。

## 需求

新增 `same_session_pc_command_material`，把同一 `2026.06.22_11-00` session 的 PC first-jog proxy 与 after-jog base status readback 接入 O1 motion-map HIL bundle：

- PC proxy command material：`02_pc_first_jog_samesession_timeoutfix.json`
- after-jog base status readback：`03_base_status_after_pc_jog.json`
- 现有 upper manual material：`01_upper_manual_samesession_012.json` 继续保留上一轮语义

## OKR 映射

- Objective 1：打通官方硬件协议，建立可信底盘控制层。
- 本轮不归档 KR；若实现和验证通过，可作为 O1 historical same-session PC command material delta 的保守增量候选。
- O5 仍是最低项，但本轮不继续 O5 support-only readiness，因为缺真实 production external evidence。

## 验收标准

- Bundle 输出 `same_session_pc_command_material_present=true` 与 `same_session_pc_command_material_status=same_session_pc_command_material_ready_not_hil_pass`。
- 输出 PC command 摘要：direction、speed、duration、checklist、captured evidence status。
- 输出 remote motion key value 摘要：`wheel_feedback_lr_nonzero_material_present=true`、nonzero frame count、latest left/right speed、manual/feedback/auto-stop flags。
- 输出 after-jog readback 摘要：T1001 observed、latest base status wheel L/R zero、feedback samples latest stale/readback context。
- Negative tests 覆盖 dangerous true、unsafe consumed strings、remote key mismatch、after-jog readback schema mismatch。
- 文档同步说明 vendor 来源、proof boundary 和 remaining current live HIL gaps。

## 不做范围

- 不改 WAVE ROVER command 行为、UART、launch 参数、ROS topic/service。
- 不连接真实硬件，不发送新 motion command。
- 不把 historical material 写成 current live HIL、safe-to-control、delivery success 或 route execution success。
