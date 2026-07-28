# WAVE ROVER Nonzero Feedback HIL Gate

## Vendor sources

本轮 O1 gate 只采用以下本地资料，不凭记忆补协议：

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/hardware/wave_rover_json_bridge.md`

已采用的事实：

- WAVE ROVER 上下位机链路是 UART newline-delimited JSON。
- `json_cmd.h` 定义 `FEEDBACK_BASE_INFO=1001`。
- 项目 parser 只承认 `T=1001` 且要求同帧存在 `L/R/r/p/y/v`。
- `base_ctrl.py` 的串口读取方式是一行一帧 JSON。

## Scope

`ros2_trashbot_hardware.wave_rover_nonzero_feedback_gate` 是纯 Python、离线、fail-closed 的 software proof gate：

- 读取 `feedback_T1001.log` 或 `--feedback-sample-json`。
- 复用 `wave_rover_feedback.py` 的 parser，不重复解析 vendor 字段。
- 只输出结构化 JSON summary，不打开串口、不 import ROS2 node、不发送控制命令。
- 固定输出：
  - `evidence_boundary=software_proof_o1_wave_rover_nonzero_feedback_hil_gate_only`
  - `source=software_proof`
  - `hil_pass=false`
  - `safe_to_control=false`

## Gate behavior

本 gate 至少输出四类事实：

1. 是否读到合法 `T=1001`。
2. 是否看到同一帧 `L/R` 同时非零。
3. `L/R` 的符号模式摘要，例如 `both_positive`、`both_negative`、`left_positive_right_negative`。
4. 当前仍缺哪些真实 HIL 材料。

fail-closed 规则：

- 坏 JSON、缺字段、非 object、非法 `T=1001` payload 都记为 blocked 或 invalid。
- 非 `T=1001` 行只记为 ignored，不会抬高 gate。
- 只要同一输入里出现任意 invalid feedback line，顶层 `status` 就必须 blocked/invalid，CLI 也必须返回非 0；即使另一个样本里已经看到 `L/R` 非零，`counts`、`direction_summary`、`latest_nonzero_pair` 也只能作为诊断信息保留。
- 即使 mock 中观测到 `L/R` 非零，顶层仍保持 `hil_pass=false`、`safe_to_control=false`。
- `direction_summary` 只是 `L/R` 符号模式摘要，不等于真实车体前进/后退/转向已在现场验证。

## Remaining live HIL materials

本 gate 不能代替真实上车证据。真实履约仍需至少补齐：

- 同一 run 的真实 `feedback_T1001.log`。
- 同一 run 的 motion command record。
- 同一 run 的 operator report 或外部运动观察材料。
- 同一 run 的 HIL acceptance record。

没有这些材料时，本 gate 只能证明“软件能保守地读、判、挡”，不能证明真实 WAVE ROVER nonzero L/R，也不能证明 HIL pass。

## 2026-07-21 v8 current-live 结果

Product 已按 `PRODUCT_CLOSEOUT=ACCEPT_REAL_ATTEMPT_HIL_FAIL_CLOSED_FINAL_STOP_PROVEN` 接受这次真实尝试的证据边界。它补充了 offline software gate 无法自行产生的 live transport、同窗反馈和最终停止材料，但没有让 offline gate 或 O1 HIL 自动通过：

- authorization `ceo_20260721_0651_current_wheel_feedback_hil_v8` 已是 `consumed_no_retry`，exactly-once 计数为 `pre/nonzero/post/retry=1/1/1/0`；该 exact slice 永久退役，不得复用或重放。
- 唯一 nonzero 请求为前进 `0.08 m/s`、`300 ms`。Upper 在 `/cmd_vel` 发布 6 帧，唯一 bridge subscriber 同窗记录实际 transport command `T=11 L=164 R=164`。
- 与 nonzero command window 直接对齐的 3 个 `T=1001` pair 全部为 `L=0/R=0`；Upper 的 80 帧汇总也没有非零 pair。因此这是真实 HIL attempt，不是 nonzero wheel-feedback success。
- dedicated stop 与 post-stop 均成功；最终 bridge command 为 `T=11 L=0 R=0 sent=true`，post-stop `T=1001 L=0 R=0`，`final_stopped=true`。
- 反馈证据 class 是 `bridge_debug_serial_derived`：bridge 从 UART 解析 `source=wave_rover_uart_t1001` 后写入 debug log；它不是 byte-for-byte raw serial dump。实际 command debug 为 `T=11`，所以 `T=13 wire not proven`；本窗口依赖 continuous `T=131` feedback flow，direct `T=130 request not proven`。
- 验收结论保持 `hil_pass=false`、`safe_to_control=false`、`route_execution_success=false`、`delivery_success=false`。IMU 姿态变化和成功 stop 都不能替代 `speedGetA/speedGetB` 非零轮速。

offline gate 与 live evidence 的关系是加法而非替代：offline gate 继续负责 parser、invalid-input 和 fail-closed 回归；v8 live evidence 证明真实控制 transport、真实反馈仍为零以及最终停止。两者合并后的结论仍是 HIL fail-closed。

下一入口必须先走 non-motion/offline/maintenance diagnostics，定位 encoder、`mainType`、firmware、`speedGetA/speedGetB` 更新链和 bridge sampling。只读源码/日志分析与离线 fixture 不需要运动；任何 service、UART、firmware 修改或再次运动都必须获得新授权。

## 2026-07-21 v8 根因诊断 CLI

`ros2_trashbot_hardware.wave_rover_feedback_root_cause` 已实现为标准库-only、离线、fail-closed CLI。它只读取本地 vendor source、
冻结的 v8 artifacts 与可选严格只读 runtime inventory；不会 import ROS2 node、打开 UART、调用 HTTP control、改变 service 或写入
firmware。当前运行命令为：

```bash
PYTHONPATH=onboard/src/ros2_trashbot_hardware \
python3 -m ros2_trashbot_hardware.wave_rover_feedback_root_cause \
  --v8-artifact-dir sprints/2026.07.21_05-50_o1_current_wheel_feedback_hil/artifacts \
  --vendor-source-root docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9 \
  --output sprints/2026.07.21_08-50_o1_wheel_feedback_root_cause/artifacts/root_cause_diagnostic.json
