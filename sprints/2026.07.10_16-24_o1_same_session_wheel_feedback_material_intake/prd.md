# O1 Same-session WAVE ROVER Wheel Feedback Material Intake PRD

## 用户价值和产品北极星

产品北极星仍是“机器人可以安全、可验证地完成垃圾收取与送达”。O1 的用户价值不是再新增一个 HIL 口号，而是把已经存在的真实上位机 wheel feedback 证据整理成当前可复验、可脱敏、可 fail-closed 消费的材料合同。这样后续做真实上车 HIL 时，团队能清楚区分“历史 same-session wheel feedback material 已被安全接入”和“当前 live HIL pass 尚未证明”。

## OKR 映射和方向判断

- 映射 Objective：O1 硬件协议可信底盘。
- 方向判断：**调整执行重心到 O1，暂停 O5 的新增百分比推进**。
- 判断理由：
  1. O5 约 85%，是当前最低 Objective，但下一步必须有真实 production cloud、production DB/queue、真实 live endpoint 或真实 browser/手机材料。
  2. 当前环境没有这些 O5 外部材料，且 recent credit gate 已禁止 local/mock probe、readback-only、checklist-only 继续计 OKR。
  3. O1 约 86%，虽然不是最低，但有可消费的真实历史上位机材料：同一手控窗口内 `T=1001 L/R=61/61`，stop 后回到 `0/0`。
  4. 本轮 O1 不冒充 current live HIL pass，只把真实历史 material 接入当前可验证、可回归的 intake 合同。

## KR 拆解

本轮不归档 KR，也不调整 `OKR.md`。后续 implementation 应推进 O1 当前 KR 的材料化子项：

1. **材料消费**：读取 `sprints/2026.06.22_11-00_wheel_lr_samesession_first_jog/artifacts/01_upper_manual_samesession_012.json`，消费同一会话内 motion command、feedback request、`T=1001` nonzero wheel feedback 与 stop 后 `0/0`。
2. **合同输出**：新增 `trashbot.wave_rover_same_session_wheel_feedback_material.v1` 或等价清晰命名，至少包含 material status、source references、same-session 判断、nonzero pair summary、stop-zero readback、blocked reasons、next required evidence 和固定 false safety fields。
3. **脱敏与 fail-closed**：只输出 safe summary，不输出 raw payload、绝对路径、串口设备完整上下文、token、URL、traceback 或 base64；缺字段、错 schema、危险 true、source mismatch、不可证明 same-session 时必须 blocked。
4. **证据边界**：固定 `hil_pass=false`、`delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`，不得把历史材料写成 current live HIL pass。

## 本轮核心抓手

核心抓手是“material intake”，不是再写 review、handoff 或状态面板。Hardware owner 要把 6 月真实上位机材料变成一个当前可跑测试、可被后续 O1/O6/O7 消费的安全摘要合同。该合同应为下一轮真实现场执行命令服务：当新的 same-run `feedback_T1001.log`、motion command、operator report 或 HIL acceptance record 到位时，可以直接替换输入材料进行判定。

## 需要做什么

- 规划一个单 owner implementation，让 `robot-hardware-engineer` 完成：
  - material intake 脚本或模块；
  - unit tests / smoke fixture；
  - 最小硬件文档同步；
  - 本 sprint `tech-done.md` 留档。
- Product / 主节点只做验收和收口，不进入代码实现。
- 本 planning 阶段只创建 `pre_start.md`、`prd.md`、`tech-plan.md`。

## 优先级和验收口径

- 优先级：P0。
- 验收口径：
  1. 能在当前 macOS 环境复验，不依赖真实硬件、4G、cloud 或浏览器。
  2. 能从历史真实 artifact 中提取 `T=1001 L/R=61/61` 与 stop 后 `0/0`，并标记 same-session material present。
  3. 能对危险输入 fail-closed，并把 `hil_pass=false`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false` 固定为不可被输入覆盖。
  4. 能清楚输出 next required evidence：current live same-run feedback log、motion command record、operator material、HIL acceptance record。
  5. 不修改 `OKR.md` 或 `docs/process/okr_progress_log.md`；收口后再由 Product 判断是否需要更新进度。

## 对应责任 Engineer

- `robot-hardware-engineer`

## 风险、阻塞和需要补齐的证据链

- 历史 artifact 是真实上位机材料，但不是当前 live run；不能作为当前 HIL pass。
- `T=1001 L/R=61/61` 能证明历史 same-session wheel feedback material 存在，但不能单独证明完整路线执行、Nav2 成功、delivery success 或 hardware safety。
- 仍缺当前同 run 的：
  - `feedback_T1001.log`
  - motion command record
  - operator report / external observation material
  - HIL acceptance record
- 如果实现只产出 wrapper、review 或 checklist，而没有消费上述历史 artifact 并生成合同，应视为 support-only，不允许计入 O1 进度。

## 已完成 KR 的历史记录位置、证据来源和剩余风险

- 本轮 planning 不移动已完成 KR，不更新 `OKR.md` 历史区。
- 证据来源：
  - `sprints/2026.06.22_11-00_wheel_lr_samesession_first_jog/artifacts/01_upper_manual_samesession_012.json`
  - `sprints/2026.06.22_11-00_wheel_lr_samesession_first_jog/tech-done.md`
  - `sprints/2026.06.27_00-42_first_jog_motion_feedback_window/tech-done.md`
  - `sprints/2026.07.10_10-30_o1_wave_rover_nonzero_feedback_hil_gate/tech-done.md`
  - `sprints/2026.07.10_10-30_o1_wave_rover_nonzero_feedback_hil_gate/final.md`
- 剩余风险：这些材料足以启动 material intake，不足以把 O1 标为 HIL 完成或 safe-to-control 完成。

## 需要创建或更新的 sprint 文档

本轮创建：

- `sprints/2026.07.10_16-24_o1_same_session_wheel_feedback_material_intake/pre_start.md`
- `sprints/2026.07.10_16-24_o1_same_session_wheel_feedback_material_intake/prd.md`
- `sprints/2026.07.10_16-24_o1_same_session_wheel_feedback_material_intake/tech-plan.md`

implementation 和收口阶段后续再补：

- `tech-done.md`
- `side2side_check.md`
- `final.md`

