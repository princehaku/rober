# Tech Plan：O1 runtime identity / raw encoder 独占维护

## 状态、授权与单 owner

- `status: planning_complete`
- `sprint_type: epic`
- 单一实现、现场与修复 owner：`rober-hardware-engineer`
- `O1_EXCLUSIVE_SERVICE_UART_FIRMWARE_MAINTENANCE_AUTHORIZED=true`
- `AUTHORIZATION_RECONFIRM_REQUIRED=false`
- CEO blocker reset / continue 原话：“我都授权过了”“继续推进啊”
- `ENGINEER_DISPATCH_READY=true`

不得再次向 CEO 询问相同授权。完整授权已覆盖 operator 看护、路线清空、物理限位、所有运动与部署、
service/systemd stop/restart、必要 holder termination、独占 `/dev/ttyS5@115200`、`T=900`、diagnostic maintenance deploy、
必要的 ESP32 instrumentation/build/flash，以及 counter 可观测后的一次 supervised minimal motion。旧 v8
`consumed_no_retry` 不复用；本轮必须生成新的 attempt identity。

## 强制 vendor 来源

Hardware 执行前必须逐个读取并在 `tech-done.md` 记录采用的 symbol/line/hash：

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_config.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/WAVE_ROVER_V0.9.ino`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`

必须采用的 vendor facts：UART 是 UTF-8 newline-delimited JSON，目标现场端口为已冻结的
`/dev/ttyS5@115200`；`T=900` 是 `CMD_MM_TYPE_SET`；`T=1001 L/R` 来自 `speedGetA/speedGetB`；
encoder 初始化/读取来自 `initEncoders/getLeftSpeed/getRightSpeed`。源码默认 `mainType=1` 不是 runtime 证明。

## Hardware 精确本地文件范围

Engineer 只允许创建或修改：

- `onboard/scripts/o1_runtime_identity_raw_encoder_maintenance.py`
- `onboard/tests/test_o1_runtime_identity_raw_encoder_maintenance.py`
- `onboard/src/esp32_firmware/**`（仅 instrumentation 必要时；必须建立 vendor V0.9 派生的隔离诊断工程）
- `docs/hardware/wave_rover_nonzero_feedback_hil_gate.md`
- `sprints/2026.07.28_17-59_o1_runtime_identity_raw_encoder_maintenance/artifacts/**`
- `sprints/2026.07.28_17-59_o1_runtime_identity_raw_encoder_maintenance/tech-done.md`

不得修改 `docs/vendor/**`、vendor factory binary、旧 sprint、`OKR.md`、workstation、Nav2 或其他产品代码。当前
`onboard/src/esp32_firmware/main.cpp` 是不同的 binary-protocol 示例，不能直接刷入 vendor newline-JSON WAVE ROVER；
若使用该目录，必须新增隔离的 `wave_rover_v0_9_diagnostic` 子工程，保存 canonical vendor source hashes、派生 patch 与
build provenance，不得让现有 generic `main.cpp` 进入 upload image。

Product 收口文件 `side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md` 不在 Hardware 范围内。

## 接口影响

1. 新增独立 maintenance runner CLI；不改变 ROS topic、Upper API、Nav2 或正常 bridge 合同。
2. 正常路径优先直接解析现有 UART/`T=1001`。若必须 instrumentation，只允许对 vendor V0.9 的 `T=1001` 增加 additive
   diagnostic fields：safe firmware build id、runtime `mainType`、module type、raw encoder A/B counts；既有 `T/L/R/r/p/y/v`
   字段不得删除、改名或改变语义。
3. 新增字段必须由 runner 独立解析；现有 bridge 对未知 additive fields 应继续兼容。除非测试证明兼容性问题，不修改 bridge。
4. `T=900` send/echo 只证明 current command 送达，不等于 runtime mainType readback；runtime 值必须来自 current
   machine-readable feedback/instrumentation。

## Artifact schema 与安全字段

主 artifact：
`sprints/2026.07.28_17-59_o1_runtime_identity_raw_encoder_maintenance/artifacts/maintenance_result.json`

schema 固定为 `trashbot.wave_rover.runtime_identity_raw_encoder_maintenance.v1`，至少包含：

