# Tech Done：O1 runtime identity / raw encoder 独占维护

## 状态与 proof boundary

- `sprint_type: epic`
- `IMPLEMENTATION_STATUS=IMPLEMENTED_VALIDATED_AND_SINGLE_CURRENT_MAINTENANCE_CONSUMED`
- `artifact_status=maintenance_blocked_fail_closed`
- `proof_boundary=current_exclusive_maintenance_runtime_feedback_toolchain_and_restoration_evidence_not_hil`
- `authorization_id=ceo_20260728_complete_motion_deploy_service_uart_firmware_maintenance`
- `attempt_id=o1-runtime-identity-raw-encoder-maintenance-attempt-1`
- `current_run_artifact_delta=1`
- `external_artifact_delta=1`
- `live_control_delta=0`
- `hil_pass=false`
- `safe_to_control=false`
- `route_execution_success=false`
- `delivery_success=false`
- `mission_attempt=false`

本轮完成 Phase S→0→1→条件式2→跳过3→4：先实现并验证单一 runner、hostile tests 与 fixture；随后消耗恰好一次真实 SSH
maintenance window。current UART 已直接观察到真实 `T=1001`，但现有 firmware 不暴露 runtime identity/raw counters，且现场
instrumentation backup/upload/toolchain gate 不成立。因此保持 motion=`0`、build/flash=`0/0`，完成 direct zero、service
恢复、holder 恢复与 final stop/readback 后保守 blocked 收口。没有第二次 runner、motion 或 mutation retry。

## 已读 vendor 来源、symbol/line/hash

Hardware Engineer 已逐个读取 Product plan 指定来源：

| 来源 | 采用的 symbol / line | SHA-256 |
|---|---|---|
| `docs/vendor/VENDOR_INDEX.md` | UART newline JSON 与 WAVE ROVER source-of-truth；`T=11/130/131/142/143` 入口 `L147-L180` | `7a407c0151d5fbb4bba00887f65d3846476779c3fba4881d2a8870c7aa8d06d7` |
| `WAVE_ROVER_V0.9/json_cmd.h` | `FEEDBACK_BASE_INFO=1001@L1`、`CMD_PWM_INPUT=11@L58`、`CMD_BASE_FEEDBACK=130@L102`、`CMD_BASE_FEEDBACK_FLOW=131@L106`、`CMD_FEEDBACK_FLOW_INTERVAL=142@L110`、`CMD_UART_ECHO_MODE=143@L116`、`CMD_MM_TYPE_SET=900@L575` | `ce6a9dff14359e09db4472dd184ca63413877e8a2f826a0ef0fe47c8b72bc997` |
| `WAVE_ROVER_V0.9/uart_ctrl.h` | `T=11` dispatch `@L16-L20`、`T=130/131/142/143 @L54-L64`、`T=900 -> mm_settings @L484-L488`、newline receive `@L496-L512` | `258a08727270f23789e4c9e48886c64dca040a0c793eee746f1698626d4c32c7` |
| `WAVE_ROVER_V0.9/movtion_module.h` | `speedGetA/B @L135-L136`、`initEncoders @L141`、`getLeftSpeed @L170`、`getRightSpeed @L182`、`mm_settings @L408-L447` | `3964c2702925b1af0f1e42784f75ecee37b9eafe0ebe2966c28b03f569205768` |
| `WAVE_ROVER_V0.9/ugv_advance.h` | `T=1001 @L384`、`L=speedGetA @L386`、`R=speedGetB @L387`、newline JSON send `@L423-L424` | `7b7b7d011c20704e372db26d298d31afb277d89db75a569cf56a4274391e99b9` |
| `WAVE_ROVER_V0.9/ugv_config.h` | source default `mainType=1 @L38`、`moduleType=0 @L43`；只作 source default，不当 runtime proof | `9a752ae8e2fafb319fdbcc0f92223c7277e1e377804c0c8b739ef6e2da2c601a` |
| `WAVE_ROVER_V0.9/WAVE_ROVER_V0.9.ino` | `Serial.begin(115200) @L101`、`mm_settings @L111`、`initEncoders @L216`、loop `getLeftSpeed/getRightSpeed @L248/L252` | `1203fbc8c07a57213898068ff7bd5a05f7c3eeccb113a0d85cee711415cdaf0b` |
| `ugv_rpi/base_ctrl.py` | serial open configurable `@L134`、UTF-8 newline JSON write `@L182`、vendor RPi reference `/dev/ttyAMA0@115200 @L268` | `2b616c0701f187c0a4322e9222f6288f5d9be71aa37c7c39f1f1dba58f9779f6` |

