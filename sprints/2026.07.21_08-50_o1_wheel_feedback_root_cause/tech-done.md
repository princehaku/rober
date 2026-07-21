# Tech Done：O1 轮速反馈根因诊断

## 状态与 proof boundary

- `sprint_type: epic`
- `IMPLEMENTATION_STATUS=IMPLEMENTED_AND_VALIDATED`
- `proof_boundary=offline_vendor_v8_diagnostic_plus_single_remote_readonly_inventory_only`
- `primary_classification=encoder_update_path_not_observed`
- `primary_classification_status=highest_priority_unconfirmed`
- `current_run_artifact_delta=true`
- `external_artifact_delta=readonly_runtime_inventory_only`
- `live_control_delta=false`
- `user_action_delta=false`
- `okr_credit=product_review_required_supporting_diagnostic_default_flat`

本轮已复用批准的 `tech-plan.md`，没有再开 planning/review/handoff wrapper。已实现离线 CLI、hostile-input 单测、真实 v8
诊断 artifacts、一次严格只读上位机 inventory 与硬件文档同步。该结果把根因入口从“再运动猜测”收窄到 runtime identity 与
raw encoder counter 可观测性，但不确认物理根因，也不证明 HIL 或 safe-to-control。

## 已读 vendor 来源

Hardware Engineer 已读取并采用：

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_config.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/WAVE_ROVER_V0.9.ino`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`

真实输出中的 vendor fact table 已记录每个 source SHA-256 与 symbol/line evidence。关键核验为：

- `json_cmd.h`：`FEEDBACK_BASE_INFO=1001@L1`、`CMD_PWM_INPUT=11@L58`、`CMD_ROS_CTRL=13@L61`、
  `CMD_BASE_FEEDBACK=130@L102`、`CMD_BASE_FEEDBACK_FLOW=131@L106`、`CMD_MM_TYPE_SET=900@L575`。
- `uart_ctrl.h`：T=11 dispatch `@L16`，`leftCtrl/rightCtrl @L19/L20`。
- `movtion_module.h`：`initEncoders @L141`、`getLeftSpeed @L170`、`getRightSpeed @L182`、
  `speedGetA/B=pwmIntA/B @L235/L265`。
- `ugv_advance.h`：T=1001 `L/R` 来自 `speedGetA/speedGetB @L386/L387`。
- `ugv_config.h`：源码默认 `mainType=1 @L38`；该默认值不等于板上 runtime 观察。
- `WAVE_ROVER_V0.9.ino`：setup 调 `initEncoders @L216`；loop 在 feedback 前调用 `getLeftSpeed @L248`、
  `getRightSpeed @L252`，之后才进入 `baseFeedbackFlow @L260`。
- `base_ctrl.py`：newline-delimited JSON write `@L182`。

## 实际改动

1. `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_feedback_root_cause.py`
   - 新增纯 Python/标准库 CLI：`--v8-artifact-dir`、`--vendor-source-root`、可选
     `--runtime-inventory-json`、`--output`。
   - 严格校验 vendor 文件、宏值、代码分支、source line/hash；缺失、重复或冲突均 fail closed。
   - 严格读取 v8 JSON/JSONL，重算 authorization/attempt identity、exactly-once counts、T=11/T=1001 counts、command
     window、normalized/vendor-frame 一致性、post-stop 与 final stop。
   - 严格校验 runtime inventory schema、只读 allowlist、每条命令 exit/摘要、显式 null 观察与零 mutation counters。
   - 输出稳定 schema `trashbot.wave_rover.feedback_root_cause_diagnostic.v1`、6 个有序 candidates 与唯一下一维护动作。
   - 输入坏 JSON/JSONL、缺文件、vendor symbol 冲突、v8 count 冲突、危险 true、runtime 缺字段时 exit `4`；正常诊断
     exit `0`，但四个安全结论仍固定 false。
