# pc-tools/ — PC 工作站开发工具集

本目录是 `ros_rbs` 的 **PC 端 dev tool 集合**：路径学习、视觉样本标注/复核、证据交叉检查、模型训练等工作流，统一收口在这里。

> 当前状态：sprint `2026.05.13_01-02_codebase-restructure-four-tier` 的 Phase 1 已建立脚手架；真正的工具脚本会在 Phase 4 由 `autonomy-engineer` 从 `onboard/src/ros2_trashbot_nav/` 和 `scripts/` 搬到这里。

## 用途（What lives here）

- 给 **开发者 / 操作员 PC** 用的离线工具集合，不上车、不进云。
- 消费 onboard 产出的产物（route CSV、phone API JSON、vision sample manifest 等），生成可视化、标注、训练数据集等下游产物。

## 子目录

| 目录 | 用途 | 主要文件（P4 完成后） |
| --- | --- | --- |
| `pc-tools/route/` | 路径学习 + debug Web | `route_debug_web.py`（标准库 HTML/JSON API 路径复盘）、`route_csv_to_yaml.py`（CSV → YAML 转换，仍在 onboard） |
| `pc-tools/labeling/` | 视觉样本标注 / 复核 GUI 占位 | 见 `CONTRACT.md`；本 sprint 不实现真实 GUI，留给 autonomy 后续 sprint |
| `pc-tools/evidence/` | 证据交叉检查、phone browser gate | `evidence_crosscheck.py`、`phone_browser_acceptance_gate.py` |
| `pc-tools/training/` | YOLO / RT-DETR 训练入口、数据集组织规范 | 占位，留给 autonomy 后续 sprint |

## 部署目标（Deployment target）

- **环境**：PC 工作站（macOS / Linux / Windows + WSL），Python **3.10+**。
- **可选**：ROS2 dev container（如需在 PC 上本地 simulate `rclpy` 行为时）。
- **网络**：可访问 onboard 产出的数据目录（NAS / 本地拷贝 / scp），可选连云端 OSS / S3 拉样本。
- **不上车**：本目录的工具运行在 PC 上，不会被 Orange Pi 调度；不要把 `pc-tools/*` 误打入 `onboard/docker/humble` 镜像。

## 运行时契约（Runtime contracts）

- **与 `onboard/` 的契约**：消费 onboard 产生的 route CSV、phone-safe JSON、vision sample manifest（`trashbot.vision_samples.v1`）；异步、离线、单向。
- **与 `cloud-relay/` 的契约**：可选消费 cloud-relay 暴露的 phone-safe JSON 做证据交叉检查；不写回。
- **与 `mobile/` 没有直接契约**：mobile 是手机用户视角，pc-tools 是开发者视角，两者独立演进。

## 当前状态（本轮）

- `pc-tools/evidence/evidence_crosscheck.py`、`pc-tools/evidence/phone_browser_acceptance_gate.py` 已从仓库根 `scripts/` 迁入。
- `pc-tools/route/route_debug_web.py` 已落地为 PC 工作站独立工具：只读消费 fixed-route status JSON 与可选 task/task_record JSON 或 task_record dir，输出 `schema=trashbot.pc_route_debug_console.v1`、`evidence_boundary=software_proof_docker_pc_route_debug_console_gate`、`route_progress`、`keyframe_preflight`、recent task summary、`not_proven` 和 `delivery_success=false`。
- `route_csv_to_yaml.py` 仍位于 `onboard/src/ros2_trashbot_nav/`（可选后续再抽到 `pc-tools/route/` 以降低与 colcon 的耦合）。
- `labeling/`、`training/` 仍为占位与契约说明。

## PC route debug console

`pc-tools/route/route_debug_web.py` 是本地 PC console，不依赖 ROS2，不 import `ros2_trashbot_*`，不访问硬件、serial/UART、Nav2 runtime、ROS graph 或网络外部服务：