- identity：`attempt_id`、`authorization_id`、`captured_at`、host hash prefix；
- provenance：vendor source hashes、deployed hashes before/after、flash backup hash、instrumented source/build/image hash；
- runtime：firmware identity before/after、runtime `mainType`/module type before/after；
- counters：静止和 motion window 的 timestamped raw encoder A/B samples、delta A/B、`speedGetA/speedGetB`、T=1001；
- actions：allowlisted command ledger、phase/exit/error、service/holder/UART/build/flash/motion/stop/rollback counts；
- restoration：service/holder before/after、final stop/readback、rollback result、run-owned residual；
- evidence boundary 与 `current_run_artifact_delta` / `external_artifact_delta` / `live_control_delta`。

所有路径只输出安全 basename/hash。顶层必须始终显式包含：

```text
instrumentation_success=<true|false>
hil_pass=false
safe_to_control=false
route_execution_success=false
delivery_success=false
mission_attempt=false
```

不可把 `instrumentation_success=true`、`build_count=1`、`flash_count=1`、counter 字段存在或静止 counter=0 当作 HIL、route、
delivery、mission 或 `safe_to_control`。只有 Product final 能依据完整 current evidence调整结论。

## Exactly-once 与计数合同

一个 runner、一个 maintenance window、一个 attempt：

```text
runner_invocation_count=1
maintenance_window_count=1
inventory_invocation_count=1
pre_stop_invocation_count=1
service_stop_count<=1
holder_termination_count<=1
uart_open_count<=1
t900_write_count<=1
instrumentation_build_count<=1
instrumentation_flash_count<=1
rollback_flash_count<=1
nonzero_motion_invocation_count<=1
post_stop_invocation_count<=1
final_stop_verification_count=1
service_restore_count<=1
retry_count=0
second_motion_count=0
```

counter/feedback observability gate 未通过时：
`nonzero_motion_invocation_count=0`。通过后，唯一 motion 参数冻结为 vendor `T=11,L=164,R=164`、最长 `300ms`，不得改变
command mode、延长时间或第二次尝试。一次逻辑 stop 可写多种 vendor zero frame，但 artifact 必须区分 logical stop count 与
raw UART frame count。

## 远端 action allowlist

唯一目标为 `ssh root@192.168.1.11 -p 37878`。runner 必须冻结 stdin/request SHA 和以下 allowlist；范围外命令立即停止。

### A. Inventory、hash 与 toolchain check

- `date`、`hostname`/`uname` 的脱敏 inventory；
- `systemctl show/status/cat/is-active trashbot-esp32-bridge.service`；
- `ps`、`ss`、只读 `lsof /dev/ttyS5`、`fuser /dev/ttyS5`、`readlink`、`stat`、`test`、`ls`；
- `sha256sum` 冻结 service unit、deployed bridge/script/source、run-owned payload、firmware backup/build image；
- `journalctl -u trashbot-esp32-bridge.service` 的 bounded read；
- `command -v` 与只读 `--version` 检查 Python/pyserial、PlatformIO、Arduino CLI、esptool 及可用 upload device；
- 读取当前 health/base status/feedback 的 GET；不得用历史 latest 代替 current。

### B. 安全停机、service 与 holder

- mutation 前一次 existing Upper/base stop，写入 `pre_stop_invocation_count=1`；
- `systemctl stop trashbot-esp32-bridge.service`，随后验证 inactive；
- 再次 `lsof/fuser /dev/ttyS5`；只有 PID、start time、command 与冻结 holder 一致时才允许 `kill -TERM <exact_pid>`；
- 等待后若 exact PID 仍相同且持有端口，才允许一次 `kill -KILL <exact_pid>`；禁止 `killall`、宽泛 `pkill`、`fuser -k`；
- holder 不明、PID identity 变化或出现并发 task 时 fail closed。

### C. Diagnostic deploy、独占 UART 与 T=900

- `scp`/stdin 仅部署 hash-matched runner/patch 到唯一 run-owned
  `/tmp/trashbot-o1-runtime-encoder-<attempt_id>/`；允许 `mkdir`、`install/cp`、`chmod`、最后只删除该精确临时目录；
- 仅在 service inactive、holder empty 后由 runner 独占打开 `/dev/ttyS5@115200` 一次；
- 允许 vendor `T=143/142/131/130` 配置/查询、一次 `T=900,main=1,module=0` 与 vendor zero frames；
- 不允许任何未列明 JSON command；所有 raw TX/RX frame、时间、write bytes 与 parse result 进入 artifact。

### D. 条件式 instrumentation / PlatformIO build/upload

仅当现有 firmware 无法 current readback firmware identity/runtime `mainType`/raw counters 时进入：

