# O6/O7 Field Motion Evidence Packet Pre-Start

## sprint_type: epic

## 背景

`OKR.md` 4.1 当前最低 active Objective 为 O6 与 O7，均约 47%。`sprints/2026.07.09_12-58_o6_o7_route_root_seed_gate/final.md` 已把 route-root seed 对 `route_bag` 的硬 gate 拆掉，但也明确要求下一轮不能继续新增 local/mock wrapper，必须开始消费真实或离线现场材料。

`sprints/2026.06.10_00-45_integrated-sensor-motion-capture/final.md` 已证明 6 月现场链路至少拿到了同轮 `map`、`motion`、`route.csv`、`manifest.json`、`keyframes/001..010`、`/scan`、`/camera/image_raw` 与 `/odom` 对比样本。`sprints/2026.06.09_20-21_board-live-evidence-capture/final.md` 与 `sprints/2026.06.09_17-03_field-evidence-artifact-gate/final.md` 又把 fallback manifest / replay packet 和 SSH 不可达时的 fail-closed 边界补齐。

本轮是 planning-only sprint。目标不是再造新的 safe summary，而是把已有 6 月现场 `map/route/keyframes/remote_capture` 运动日志与可选 `route_bag` 组织成同一 `task_id` 的 field motion evidence packet，供后续 O6 archive ingest 与 O7 consumer replay 直接消费。

## 本轮目标

创建一个 Epic sprint 计划，推动 O6/O7 从 `software_proof_local_mock_route_root_seed_gate_only` 继续向“消费现场运动证据包”的方向前进。

核心抓手：

- 优先消费 6 月现场已存在材料，而不是继续新增 wrapper。
- 统一同一 `task_id` 下的 `map.yaml`、`route.csv`、keyframes、remote_capture motion 日志、derived replay 与 manifest。
- 把 `route_bag` 定义为可选增强证据，不再作为 `route_bag_or_live_nav2_log` 之外的硬阻塞。

## owner分工 / Owner 分工

- `product-okr-owner`：负责 OKR 对齐、范围裁剪、验收口径和最终方向判断。
- `robot-algorithm-engineer`：主责 6 月现场 `map/route/keyframes/remote_capture` 的语义归一，定义 packet 内最小必需材料与 `route_bag_or_live_nav2_log` 的可选增强关系。
- `robot-software-engineer`：主责 O6 archive ingest / consumer detail 的 packet contract、同一 `task_id` ingest 入口与 fail-closed 规则。
- `full-stack-software-engineer`：主责 O7 consumer replay / labeling workspace 读取同一 packet 摘要，不直接读取任意原始路径。
- `rober-hardware-engineer`：本轮无实现任务；若后续进入真实上车补证，必须按 `docs/vendor/VENDOR_INDEX.md` 二次确认硬件事实。

## 文件范围

本次 planning-only 动作只允许创建以下三个文件：

- `sprints/2026.07.09_14-00_o6_o7_field_motion_evidence_packet/pre_start.md`
- `sprints/2026.07.09_14-00_o6_o7_field_motion_evidence_packet/prd.md`
- `sprints/2026.07.09_14-00_o6_o7_field_motion_evidence_packet/tech-plan.md`

不得修改产品代码、测试代码、硬件配置、`OKR.md` 或其他 sprint 文档。

## 接口边界

- field motion evidence packet 只服务 O6 ingest 与 O7 replay/readiness，不代表真实控制、真实送达或真实生产云完成。
- packet 必须围绕同一 `task_id` 组织材料；缺失必需材料时必须 fail-closed。
- `route_bag` 是可选增强，不是本轮硬 gate；若缺失，只能落为 `route_bag_or_live_nav2_log` 证据缺口。
- 不允许把 `safe_to_control`、`delivery_success`、`primary_actions_enabled` 写成 true。

## safe flags false / 安全旗标

safe_to_control: false
delivery_success: false
primary_actions_enabled: false
robot_control_executed: false

## 预期收口

后续实现完成时，`tech-done.md` 必须给出 packet 生成、O6 ingest readback、O7 replay 消费的真实日志或测试片段，并继续明确所有控制类字段为 false / not proven。若 6 月现场材料不完整，必须在 `final.md` 中指出缺口来自哪一段材料，而不是再新增本地包装层。