```bash
python3 pc-tools/route/route_debug_web.py \
  --status-json /tmp/trashbot_fixed_route_status.json \
  --task-record /tmp/task_record.json \
  --once-json
```

启动 HTML/API：

```bash
python3 pc-tools/route/route_debug_web.py \
  --status-json /tmp/trashbot_fixed_route_status.json \
  --task-record-dir ~/.ros/trashbot_tasks \
  --host 127.0.0.1 \
  --port 8766
```

API `/api/status` 与 `/api/summary` 返回同一份只读 summary：`pc_route_debug_console`、`software_proof_docker_pc_route_debug_console_gate`、`route_progress`、`keyframe_preflight`、当前位置/当前 checkpoint、目标点、匹配状态、失败原因、recent task/task_record summary、`not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。该结果只证明 PC/local/Docker 软件复盘材料可读，不是真实 fixed-route/Nav2 实跑、HIL、dropoff/cancel completion 或 delivery success。

## route/task rehearsal artifact

`pc-tools/evidence/evidence_crosscheck.py` 可在原有只读复账基础上额外写出 route/task rehearsal artifact：

```bash
python3 pc-tools/evidence/evidence_crosscheck.py \
  /tmp/trashbot_fixed_route_status.json \
  --evidence-ref /tmp/route_replay_evidence.json \
  --task-record-dir ~/.ros/trashbot_tasks \
  --rehearsal-artifact /tmp/route_task_rehearsal_artifact.json
```

artifact 使用 `schema=trashbot.route_task_rehearsal_artifact`、`schema_version=1`，证据边界固定为 `evidence_boundary=software_proof_docker_route_task_rehearsal_artifact_gate`。内容包括 `evidence_ref`、route status summary、task record summary、crosscheck status、HIL alignment status、`diagnostics_summary` 和 `not_proven`。当 fixed-route status、software proof replay 与 task record 对账通过时，`crosscheck_status.status=pass` 只表示本地/Docker 软件排练一致，不表示真实 Nav2/fixed-route 实跑、WAVE ROVER 运动、真实串口反馈、真实 HIL 或 delivery success。

可选 `--hil-gate-output` 只用于记录 HIL gate 对齐状态。未提供、文件缺失、`status=software_proof` 或 `status=blocked` 时 artifact 仍会保存，但 `hil_alignment_status.alignment_status=not_proven`，`not_proven` 继续包含 `real_hil_pass`。summary/artifact 输出会过滤 bearer token、Authorization header、OSS secret、AK/SK、root password、DB URL、queue URL、串口设备、波特率和 raw traceback。

`diagnostics_summary` 是给 `/api/diagnostics` 或支持面消费的 phone-safe 摘要，schema 为 `trashbot.route_task_rehearsal_diagnostics_summary`，证据边界固定为 `software_proof_docker_route_task_rehearsal_diagnostics_gate`。该 summary 只暴露脱敏后的 `status`、`evidence_boundary`、`evidence_ref`、`crosscheck_status`、`hil_alignment_status`、`not_proven` 和 `next_step`；diagnostics 可以把它作为 `route_task_rehearsal` 展示，但不能据此放行控制动作、声明真实 fixed-route/Nav2、HIL、delivery success 或云/4G/OSS/CDN/DB/queue proof。

## route/task rehearsal execution bundle

`pc-tools/evidence/route_task_rehearsal_bundle.py` 在 `evidence_crosscheck.py` 之上生成可传递 execution bundle manifest：

```bash
python3 pc-tools/evidence/route_task_rehearsal_bundle.py \
  /tmp/trashbot_fixed_route_status.json \
  --task-record /tmp/task_record.json \
  --output-dir /tmp/route_task_rehearsal_bundle
