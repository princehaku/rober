# Elevator Assisted Delivery Product Contract

## 状态

- 当前结论：已纳入 OKR 与产品 contract；是当前 MVP 需要完成的能力。
- 硬件边界：不新增 ESP32 下位机职责，不新增引脚、串口、波特率、电压或电梯控制假设。
- 能力归属：Orange Pi / ROS2 上位机的行为编排、感知判断、语音提示和手机状态解释。

## 用户价值和北极星

电梯 assisted delivery 的用户价值是让普通手机用户在楼宇场景里仍然只做“把垃圾交给小车、选择目标楼层/垃圾站、看状态”的动作。小车负责把跨楼层过程拆成可理解、可求助、可接管的低速流程。

它延续 `ros_rbs` 北极星：低成本 trash delivery，而不是机械臂捡垃圾，也不是全自动控制电梯。

## 最小用户流程

1. 用户在手机端选择目标垃圾站和目标楼层，例如 `1 楼垃圾站`。
2. 用户把垃圾放到小车上并确认发车。
3. 小车沿固定路线到达电梯厅，在电梯门口低速等待。
4. 小车识别电梯开门后进入电梯；如果超时未开门，进入 `needs_human_help`。
5. 小车进入电梯后播放语音：

```text
你好,好心人,.我要去1楼扔垃圾,请帮我按一下电梯,
```

6. 小车在电梯内持续等待目标楼层证据，并保持低速可停。
7. 小车判断到达目标楼层且电梯开门后，立即驶出电梯。
8. 小车继续前往目标楼层垃圾站/垃圾桶点位，完成投递/提醒人工取走。
9. 如果目标楼层、开门或驶出条件不可靠，小车停止并在手机端显示需要人工协助。

## 状态机边界

电梯子流程建议作为 `task_orchestrator` 的 H2 可选子状态，不默认进入 MVP 主链路。

| 状态 | 进入条件 | 退出条件 | 失败处理 |
| --- | --- | --- | --- |
| `approaching_elevator` | 任务目标需要跨楼层，且路线包含电梯厅 waypoint | 到达电梯厅等待点 | 导航失败则返回任务失败与人工接管 |
| `waiting_elevator_open` | 已到电梯厅等待点 | 电梯门开并且前方可进入 | 超时后提示人工协助 |
| `entering_elevator` | 电梯门开 | 已进入轿厢并停车 | 入内失败或门关闭则停止并请求人工处理 |
| `requesting_floor_help` | 已进入轿厢 | 语音播放完成并进入等待 | TTS/喇叭失败时手机端显示求助文案 |
| `waiting_target_floor` | 已请求按目标楼层 | 识别到目标楼层到达证据 | 超时或证据冲突则请求人工确认 |
| `exiting_elevator` | 目标楼层到达且电梯开门 | 已驶出电梯并到达目标楼层安全点 | 驶出失败则停止并请求人工接管 |
| `resume_delivery` | 已驶出电梯 | 继续导航到垃圾站/垃圾桶点位 | 按送达任务失败路径处理 |

## 识别要求

P0 识别要求：

- 电梯门是否开门：能区分 `door_open`、`door_closed_or_unknown`、`unsafe_to_enter`。
- 是否已进入电梯：能给出进入轿厢后的停车/等待证据。
- 是否到达目标楼层：必须有目标楼层到达证据，不能只靠固定等待时间。
- 目标楼层是否开门：必须同时满足目标楼层证据和门开证据，才允许驶出。

P1 识别要求：

- 识别当前楼层或楼层显示屏。
- 记录每次门开、进入、等待、驶出的相机快照引用。
- 把失败原因写入 diagnostics 和 task record。

## Dry-run Evidence Schema

本轮软件 dry-run 只定义离线证据结构，不做真实相机识别、楼层 OCR 或电梯实景验证。Robot Platform、Operator diagnostics 和后续视觉/路线证据统一消费 `elevator_assist.evidence` dict：

```json
{
  "schema_version": "elevator_assist.evidence.v1",
  "status": "target_floor_unconfirmed",
  "source": "visual_gate_offline_proof",
  "confidence": 0.0,
  "detail": "visual gate passed; elevator door and floor evidence remain unconfirmed",
  "checkpoint": 1,
  "observed_at": null,
  "robot_readable": "target floor evidence is not confirmed",
  "operator_readable": "未确认目标楼层。",
  "reliable": false,
  "allows_entry": false,
  "confirms_target_floor": false,
  "allows_exit": false,
  "requires_operator": true,
  "metadata": {}
}
```

允许的 `status` 固定为：

| Status | Robot 含义 | Operator 含义 | 行为含义 |
| --- | --- | --- | --- |
| `door_open` | 电梯门已打开。 | 电梯门已打开。 | 可作为进入电梯的必要证据之一。 |
| `door_closed_or_unknown` | 电梯门关闭或未知。 | 电梯门未打开或状态未知。 | 不允许进入；需要等待或人工协助。 |
| `inside_elevator` | 小车已在轿厢内停车。 | 小车已进入电梯并停车等待。 | 可进入请求按楼层和等待目标楼层阶段。 |
| `target_floor_confirmed` | 目标楼层证据已确认。 | 已确认到达目标楼层。 | 只确认楼层，不单独允许驶出。 |
| `target_floor_unconfirmed` | 目标楼层证据未确认。 | 未确认目标楼层。 | 不允许驶出；需要继续等待或人工确认。 |
| `safe_to_exit` | 目标楼层和驶出路径证据满足。 | 目标楼层和驶出条件已满足。 | 可进入驶出电梯阶段。 |
| `unsafe_to_exit` | 驶出条件不安全或未知。 | 驶出条件不安全或未知。 | 停止并请求人工接管。 |

