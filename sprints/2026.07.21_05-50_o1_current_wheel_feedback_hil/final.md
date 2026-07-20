# Final：O1 当前轮速反馈 HIL Product Closeout

## 收口结论

- `PRODUCT_CLOSEOUT=ACCEPT_REAL_ATTEMPT_HIL_FAIL_CLOSED_FINAL_STOP_PROVEN`
- 状态：`closed_consumed_no_retry_hil_failed_final_stop_proven`
- authorization：`ceo_20260721_0651_current_wheel_feedback_hil_v8=consumed_no_retry`
- counts：`pre/nonzero/post/retry=1/1/1/0`
- proof boundary：`real_live_control_attempt_bridge_debug_serial_derived_wheel_feedback_nonzero_failed_final_stop_proven_not_safe_or_mission`

Product 接受本轮真实 live-control 与 external artifact delta，也接受 dedicated stop 后的 final stopped；拒绝 wheel feedback HIL pass、安全准入、路线执行、送达与 Mission Objective 0。真实 attempt 只改变证据类别，不自动改变完成百分比。

## 最终事实

- Phase0 为 GO；唯一 nonzero 请求通过 frozen stdin curl 发送，exit `0`，forward=`0.08m/s`、duration=`300ms`、retry=`0`。
- Upper `/cmd_vel` 发布 `6` 个非零 frames；bridge 同窗记录 `6` 帧 `T=11 L=164 R=164 sent=true`。
- during-motion 的 raw-UART-derived `T=1001` 同窗三对全部 `L/R=0/0`，因此 `speedGetA/speedGetB` nonzero 未证明，`hil_pass=false`。
- dedicated stop curl exit `0`；post-stop `T=1001 L/R=0/0`，final bridge command=`T=11 L=0 R=0 sent=true`，且无 8787 established connection，故 Product 接受 final stopped。
- source class=`bridge_debug_serial_derived`，不是 raw serial byte dump；`T=13 wire not proven`。未直接发出或观察 `T=130`，实际使用 continuous `T=131` flow，因此 direct `T=130 request not proven`。
- `safe_to_control=false`、`route_execution_success=false`、`delivery_success=false`、`mission_objective_0_satisfied=false`。

## OKR、KR 与方向判断

- O1 保持约 95%，方向调整为暂停同参数现场重采，先做无运动根因诊断。
- O5 保持约 85%，provider/runtime blocker `2/2` 继续暂停。
- O6/O7 各保持约 93%，未获得 route、delivery 或 production credit。
- KR `不归档`，没有完成、取消、替换或过期项移入历史区。

## 失败定位、anti-repeat 与下一唯一入口

失败发生在控制发送之后、反馈语义之前：Upper 和 bridge 已证明 nonzero command path，但 `T=1001` 中由 `speedGetA/speedGetB` 提供的反馈仍为 `0/0`。v8 永久封存；禁止再以相同 `0.08m/s / 300ms minimal jog + readback` 重采、补采、retry 或包装成新 evidence sprint。

下一唯一入口是 non-motion / offline / maintenance diagnostics：由 Hardware 定位 encoder、`mainType`、firmware、`speedGetA/speedGetB` 与 bridge 采样/解析链的根因。若诊断需要修改 service、UART、firmware，必须另立 maintenance lane 并取得维护授权；若需要再次运动，必须另立 motion lane 并取得新的 bounded-motion 授权。

## 范围与发布检查

Product 本轮只做离线证据核对与文档收口；未执行 SSH、HTTP、ROS、串口、control、stop、nonzero 或其他 live 命令。未修改历史 sprint、产品代码、测试、hardware docs、`06-20`、`06-45` 或其他范围外 dirty WIP；未 commit/push。

## Late-writer docs sync reconciliation

Hardware 在首次 Product closeout 后只更新了 `docs/hardware/wave_rover_nonzero_feedback_hil_gate.md` 与本 sprint `tech-done.md`。Product 已只读核对 late-writer diff：hardware 文档准确补充 offline gate 与 v8 live evidence 的加法关系、`bridge_debug_serial_derived` 非 raw serial byte dump 边界、exact slice 退役以及 non-motion/offline/maintenance diagnostics 入口；`tech-done.md` 同步记录 docs sync 未执行任何 live 命令。两处均未改变既有 artifact、计数或结论。

Reconciliation 接受：保持 `PRODUCT_CLOSEOUT=ACCEPT_REAL_ATTEMPT_HIL_FAIL_CLOSED_FINAL_STOP_PROVEN`；v8 保持 `consumed_no_retry` 并永久封存；`hil_pass=false`、`safe_to_control=false`、route/delivery/Mission Objective 0 均不变。O1/O5/O6/O7 完成度保持 flat，KR `不归档`。本次 reconciliation 只修改当前 `final.md`，未执行 live 命令、未修改范围外文件、未 commit/push。