```

诊断采用并在 JSON 中记录了以下 vendor symbol/line/hash 事实：

- `json_cmd.h`：`FEEDBACK_BASE_INFO=1001`、`CMD_PWM_INPUT=11`、`CMD_ROS_CTRL=13`、`CMD_BASE_FEEDBACK=130`、
  `CMD_BASE_FEEDBACK_FLOW=131`、`CMD_MM_TYPE_SET=900`。
- `uart_ctrl.h`：`CMD_PWM_INPUT` 分支把 `L/R` 分别交给 `leftCtrl/rightCtrl`。
- `movtion_module.h`：encoder 初始化和 `getLeftSpeed/getRightSpeed` 更新 `speedGetA/speedGetB`；`mainType != 3` 时
  `leftCtrl/rightCtrl` 会先写 PWM 数值，但这不是最终反馈采样值。
- `WAVE_ROVER_V0.9.ino`：loop 在 UART command 处理后无条件调用 `getLeftSpeed/getRightSpeed`，之后才在
  `baseFeedbackFlow` 分支调用 `baseInfoFeedback`。因此参考源码里的 T=1001 `L/R` 是 encoder update 后的值，不能把 `T=11
  L=164/R=164` 误当成应直接 echo 为 `T=1001 L=164/R=164`。
- `ugv_advance.h`：T=1001 的 `L/R` 明确来自 `speedGetA/speedGetB`。
- `ugv_config.h` 的 `mainType=1` 只是本地参考源码默认值；它不证明板上 runtime `mainType`。
- `ugv_rpi/base_ctrl.py`：UART write 是 UTF-8 newline-delimited JSON。

CLI 对 v8 重新计算得到 `6` 个已发送 nonzero `T=11` frame、`14` 个 `T=1001` frame，其中 command window 内恰有 `3`
帧并全部为 `0/0`；normalized `left_speed/right_speed` 与每帧 `vendor_frame.L/R` 一致。输入身份、exactly-once
`pre/nonzero/post/retry=1/1/1/0`、final stop 和四个安全 false 字段全部通过。因此当前首要分类是
`encoder_update_path_not_observed`，而不是 parser bug；它仍是候选排序，不是已确认物理根因。

本轮另执行了一次严格只读 inventory：`systemctl show/cat`、`ps`、`ss`、`sha256sum` 全部 exit `0`。它证实 bridge service
`active/running`、bridge 配置为 `command_mode=pwm` 与 `bridge_main_type=1`，并冻结了已部署 bridge/parser/protocol/script/unit
hash；但 systemd 配置仍不是 ESP32 runtime `mainType` 证明，ESP32 firmware binary/build identity 也未暴露，所以两者继续为
`not_observed`。该 inventory 的 motion/control/stop/nonzero/service mutation/UART write/firmware mutation 均为 `0`。

唯一下一动作是：取得独占 service/UART/firmware 维护授权后，先冻结 deployed ESP32 firmware identity 与 runtime
`mainType`，再增加或读取 raw encoder A/B counter delta。在 encoder counter path 可观测前，不批准新的 motion retry。该动作不由
本 CLI 自动执行；本轮继续固定 `hil_pass=false`、`safe_to_control=false`、`route_execution_success=false`、
`delivery_success=false`。

## 2026-07-28 current runtime/raw encoder 独占维护结果

本轮已使用新 authorization
`ceo_20260728_complete_motion_deploy_service_uart_firmware_maintenance` 和新 attempt
`o1-runtime-identity-raw-encoder-maintenance-attempt-1` 执行恰好一次真实维护 runner。旧 v8 没有复用；runner、maintenance
window、inventory、pre-stop、service stop、UART open、`T=900`、service restore 和 final stop verification 均为 `1`，
retry/second motion 均为 `0`。

当前 direct UART 窗口的事实为：

- `pyserial 3.5` 成功独占打开 `/dev/ttyS5@115200`；service stop 后 `lsof/fuser` 都证实 holder empty。
- TX 恰好包含一次 `T=143`、`T=142`、`T=131`、`T=900,main=1,module=0`、`T=130` 和最终 `T=11,L=0,R=0`。
- RX 共解析 `57` 帧 current `T=1001`，全部 `L/R=0/0`；字段只有 `T/L/R/r/p/y/v`，没有 firmware build id、runtime
  `mainType`、module type 或 raw encoder A/B counter。
- `T=900` 没有 current echo/readback；即使有 echo 也只会证明 command receipt，仍不能证明 runtime `mainType`。
- observability gate 因 firmware/runtime/raw-counter 三类字段缺失而保持 false，所以唯一允许的
  `T=11,L=164,R=164,300ms` 没有发送；motion/post-motion-stop/retry=`0/0/0`。

条件式 instrumentation 没有执行：现场存在 Python/pyserial，但 PlatformIO、Arduino CLI、esptool 和 dedicated verified ESP32
upload alias 都未观测到，无法先完成当前 flash backup 与 upload provenance。按 gate 要求
instrumentation build/flash/rollback=`0/0/0`；没有创建或刷入 generic binary-protocol `main.cpp`，也没有覆盖 vendor factory
binary。

恢复阶段已证明 deployed bridge/parser/protocol/script/unit hashes 前后一致、service `active/running`、final
`POST /api/base/stop` 与 `/api/base/status` zero readback 成立。runner 内首次 holder check 发生在 service child 尚未打开 UART 的
启动间隙；随后一次有界只读 post-restore 验证确认 MainPID `6422` 的 child `esp32_bridge` PID `6872` 已重新持有
`/dev/ttyS5`，且 service `NRestarts=0`。该验证只执行 `systemctl show/status`、bounded journal、`ps`、`lsof/fuser`，service/UART
write/firmware/motion mutation 全为 `0`。

主 artifact 为
`sprints/2026.07.28_17-59_o1_runtime_identity_raw_encoder_maintenance/artifacts/maintenance_result.json`。结论是
`maintenance_blocked_fail_closed`：本轮产生了 current runtime/feedback/toolchain/restoration 证据，但尚未让 raw counters
可观测，也没有执行 motion。因此继续固定 `instrumentation_success=false`、`hil_pass=false`、`safe_to_control=false`、
`route_execution_success=false`、`delivery_success=false`、`mission_attempt=false`。下一次不得重复本轮 motion；只有先建立
verified ESP32 upload port、当前 flash backup 和 PlatformIO/esptool provenance，才能在新维护窗口考虑 additive
instrumentation。

## 2026-07-28 runtime identity/raw encoder maintenance Phase S

`onboard/scripts/o1_runtime_identity_raw_encoder_maintenance.py` 已建立单一 runner 的离线 schema、fixture、hostile validator、
vendor provenance hash、冻结 SSH request 和 fail-closed 恢复骨架。targeted tests 与 fixture CLI 只证明软件合同，不是
hardware/HIL 证据；fixture 固定 `maintenance_window_count=0`、`uart_open_count=0`、
`nonzero_motion_invocation_count=0`、`live_control_delta=0`，并持续固定五个 mission/HIL 安全字段为 `false`。

本轮采用的 vendor 事实与来源如下：

- `json_cmd.h` SHA-256
  `ce6a9dff14359e09db4472dd184ca63413877e8a2f826a0ef0fe47c8b72bc997`：`CMD_PWM_INPUT=11`、
  `CMD_BASE_FEEDBACK=130`、`CMD_BASE_FEEDBACK_FLOW=131`、`CMD_MM_TYPE_SET=900`，且 `T=900` 参数为
  `main/module`。
- `uart_ctrl.h` SHA-256
  `258a08727270f23789e4c9e48886c64dca040a0c793eee746f1698626d4c32c7`：`CMD_MM_TYPE_SET` 分支把
  `main/module` 交给 `mm_settings`。
- `movtion_module.h` SHA-256
  `3964c2702925b1af0f1e42784f75ecee37b9eafe0ebe2966c28b03f569205768`：
  `initEncoders/getLeftSpeed/getRightSpeed` 读取 raw encoder，并更新 `speedGetA/speedGetB`。
- `ugv_advance.h` SHA-256
  `7b7b7d011c20704e372db26d298d31afb277d89db75a569cf56a4274391e99b9`：`T=1001` 的 `L/R`
  来自 `speedGetA/speedGetB`。
- `ugv_config.h` SHA-256
  `9a752ae8e2fafb319fdbcc0f92223c7277e1e377804c0c8b739ef6e2da2c601a`：参考源码默认
  `mainType=1`；该默认值不是目标 ESP32 runtime readback。
- `WAVE_ROVER_V0.9.ino` SHA-256
  `1203fbc8c07a57213898068ff7bd5a05f7c3eeccb113a0d85cee711415cdaf0b`：setup 调用
  `initEncoders`，loop 在反馈前调用 `getLeftSpeed/getRightSpeed`。
- `ugv_rpi/base_ctrl.py` SHA-256
  `2b616c0701f187c0a4322e9222f6288f5d9be71aa37c7c39f1f1dba58f9779f6`：UART TX 使用 UTF-8
  newline-delimited JSON；Raspberry Pi 的 `/dev/ttyAMA0` 不能替代本项目已冻结的 Orange Pi 现场
  `/dev/ttyS5@115200`。

共享任务在 Phase S 实现落盘期间已经产生一次 current maintenance artifact；后续不得重跑该 maintenance window。该 artifact
表明：runner/inventory/pre-stop/service-stop/UART-open/T=900/final-stop/service-restore 为
`1/1/1/1/1/1/1/1`，retry/second-motion/nonzero-motion/build/flash 均为 `0`；service 恢复 active、最终 stop
确认成功、部署 hash 前后一致。它仍未观测 firmware identity、runtime `mainType`、module type 或 raw encoder counters；
`counter_feedback_observability_gate=false`，因此正确禁止 motion。

当前 blocker 是 dedicated verified ESP32 upload port 未观测、PlatformIO/Arduino CLI/esptool 不可用，以及
instrumentation backup/upload gate 未打开。service start 后第一次 `lsof/fuser` 采样发生在 child 尚未打开 UART 的间隙；
随后一次严格只读 post-restore verification 证明 service 持续 `active/running`、`NRestarts=0`，预期
`esp32_bridge` child 已重新持有 `/dev/ttyS5`，因此收敛为 `holder_restored=true`。该 recovery 的
service/firmware/UART-open/UART-write/motion mutation counts 全部为 `0`，没有重开 maintenance window。

这不是 HIL 通过，继续固定 `instrumentation_success=false`、`hil_pass=false`、`safe_to_control=false`、
`route_execution_success=false`、`delivery_success=false`、`mission_attempt=false`。后续不得重跑该 maintenance
window、不得再次发送 `T=900`、不得 motion、不得 build/flash；如另开 instrumentation lane，必须先补 verified upload port、
current flash backup 与 toolchain，并建立新的计划和 attempt identity。
