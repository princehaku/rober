# Tech Done：O1 verified upload / backup / vendor additive instrumentation

## 状态与 proof boundary

- `sprint_type: epic`
- `IMPLEMENTATION_STATUS=IMPLEMENTED_VALIDATED_AND_SINGLE_LIVE_ATTEMPT_CONSUMED`
- `artifact_status=verified_upload_backup_vendor_instrumentation_blocked_fail_closed`
- `proof_boundary=current_verified_upload_backup_vendor_instrumentation_maintenance_evidence_not_hil`
- `authorization_id=ceo_20260728_complete_motion_deploy_service_uart_firmware_maintenance`
- `attempt_id=o1-verified-upload-backup-vendor-instrumentation-attempt-1`
- `runner_invocation_count=1`
- `current_run_artifact_delta=1`
- `external_artifact_delta=1`
- `live_control_delta=0`
- `hil_pass=false`
- `safe_to_control=false`
- `route_execution_success=false`
- `delivery_success=false`
- `mission_attempt=false`
- `okr_credit=false`

本轮完成 runner/tests/fixture、canonical V0.9 additive patch/toolchain 合同与一次 current strict-no-motion live runner。
current Gate U/B/V-prebuild=`false/false/false`，所以 build/diagnostic-flash/readback/rollback 正确保持 `0/0/0/0`。service、
expected holder、deployed hashes 与 final stop 已恢复；没有 live retry，也没有把 current NO-GO 冒充 instrumentation、
HIL、safe-to-control 或 mission。

## 已读 vendor 来源、symbol/line/hash

Hardware Engineer 已完整读取 Product plan 指定来源；PDF 使用 `pdftotext -layout` 提取并渲染 SPIDownload/COM/BAUD 页面复核：

| 来源 | 采用的 symbol / line | SHA-256 |
|---|---|---|
| `docs/vendor/VENDOR_INDEX.md` | source-of-truth order、factory binary 只读、normal UART 与 upload port 必须现场确认 | `7a407c0151d5fbb4bba00887f65d3846476779c3fba4881d2a8870c7aa8d06d7` |
| `WAVE_ROVER_V0.9/WAVE_ROVER_V0.9.ino` | `Serial.begin(115200)@L101`、`initEncoders@L216`、`getLeftSpeed/getRightSpeed@L248/L252` | `1203fbc8c07a57213898068ff7bd5a05f7c3eeccb113a0d85cee711415cdaf0b` |
| `WAVE_ROVER_V0.9/json_cmd.h` | `FEEDBACK_BASE_INFO=1001@L1`、`CMD_BASE_FEEDBACK=130@L102`；本轮明确禁止 `CMD_MM_TYPE_SET=900@L575` | `ce6a9dff14359e09db4472dd184ca63413877e8a2f826a0ef0fe47c8b72bc997` |
| `WAVE_ROVER_V0.9/uart_ctrl.h` | `T=130 -> baseInfoFeedback@L54-L55`、newline receive `@L493-L515` | `258a08727270f23789e4c9e48886c64dca040a0c793eee746f1698626d4c32c7` |
| `WAVE_ROVER_V0.9/movtion_module.h` | `encoderA/B@L126-L127`、`speedGetA/B@L135-L136`、raw counts `@L170-L191` | `3964c2702925b1af0f1e42784f75ecee37b9eafe0ebe2966c28b03f569205768` |
| `WAVE_ROVER_V0.9/ugv_advance.h` | `baseInfoFeedback@L374`、T1001 `@L384`、L/R `@L386-L387`、newline send `@L422-L424` | `7b7b7d011c20704e372db26d298d31afb277d89db75a569cf56a4274391e99b9` |
| `WAVE_ROVER_V0.9/ugv_config.h` | source defaults `mainType=1@L38`、`moduleType=0@L43`；只作 source fact | `9a752ae8e2fafb319fdbcc0f92223c7277e1e377804c0c8b739ef6e2da2c601a` |
| `Flash_Download_Tool__cn.pdf` | v3.9.5；ESP32 使用 UART、COM/BAUD、download mode、flash detected info 与 tool ownership | `7361038d40d506caea383bbb1abb2d8c00dfcc36d57c5af2027bdb96e7161957` |
| `WAVE_ROVER_FACTORY/.../combine/target.bin` | 只读 factory comparator，size=`896192`；绝不替代 current backup | `3d5a7534c7c700f8e94cb7c7fd6188ac9db8c16b8242fd261a80dda75e1f9e00` |