```

该命令会先写出 `route_task_rehearsal_artifact.json`，再写出 `route_task_rehearsal_execution_bundle.json`。manifest 使用 `schema=trashbot.route_task_rehearsal_execution_bundle`、`schema_version=1`，证据边界固定为 `software_proof_docker_route_task_rehearsal_execution_bundle_gate`。manifest 顶层直接提供 diagnostics 只读消费字段：`route_task_rehearsal_artifact_ref`、`crosscheck_status`、`hil_alignment_status` 和 `diagnostics_summary`；同时保留脱敏后的 route status、task record、task record dir、HIL gate output 和 artifact 路径引用，以及 `not_proven` 和 `next_step`。

`status=available_software_proof` 和顶层 `crosscheck_status.status=pass` 只代表 status/replay/task_record 软件对账通过，适合交给 diagnostics 或 sprint closeout 做同一 `evidence_ref` 的材料传递。顶层 `hil_alignment_status.alignment_status=not_proven` 时必须继续显示缺真实 HIL。该 manifest 不证明真实 Nav2/fixed-route 实跑、真实路线采集、WAVE ROVER 运动、真实串口/UART feedback、真实 HIL、dropoff/cancel completion 或 delivery success。

## route/task rehearsal operator review

`pc-tools/evidence/route_task_rehearsal_operator_review.py` 只读取上一节生成的 execution bundle JSON，并生成操作员复盘/下一轮重跑决策包：

```bash
python3 pc-tools/evidence/route_task_rehearsal_operator_review.py \
  --execution-bundle /tmp/route_task_rehearsal_bundle/route_task_rehearsal_execution_bundle.json \
  --output-dir /tmp/route_task_rehearsal_review
```

默认输出文件名为 `route_task_rehearsal_operator_review.json`；也可以用 `--output` 指定完整输出路径。review package 使用 `schema=trashbot.route_task_rehearsal_operator_review.v1`、`schema_version=1`，证据边界固定为 `software_proof_docker_route_task_rehearsal_operator_review_gate`。该工具只读 JSON，不访问硬件、serial/UART、ROS graph、Nav2 或网络；missing、read_error、unsupported schema 也会写出 `overall_status=blocked_*` 的 review package，避免复盘时只有异常没有材料。

`next_rehearsal_decision` 是给操作员看的下一步分支：crosscheck pass 但 HIL not_proven 时，准备真实路线/任务材料或同 `evidence_ref` 的真实 HIL 复账；crosscheck fail 时，先修 route status/task record mismatch 后重跑 execution bundle；missing/read_error/unsupported schema 时，重建 execution bundle；safe copy whitelist 失败时，先修 whitelist-only 摘要。`safe_copy` 只包含固定白名单摘要，不复制 artifact/raw path、本机绝对路径、凭证、ROS topic、serial/UART、baudrate、WAVE ROVER、traceback、checksum 或 complete artifact。`primary_actions_enabled=false`、`delivery_success=false` 是固定防误读字段，review 不能放行控制动作或声明 delivery success。

## route/task field-run readiness handoff

`pc-tools/evidence/route_task_field_run_readiness.py` 把 PC route debug console summary、route_task operator review 和 execution bundle 聚合为下一次真实路线-任务联跑前的 handoff：

```bash
python3 pc-tools/evidence/route_task_field_run_readiness.py \
  --pc-route-debug /tmp/pc_route_debug_console.json \
  --operator-review /tmp/route_task_rehearsal_operator_review.json \
  --execution-bundle /tmp/route_task_rehearsal_execution_bundle.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --once-json
```

输出 `schema=trashbot.route_task_field_run_readiness.v1`、`schema_version=1`、`evidence_boundary=software_proof_docker_route_task_field_run_readiness_gate`、`same_evidence_ref_required=true`、`required_field_run_materials`、`missing_materials`、`commands_to_run`、`phone_support_safe_summary`、`not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。`overall_status=ready_for_field_run_materials` 只表示三份 Docker/local 软件 handoff 材料可读、schema 可支持、同一 `evidence_ref` 可对齐且摘要可安全分享；它不是 HIL、真实 fixed-route/Nav2 实跑、真实路线采集、dropoff/cancel completion、delivery success 或 Objective 5 外部 proof。

