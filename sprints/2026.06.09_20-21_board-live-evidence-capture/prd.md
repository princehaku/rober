# PRD - Board Live Evidence Capture

## 用户价值和产品北极星

普通用户不关心机器人是否有漂亮的调试页面，只关心小车是否能沿真实路线完成垃圾投递。对当前阶段，最有价值的产品证据是：真实上位机采集出的地图、路线、关键帧、rosbag 或 replay，可被 O3 现场验证、O6 数据存档、O7 回放标注共同消费。

本 PRD 定义 `board_live_evidence_capture` 的功能点完整性。功能点完整前，不允许进入代码实现。

## 目标用户与使用场景

- CEO/现场执行者：拿到一条明确命令链，能知道 SSH 是否通、ROS2 是否可用、topic 是否有数据、材料是否成功产出。
- Robot Algorithm Engineer：能围绕真实 O3 lane 执行 capture，而不是继续写 fixture 或 surface。
- O6/O7 后续 owner：能消费同一份 `trashbot.field_evidence_manifest.v1`，不再分叉出另一套“真实材料”解释。

## 功能点定义

功能点名称：`board_live_evidence_capture`

该功能点必须覆盖：

1. Live SSH preflight：验证 `ssh root@192.168.1.11 -p 37878` 是否可达。
2. Board runtime preflight：验证上位机 hostname/date、ROS2 命令、setup 文件、工作区 package、关键 topic。
3. Live evidence capture：尽力产出 `map.yaml`、`route.csv`、keyframes、rosbag、replay JSONL 至少一种真实材料。
4. Manifest gate：用既有 manifest contract 标记 artifact 状态，禁止把 preflight 或 mock 误报为真实送达。
5. Fallback evidence：SSH 不通时仍生成可执行 fallback JSON 与 runbook，明确下一次要改什么条件。

## 功能点完整性门槛

只有同时满足以下门槛，后续 Engineer 才允许开始写功能代码：

1. **入口明确**：live 入口固定为 `ssh root@192.168.1.11 -p 37878`，所有命令都可复制执行。
2. **成功路径明确**：SSH 成功后必须从 ROS2 preflight 进入材料采集，而不是停在 `echo ok`。
3. **产物门槛明确**：成功验收至少需要 `map.yaml`、`route.csv`、keyframe、rosbag、replay JSONL 中任一项真实材料，且需要 manifest gate 标注。
4. **失败分层明确**：SSH 不通、ROS2 不存在、setup 缺失、package 缺失、topic 缺失、capture 不安全、产物缺失要分层记录。
5. **降级产物明确**：SSH 不通也必须产出 preflight JSON、manifest local fixture 或 capture runbook，不能只写“blocked”。
6. **禁止误报明确**：任何 fallback/mock/preflight-only 状态都必须保持 `not_proven=true`、`delivery_success=false`、`safe_to_control=false`。
7. **代码开写边界明确**：未证明既有脚本无法满足需求前，不允许新增或修改产品代码。
8. **硬件事实边界明确**：涉及 WAVE ROVER、ESP32、Orange Pi、UART、串口、波特率、JSON 指令、反馈协议、引脚、电压或机械尺寸时，必须先读 vendor 本地资料。

## 代码开写禁止项

以下条件未满足时，禁止开始写产品代码：

- 未读完本 sprint 的 `pre_start.md`、`prd.md`、`tech-plan.md`。
- 未运行 live SSH preflight 或无法说明为什么不能运行。
- 未先尝试既有入口：`board_live_route_preflight.sh`、`field_route_evidence_preflight.py`、`field_route_evidence_manifest.py`。
- 未定义要补的代码功能点属于哪个缺口：preflight、capture、manifest、replay、archive 或 consumer。
- 只是为了包装 `blocked_ssh_unreachable`、safe summary、handoff、review decision 或 UI 展示。
- 代码改动会绕过 `not_proven`、`delivery_success=false`、`safe_to_control=false` 的 fail-closed 语义。
- 代码改动涉及硬件事实但未引用 `docs/vendor/VENDOR_INDEX.md`。

## 允许改代码的条件

只有出现以下真实缺口，才允许在后续实现 sprint 里改代码：

- 既有 preflight CLI 无法把 live SSH 成功/失败分层写入 JSON。
- 既有 capture 脚本无法输出或提示 `map.yaml`、`route.csv`、keyframes、rosbag、replay JSONL 的采集命令。
- 既有 manifest CLI 无法扫描真实材料目录或无法给出 gate/pass/fail 状态。
- fixed-route replay 无法消费真实 `route.csv`，且失败可由软件修复。
- O6/O7 consumer 无法读取已产出的真实 manifest，但必须等 live 材料或 local fixture gate 先形成。

## 优先级与验收口径

P0：

- 运行真实 SSH preflight。
- SSH 成功时完成上位机 ROS2 preflight。
- 产出真实材料或分层 fallback JSON。

P1：

- 产出 manifest gate，标记 artifact 状态。
- 在 `tech-done.md` 留存命令、输出、路径、失败层级和剩余风险。

P2：

- 将真实 manifest 交给 O6/O7 后续 sprint 消费。
- 补充 PC 回放/标注入口，但不得早于 P0/P1。

验收成功定义：

- 至少一类真实材料存在并可定位路径；或
- SSH 不通时，fallback JSON 和 runbook 足以让 CEO 判断网络/凭证/端口/主机状态下一步如何处理。

## 对应责任 Engineer

- 主责：`robot-algorithm-engineer`
- 条件介入：`robot-software-engineer`
- 硬件事实介入：`robot-hardware-engineer`
- 后续消费：`full-stack-software-engineer`

## 风险、阻塞和证据链

- 风险：继续卡在 `blocked_ssh_unreachable`。
  - 证据要求：必须保存 SSH 命令、退出状态、错误摘要、preflight JSON 和 CEO 决策点。
- 风险：ROS2 或 workspace 不在预期路径。
  - 证据要求：保存 `command -v ros2`、setup 查找结果和 `ros2 pkg list` 输出。
- 风险：topic 缺失或没有频率。
  - 证据要求：保存 `ros2 topic list` 与 `ros2 topic hz` 结果。
- 风险：现场不可移动。
  - 证据要求：至少采集静态 topic、keyframe 或 rosbag；无法移动不等于可以回到 surface sprint。

## KR 拆解与历史归档

- 当前不移动 `OKR.md` KR，也不把任何 KR 标为完成。
- 若后续真实 `map.yaml`、`route.csv`、keyframe、rosbag 或 replay JSONL 产出并通过 manifest gate，可作为归档 O3 重新激活的证据。
- 已完成 KR 历史记录仍以 `docs/process/okr_progress_log.md` 为准；本轮只新增 sprint 设计证据，不新增历史归档。

## 需要更新的 sprint 文档

- 本设计阶段：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 后续执行阶段：`tech-done.md`、`side2side_check.md`、`final.md`。
