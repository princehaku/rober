# O1 最小轮动 frozen artifact 封存审核

- `sprint_type: micro`
- owner: `robot-hardware-engineer`
- target: Objective 1（可信底盘控制层）
- audit_mode: `offline_read_only_frozen_artifacts`
- authorization_ref: `ceo_20260721_0154_minimal_wheel_jog_v6`
- authorization_status: `consumed_no_retry`

## 实际动作

本次只读审核 `artifacts/hardware/` 中已冻结的 live window，未产生新的网络、ROS、串口或控制请求。冻结证据记录的原 live 动作为：初始 gate 因历史非零命令不 clean 后，经固定 proxy 执行 1 次 corrective pre-stop；随后仅执行 1 次非零 `forward / 0.08 m/s / 300 ms` first-jog，请求内部记录 1 次 auto-stop；最后执行 1 次显式 post-stop。`nonzero_request_count=1`、`retry_count=0`，exactly-one 合同满足。

本次新增文件仅为本 `tech-done.md`；未修改 artifacts、产品代码、测试、vendor 文档、OKR、progress 或其他 sprint。

## Vendor 来源与采用事实

按要求依次复核：

1. `docs/vendor/VENDOR_INDEX.md`
2. `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
3. `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
4. `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`
5. `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`

采用的 vendor 事实：UART 上位机参考使用 UTF-8 newline-delimited JSON；`T=13` 是 `CMD_ROS_CTRL`，字段 `X/Z` 分别表示 m/s、rad/s；`T=11` 是直接 PWM `L/R`；`T=130` 进入 `baseInfoFeedback()`；反馈 `T=1001` 的同帧 `L/R` 来自 `speedGetA/speedGetB`，`r/p/y` 来自 IMU 姿态，`v` 来自电压。

## 可接受的 current live 结论

- **current live-control transport signal：接受。** first-jog proxy 返回 `HTTP 200`、`proxy_status=command_forwarded`、`manual_command_executed=true`、`auto_stop_executed=true`；同窗 bridge debug 的最新已发送非零命令为 `T=11,L=164,R=164`，`linear_x=0.08`，transport 为 HTTP。它证明 live 非零控制请求到达现有 bridge 并被记录为已发送。
- **exactly-once / no-retry：接受。** `pre_stop_request_count=1`、`nonzero_request_count=1`、`post_stop_request_count=1`、`upper_internal_auto_stop_count=1`、`retry_count=0`；授权已由唯一 first-jog transport attempt 消费，禁止重试或复用。
- **same-window motion signal：限界接受。** first-jog 窗口内读取到 80 帧 `T=1001`，roll 最大变化 `1.218602°`、pitch 最大变化 `0.479262°`，均有超过 `0.35°` 阈值的变化，因此可接受 `motion_signal_observed=true`、source=`imu_attitude_delta`。这只是间接运动信号，不证明轮子实际转动方向、位移、里程计或可重复运动性能。
- **stop command path/current stopped control state：接受。** first-jog 内部 auto-stop 与显式 post-stop 均返回成功；最终 bridge 最新命令为 `T=11,L=0,R=0` 且 `sent=true`，最终 Nav2 为 `lifecycle_running=false`、`lifecycle_state=stopped`，未观察到 active goal/manual hold。这证明停止命令路径和最终命令状态，不等同于停止后的实测轮速归零。

注意：顶层安全 envelope 保持 `robot_control_executed=false`，而嵌套 `bridge_command_debug.robot_control_executed=true` 仅表达 bridge 已发送命令。二者不得合并成 HIL/安全准入结论；本审核只接受上述窄化的 live-control transport signal。

## 不可接受或尚未证明

- **非零 T=1001 轮速反馈：未证明。** 80 帧同帧 `T=1001 L/R` 的 `nonzero_frame_count=0`，`wheel_feedback_lr_nonzero_proven=false`，最新与全部可见 pair 均为 `0/0`。
- **直接 T=130 request/ACK：未证明。** artifact 的请求合同写有 `T=130`，但实际 sample 1 来自 fresh bridge debug log，`serial_write.command=null`；sample 2 没有 T=1001，`all_samples_observed_t1001=false`，`robot_ack_connected=false`。
- **requested ROS `T=13` wire frame：未证明。** 请求及上位语义报告 `command_mode=ros`，但 bridge 中实际可见的 live 非零 vendor command 是 `T=11,L=164,R=164`；不能把上位语义当作 `T=13` wire proof。
- **post-stop wheel zero：未证明。** first-jog 明确记录 `feedback_after_stop_t1001_frame_count=0`；最终可见 `T=1001 L/R=0/0` 没有 dedicated post-stop 时间归属，不能作为停止后轮速归零证据。
- **HIL / safe-to-control / route / delivery：均未证明。** 冻结字段继续为 `hil_pass=false`、`safe_to_control=false`、`route_execution_success=false`、`delivery_success=false`、`okr_credit_allowed=false`；不做百分比或归档判断。

## 验证结果

- `python3 -m json.tool`：目录内 18 个 JSON 全部通过，exit `0`。
- `jq` 结构断言：exactly-once/authorization、first-jog/auto-stop、bridge 非零与最终零命令、T=1001/IMU、安全字段、最终 Nav2 stopped 共 5 组断言全部返回 `true`。
- `rg` 交叉核对：request counts、manual/auto-stop、command raw、IMU delta、T=1001 counts，以及 `safe_to_control/delivery_success/robot_control_executed/route_execution_success/hil_pass` 字段均完成。
- `git diff --check -- sprints/2026.07.21_01-54_o1_minimal_wheel_jog`：见最终 scoped 验证，要求 exit `0`。

未发现 JSON 语法失败。发现的是证据边界缺口而非文件解析故障：没有非零 `T=1001 L/R`、没有 dedicated post-stop T=1001 window、没有 `T=13` wire frame，且顶层危险字段仍 fail-closed。

## 剩余风险与下一步

当前 authorization 已消费，本 sprint 必须封存，不得发起第二次请求或 retry。后续若要补齐 O1 HIL，只能在新的 fresh authorization 与独立安全 gate 下设计新的单次窗口，同时采集带明确时间边界的 during-motion 非零 `T=1001 L/R` 与 dedicated post-stop `T=1001 L/R=0/0`；在此之前不得宣称 `hil_pass=true` 或 `safe_to_control=true`。

## 本次审核安全确认

本次审核未执行 SSH、SCP、HTTP、curl、ROS、串口、base stop/manual、Nav2 或任何控制/物理运动命令；未生成第二次请求，也未 commit/push。
