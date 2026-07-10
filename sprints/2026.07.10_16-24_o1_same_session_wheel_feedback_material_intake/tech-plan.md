# O1 Same-session WAVE ROVER Wheel Feedback Material Intake Tech Plan

## sprint_type

sprint_type: epic

## 目标

新增一个当前可复验、脱敏、fail-closed 的 O1 WAVE ROVER same_session wheel_feedback material intake。该 intake 消费历史真实上位机 artifact，输出 `trashbot.wave_rover_same_session_wheel_feedback_material.v1` 或等价清晰命名，并固定 `hil_pass=false`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。本轮只规划 implementation，不修改产品进度和代码。

## 用户价值和产品北极星

用户需要的是能把底盘真实反馈材料纳入可审计证据链，而不是把历史材料包装成当前 HIL 通过。该 intake 能把“同一手控会话里出现过 `T=1001 L/R=61/61`，stop 后回到 `0/0`”变成后续可回归的软件合同，同时保留所有安全动作关闭状态。

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节里完成度最低的 Objective 是 O5，约 85%。
2. 本 sprint 不针对最低 Objective O5，而是转向次低 Objective O1，约 86%。
3. 不推进 O5 的具体理由：
   - O5 下一步必须消费真实 production cloud、production DB/queue、真实 live endpoint、真实 browser/手机或生产 worker/cutover 材料。
   - 当前环境没有这些外部材料。
   - `2026.07.10_08-14_same_task_mission_artifact_credit_gate` 已把 local/mock probe、readback-only、checklist-only、support-only 工作固定为 `okr_credit_allowed=false`，继续做 O5 wrapper 不应再计 OKR。
4. 转向 O1 的理由：
   - O1 仍缺真实或准现场同 run wheel feedback / motion command / operator material。
   - 仓库已有更强历史真实上位机材料，可消费 `T=1001 L/R=61/61` 与 stop 后 `0/0`，适合推进一个 material intake。
   - 本轮会明确不证明完整 HIL、不证明 delivery success、不打开 primary actions，因此不会越界计分。

## Owner

- 主责 owner：`robot-hardware-engineer`
- 执行方式：单线闭环。
- `robot-hardware-engineer` 负责后续实现、测试、修复和 `tech-done.md`。
- Product / 主节点只负责验收、side2side_check 和 final 收口，不直接写代码、不运行实现命令、不修改硬件配置。

## 后续 implementation 文件范围

允许 `robot-hardware-engineer` 后续修改：

- `onboard/src/ros2_trashbot_hardware/**/*`
- `onboard/tests/**/*wave*rover*`
- `onboard/tests/**/*hardware*`
- `docs/hardware/**/*.md`
- `sprints/2026.07.10_16-24_o1_same_session_wheel_feedback_material_intake/tech-done.md`

只读输入材料：

- `sprints/2026.06.22_11-00_wheel_lr_samesession_first_jog/artifacts/01_upper_manual_samesession_012.json`
- `sprints/2026.06.22_11-00_wheel_lr_samesession_first_jog/tech-done.md`
- `sprints/2026.06.27_00-42_first_jog_motion_feedback_window/tech-done.md`
- `sprints/2026.07.10_10-30_o1_wave_rover_nonzero_feedback_hil_gate/tech-done.md`

禁止后续 implementation 修改：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- 本 sprint `pre_start.md`、`prd.md`、`tech-plan.md`，除非 Product 明确要求修正 planning
- 云端、O6/O7、PC UI、Nav2 或无关产品文件

## 计划任务

### 1. Vendor 与历史材料事实对齐

- 复核 `docs/vendor/VENDOR_INDEX.md` 指向的 WAVE ROVER 本地资料，采用 UART newline-delimited JSON、`T=130` feedback request、`T=1001` base feedback 等事实。
- 读取历史 artifact，确认同一 manual session 内包含：
  - motion command：`T=1 L=0.12 R=0.12`
  - feedback request：`T=130`
  - motion window feedback：`T=1001 L/R=61/61`
  - stop command：`T=1 L=0 R=0`
  - after-stop feedback：`T=1001 L/R=0/0`
- 在文档和输出里明确这是历史真实上位机材料，不是 current live HIL pass。

### 2. Material intake 合同

