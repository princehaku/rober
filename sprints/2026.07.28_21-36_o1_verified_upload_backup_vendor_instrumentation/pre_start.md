# Pre-start：O1 verified upload / backup / vendor additive instrumentation

## Sprint 元数据

- `sprint_type: epic`
- `status: planning_complete`
- 目标 Objective：O1「打通官方硬件协议，建立可信底盘控制层」
- 核心 lane：`o1_verified_upload_backup_vendor_additive_instrumentation`
- 单一主责 owner：`rober-hardware-engineer`
- Sprint 路径：`sprints/2026.07.28_21-36_o1_verified_upload_backup_vendor_instrumentation/`
- 新 attempt：`o1-verified-upload-backup-vendor-instrumentation-attempt-1`
- `O1_EXCLUSIVE_SERVICE_UART_FIRMWARE_MAINTENANCE_AUTHORIZED=true`
- `AUTHORIZATION_RECONFIRM_REQUIRED=false`
- `ENGINEER_DISPATCH_READY=true`

这是单 owner、强耦合的硬件 Epic。verified port、flash backup、vendor source/patch/toolchain、条件式 build/flash 与恢复必须由
同一 `rober-hardware-engineer` 单线闭环，不能拆成假并行。

## 用户价值与产品北极星

用户价值是避免在不知道 bootloader 入口、没有 current firmware 可恢复副本、也无法证明诊断镜像来源时盲刷 ESP32。产品
北极星仍是可信、安全、可解释的真实底盘控制与反馈闭环。

本轮核心抓手不是重跑 maintenance runner、静止 `T=900` 或 motion，而是把以下三项变成 current、结构化、可复核证据：

1. verified ESP32 bootloader/upload alias 与唯一 port identity；
2. current flash backup、完整 hash、芯片/端口绑定与 rollback provenance；
3. canonical vendor V0.9 source hash、additive diagnostic patch、toolchain 与 build provenance。

三门全绿前 build/flash 必须为 `0/0`。三门全绿后，本 Epic 才允许 exactly-one additive diagnostic build、exactly-one diagnostic
flash 与 rollback-safe proof；全程禁止任何 motion。build、flash 或静止诊断 readback 都不等于 HIL、safe-to-control、route、
delivery 或 mission。

## 上轮事实与 blocker 计数

最新关闭 sprint
`sprints/2026.07.28_17-59_o1_runtime_identity_raw_encoder_maintenance/` 已消费恰好一次 current maintenance window：

- 旧 blocker `paused_pending_exclusive_maintenance_authority` 已解除并真实消费，不得再次询问 CEO；
- runner/window/UART-open/`T=900` 均已封存为一次，motion/build/flash/rollback=`0/0/0/0`；
- current direct UART 收到 57 帧静止 `T=1001`，全部 `L/R=0/0`，但 firmware identity、runtime
  `mainType/moduleType` 与 raw encoder A/B counters 仍未观测；
- service、expected holder、deployed hashes 与 final stop 已恢复；
- 新 canonical blocker
  `verified_esp32_upload_port_flash_backup_vendor_v0_9_diagnostic_toolchain_provenance_missing` 已消费 `1/2`。

本轮是该新 blocker 的第二次、也是最后一次允许消费。若三门未全绿，必须以 current gate evidence fail closed 收口；下一轮
切换 Objective 或升级 CEO，不得第三轮包装 instrumentation-readiness、port inventory、backup plan 或 toolchain summary。

## OKR 映射与方向判断

- O1 当前约 `95%`，方向=`继续但仅推进可执行硬件 lane`。
- 当前最低 Objective 是 O5，约 `85%`；其 production provider/runtime blocker 已消费 `2/2` 并退役，禁止用 local
  wrapper、readiness packet 或重复 external probe 继续消费。
- 因 O5 无可行动 lane，而 CEO 完整维护授权已打开 O1 的 verified upload/backup/vendor instrumentation 路径，本轮转向 O1。
- 本轮不修改 `OKR.md`；KR 在 Product final 验收前全部不归档，历史区无新增。

## 授权、执行边界与禁止项

CEO 已明确完整维护授权，覆盖 operator 在场、路线清空、物理限位、service/systemd stop/restart、必要 exact holder
termination、独占 `/dev/ttyS5@115200`、诊断部署、必要 ESP32 instrumentation/build/flash。不得重复询问授权。

本轮强制禁止：

- 重跑前序 maintenance runner、前序 attempt 或 `T=900`；
- 发送任何 nonzero、zero-jog、`T=11` motion、`/cmd_vel`、`/api/base/manual` 或 Nav2 goal；
- 三门全绿前 build/flash；
- 修改 `docs/vendor/**` 或覆盖 factory binary；
- 把仓库既有 generic binary-protocol `onboard/src/esp32_firmware/main.cpp` 刷入 WAVE ROVER；
- 自动 retry、第二次 diagnostic flash、第二次 rollback 或扩大目标设备。

## 预期产物与验收重点

- machine-readable upload alias/port identity 与只读 bootloader identity proof；
- current full flash backup、byte size、SHA-256、chip/port/tool binding、rollback manifest；
- canonical vendor V0.9 source manifest、additive patch hash、toolchain/package/build manifest；
- 三门 gate artifact；任一门红时 build/flash=`0/0` 且恢复 service/holder；
- 三门全绿时最多一次 additive build/diagnostic flash/静止 readback/原 flash rollback-safe proof；
- 全程 motion=`0`，最终 service/holder/hash/zero state 可复核；
- Engineer 后续只在真实执行后创建 `tech-done.md`；本 planning 阶段不预生成
  `tech-done.md`、`side2side_check.md` 或 `final.md`。

## 风险与停止规则

- 当前 upload 入口可能不是 `/dev/ttyS5`；未以稳定 alias、sysfs/by-id identity 与 bootloader probe 证明唯一映射前不得假定。
- factory `target.bin` 只作只读 vendor provenance，不是 current board rollback image。
- backup 缺字节范围、大小、hash、chip identity 或可写回命令任一项即 gate red。
- vendor source、patch、toolchain package、board/framework、build flags 或 image hash 任一不可复现即 gate red。
- diagnostic flash 一旦开始，finally 必须优先执行本轮 current backup rollback、service/holder 恢复与 final stop verification；
  无法恢复时保持 fail closed，由 operator 继续物理限位。