`required_field_run_materials` 会列出下一次现场联跑必须收集的同一 `evidence_ref` 材料：route status、task record、PC route debug summary、operator review、execution bundle、Nav2/fixed-route runtime log、robot-side task evidence 和 support-safe mobile summary。CLI 不读取 serial/UART、ROS graph、WAVE ROVER、DB/queue、OSS/CDN 或 raw robot response；缺文件、unsupported schema、不同 `evidence_ref` 或 unsafe copy 时会保守输出 blocked/not_proven。

## route/task field-run intake crosscheck

`pc-tools/evidence/route_task_field_run_intake.py` 是 readiness handoff 之后的现场材料入口。它只读接收五份 JSON object：route status、task record、Nav2/fixed-route runtime log、robot-side task evidence 和 support-safe mobile summary，并用同一个 `evidence_ref` 做交叉校验：

```bash
python3 pc-tools/evidence/route_task_field_run_intake.py \
  --route-status-json /tmp/route_status.json \
  --task-record-json /tmp/task_record.json \
  --runtime-log-json /tmp/runtime_log.json \
  --robot-side-task-evidence-json /tmp/robot_evidence.json \
  --support-safe-mobile-summary-json /tmp/mobile_summary.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --once-json
```

输出 `schema=trashbot.route_task_field_run_intake_crosscheck.v1`、`schema_version=1`、`evidence_boundary=software_proof_docker_route_task_field_run_intake_crosscheck_gate`、`same_evidence_ref_required=true`、`missing_materials`、`mismatch_reasons`、`commands_to_rerun`、`phone_safe_summary`、`not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。`overall_status=ready_for_review` 只表示五份 Docker/local 软件材料都可读、schema 支持、同一 `evidence_ref` 对齐且手机/售后摘要可安全展示；它不是 HIL、真实 Nav2/fixed-route 实跑、真实路线采集、dropoff/cancel completion、delivery success 或 Objective 5 外部 proof。

缺文件、坏 JSON、非 JSON object、unsupported schema、任一材料缺 `evidence_ref`、同 run 不一致或 support-safe mobile summary 含敏感材料时，CLI 会保守输出 blocked 状态，不抛未处理异常。`phone_safe_summary` 只包含 status、safe evidence ref、材料 present/missing/mismatch、`commands_to_rerun`、`not_proven` 和 accepted/processing support metadata only 语义；不得包含 raw artifact、完整本机路径、ROS 控制 topic、serial/UART、baudrate、WAVE ROVER 参数、token、Authorization、OSS AK/SK、DB/queue URL、traceback、checksum、complete artifact 或 raw robot response。

## Agent 工作纪律

- 修改本目录前必读 `AGENTS.md`、`OKR.md`、对应 sprint 文档。
- 涉及视觉样本 schema / 标注格式时，必读 `pc-tools/labeling/CONTRACT.md` 和 `onboard/src/ros2_trashbot_vision/` 对应接口定义，不发明字段。
- 中文注释比例 >20%，注释解释"为什么"而非"做什么"。
- 测试覆盖核心场景：CSV → YAML 转换、debug web 渲染、evidence crosscheck 一致性、phone gate 报告生成。
- 不允许 pc-tools/* 直接 import 任何 `ros2_trashbot_*` ROS2 包；这些工具应能在没有 ROS2 安装的 PC 上独立运行（如必须依赖 rclpy，必须明确写在子目录 README 顶部 + 测试可绕过）。

## 路线图（Roadmap）

| 阶段 | 工作 |
| --- | --- |
| 本 sprint P1（当前） | README 脚手架 + labeling CONTRACT 占位 |
| 本 sprint P4 | route / evidence 工具搬迁 |
| 后续 sprint | labeling GUI 实现、training pipeline 集成、数据集版本管理 |