采用结论：目标现场端口继续是冻结并实测的 `/dev/ttyS5@115200`，不是 vendor RPi 默认路径；`T=900` 是 current maintenance
set command，不等于 readback；`T=1001 L/R` 来自 `speedGetA/speedGetB`；raw encoder 参考更新路径来自
`initEncoders/getLeftSpeed/getRightSpeed`。

## 实际改动

1. `onboard/scripts/o1_runtime_identity_raw_encoder_maintenance.py`
   - 新增标准库-only fixture/live CLI、固定 SSH target、vendor hash/provenance、single-transport request hash 和稳定 artifact
     schema。
   - 远端单一程序实现 inventory、pre-stop、service/holder freeze、exact holder termination guard、UART allowlist、T=900/current
     feedback、observability gate、conditional motion、finally zero/service/holder/final-stop 恢复。
   - 所有安全字段默认且持续 false；transport/phase 异常都生成 fail-closed artifact，不自动 retry。
2. `onboard/tests/test_o1_runtime_identity_raw_encoder_maintenance.py`
   - 新增 `17` 个 targeted tests，覆盖 fixture CLI、缺 fixture、bool counter、危险 truth、observability/motion、post-stop、
     retry/second motion、live/fixture window 边界、远端 marker、非 object JSON、SSH/authorization/attempt freeze、vendor
     hashes、embedded remote syntax、restoration validator 和 instrumentation contract hash。
3. `artifacts/fixtures/pass/fixture.json` 与 `artifacts/mock_maintenance_result.json`
   - 新增 deterministic pass fixture 与 mock-only schema 输出；`maintenance_window_count=0`，不冒充 live。
4. `artifacts/maintenance_result.json`
   - 保存唯一 current maintenance 的 phase/command ledger、57 帧 T=1001、toolchain、hash、restoration、stop 和安全结论。
5. `artifacts/post_restore_verification.json`
   - 保存一次 bounded read-only holder 启动延迟核验；完整 ledger/hash 与 mutation counters 均可复查。
6. `docs/hardware/wave_rover_nonzero_feedback_hil_gate.md`
   - 同步 current maintenance 的 runtime/raw-counter/toolchain gate、exactly-once 计数、恢复和下一准入条件。
7. `tech-done.md`
   - 本文件记录实际改动、验证、首轮失败修复、现场 ledger 与剩余风险。

没有创建 `wave_rover_v0_9_diagnostic` 工程：Phase 2 在任何 build 前已证实 verified upload port、flash backup、PlatformIO/esptool
provenance 不成立，按 plan 必须保持 build/flash=`0/0`。现有 generic binary-protocol `main.cpp` 没有进入 upload image，vendor
source/factory binary 未修改。

## 当前维护 ledger 与硬件结论

### Exactly-once / mutation counts

```text
runner_invocation_count=1
maintenance_window_count=1
inventory_invocation_count=1
pre_stop_invocation_count=1
service_stop_count=1
holder_termination_count=0
uart_open_count=1
uart_write_frame_count=6
t900_write_count=1
instrumentation_build_count=0
instrumentation_flash_count=0
rollback_flash_count=0
nonzero_motion_invocation_count=0
post_stop_invocation_count=0
final_stop_verification_count=1
service_restore_count=1
retry_count=0
second_motion_count=0
raw_uart_stop_frame_count=1
```

### Runtime、counter 与 instrumentation gate

- direct UART 成功打开一次；service stop 后 `lsof/fuser /dev/ttyS5` 均为空，独占成立。
- TX 为 `T=143/142/131/900/130` 各一次，加一个 final `T=11,L=0,R=0`；没有非 allowlist frame。
- RX parsed frame 共 `61`：`T=1001` 为 `57`，另有 `T=143/142/131/130` 各一；`T=900` echo/readback 为 `0`。
- 57 个 `T=1001` 全部 `L/R=0/0`，keys 仅有 `T/L/R/r/p/y/v`；raw encoder A/B samples=`0/0`。
- `firmware_identity_before/after=null/null`、`runtime_main_type_before/after=null/null`、
  `module_type_before/after=null/null`、counter delta=`null/null`。
- `counter_feedback_observability_gate=false`，故 nonzero motion=`0`；这不是 HIL attempt，也没有消费一次 motion。
- toolchain：Python/pyserial `3.5` 可用；PlatformIO、Arduino CLI、esptool、dedicated verified upload alias 均未观测。
- `instrumentation_required=true`，但 backup/upload gate 不绿；build/flash/rollback=`0/0/0`，
  `instrumentation_success=false`。

### 恢复、hash 与 final stop

- service before=`active/running MainPID 1189`；after=`active/running MainPID 6422`，restore count=`1`。
- holder before 为 expected bridge PID `3940`；runner 内 1 秒首次 check 尚未看到新 holder。
- 追加一次 bounded read-only post-restore 诊断，没有 service/UART write/firmware/motion mutation；同窗确认 service
  `active/running`、`NRestarts=0`，bridge child PID `6872` 已重新持有 `/dev/ttyS5`，最终 `holder_restored=true`。
