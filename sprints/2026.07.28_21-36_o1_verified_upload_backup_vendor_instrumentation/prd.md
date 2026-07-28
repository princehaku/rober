# PRD：O1 verified upload / backup / vendor additive instrumentation

## 状态与产品目标

- `sprint_type: epic`
- `status: planning_complete`
- 单一主责 owner：`rober-hardware-engineer`
- lane：`o1_verified_upload_backup_vendor_additive_instrumentation`
- `AUTHORIZATION_RECONFIRM_REQUIRED=false`

产品北极星是可信、安全、可解释的真实底盘控制与反馈闭环。本 Epic 要在零运动条件下，证明 WAVE ROVER ESP32 的唯一可上传
入口、current flash 可恢复副本和 canonical vendor V0.9 additive diagnostic 构建链。它不以 planning、inventory、build
success 或 flash success 冒充业务闭环。

## 产品问题

前序 current maintenance 已证明现有 firmware 不暴露 firmware identity、runtime `mainType/moduleType` 或 raw encoder A/B
counters，同时现场没有 verified upload port、current flash backup 或 PlatformIO/esptool provenance。若直接 build/flash，
会同时失去目标设备身份、当前固件可恢复性和镜像来源三条安全链。

因此本轮必须先关闭三个前置门。三门全绿前禁止 build/flash；全绿后才允许 exactly-one additive diagnostic
build/flash/rollback-safe proof，仍然禁止 motion。

## 功能需求

### Gate U：verified bootloader/upload identity

1. 在任何 flash mutation 前冻结 service、holder、`/dev/ttyS5@115200`、候选 upload ports、`/dev/serial/by-id` 或经验证
   durable alias、sysfs device path、VID/PID/serial（敏感 identity 只存 hash prefix）和 tool version。
2. 候选 port 必须唯一；stable alias 必须解析到同一 canonical device，且 service stop 后没有并发 holder。
3. 使用只读 bootloader identity probe 证明该 port 是目标 ESP32；记录 chip family、revision、flash identity、MAC hash prefix、
   command/exit/timestamp。probe 失败、多个候选、alias 漂移或无法进入 bootloader，Gate U 立即红。
4. 不得把 normal UART 可读、`/dev/ttyS5` 存在或 generic `/dev/ttyUSB*` 名称单独当作 verified upload identity。

### Gate B：current flash backup / hash / rollback provenance

1. Gate U 绿后才允许恰好一次 current full-flash backup read；读取范围必须由 current chip/flash identity 得出，不得凭记忆
   硬编码容量。
2. backup artifact 必须记录 exact byte range、实际大小、SHA-256、chip identity hash、port identity hash、esptool/toolchain
   version、命令 ledger、开始/结束时间与 exit。
3. rollback manifest 必须把同一 backup、同一 chip、同一 verified port、write offset/range、tool version与预期验证步骤绑定；
   factory binary 只能作只读比较，不能替代 current backup。
4. backup 缺失、大小不符、hash 缺失、identity mismatch、空文件、命令失败或 rollback manifest 不完整时，Gate B 红且
   diagnostic flash count 必须为 0。

### Gate V：canonical vendor V0.9 additive diagnostic provenance

1. source 必须来自 `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/`，逐文件记录 basename、SHA-256、采用 symbol/line；
   `docs/vendor/**` 只读。
2. 在 run-owned 隔离 build tree 应用版本化 additive patch；记录 pristine tree hash、patch hash、patched tree hash、差异
   allowlist 与生成命令。
3. additive instrumentation 只允许在既有 newline-JSON feedback 中增加 firmware build id、runtime `mainType/moduleType`、
   raw encoder A/B counts 与 `speedGetA/speedGetB` 的 machine-readable 字段；既有 `T/L/R/r/p/y/v` 字段、command IDs、
   motor control、watchdog、pin/voltage、Wi-Fi 与 factory binary 均不得改变。