补充读取本地 `WAVE_ROVER.wiki.html` 的固件更新段：官方流程要求拆机后用 USB 连接驱动板中间接口，并在下载工具选择“新出现”
COM；这进一步证明 `/dev/ttyS5` 或任意现存 generic tty 不能单独认作 upload identity。

## 实际改动

1. `onboard/scripts/o1_verified_upload_backup_vendor_instrumentation.py`
   - 新增标准库-only fixture/live CLI、冻结 host/authorization/attempt、single SSH stdin transport、U/B/V/D/R phase、
     allowlisted command ledger、exactly-once validator 和 fail-closed restoration。
   - Gate U 只从 current `/dev/serial/by-id` 选 stable alias；Gate B 从 current flash identity 推导读取范围；Gate V 在
     run-owned vendor copy 应用 versioned additive patch并冻结 source/patch/toolchain/image provenance。
   - 只有 U/B/V-prebuild 与 build provenance 全绿才允许一次 build/flash；flash 一旦开始最多一次 current-backup rollback。
     静止 readback 只允许一个 `T=130` 请求；没有任何 motion/T900/manual/cmd_vel/Nav2 路径。
2. `onboard/tests/test_o1_verified_upload_backup_vendor_instrumentation.py`
   - 新增 `19` 个 targeted tests，覆盖 fixture CLI、hostile count/truth、gate ordering、flash/rollback binding、marker、
     canonical patch apply、toolchain lock、vendor hashes、embedded remote syntax、frozen identity、backup export 与恢复。
3. `onboard/src/esp32_firmware/wave_rover_v0_9_diagnostic/platformio.ini`
   - 冻结 `espressif32@6.10.0`、`esp32dev`、Arduino framework、monitor/upload speed 与逐项 pinned libraries。
4. `.../patches/additive_diagnostic.patch`
   - 只修改 `ugv_advance.h` 的 T1001 feedback，增加 fixed firmware build id、runtime `mainType/moduleType`、
     `encA/encB` 与 `speedGetA/speedGetB`；保留既有 `T/L/R/r/p/y/v`。
5. `.../toolchain.lock`
   - 冻结 PlatformIO core `6.1.18`、esptool `4.8.1`、platform/framework/board/environment/build id。
6. `artifacts/fixtures/pass/fixture.json`、`artifacts/mock_result.json`
   - 保存 deterministic fixture 与 mock-only schema；`runner_invocation_count=0`，不冒充 hardware。
7. `artifacts/verified_upload_backup_vendor_instrumentation_result.json`
   - 保存唯一 current live attempt 的 port/toolchain/source/patch/gates/ledger/restoration/final-stop 原始结构化摘要。
8. `docs/hardware/wave_rover_nonzero_feedback_hil_gate.md`
   - 同步本轮 current U/B/V NO-GO、恢复、proof boundary 与 blocker `2/2`。

没有创建 `onboard/udev/99-wave-rover-esp32-upload.rules`：current stable alias 是 STC USB Serial，且没有可唯一绑定目标 ESP32 的
current serial identity，不能凭 VID/PID 猜规则。没有修改 `docs/vendor/**`、factory binary、generic `main.cpp`、旧 sprint 或
`OKR.md`。

## Current live ledger 与硬件结论

### Exactly-once / mutation counts