- 新增一个 O1 material intake 输出，建议命名为 `trashbot.wave_rover_same_session_wheel_feedback_material.v1`。
- 输出字段建议包括：
  - `schema`
  - `status`
  - `proof_scope`
  - `source_refs`
  - `same_session_material_present`
  - `motion_command_present`
  - `feedback_request_present`
  - `wheel_feedback_material_present`
  - `latest_nonzero_pair`
  - `stop_zero_readback_present`
  - `blocked_reasons`
  - `next_required_evidence`
  - `hil_pass=false`
  - `safe_to_control=false`
  - `delivery_success=false`
  - `primary_actions_enabled=false`
- 所有字段缺失、类型错误或语义不一致时，默认 blocked。

### 3. 脱敏与 fail-closed 规则

- 只输出 safe summary；不得输出 raw artifact payload、完整绝对路径、token、URL、base64、traceback 或串口敏感上下文。
- 输入出现下列情况必须 fail-closed：
  - 缺少 `T=1001`
  - nonzero pair 不在 same-session motion window
  - stop 后没有 `0/0` readback
  - safety 字段被输入设置为 true
  - schema/source 与预期不一致
  - JSON 解析失败、非 object、字段类型异常
- fail-closed 时仍可保留安全的 blocked reason 和 next required evidence，方便现场补证。

### 4. 测试与文档

- 增加单元测试覆盖：
  - positive historical artifact：提取 `T=1001 L/R=61/61` 与 stop 后 `0/0`
  - missing nonzero feedback blocked
  - missing stop-zero readback blocked
  - unsafe true fields blocked
  - raw/path/token/url/traceback 不外泄
- 同步最小硬件文档，说明采用的 vendor 来源、历史材料来源、证据边界和后续 current live HIL 所需材料。
- implementation 完成后更新本 sprint `tech-done.md`，记录实际改动、验证结果、失败定位和剩余风险。

## 验收命令

后续 implementation 必须至少运行：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_hardware/**/*.py
python3 -m unittest discover -s onboard/src/ros2_trashbot_hardware/test -p '*wave*rover*.py'
git diff --check -- onboard/src/ros2_trashbot_hardware docs/hardware sprints/2026.07.10_16-24_o1_same_session_wheel_feedback_material_intake
```

如果实际实现落在 `onboard/tests/`，Hardware owner 可增加等价 scoped unittest，但不得少于：

- Python 编译检查
- WAVE ROVER / hardware intake 单元测试
- scoped `git diff --check`

本 planning 阶段验收命令为：

```bash
test -f sprints/2026.07.10_16-24_o1_same_session_wheel_feedback_material_intake/pre_start.md && test -f sprints/2026.07.10_16-24_o1_same_session_wheel_feedback_material_intake/prd.md && test -f sprints/2026.07.10_16-24_o1_same_session_wheel_feedback_material_intake/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|O5|O1|same_session|wheel_feedback|T=1001|robot-hardware-engineer|hil_pass=false|delivery_success=false|safe_to_control=false" sprints/2026.07.10_16-24_o1_same_session_wheel_feedback_material_intake
git diff --check -- sprints/2026.07.10_16-24_o1_same_session_wheel_feedback_material_intake
```

## 接口影响

- 仅新增 O1 material intake 的只读软件摘要，不改变控制策略、launch 默认值、串口配置或真实硬件动作。
- 不写入 OKR 进度，不更新进度日志。
- 若后续需要给 O6/O7 消费，应另起 sprint 或在收口后由 Product 重新定范围。

## 证据边界

必须固定：

- `proof_scope=software_proof_o1_same_session_wheel_feedback_material_intake_only`
- `hil_pass=false`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`

不能宣称：

- current live HIL pass
- hardware safe-to-control
- delivery success
- Nav2 route execution success
- production cloud / DB / endpoint success

## 风险和阻塞

- 历史材料能证明真实上位机 same-session wheel feedback material 存在，但不是当前 live HIL。
- 如果只做 wrapper/checklist 而未消费历史 artifact，则不满足本轮目标。
- 当前仍需要新的同 run `feedback_T1001.log`、motion command record、operator report 和 HIL acceptance record，才能推进 O1 的真实现场验收。
- 后续收口时若没有新增 material intake 测试输出，Product 不应上调 O1 进度。