- 从 canonical vendor V0.9 source 生成隔离诊断工程，验证 source hash 和 additive patch；
- additive instrumentation 只暴露 build id、runtime `mainType`/module type、encoder A/B raw counts 与既有 speed values；
- 先用已验证的 esptool/PlatformIO upload device 读取当前 flash backup、hash 并验证可回滚；无法 backup 则禁止 flash；
- `platformio run --project-dir onboard/src/esp32_firmware/wave_rover_v0_9_diagnostic` 最多一次 build；
- 仅在 build/provenance/backup 全绿后允许一次
  `platformio run --project-dir onboard/src/esp32_firmware/wave_rover_v0_9_diagnostic --target upload --upload-port <verified_port>`；
- 禁止覆盖 `docs/vendor/waveshare_wave_rover/WAVE_ROVER_FACTORY/**`；factory binary 只作只读 provenance，不作默认 rollback。

### E. 条件式 minimal motion、恢复与 rollback

- flash 后先无运动复验 runtime/counter fields；字段缺失或 invalid 时 motion=`0`；
- observability gate 全绿后才允许一次 `T=11,L=164,R=164`，最长 `300ms`；
- motion 结束或任何异常立即 direct UART post-stop；不得 retry；
- 若 instrumentation readback/compatibility/service recovery 失败，使用本轮 flash backup 执行最多一次 rollback flash；
- `systemctl start trashbot-esp32-bridge.service`，验证 active/running、唯一 expected holder 重新占有 `/dev/ttyS5`；
- 最终通过现有 stop path 再确认 zero/stopped，保存 final current feedback、service/holder/hash 和 residual；
- 无法确认 stop、rollback 或 service/holder 恢复时保持 fail closed，并由 operator 维持物理限位。

## 执行阶段与失败分支

1. **Phase S：离线实现与测试**
   实现 runner、mock/hostile tests、schema validator、命令 allowlist 与 dry-run。失败必须修复并完整复验。
2. **Phase 0：冻结 current 基线**
   保存 authorization/attempt、operator 条件、service/holder/hash/toolchain/provenance。并发 task、身份漂移或 pre-stop 未确认即
   NO-GO；仍写 final artifact。
3. **Phase 1：独占 UART、无运动事实**
   stop service、必要 holder termination、独占 UART、current T=900/feedback/runtime/counter readback。能直接观察则跳过 flash。
4. **Phase 2：条件式 instrumentation/build/flash**
   只有缺少 required runtime/counter fields 才进入。toolchain/upload/backup 任一不可用时不得 flash，但必须留下 current
   runtime/raw-counter blocked artifact、真实 blocker 与恢复证据，不能退化为 planning-only。
5. **Phase 3：条件式 exactly-once motion**
   counter/feedback observability 全绿才执行一次 minimal motion。counter delta 为零或 nonzero 都是有效 current evidence；
   不得因结果不理想而 retry。
6. **Phase 4：stop、rollback、恢复、封存**
   恢复 firmware（若需）、service、holder 和 zero state，写出 final artifact 与 `tech-done.md`。

任何 transport 断开、UART exception、invalid frame、PID identity 变化、build/upload 失败、flash verify 失败、counter schema
不完整、stop 缺失或 service 恢复失败，都跳转 Phase 4；`retry_count=0`、`second_motion_count=0`。

## Engineer 验收命令

Hardware 必须运行、修复至通过，并把关键原始输出写入 `tech-done.md`：

