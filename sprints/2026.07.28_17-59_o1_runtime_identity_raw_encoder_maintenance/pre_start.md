# Pre-start：O1 runtime identity / raw encoder 独占维护

## Sprint 元数据

- `sprint_type: epic`
- `status: planning_complete`
- 目标 Objective：O1「打通官方硬件协议，建立可信底盘控制层」
- 单一主责 owner：`rober-hardware-engineer`
- Sprint 路径：`sprints/2026.07.28_17-59_o1_runtime_identity_raw_encoder_maintenance/`
- 核心 lane：`maintenance_freeze_runtime_identity_then_observe_raw_encoder_counters`
- `O1_EXCLUSIVE_SERVICE_UART_FIRMWARE_MAINTENANCE_AUTHORIZED=true`
- `AUTHORIZATION_SEMANTIC_CHANGE=true`
- `AUTHORIZATION_RECONFIRM_REQUIRED=false`
- `ENGINEER_DISPATCH_READY=true`

## 授权变化与 blocker reset

CEO 已明确：“我都授权过了”“继续推进啊”。该原话构成本轮 blocker reset 与继续执行证据；不得再次询问、等待或要求 CEO
确认同一授权。

本轮授权完整覆盖：operator 现场看护、路线清空、物理限位、所有运动与部署、service/systemd stop/restart、必要 holder
termination、独占 `/dev/ttyS5@115200`、vendor `T=900`、diagnostic maintenance deploy，以及必要的 ESP32
instrumentation/build/flash。旧 v8 authorization 仍为 `consumed_no_retry`，不得复用；本 Epic 使用新的完整维护授权与新的
attempt identity，不回填或重跑旧 v8 slice。

## 用户价值与产品北极星

北极星是可信、安全、可解释的真实底盘控制与反馈闭环。当前真实链路已证明非零 `T=11` 能让车轮动作并最终停车，但同窗
`T=1001 L/R` 仍为 `0/0`。本 Epic 不再产出 review/handoff/status wrapper，而是在真实上位机独占维护窗口直接冻结 deployed
ESP32 firmware identity 与 runtime `mainType`，再让 raw encoder A/B counter 可观测，从而判断问题位于 firmware identity、
runtime mode、encoder signal/update path 还是反馈采样链。

用户最终获得的是可复核的 runtime/counter 事实和安全恢复结果；只有 counter/feedback 链已经可观测，才允许一次 supervised
minimal motion validation。instrumentation、build 或 flash 成功本身不等于 HIL、route execution、delivery 或
`safe_to_control`。

## 上轮证据与本轮起点

- `sprints/2026.07.21_08-50_o1_wheel_feedback_root_cause/` 已完成离线诊断与一次只读 inventory。
- 已知 bridge 配置为 `command_mode=pwm`、`bridge_main_type=1`、`module_type=0`、`/dev/ttyS5@115200`；这些只是上位机配置，
  不是 ESP32 runtime `mainType` 或 firmware identity。
- 旧 v8 已冻结 `T=11` 非零发送、同窗三个 `T=1001=0/0`、最终停稳；parser 与已见 vendor frame 一致。
- 仍缺 deployed firmware identity、runtime `mainType`、raw encoder A/B counters、counter delta、raw UART timing、nonzero
  current wheel feedback 与 HIL acceptance。
- 唯一下一动作已经由旧 final 固定为
  `maintenance_freeze_runtime_identity_then_observe_raw_encoder_counters`；本轮授权变化正式打开该 lane。

## Owner、执行边界与安全条件

`rober-hardware-engineer` 单线负责实现、离线测试、真实 SSH 维护、必要 instrumentation/build/flash、rollback、最终恢复验证与
`tech-done.md`。这是一条强耦合硬件维护链，不为凑并行拆给其他 Engineer。

Hardware 开工必须先读：

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_config.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/WAVE_ROVER_V0.9.ino`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`

执行顺序固定：离线实现/测试 → 冻结远端 inventory/hash/rollback 基线 → pre-stop → 独占 service/UART 维护 → 无运动
runtime/counter 观测 → 条件式 instrumentation/build/flash → 无运动复验 → 条件式 exactly-once minimal motion → post-stop →
rollback/恢复 service 与 holder → final stop/readback。任一阶段失败均 fail closed，不得 retry motion。

## 预期产物与停止规则

- 一个可复验 maintenance runner、targeted tests、mock fixture 结果和稳定 artifact schema。
- current deployed bridge/service/config/source hashes、可用 firmware/toolchain/provenance、runtime `mainType` 与 raw encoder A/B
  counter 的真实 artifact。
- 必要时的最小 vendor-sourced diagnostic instrumentation、PlatformIO build/upload 记录、上传前后 identity 与 rollback 证据；
  禁止修改或覆盖 `docs/vendor/` factory binary。
- counter/feedback 链不可观测时，动作计数必须保持零；即使 build/flash 工具不可用，也必须留下 current runtime/raw-counter
  fail-closed artifact、真实 toolchain blocker、原状态恢复证据，不能退化成 planning-only。
- motion 最多一次，必须 pre/post stop、最终停稳、no retry；任何无法确认 stop、service 恢复、holder 归还或 artifact 完整性
  的情况都保持 `hil_pass=false`、`safe_to_control=false`、`route_execution_success=false`、`delivery_success=false`。
