# Tech Plan：O1 verified upload / backup / vendor additive instrumentation

## 状态、授权与 owner

- `sprint_type: epic`
- `status: planning_complete`
- lane：`o1_verified_upload_backup_vendor_additive_instrumentation`
- attempt：`o1-verified-upload-backup-vendor-instrumentation-attempt-1`
- 单一主责 owner：`rober-hardware-engineer`
- `O1_EXCLUSIVE_SERVICE_UART_FIRMWARE_MAINTENANCE_AUTHORIZED=true`
- `AUTHORIZATION_RECONFIRM_REQUIRED=false`
- `ENGINEER_DISPATCH_READY=true`

CEO 完整维护授权已成立，覆盖 operator 在场、路线清空、物理限位、service/systemd stop/restart、必要 exact holder
termination、独占 `/dev/ttyS5@115200`、诊断部署和必要 ESP32 instrumentation/build/flash；不得重复询问。该链路强耦合，
由一个 `rober-hardware-engineer` 单线实现、验证、现场执行、修复、恢复和留档，不能拆假并行。

旧 maintenance runner、旧 attempt、`T=900` 与 v8 motion slice 均已封存。本 Epic 全程禁止任何 motion。

## 必读来源与 provenance 基线

Hardware 开工必须逐个读取，并在 `tech-done.md` 记录采用的 symbol/line/SHA-256：

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/WAVE_ROVER_V0.9.ino`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_config.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_FACTORY/flash_download_tool_3.9.5/doc/Flash_Download_Tool__cn.pdf`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_FACTORY/flash_download_tool_3.9.5/combine/target.bin`
- `docs/hardware/wave_rover_nonzero_feedback_hil_gate.md`

采用边界：canonical source 是 top-level vendor V0.9 tree；factory binary 只读、只作比较，不是 current flash backup；
`/dev/ttyS5@115200` 是 current normal UART 事实，不自动等于 bootloader upload port；既有
`onboard/src/esp32_firmware/main.cpp` 是 generic binary protocol，禁止进入 WAVE ROVER image。

## 文件范围

本 planning 轮只新增本 sprint 的 `pre_start.md`、`prd.md`、`tech-plan.md`。

后续 Hardware implementation 只允许创建或修改：

- `onboard/scripts/o1_verified_upload_backup_vendor_instrumentation.py`
- `onboard/tests/test_o1_verified_upload_backup_vendor_instrumentation.py`
- `onboard/src/esp32_firmware/wave_rover_v0_9_diagnostic/platformio.ini`
- `onboard/src/esp32_firmware/wave_rover_v0_9_diagnostic/patches/additive_diagnostic.patch`
- `onboard/src/esp32_firmware/wave_rover_v0_9_diagnostic/toolchain.lock`
- `onboard/udev/99-wave-rover-esp32-upload.rules`（仅在 current VID/PID/serial 可唯一绑定且无 stable by-id alias 时允许）
- `docs/hardware/wave_rover_nonzero_feedback_hil_gate.md`
- `sprints/2026.07.28_21-36_o1_verified_upload_backup_vendor_instrumentation/artifacts/**`
- `sprints/2026.07.28_21-36_o1_verified_upload_backup_vendor_instrumentation/tech-done.md`

隔离 build tree 与 remote payload 只允许位于 exact run-owned
`/tmp/trashbot-o1-verified-upload-backup-vendor-instrumentation-<attempt_id>/`；不得修改 `docs/vendor/**`、factory binary、
generic `main.cpp/platformio.ini`、旧 sprint、`OKR.md`、Nav2、workstation、Upper API 或 bridge 产品代码。

## 接口边界

1. 不改变 ROS topic、Upper API、normal bridge command、UART baud、command IDs、motor/watchdog、pin、电压或 Wi-Fi 合同。
2. additive patch 只允许在 vendor newline-JSON feedback 中增加 firmware build id、runtime `mainType/moduleType`、raw encoder
   A/B counters 与 `speedGetA/speedGetB` 的 machine-readable fields；既有 `T/L/R/r/p/y/v` 不得删除、改名或改变语义。
3. direct diagnostic reader 解析 additive fields；normal bridge 对未知 fields 的兼容性必须由离线 tests 证明，否则禁止 flash，
   且本 Epic 不扩范围修改 bridge。
4. port alias、chip identity、backup 与 toolchain只输出安全 basename/hash prefix，不泄露完整 MAC、凭证、环境变量或 Wi-Fi。

## Phase gate

### Phase S：离线合同与 hostile tests

实现单一不可重入 runner、artifact schema、allowlist、fixture、hostile validator、source/patch/toolchain manifest validator 和
restore/finally 骨架。离线失败必须修复并复验；不得触发 SSH、service、port、build、flash 或 motion。

### Phase 0：current inventory 与 pre-stop

冻结 authorization/attempt、service/holder、normal UART、候选 upload devices、by-id/sysfs identity、deployed hashes、toolchain
和 operator 条件。并发 task、身份漂移、pre-stop 或 physical limit 未确认即 NO-GO，恢复后收口。

### Gate U：verified ESP32 bootloader/upload alias/port identity

service inactive、holder empty 后，唯一 stable alias 必须解析到唯一 canonical device；只读 bootloader logical probe 必须记录
chip family/revision、flash identity、MAC hash prefix、sysfs identity、tool version、command/exit/time。listing、normal UART 可读、
generic tty 名或多候选不算通过。Gate U 红时后续 backup/build/flash 全为 0。

### Gate B：current flash backup/hash/rollback provenance

Gate U 绿后才允许一次 full-flash backup；读取范围由 current flash identity 得出。验收 exact range、byte size、SHA-256、
chip/port/tool binding、rollback write manifest 和验证步骤。factory `target.bin` 不得替代 current backup。任一字段缺失即 Gate B
红，build/flash=0。

### Gate V-prebuild：canonical vendor V0.9 source/patch/toolchain provenance

从只读 canonical vendor tree 复制到 run-owned tree，冻结 pristine source manifest，应用唯一 additive patch，再冻结 patch hash、
patched tree hash、diff allowlist、PlatformIO/esptool/platform/framework/board/packages/flags 与 lock hash。forbidden diff、未固定
依赖、generic `main.cpp` 混入或 manifest mismatch 即红。

只有 `Gate U && Gate B && Gate V-prebuild` 三门全绿，才允许一次 additive build。build 后必须形成 image/bootloader/partition
hash 与完整 command manifest；build provenance 红时禁止 flash。

### Phase D：exactly-one additive diagnostic build/flash/rollback-safe proof

build provenance 绿后才允许一次 diagnostic flash。flash 后只做一次静止 additive readback，验证 image identity、
runtime fields 与 raw counters schema；禁止 motion。随后无论 readback 成功或失败，都使用本轮 current backup 执行最多一次
rollback，恢复 original flash identity/hash、service/expected holder、deployed hashes、final stop 和无 run-owned residual。

### Phase R：fail-closed restore 与封存

任一 transport、PID、alias、bootloader、backup、hash、source、patch、toolchain、build、flash、readback 或 rollback 失败立即进入
finally。若 diagnostic flash 未开始，rollback 为显式 no-op；若已开始，必须优先回滚再恢复 service。不得 retry。

## Exactly-once 计数合同

```text
runner_invocation_count=1
attempt_count=1
inventory_invocation_count=1
pre_stop_invocation_count=1
service_stop_count<=1
holder_termination_count<=1
bootloader_identity_probe_count<=1
flash_backup_read_count<=1
vendor_tree_prepare_count<=1
additive_patch_apply_count<=1
instrumentation_build_count<=1
diagnostic_flash_count<=1
stationary_diagnostic_readback_count<=1
rollback_flash_count<=1
service_restore_count<=1
final_stop_verification_count=1
motion_command_count=0
t900_write_count=0
retry_count=0
second_build_count=0
second_flash_count=0
```

任一 U/B/V-prebuild gate 红时 build/diagnostic-flash/rollback=`0/0/0`。三门全绿但 build provenance 红时
diagnostic-flash/rollback=`0/0`。diagnostic flash 已开始时 rollback 最多 `1`，无论结果如何不得第二次 flash。

## Artifact 与 fail-closed 合同

主 artifact：
`artifacts/verified_upload_backup_vendor_instrumentation_result.json`，schema=
`trashbot.wave_rover.verified_upload_backup_vendor_instrumentation.v1`。

必须包含 U/B/V gates、first failure、port/chip/backup/source/patch/toolchain/build manifests、command ledger、所有计数、
service/holder/hash before/after、rollback/final stop/residual、proof boundary 与：

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

缺字段、危险真值、非 current sample、attempt mismatch、identity/hash mismatch、restore/rollback 未确认全部 fail closed。
build/flash/静止 counter/rollback success 均不得提升上述安全字段。

## Engineer 验收命令

Hardware 必须运行、修复至通过，并把关键原始输出写入 `tech-done.md`：

```bash
python3 -m py_compile \
  onboard/scripts/o1_verified_upload_backup_vendor_instrumentation.py \
  onboard/tests/test_o1_verified_upload_backup_vendor_instrumentation.py

python3 -m unittest \
  onboard/tests/test_o1_verified_upload_backup_vendor_instrumentation.py

python3 onboard/scripts/o1_verified_upload_backup_vendor_instrumentation.py \
  --mode fixture \
  --fixture-dir sprints/2026.07.28_21-36_o1_verified_upload_backup_vendor_instrumentation/artifacts/fixtures/pass \
  --output sprints/2026.07.28_21-36_o1_verified_upload_backup_vendor_instrumentation/artifacts/mock_result.json

python3 onboard/scripts/o1_verified_upload_backup_vendor_instrumentation.py \
  --mode ssh-maintenance \
  --ssh-host root@192.168.1.11 \
  --ssh-port 37878 \
  --authorization-id ceo_20260728_complete_motion_deploy_service_uart_firmware_maintenance \
  --attempt-id o1-verified-upload-backup-vendor-instrumentation-attempt-1 \
  --strict-no-motion \
  --allow-exactly-one-diagnostic-build-flash-after-all-gates \
  --output sprints/2026.07.28_21-36_o1_verified_upload_backup_vendor_instrumentation/artifacts/verified_upload_backup_vendor_instrumentation_result.json

python3 -m json.tool \
  sprints/2026.07.28_21-36_o1_verified_upload_backup_vendor_instrumentation/artifacts/verified_upload_backup_vendor_instrumentation_result.json \
  >/dev/null

python3 - <<'PY'
import json
from pathlib import Path
p = Path("sprints/2026.07.28_21-36_o1_verified_upload_backup_vendor_instrumentation/artifacts/verified_upload_backup_vendor_instrumentation_result.json")
d = json.loads(p.read_text())
assert d["schema"] == "trashbot.wave_rover.verified_upload_backup_vendor_instrumentation.v1"
assert d["runner_invocation_count"] == 1
assert d["motion_command_count"] == 0
assert d["t900_write_count"] == 0
assert d["retry_count"] == 0
assert d["instrumentation_build_count"] in (0, 1)
assert d["diagnostic_flash_count"] in (0, 1)
assert d["rollback_flash_count"] in (0, 1)
if d["instrumentation_build_count"] or d["diagnostic_flash_count"]:
    assert d["gate_u"] and d["gate_b"] and d["gate_v_prebuild"]
for key in ("hil_pass", "safe_to_control", "route_execution_success", "delivery_success", "mission_attempt", "okr_credit"):
    assert d[key] is False, (key, d[key])
assert d["service_restored"] is True
assert d["holder_restored"] is True
assert d["final_stopped"] is True
print("o1 verified upload backup vendor instrumentation assertions: PASS")
PY

python3 - <<'PY'
from pathlib import Path
for name in (
    "onboard/scripts/o1_verified_upload_backup_vendor_instrumentation.py",
    "onboard/tests/test_o1_verified_upload_backup_vendor_instrumentation.py",
):
    lines = [line for line in Path(name).read_text().splitlines() if line.strip()]
    comments = [line for line in lines if line.lstrip().startswith("#")]
    ratio = len(comments) / len(lines) if lines else 0
    print(f"{name}: chinese_comment_ratio={ratio:.2%}")
    assert ratio > 0.20
PY

git diff --check -- \
  onboard/scripts/o1_verified_upload_backup_vendor_instrumentation.py \
  onboard/tests/test_o1_verified_upload_backup_vendor_instrumentation.py \
  onboard/src/esp32_firmware/wave_rover_v0_9_diagnostic \
  onboard/udev/99-wave-rover-esp32-upload.rules \
  docs/hardware/wave_rover_nonzero_feedback_hil_gate.md \
  sprints/2026.07.28_21-36_o1_verified_upload_backup_vendor_instrumentation
```

runner 内部的 bootloader probe、backup、build、flash 与 rollback 命令必须从 verified tool version 和 current identity 生成并写入
allowlisted ledger；禁止 Engineer 在 runner 外手工补跑。Gate 未全绿时不得单独运行 PlatformIO upload。

## OKR 最低优先级核对

1. 当前最低 Objective 是 O5，约 `85%`。
2. 本 Epic 不针对 O5：其 production provider/runtime blocker 已消费 `2/2` 并退役，当前没有 success-class production
   evidence，继续 wrapper/probe 违反 anti-repeat。
3. O1 当前约 `95%`，但 CEO 完整维护授权已打开 verified upload、current backup 与 canonical vendor V0.9 additive
   instrumentation 的真实硬件 lane，所以本轮转 O1。
4. 本轮只有 current port/backup/provenance/rollback-safe evidence 才可供 Product final 判断；planning、build 或 flash 不自动
   加分，KR 不归档，`OKR.md` 本轮不修改。

## 完成定义与剩余风险

Engineer 完成定义是：代码/tests/硬件文档、current U/B/V artifacts、严格计数、条件式唯一 build/flash/rollback、完整恢复和
`tech-done.md` 落盘。若三门仍未全绿，本 blocker 达到 `2/2`，必须明确 blocked 并在下一轮切换 Objective 或升级 CEO，
不得第三轮包装。

即使全部通过，仍只证明 upload/backup/vendor additive instrumentation/rollback-safe 维护链；未执行 motion，不证明 current
nonzero wheel feedback、HIL、safe-to-control、route execution、delivery/operator acceptance 或 mission。