```text
runner_invocation_count=1
attempt_count=1
inventory_invocation_count=1
pre_stop_invocation_count=1
service_stop_count=1
holder_termination_count=0
bootloader_identity_probe_count=0
flash_backup_read_count=0
vendor_tree_prepare_count=1
additive_patch_apply_count=1
instrumentation_build_count=0
diagnostic_flash_count=0
stationary_diagnostic_readback_count=0
rollback_flash_count=0
service_restore_count=1
final_stop_verification_count=1
motion_command_count=0
t900_write_count=0
retry_count=0
second_build_count=0
second_flash_count=0
```

### Gate U/B/V-prebuild

- current stable alias count=`1`：`usb-STC_STC_USB_Serial-if00 -> ttyACM0`；identity hash prefix=`f2dc36fefc7bcfee`。
  `/dev/ttyS5` 继续只作 normal UART，`normal_uart_is_upload_identity=false`。
- pinned esptool `4.8.1` 未安装，PlatformIO `6.1.18` 未安装；
  `first_failure=verified_esptool_version_unavailable`。为避免用未固定工具 probe 非目标 STC device，
  `bootloader_identity_probe_count=0`，Gate U=`false`。
- Gate U 红后 current backup 未读取，Gate B=`false`；factory target 只读比较，未生成 current rollback image。
- canonical source required hashes 全匹配，pristine tree=`26` files、generic `main.cpp` absent；但 live patch
  `apply_exit_code=1`，产生 `.orig/.rej`，且 pinned tools unavailable，所以 Gate V-prebuild=`false`。
- 结论：U/B/V-prebuild=`false/false/false`，build/diagnostic-flash/readback/rollback=`0/0/0/0`。

### 恢复、hash 与 final stop

- service before=`active/running MainPID 6422`；after=`active/running MainPID 7516`。
- expected bridge holder before PID=`6872`、after PID=`7966`，command hash prefix 均为 `f0b175786f431502`。
- bridge/parser/protocol/script/unit 五个 deployed hashes 前后一致。
- final stop POST 与 base status zero readback 均成立。
- `service_restored=true`、`holder_restored=true`、`final_stopped=true`、`run_owned_residual=false`。
- SSH transport invocation=`1`、exit=`0`、request SHA-256=
  `0f441c67afe31dcfd657c3ac277521d7f551fecb6dc8c60f829e3461604baf98`。
- 主 artifact SHA-256=`db1019d79bd93162411f81056730763ae7071f41582b28da14a3b9cef7c19903`，
  `artifact_validation_errors=[]`。

## 验证结果

### Phase S 与 post-live hardening

```text
python3 -m py_compile ...verified...py ...test...py
exit=0

...................
----------------------------------------------------------------------
Ran 19 tests in 0.108s

OK

fixture CLI: status=fixture_complete
fixture json.tool: exit=0
runner chinese_comment_ratio=20.20%
tests chinese_comment_ratio=20.61%
scoped git diff --check: exit=0
```

live runner 后没有重跑 SSH。post-live hardened source SHA-256=
`fa22a7184a1e9ce34bd9914c24c6e6c8dbb2eee25b0e389027d5182d074478b7`，tests SHA-256=
`bf8607305e29f9e157cd8caa97301a05f87159cc96595a124b33f6f5867d4309`；它们与唯一 live request SHA 不同，不能倒推为现场已执行。

### Current artifact assertions

```text
verified_upload_backup_vendor_instrumentation_result.json json.tool exit=0
o1 verified upload backup vendor instrumentation assertions: PASS
artifact_validation_errors=[]
gate_u/gate_b/gate_v_prebuild=false/false/false
service_restored/holder_restored/final_stopped=true/true/true
motion/T900/retry/build/flash/rollback=0/0/0/0/0/0
```

## 首轮失败、修复与复验

