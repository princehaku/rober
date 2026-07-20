# Side-to-side Product 验收

- `PRODUCT_CLOSEOUT=ACCEPT_REAL_ATTEMPT_HIL_FAIL_CLOSED_FINAL_STOP_PROVEN`
- Product owner：`product-okr-owner`
- authorization：`ceo_20260721_0651_current_wheel_feedback_hil_v8=consumed_no_retry`
- evidence source class：`bridge_debug_serial_derived`，不是 raw serial byte dump

## 合同与实际对照

| 合同 | 实际证据 | Product 判定 |
|---|---|---|
| Phase0 全绿后才允许非零 | unique owner、service/health、stopped、no active hold、feedback path、operator、路线清空、物理限位、emergency stop 均为 true，`PHASE0_PASS=true` | 接受 Phase0 GO |
| pre/nonzero/post/retry | `1/1/1/0`，唯一 live window，无第二次 nonzero | 接受 exactly-once / no-retry |
| 唯一 nonzero `<=0.08m/s, <=300ms` | stdin `curl --data-binary @-` exit `0`，`0.08m/s`、`300ms` | 接受真实 live-control attempt |
| Upper `/cmd_vel` | subscriber count `1`，非零 burst `6` frames | 接受 Upper transport artifact |
| bridge 非零命令 | 同窗 `6` 帧 `T=11 L=164 R=164 sent=true` | 接受 bridge command delta；不外推轮速 |
| during-motion `T=1001 L/R != 0` | raw-UART-derived 同窗 `3` 对全部 `0/0` | **拒绝 wheel feedback nonzero；`hil_pass=false`** |
| dedicated stop | stop curl exit `0`；post-stop `T=1001 L/R=0/0`；final `T=11 L=0 R=0 sent=true`；无 8787 established connection | 接受 final stopped |
| wire 请求边界 | `T=13 wire not proven`；direct `T=130 request not proven`，实际为 continuous `T=131` feedback flow | 保持未证明 |
| 产品闭环 | `safe_to_control=false`、`route_execution_success=false`、`delivery_success=false` | 全部拒绝 |

## Product acceptance

接受本轮 `live_control_delta=true` 与 `external_artifact_delta=true`：这是一次真实、受控、可审计且失败后关闭的 O1 HIL attempt，并有独立 final stop 证据。`current_run_artifact_delta=true` 仅表示本 sprint 的新现场 artifact，不表示成功。

拒绝 `hil_pass`、`safe_to_control`、route/delivery 与 Mission Objective 0。`T=11` 非零发送与 `/cmd_vel` 六帧不能覆盖 `T=1001 L/R=0/0` 的直接失败事实；bridge debug 解析自串口也不能冒充 byte-for-byte raw serial capture。

## OKR / KR 与 anti-repeat

- O1 保持约 95%；真实 attempt 不因“发生过”自动加分，current wheel feedback HIL 仍未闭环。
- O5 保持约 85%，provider/runtime blocker `2/2` 继续暂停；O6/O7 各保持约 93%。
- KR `不归档`，历史区无新增完成项。
- v8 永久封存为 `consumed_no_retry`；禁止再以相同 `0.08m/s / 300ms minimal jog + readback` 重采或消费同一 blocker。

## 失败定位与下一唯一入口

失败点在唯一 nonzero 已发送之后：Upper 已 publish、bridge 已记录 `T=11` nonzero，但 `T=1001` 中来自 `speedGetA/speedGetB` 的左右轮速仍全部为零。下一唯一入口是 non-motion / offline / maintenance diagnostics，定位 encoder、`mainType`、firmware 与 bridge 反馈采样链；若需要修改 service、UART、firmware 或再次运动，必须另立清晰 lane 并取得对应维护或运动授权。