2. `onboard/src/ros2_trashbot_hardware/test/test_wave_rover_feedback_root_cause.py`
   - 新增 `12` 个测试，覆盖正常 vendor+v8、缺 v8、count conflict、非法 JSON、非法 JSONL、危险 safety true、vendor
     symbol 缺失、vendor define 冲突、runtime inventory 缺字段/伪装 mutation、合法 readonly inventory 和 CLI output。
3. `docs/hardware/wave_rover_nonzero_feedback_hil_gate.md`
   - 补充参考源码中 T=11 dispatch、encoder refresh、T=1001 采样顺序，解释为什么 T=1001 不是 T=11 PWM echo。
   - 记录 CLI 用法、真实结果、只读 inventory 边界与唯一维护动作。
4. `sprints/2026.07.21_08-50_o1_wheel_feedback_root_cause/artifacts/root_cause_diagnostic.json`
   - 计划内、不带 runtime inventory 的 deterministic 真实输出。
5. `sprints/2026.07.21_08-50_o1_wheel_feedback_root_cause/artifacts/readonly_runtime_inventory.json`
   - 一次严格只读 SSH inventory 的完整 allowlist、逐命令 exit code、脱敏摘要、observations/hash 和零 mutation 计数。
6. `sprints/2026.07.21_08-50_o1_wheel_feedback_root_cause/artifacts/root_cause_diagnostic_with_inventory.json`
   - 合并只读 inventory 后的真实诊断；runtime ESP32 `mainType` 与 firmware identity 继续显式 `null/not_observed`。
7. `sprints/2026.07.21_08-50_o1_wheel_feedback_root_cause/tech-done.md`
   - 用真实实现、验证与风险替换此前 runtime-blocked 记录；Product closeout 文件仍留给 Product owner。

## 已证实硬件与 artifact 结论

### v8 冻结证据重算

CLI 对冻结 artifacts 重算并通过：

- authorization：`ceo_20260721_0651_current_wheel_feedback_hil_v8=consumed_no_retry`
- attempt：`o1-current-wheel-feedback-hil-v8-attempt-1`
- historical exactly-once：`pre/nonzero/post/retry=1/1/1/0`
- historical bridge T=11：`nonzero=6`、`zero=8`
- historical T=1001：总计 `14`，command window 内 `3`，nonzero pair `0`
- during-window pairs：`[0,0] [0,0] [0,0]`
- normalized `left_speed/right_speed` 与每帧 `vendor_frame.L/R` 一致
- `final_stopped=true`
- `raw_serial_byte_capture=false`、`T=13 wire not observed`、direct `T=130 not observed`

因此 `bridge_parser_consistent_with_vendor_frame=observed`；parser 不是当前首修对象。参考源码证明 loop 在 feedback 前刷新
encoder speed，而 v8 同窗仍为 0/0，所以首要候选为 `encoder_update_path_not_observed`。该词的边界是“更新链/计数尚不可见”，
不是“已确认 encoder 损坏”。

### 严格只读上位机 inventory

本轮执行一次 SSH session，远端命令只由以下五类组成并以 `&&` 串联；session exit `0`，所以五条都 exit `0`：

1. `systemctl show trashbot-esp32-bridge.service --no-pager --property=Id,ActiveState,SubState,MainPID,ExecStart,FragmentPath`
2. `systemctl cat trashbot-esp32-bridge.service --no-pager`
3. `ps -C python3 -o pid=,ppid=,comm=,args=`
4. `ss -ltnp`
5. `sha256sum` 读取 deployed `esp32_bridge_node.py`、`wave_rover_feedback.py`、`wave_rover_protocol.py`、
   `esp32_bridge_http.sh` 与 `trashbot-esp32-bridge.service`

只读事实：bridge service 为 `active/running`；unit 配置为 `command_mode=pwm`、`bridge_main_type=1`、`module_type=0`、
`/dev/ttyS5 @ 115200` 和 HTTP transport；five deployed hashes 已冻结。`bridge_main_type=1` 只是上位机 unit 配置，不能证明
ESP32 runtime `mainType=1`。本次只读接口没有暴露 ESP32 binary/build identity，故：