1. 首轮离线 patch apply 因 canonical vendor header 使用 CRLF，而本地 unified patch 为 LF，hunk fail。先加
   `--ignore-whitespace` 后，canonical temp-copy patch test 通过，离线 `19 tests OK` 后才消耗 live。
2. 唯一 live runner 的首个 current failure 是 pinned esptool 不可用；因此没有 bootloader probe、backup、build、flash 或
   rollback，不能在本 attempt 安装工具后重试。
3. live 的 secondary failure 是目标机 `patch` 实现仍对 CRLF 生成 `.orig/.rej`。live 后只在本地把实现加固为：复制到
   run-owned tree 后先把 `ugv_advance.h` CRLF 统一成 LF，再应用同一 versioned patch；离线 py_compile、19 tests、fixture、
   注释比例和 scoped diff 全部复验通过。该修复没有再次 live 执行。

## 剩余风险与下一履约动作

- 未证明 current WAVE ROVER ESP32 bootloader/upload port；当前唯一 stable alias 标识 STC USB Serial，不得猜作目标 ESP32。
- pinned esptool/PlatformIO 不可用，current flash backup、chip/flash identity、rollback image 与 diagnostic build provenance
  均未建立。
- additive patch 已在本地 canonical temp copy 复验，但 post-live CRLF portability 加固没有 current board 复验。
- 没有 instrumentation build/flash/readback，所以 firmware identity、runtime `mainType/moduleType`、raw encoder A/B counters
  仍不可观测。
- 本 attempt 已封存且禁止 live retry。canonical blocker
  `verified_esp32_upload_port_flash_backup_vendor_v0_9_diagnostic_toolchain_provenance_missing` 已达到 `2/2`；下一轮必须切换
  Objective 或升级 CEO，不得第三次包装同一 lane。
- 本轮严格未执行 motion，不证明 current nonzero wheel feedback、HIL、safe-to-control、route execution、delivery、
  operator acceptance 或 mission。Hardware 不调整 OKR 百分比、不归档 KR。

## 2026-07-28 Hardware owner 离线复验

复验开始时仓库状态已从派单时的 staged tree 漂移为 clean published tree：`HEAD=origin/master=dda8af5c3`，没有 cached
scoped diff。Hardware 仍按本 Epic 允许范围审计该 commit 与 current artifact，全程没有运行 SSH、service、UART、
bootloader、backup、build、flash、rollback 或 motion 命令。

首次复验的 py_compile、19 tests、fixture、JSON、current artifact assertions 与中文注释比例均通过；但
`git show --check HEAD` 发现 `additive_diagnostic.patch` 的 nested diff context 有 7 个
space-before-tab/trailing-whitespace 错误。该缺陷不改变已经封存的 live artifact，但不满足 scoped diff 质量门。

Hardware 将 patch 改为 source-hash 前置校验下的 zero-context additive insertion，去掉 nested context 自身的空白噪声；
它仍只向 `ugv_advance.h` 增加原 7 个诊断字段。修复后 patch SHA-256=
`a16cd790279ca218bd2b04bba915ed875649b98c49102eb65c71093e43f83349`，canonical CRLF-to-LF temp copy 上 clean apply。
完整离线复验结果：

```text
py_compile exit=0
Ran 19 tests in 0.109s / OK
fixture status=fixture_complete / exit=0
current artifact json.tool exit=0
o1 verified upload backup vendor instrumentation assertions: PASS
runner/tests chinese_comment_ratio=20.20%/20.61%
```

current artifact 未修改，SHA-256 继续为
`db1019d79bd93162411f81056730763ae7071f41582b28da14a3b9cef7c19903`；Gate
U/B/V-prebuild 继续为 `false/false/false`，bootloader probe/backup/build/diagnostic flash/readback/rollback/motion/T900/retry
继续为 `0/0/0/0/0/0/0/0/0`，service/holder/final stop 继续为 `true/true/true`。本地 patch 修复没有 live
重试，不得倒推 Gate V current green。
