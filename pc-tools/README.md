# pc-tools/ — PC 工作站开发工具集

本目录是 `ros_rbs` 的 **PC 端 dev tool 集合**：路径学习、视觉样本标注/复核、证据交叉检查、模型训练等工作流，统一收口在这里。

> 当前状态：sprint `2026.05.13_01-02_codebase-restructure-four-tier` 的 Phase 1 已建立脚手架；真正的工具脚本会在 Phase 4 由 `autonomy-engineer` 从 `onboard/src/ros2_trashbot_nav/` 和 `scripts/` 搬到这里。

## 用途（What lives here）

- 给 **开发者 / 操作员 PC** 用的离线工具集合，不上车、不进云。
- 消费 onboard 产出的产物（route CSV、phone API JSON、vision sample manifest 等），生成可视化、标注、训练数据集等下游产物。

## 子目录

| 目录 | 用途 | 主要文件（P4 完成后） |
| --- | --- | --- |
| `pc-tools/route/` | 路径学习 + debug Web | `route_debug_web.py`（FastAPI/HTML 路径回放）、`route_csv_to_yaml.py`（CSV → YAML 转换） |
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
- `route_debug_web.py`、`route_csv_to_yaml.py` 仍位于 `onboard/src/ros2_trashbot_nav/`（可选后续再抽到 `pc-tools/route/` 以降低与 colcon 的耦合）。
- `labeling/`、`training/` 仍为占位与契约说明。

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