4. toolchain provenance 必须记录 PlatformIO/esptool 版本、platform/framework/board、packages/locks、build flags、source/patch
   hashes、build command、firmware image/bootloader/partitions hashes；generic binary-protocol project不得进入 image。
5. 任一 forbidden diff、依赖漂移、未固定 package、source/hash mismatch 或无法生成可复验 build manifest，Gate V 红。

### 三门全绿后的唯一 diagnostic slice

1. 只有 `gate_u=true && gate_b=true && gate_v=true` 才允许：
   `instrumentation_build_count=1`、`diagnostic_flash_count=1`。
2. flash 后只做静止 additive readback，验证 firmware/runtime/raw-counter 字段存在、类型合法、identity 与 build image 对齐；
   `motion_command_count=0`，禁止任何 motion。
3. 完成 readback 或发生任何异常后，使用本轮 current flash backup 执行最多一次 rollback，并验证 original flash hash/identity、
   service active/running、expected holder 恢复、deployed files unchanged、final stopped 与无 run-owned residual。
4. diagnostic build/flash/readback/rollback 任一步失败都 fail closed；不得重试 build、diagnostic flash 或 rollback。

## Artifact 合同

主 artifact schema：
`trashbot.wave_rover.verified_upload_backup_vendor_instrumentation.v1`，至少包含：

- `attempt_id`、`authorization_id`、capture timestamps、host hash prefix；
- Gate U port alias/canonical device/sysfs/bootloader identity/tool command摘要；
- Gate B backup byte range/size/SHA-256/chip-port binding/rollback manifest；
- Gate V vendor source manifest、patch manifest、toolchain/build/image manifest；
- phase states、allowlisted command ledger、exactly-once counters、errors/blockers；
- service/holder/deployed hash before/after、rollback result、final stop、run-owned residual；
- `current_run_artifact_delta`、`external_artifact_delta` 与 proof boundary。

顶层必须持续显式固定：

```text
motion_command_count=0
live_control_delta=0
hil_pass=false
safe_to_control=false
route_execution_success=false
delivery_success=false
mission_attempt=false
okr_credit=false
```

## 验收口径

- 三门各有 current machine-readable evidence；red gate 必须列出 exact first failure 和缺失材料。
- 任一 gate 红：build/diagnostic-flash/rollback=`0/0/0`，service/holder/final stop 恢复并封存。
- 三门全绿：build/diagnostic-flash/rollback 最多 `1/1/1`，静止 readback 完成，motion=`0`，original current flash 与正常
  service/holder 状态恢复。
- 所有 Engineer 新增代码技术注释使用中文且有意义注释比例严格 `>20%`。
- py_compile、targeted unittest、fixture/hostile cases、JSON/schema/safety assertions、source/patch/toolchain manifest assertions、
  scoped `git diff --check` 全部通过。
- `tech-done.md` 记录实际改动、原始验收命令摘要、首轮失败与修复、current ledger、恢复状态和剩余风险。

## 非目标与拒绝项

- 不重跑前序 runner、`T=900`、v8 HIL slice 或任何 motion。
- 不执行 `T=11` nonzero/zero-jog、`/cmd_vel`、manual API、Nav2、route 或 delivery。
- 不修改 `OKR.md`、`docs/vendor/**`、factory firmware 或 generic `onboard/src/esp32_firmware/main.cpp`。
- 不接受 port listing、backup plan、tool version、build success、flash success、静止 counter 或 rollback manifest 单项作为
  instrumentation/HIL/safe-to-control 完成。
- 不拆给多个 owner，不用并行进程争抢 port，不允许无 current backup 的 flash。

## OKR、KR 与历史

- O1 约 `95%`，方向=`继续`；本轮只在 Product final 依据 current proof 判断是否调分。
- O5 约 `85%` 虽最低，但 production blocker 已消费 `2/2` 并退役，因此本轮不回到 O5。
- O1 KR 当前全部不归档；已完成 KR 历史区无新增。本 planning 阶段不改 `OKR.md`。