- 五个 deployed bridge/parser/protocol/script/unit hashes 前后一致。
- direct UART final zero 写入一次；service 恢复后 final stop POST 与 base status zero readback 成立，
  `final_stopped=true`。
- flash 未发生，所以 rollback 为显式 no-op `attempted=false/restored=true/reason=no_flash_performed`；
  run-owned residual=`false`。

## 验证结果

### Phase S 离线验收

```text
python3 -m py_compile ...o1_runtime_identity_raw_encoder_maintenance.py ...test_o1_runtime_identity_raw_encoder_maintenance.py
exit=0

.................
----------------------------------------------------------------------
Ran 17 tests in 0.086s

OK

mock fixture CLI:
status=fixture_complete
json.tool exit=0

runner chinese_comment_ratio=20.18%
tests chinese_comment_ratio=20.51%
```

### Current artifact 验收

```text
ssh-maintenance CLI exit=0
ssh transport exit=0
runner invocation=1
status=maintenance_blocked_fail_closed

maintenance_result.json json.tool exit=0
post_restore_verification.json json.tool exit=0
o1 maintenance artifact assertions: PASS
```

主 artifact assertion 在 runner 刚结束时首轮曾因 `holder_restored=false` 失败；定位发现 service 已 active，但 child 尚未在 1 秒
check 内重新打开 UART。严格禁止重跑 runner/service/UART/motion 后，按 Product 指令执行一次 bounded read-only
`systemctl show/status + bounded journal + ps + lsof/fuser` 核验，当前 expected holder 已恢复，随后相同完整 assertions 通过。

主 artifact 最终 SHA-256 为
`8391806b88614361f65428b2a2c7af9996351c2417d76c2596fcb2ea6f94aafc`；read-only 恢复补证 SHA-256 为
`f7034cde4ec21d743d5a3bbb822e55f2960c9eab3a4f85da7706f6cf5b9031d0`。唯一现场 SSH request SHA-256 为
`6ba79eac5efd66de03ba6aeb16800f10f4e822063649ea6ac325fcef95f2dd65`，与当前继续加固后的本地 runner SHA-256
`c0d19fd50e6b91376f15cfc755cd6920eb0429c69c77e258ab85128d0cd69784` 不同。当前 runner 已通过 `17` 项离线测试，但没有
再次 live 执行；不得把现场窗口完成后新增的 allowlist、validator 与恢复身份检查倒推成唯一 live request 已执行的代码。

最终 scoped `git diff --check` 通过；live validator errors=`[]`；两文件注释比例最终为 `20.18%/20.51%`。

## 首轮失败、修复与复验

1. 功能测试首轮即通过，最终扩展为 `17 tests OK`；但首轮注释比例验收发现 runner=`6.63%`、tests=`13.92%`，未达到严格
   `>20%`。已补充与 Phase、UART、instrumentation、恢复和 hostile tests 一一对应的中文安全合同，最终复验为
   `20.18%/20.51%`。
2. live artifact 首轮完整 assertion 只失败于 `holder_restored=false`。未重跑 live runner 或任何 mutation；bounded read-only
   证实这是 service child startup delay，而非 holder ownership 丢失，current holder 与 expected bridge identity 对齐后复验通过。
3. 没有隐藏现场 blocker：PlatformIO/upload/backup gate 仍失败，所以 overall status 继续
   `maintenance_blocked_fail_closed`，不会因 restoration assertion 通过而改成 instrumentation/HIL success。

## 剩余风险与下一履约动作

- deployed ESP32 firmware identity、runtime `mainType/moduleType` 与 raw encoder A/B counters 仍未观测。
- 57 个 current `T=1001` 均为 `0/0`，但本轮没有 motion，不能把静止零值解释为 encoder 损坏或 HIL 失败。
- 当前上位机没有 verified ESP32 bootloader upload alias、PlatformIO/esptool 和 current flash backup provenance；在这些 gate
  全绿前禁止 build/flash。
- 本轮唯一 maintenance runner 已消费，不得在同一 attempt 重跑；motion count 仍为 `0`，也不得把未来 motion 包装成补采。
- 下一硬件动作是先独立建立 verified ESP32 upload port、可复核的 current flash backup 和 vendor V0.9 additive diagnostic
  build provenance；只有新维护窗口中 firmware/runtime/raw counters 无运动可读后，才允许一次 supervised minimal motion。
- Product owner 保守验收、决定是否新开维护 lane；Hardware 不调整 OKR 百分比、不归档 KR。