- `runtime_main_type_not_observed`
- `runtime_firmware_identity_not_observed`

## 验收结果

### 计划内命令

1. py_compile：exit `0`。

```text
python3 -m py_compile ...wave_rover_feedback_root_cause.py ...test_wave_rover_feedback_root_cause.py
exit=0
```

2. targeted unittest：exit `0`。

```text
............
----------------------------------------------------------------------
Ran 12 tests in 0.055s

OK
```

3. 真实 v8 CLI：exit `0`。

```text
sprints/2026.07.21_08-50_o1_wheel_feedback_root_cause/artifacts/root_cause_diagnostic.json
status=diagnostic_complete_fail_closed
input_valid=true
primary_classification=encoder_update_path_not_observed
validation_errors=[]
```

4. `python3 -m json.tool .../root_cause_diagnostic.json >/dev/null`：exit `0`。

5. 完整 safety assertions：

```text
root-cause safety assertions: PASS
```

6. 中文注释比例：

```text
chinese_comment_ratio=20.40%
```

7. scoped diff check：exit `0`。

```text
git diff --check -- <approved paths>
exit=0
```

### 额外只读 inventory 验收

```text
SSH readonly inventory session exit=0
readonly inventory diagnostic assertions: PASS
readonly_runtime_inventory.json json.tool exit=0
root_cause_diagnostic_with_inventory.json json.tool exit=0
```

## 首次失败与修复

首轮 py_compile、unittest、真实 CLI 与完整验收均未出现运行失败。模块首次落盘后的静态自检在执行测试前发现 vendor define
验证分支对空匹配存在潜在 `matches[0]` 访问；已先把判断改为 `len(matches) == 1 and matches[0][0] == expected`，随后 hostile
`vendor symbol missing`/`define conflict` 测试与全量 `12` tests 一次通过。没有隐藏或跳过失败命令。

## 安全与 mutation 计数

- 本轮 SSH session=`1`（严格只读）
- HTTP GET/POST/PUT/PATCH/DELETE=`0/0/0/0/0`
- ROS command/param/lifecycle=`0/0/0`
- serial/UART open/write=`0/0`
- motion/control/stop/nonzero=`0/0/0/0`
- service stop/restart/kill/mutation=`0/0/0/0`
- deploy/firmware mutation=`0/0`
- v8 reuse/retry=`0/0`
- 顶层 `motion_command_count=0`
- 顶层 `service_mutation_count=0`
- 顶层 `uart_write_count=0`
- 顶层 `firmware_mutation_count=0`

用户本轮运动授权未被本 sprint 消费；v8 仍保持 `consumed_no_retry`，没有补采、重发或不同 wrapper retry。

## 剩余风险与唯一下一动作

仍未验证：

- deployed ESP32 firmware 是否与本地 V0.9 source 一致；
- ESP32 runtime `mainType`；
- raw encoder A/B counter delta 与 encoder wiring/signal；
- byte-for-byte raw UART timing；
- nonzero wheel feedback、HIL、safe-to-control、route execution 或 delivery。

唯一下一动作：`maintenance_freeze_runtime_identity_then_observe_raw_encoder_counters`。取得独占 service/UART/firmware 维护授权后，
先冻结 deployed ESP32 firmware identity 与 runtime `mainType`，再增加或读取 raw encoder A/B counter delta；在 counter path
可观测前不批准新的 motion retry。任何 service stop/restart、UART claim、T=900 或 firmware instrumentation/flash 都不在本轮授权
内，必须由 CEO/现场 owner 另行批准。

本轮固定 `hil_pass=false`、`safe_to_control=false`、`route_execution_success=false`、`delivery_success=false`；建议 O1 主百分比
保持 flat、KR `不归档`，由 Product owner 完成 side-to-side、final、OKR 与 progress log 的保守收口。