```bash
python3 -m py_compile \
  onboard/scripts/o1_runtime_identity_raw_encoder_maintenance.py \
  onboard/tests/test_o1_runtime_identity_raw_encoder_maintenance.py

python3 -m unittest \
  onboard/tests/test_o1_runtime_identity_raw_encoder_maintenance.py

python3 onboard/scripts/o1_runtime_identity_raw_encoder_maintenance.py \
  --mode fixture \
  --fixture-dir sprints/2026.07.28_17-59_o1_runtime_identity_raw_encoder_maintenance/artifacts/fixtures/pass \
  --output sprints/2026.07.28_17-59_o1_runtime_identity_raw_encoder_maintenance/artifacts/mock_maintenance_result.json

python3 onboard/scripts/o1_runtime_identity_raw_encoder_maintenance.py \
  --mode ssh-maintenance \
  --ssh-host root@192.168.1.11 \
  --ssh-port 37878 \
  --authorization-id ceo_20260728_complete_motion_deploy_service_uart_firmware_maintenance \
  --attempt-id o1-runtime-identity-raw-encoder-maintenance-attempt-1 \
  --allow-instrumentation-build-flash \
  --allow-supervised-minimal-motion-after-observability \
  --output sprints/2026.07.28_17-59_o1_runtime_identity_raw_encoder_maintenance/artifacts/maintenance_result.json

python3 -m json.tool \
  sprints/2026.07.28_17-59_o1_runtime_identity_raw_encoder_maintenance/artifacts/maintenance_result.json \
  >/dev/null

python3 - <<'PY'
import json
from pathlib import Path
p = Path("sprints/2026.07.28_17-59_o1_runtime_identity_raw_encoder_maintenance/artifacts/maintenance_result.json")
d = json.loads(p.read_text())
assert d["schema"] == "trashbot.wave_rover.runtime_identity_raw_encoder_maintenance.v1"
assert d["runner_invocation_count"] == 1
assert d["maintenance_window_count"] == 1
assert d["inventory_invocation_count"] == 1
assert d["pre_stop_invocation_count"] == 1
assert d["retry_count"] == 0
assert d["second_motion_count"] == 0
assert d["nonzero_motion_invocation_count"] in (0, 1)
if d["nonzero_motion_invocation_count"] == 1:
    assert d["counter_feedback_observability_gate"] is True
    assert d["post_stop_invocation_count"] == 1
assert d["service_restored"] is True
assert d["holder_restored"] is True
assert d["final_stopped"] is True
for key in ("hil_pass", "safe_to_control", "route_execution_success", "delivery_success", "mission_attempt"):
    assert d[key] is False, (key, d[key])
print("o1 maintenance artifact assertions: PASS")
PY

python3 - <<'PY'
from pathlib import Path
for name in (
    "onboard/scripts/o1_runtime_identity_raw_encoder_maintenance.py",
    "onboard/tests/test_o1_runtime_identity_raw_encoder_maintenance.py",
):
    lines = [line for line in Path(name).read_text().splitlines() if line.strip()]
    comments = [line for line in lines if line.lstrip().startswith("#")]
    ratio = len(comments) / len(lines) if lines else 0
    print(f"{name}: chinese_comment_ratio={ratio:.2%}")
    assert ratio > 0.20
PY

git diff --check -- \
  onboard/scripts/o1_runtime_identity_raw_encoder_maintenance.py \
  onboard/tests/test_o1_runtime_identity_raw_encoder_maintenance.py \
  onboard/src/esp32_firmware \
  docs/hardware/wave_rover_nonzero_feedback_hil_gate.md \
  sprints/2026.07.28_17-59_o1_runtime_identity_raw_encoder_maintenance
```

若创建 instrumentation 工程，额外运行并留存：

```bash
platformio run \
  --project-dir onboard/src/esp32_firmware/wave_rover_v0_9_diagnostic

platformio run \
  --project-dir onboard/src/esp32_firmware/wave_rover_v0_9_diagnostic \
  --target upload \
  --upload-port "${VERIFIED_WAVE_ROVER_ESP32_UPLOAD_PORT}"
```

upload 命令只能由 single maintenance runner 在 backup/provenance gate 全绿时执行一次；若未进入 instrumentation 分支，必须在
`tech-done.md` 明确 `instrumentation_build_count=0`、`instrumentation_flash_count=0` 及跳过理由。

## OKR 最低优先级核对

1. 当前最低 Objective 是 O5，约 `85%`。
2. 本 Epic 不推进 O5：production external evidence gate 未打开，provider/runtime 同根因已消费 `2/2`；继续 local
   wrapper、readiness packet 或 provider probe 违反 anti-repeat。
3. O6/O7 各约 `93%`，corrected Phase 0 lane 已 `2/2`，禁止第三轮 preflight/wrapper。
4. O1 约 `95%`，但 CEO 的完整 maintenance authorization 已把唯一真实硬件 lane 打开。本 Epic 直接消费 service/UART/
   firmware/runtime/raw-counter 现场证据，能降低下一次 HIL 与 mission 执行风险，因此切到 O1；不会因 planning、
   instrumentation/build/flash 自动加分。

## 完成定义与 Product 交接

Hardware 完成条件是：实际代码/tests/docs、离线验证、恰好一次真实 maintenance runner、current runtime/raw-counter artifact、
stop/rollback/service/holder 恢复和 `tech-done.md` 全部落盘。即使 toolchain 或 flash 入口不可用，也必须完成可复核 current
artifact 和恢复闭环，不能以 planning-only 交差。

Hardware 返回后 Product 才创建/更新 `side2side_check.md`、`final.md`、`OKR.md` 与历史记录。KR 是否归档、O1 是否调分，以及
`hil_pass` 是否仍为 false，均由 Product 基于 current evidence保守判断。