固定路线和 visual gate 当前只能输出保守离线 evidence；即使 visual gate 通过，也只能说明路线 checkpoint 图像一致，不能宣称已识别电梯门或目标楼层。

## 人工协助边界

小车不会按电梯按钮，不控制电梯系统，不改造楼宇电梯。人工协助不是失败，而是该场景的产品边界：

- 进入电梯后请求旁人按目标楼层。
- 无人协助或目标楼层证据不可靠时，小车等待、停止或请求用户接管。
- 手机端必须解释当前需要什么帮助，而不是只显示错误码。
- 受控场景验收时必须有人类观察员在场，确保安全和可停。

## 手机与语音提示

| 触发点 | 手机文案 | 语音提示 |
| --- | --- | --- |
| 到达电梯厅 | 已到电梯厅，等待电梯开门。 | 等待电梯开门。 |
| 电梯未开门超时 | 电梯未开门，需要人工协助。 | 需要人工协助。 |
| 进入电梯 | 已进入电梯，正在请求帮忙按楼层。 | 你好,好心人,.我要去1楼扔垃圾,请帮我按一下电梯, |
| 等待目标楼层 | 正在等待目标楼层，请保持通道安全。 | 正在等待目标楼层。 |
| 到达目标楼层并开门 | 已到目标楼层，准备驶出。 | 到达目标楼层，准备驶出。 |
| 目标楼层证据不可靠 | 未确认目标楼层，请人工确认。 | 未确认目标楼层，需要人工协助。 |
| 成功驶出 | 已驶出电梯，继续送往垃圾站。 | 已驶出电梯，继续送垃圾。 |

## 验收口径

产品验收分三层，不能跳级宣称完成。

1. 文档/合同验收：
   - `OKR.md` 明确 H2/受控场景定位。
   - 本文档明确用户流程、语音、状态机边界、识别要求、人工协助和验收口径。
   - 不新增硬件假设，不把 ESP32 下位机写成电梯智能能力承载方。

2. 软件 dry-run 验收：
   - 行为层可用模拟事件走完电梯子状态。
   - 手机/diagnostics 能显示门未开、等待目标楼层、目标楼层开门、需要人工接管等状态。
   - 语音/TTS 或 speaker prompt contract 能输出指定求助文案。

3. 受控实景验收：
   - 楼宇、电梯、路线和目标楼层固定。
   - 人类观察员在场，急停和人工接管可用。
   - 至少完成 3 次连续受控流程：等待开门、进入、语音求助、到目标楼层、开门驶出、继续到垃圾站。
   - 每次任务留下状态转移、失败原因、语音触发和关键快照引用。

## 现场材料校验 Gate

`pc-tools/evidence/elevator_field_run_material_validation.py` 是受控实景验收前的 Docker/local software proof gate。它读取同一 `evidence_ref` 的材料目录，要求存在：

- `door_state.json`
- `target_floor_confirmation.json`
- `human_assistance_operator_note.md`
- `nav2_fixed_route_runtime_log.json`
- `task_record.json`
- `completion_signal.json`
- `diagnostics_mobile_safe_summary.json`

validation artifact 使用 `schema=trashbot.elevator_field_run_material_validation.v1`，summary 使用 `schema=trashbot.elevator_field_run_material_validation_summary.v1`，证据边界固定为 `software_proof_docker_elevator_field_material_validation_gate`。输出必须包含 `not_proven`、`operator_next_steps`、`primary_actions_enabled=false` 和 `delivery_success=false`。

该 gate 只证明现场材料目录的文件形状、同一 `evidence_ref` 和 phone-safe 摘要边界可校验；`elevator_field_material_validation_ready_not_proven` 不证明真实电梯、真实门状态、真实目标楼层、真实人工协助、真实 Nav2/fixed-route、WAVE ROVER/UART/HIL、真实投放、真实取消完成或 delivery success。缺失、模板、坏 JSON、`evidence_ref` mismatch、unsafe copy、`primary_actions_enabled=true` 或 `delivery_success=true` 都必须 fail closed。

## 不做什么

- 不把电梯能力写成当前 MVP 已完成。
- 不默认新增机械臂、深度相机、电梯控制器或昂贵硬件。
- 不让 ESP32/WAVE ROVER 下位机承担楼层识别、语音求助或场景决策。
- 不承诺开放楼宇、复杂人群、高峰期电梯或无人看护场景。
- 不新增硬件引脚、串口、电压、波特率或机械安装假设。

## 对应责任 Engineer

- `robot-software-engineer`：电梯子状态机、任务结果、失败路径、task record。
- `autonomy-engineer`：电梯门、目标楼层、驶出条件的感知 contract 和证据采集。
- `full-stack-software-engineer`：手机状态、diagnostics、speaker prompt/TTS contract。
- `hardware-engineer`：仅在后续涉及真实硬件、电气、UART、安装或 WAVE ROVER/Orange Pi 事实时介入，并必须先查 `docs/vendor/VENDOR_INDEX.md`。
