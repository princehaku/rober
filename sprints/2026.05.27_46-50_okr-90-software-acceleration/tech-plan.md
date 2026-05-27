# OKR 90 Software Acceleration Tech Plan

## 1. 方案总览

本轮规划将“所有 OKR 到 90% 以上”拆成两条可执行路径：

- 软件加速路径：集中推进 Objective 6 和 Objective 7。O6 建云端数据底座，O7 消费 O6 的任务/事件/轨迹/标注/推理 API，形成 PC 端运营调试与数据训练闭环。
- 真实证据路径：Objective 5 和 Objective 1 只准备验收清单和接入边界；没有真实公网/4G/production/OSS live traffic/真实手机/browser/真实 WAVE ROVER/UART/HIL 时，不允许超过 90%。

本 sprint 是 planning only。后续 implementation 必须由工程 agent 执行，不由主节点或 Product 直接写代码。

## 2. OKR 最低优先级核对

当前 `OKR.md` 4.1 节最低 Objective 是：

- Objective 6：0%

次低 Objective 是：

- Objective 7：约 5%

本 sprint 针对最低 Objective 6，并同步规划 Objective 7，因为 O7 的历史回放、实时地图、电梯状态、标注、ASR/TTS 和手控/寻路都依赖 O6 的云端数据底座。

Objective 5（约 80%）和 Objective 1（约 83%）不是本轮软件主攻目标。理由：二者超过 90% 必须依赖真实公网/4G/production/OSS live traffic/真实手机/browser 或真实 WAVE ROVER/UART/HIL/PR #5 硬件材料；当前资料边界仍是 `not_proven`，不能用 `software_proof` 伪造。

## 3. 分工

### Task A - O6 Cloud Archive Core

Owner: `full-stack-software-engineer`

目标：

- 建立 O6 云端核心后端最小数据模型和 API：任务存档、事件存档、OSS `evidence_ref`、标注 API、推理 API、任务/事件查询 API。
- API schema 建议使用 `trashbot.archive.v1`、`trashbot.annotation.v1`、`trashbot.inference.v1`。
- 持久层优先使用项目已有 cloud-relay 本地/Docker 能跑通的存储方式；如果 production DB 未接入，必须标记 `software_proof` 和 `not_proven_production_db`。

允许改动文件范围：

- `cloud-relay/**`
- `docs/product/cloud_4g_infrastructure.md`
- `docs/interfaces/**`
- `sprints/2026.05.27_46-50_okr-90-software-acceleration/tech-done.md`

接口影响：

- 新增或扩展云端 REST/WebSocket API，不破坏已有 `trashbot.remote.v1` commands/status/ack contract。
- 数据库或本地存储字段必须包含 `robot_id`、`task_id`、`event_id`、`event_type`、`created_at`、`evidence_ref`、`source`、`proof_status`。
- 大对象不得直接写入 DB，只保存 `evidence_ref`。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile cloud-relay/src/ros2_trashbot_cloud_relay/*.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s cloud-relay/tests
rg -n "trashbot.archive.v1|trashbot.annotation.v1|trashbot.inference.v1|evidence_ref|not_proven|software_proof" cloud-relay docs sprints/2026.05.27_46-50_okr-90-software-acceleration
git diff --check -- cloud-relay docs sprints/2026.05.27_46-50_okr-90-software-acceleration
```

### Task B - O6 Board Event Publisher

Owner: `robot-software-engineer`

目标：

- 在机器人侧提供任务/感知事件 envelope 和 cloud archive client 的 mock/software path。
- 将任务状态、电梯状态、路线帧、关键帧、检测结果、失败原因整理为可上报事件；真实网络不可用时保留本地队列或 retry stub。
- 不启动真实硬件，不假设 UART、摄像头、4G 或公网已经可用。

允许改动文件范围：

- `onboard/src/ros2_trashbot_interfaces/**`
- `onboard/src/ros2_trashbot_behavior/**`
- `onboard/src/ros2_trashbot_bringup/**`
- `docs/interfaces/**`
- `sprints/2026.05.27_46-50_okr-90-software-acceleration/tech-done.md`

接口影响：

- 可新增 ROS2 msg/srv/action 或 Python helper，但必须保持已有任务 action 和状态 topic 向后兼容。
- 事件字段应与 Task A 云端 API 对齐：`robot_id`、`task_id`、`event_type`、`timestamp`、`evidence_ref`、`source=software_proof`、`proof_status=not_proven`。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/*.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s onboard/src/ros2_trashbot_behavior/test
rg -n "archive|event|evidence_ref|software_proof|not_proven" onboard/src/ros2_trashbot_behavior onboard/src/ros2_trashbot_interfaces docs sprints/2026.05.27_46-50_okr-90-software-acceleration
git diff --check -- onboard/src/ros2_trashbot_interfaces onboard/src/ros2_trashbot_behavior onboard/src/ros2_trashbot_bringup docs sprints/2026.05.27_46-50_okr-90-software-acceleration
```

### Task C - O7 PC Operations Console on O6 API

Owner: `full-stack-software-engineer`

目标：

- 让 PC workstation 消费 O6 API，展示历史任务、事件时间线、轨迹回放、关键帧、标注队列、推理结果。
- O7 六区必须覆盖：实时地图、电梯状态、历史路线回放、数据标注、ASR/TTS、手控/寻路。
- 所有真实能力不足处必须显示 `not_proven`、`safe_to_control=false` 或 `mock_feed`，不得把 UI mock 写成已联调。

允许改动文件范围：

- `pc-tools/workstation/src/**`
- `pc-tools/workstation/test/**`
- `pc-tools/README.md`
- `docs/product/pc_tools_workstation.md`
- `docs/interfaces/**`
- `sprints/2026.05.27_46-50_okr-90-software-acceleration/tech-done.md`

接口影响：

- PC 端只通过 cloud-relay API 消费数据，不直连机器人。
- 手控/寻路下发保持 draft 或 disabled，除非 Robot/Hardware 给出安全准入。

验收命令：

```bash
cd pc-tools/workstation && npm run build
cd pc-tools/workstation && npm run test
cd pc-tools/workstation && npm run lint
rg -n "Objective 7|实时地图|电梯状态|历史路线回放|数据标注|ASR|TTS|手控|寻路|not_proven|safe_to_control" pc-tools docs sprints/2026.05.27_46-50_okr-90-software-acceleration
git diff --check -- pc-tools docs sprints/2026.05.27_46-50_okr-90-software-acceleration
```

### Task D - O6/O7 Algorithm Evidence Feed

Owner: `robot-algorithm-engineer`

目标：

- 提供离线可复验的轨迹、路线帧、关键帧、电梯门状态、楼层证据、障碍物标注样本或 generator。
- 提供 inference stub 或轻量规则模型输出，能写入 O6 事件存档并被 O7 回放/标注界面消费。
- 明确样本是 mock/offline，不代表真实路线、真实电梯或真实模型鲁棒性。

允许改动文件范围：

- `onboard/src/ros2_trashbot_nav/**`
- `onboard/src/ros2_trashbot_behavior/**`
- `docs/navigation/**`
- `docs/vision/**`
- `docs/interfaces/**`
- `sprints/2026.05.27_46-50_okr-90-software-acceleration/tech-done.md`

接口影响：

- 输出事件必须与 Task A/B 的 archive schema 对齐。
- 不破坏已有 Nav2、fixed route、learn/autonomous launch 行为。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s onboard/src/ros2_trashbot_nav/test
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s onboard/src/ros2_trashbot_behavior/test
rg -n "trajectory|route frame|keyframe|elevator|floor|inference|evidence_ref|mock|offline" onboard/src/ros2_trashbot_nav onboard/src/ros2_trashbot_behavior docs sprints/2026.05.27_46-50_okr-90-software-acceleration
git diff --check -- onboard/src/ros2_trashbot_nav onboard/src/ros2_trashbot_behavior docs sprints/2026.05.27_46-50_okr-90-software-acceleration
```

### Task E - O1/O5 90% Evidence Boundary

Owner: `robot-hardware-engineer` for O1, `full-stack-software-engineer` for O5, Product reviews final boundary.

目标：

- 输出 O1/O5 达到 90% 以上所需真实材料清单、采集命令、证据文件路径和不能被 mock 替代的判断规则。
- O1 涉及 WAVE ROVER、ESP32、Orange Pi、UART、波特率、JSON 指令、速度映射、反馈协议、引脚、电压、固件或机械尺寸时，必须先读 `docs/vendor/VENDOR_INDEX.md` 及其指向本地 vendor 文件。
- O5 涉及公网/4G/production/OSS/CDN/live traffic 时，必须明确凭证不入仓库。

允许改动文件范围：

- `docs/hardware/**`
- `docs/product/cloud_4g_infrastructure.md`
- `docs/interfaces/**`
- `sprints/2026.05.27_46-50_okr-90-software-acceleration/tech-done.md`

接口影响：

- 不改硬件配置，不改生产凭证，不改 launch 默认值。
- 只产出验收清单和真实证据路径。

验收命令：

```bash
rg -n "Objective 1|Objective 5|90|not_proven|WAVE ROVER|UART|HIL|4G|HTTPS|production|OSS|CDN|live traffic|docs/vendor/VENDOR_INDEX.md" docs sprints/2026.05.27_46-50_okr-90-software-acceleration
git diff --check -- docs sprints/2026.05.27_46-50_okr-90-software-acceleration
```

## 4. 文件范围总表

本 planning sprint 已允许改动：

- `sprints/2026.05.27_46-50_okr-90-software-acceleration/pre_start.md`
- `sprints/2026.05.27_46-50_okr-90-software-acceleration/prd.md`
- `sprints/2026.05.27_46-50_okr-90-software-acceleration/tech-plan.md`

后续 implementation 允许改动范围以各 Task 为准，且必须同步更新：

- `sprints/2026.05.27_46-50_okr-90-software-acceleration/tech-done.md`

禁止后续工程 agent 擅自改动：

- `OKR.md`，除非 Product closeout 已经验收证据并单独授权。
- vendor 原始资料。
- 生产凭证、`.env`、真实密钥。
- 与本 sprint 无关的代码和文档。

## 5. 接口影响总览

建议新增或扩展的 schema：

- `trashbot.archive.v1`
- `trashbot.annotation.v1`
- `trashbot.inference.v1`
- `trashbot.o7_operator_dataset.v1`

建议统一字段：

- `robot_id`
- `task_id`
- `event_id`
- `event_type`
- `timestamp`
- `trajectory`
- `evidence_ref`
- `annotation_status`
- `inference_status`
- `source=software_proof`
- `proof_status=not_proven`
- `safe_to_control=false`
- `mock_feed=true|false`
- `next_required_evidence`

兼容性要求：

- 不破坏 `trashbot.remote.v1` commands/status/ack。
- 不暴露 `/cmd_vel` 到公网 API。
- PC 端不得直连机器人。
- 手控/寻路默认 disabled/draft，直到 Robot/Hardware 完成安全准入。

## 6. 主节点后续派发 Prompt 要求

后续派发工程 agent 时，prompt 必须包含：

1. 对应 `.codex/agents/<role>.toml` 的完整 `developer_instructions`。
2. 本 `tech-plan.md` 中对应 Task 的目标、文件范围和验收命令。
3. 明确输出要求：实际改动文件、验证命令输出、失败定位、剩余风险。
4. 明确不得更新 `OKR.md`，不得伪造真实硬件/公网/4G/production 证据。

## 7. 风险边界

- O6/O7 后续可以通过 mock/local/Docker 形成 `software_proof`，但不能标记真实生产、真实上车或真实视频/音频完成。
- O5 没有真实公网 HTTPS/TLS、4G/SIM、production DB/queue、OSS/CDN live traffic、真实手机/browser 前，保持 90% 以下。
- Objective 1 没有真实 WAVE ROVER/UART/HIL 和 PR #5 硬件材料前，保持 90% 以下。
- 如果工程任务发现现有 cloud-relay、pc-tools 或 onboard 包结构与计划不一致，应先最小调整计划或在 `tech-done.md` 记录偏差，不扩大无关重构。

## 8. 本 planning sprint 验收命令

```bash
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 6|Objective 7|Objective 5|Objective 1|90|not_proven|software_proof|验收命令|文件范围" sprints/2026.05.27_46-50_okr-90-software-acceleration
git diff --check -- sprints/2026.05.27_46-50_okr-90-software-acceleration
```
