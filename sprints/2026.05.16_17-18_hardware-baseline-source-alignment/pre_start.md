# Sprint 2026.05.16_17-18 Hardware Baseline Source Alignment - Pre Start

sprint_type: epic

## 1. 启动原因

本轮根据近期 PR 和评审重新排序 OKR。`OKR.md` 4.1 当前数值最低为 Objective 5（约 66%），但本机只有 Docker，缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 和 worker/migration 证据；继续堆本地 O5 metadata 不会形成真实进展。

下一层最低可推进 Objective 是 Objective 1（约 73%）。近期 PR #5 的 Codex review 明确指出两个硬件基线风险：

- P1：`docs/product/production_hardware_boundary.md` 的默认硬件集与 mandatory sensor baseline 曾存在矛盾，可能导致 BOM/procurement 和 bringup 计划漏掉必需传感器。
- P2：新增传感器基线假设缺少 `docs/vendor/` 来源引用，违反项目硬件事实必须本地可追溯的规则。

本轮不声明真实硬件完成，只把 PR review 风险转成可机器验收的 `hardware_baseline_source_alignment` software proof，避免后续 Hardware / Robot / Mobile 继续消费不一致的硬件基线口径。

## 2. Owner 与并行策略

- Hardware Infra Engineer：主责 PC evidence gate 与 `docs/product/production_hardware_boundary.md` source-alignment 文档更新。
- Robot Platform Engineer：主责 Robot diagnostics metadata-only consumer 与接口文档。
- User Touchpoint Full-Stack Engineer：主责 mobile/web 只读展示、copy/export whitelist 和产品流程文档。
- Product Manager / OKR Owner：主责 closeout、OKR 进度边界和 sprint 文档收口。

本轮跨 3 个实现 owner，文件范围互不重叠，按 AGENTS 并行启动规则派 3 个 worker；Product closeout 在 worker 返回后执行。

## 3. 验收边界

本轮证据边界固定为 `software_proof_docker_hardware_baseline_source_alignment_gate`。

必须保持：

- `source=software_proof`
- `hardware_material_status=hardware_material_pending`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- 不访问真实硬件、串口、WAVE ROVER、ROS graph、Nav2 runtime、采购系统、云端或手机设备。

## 4. 阻塞扫描

最近两轮 sprint 的 blocker 分别为真实 route/task/elevator field materials 缺失和真实 hardware receipt/materials 缺失；本轮不重复消费同一 blocker，而是处理 PR #5 review 中可在 Docker 内推进的源引用与基线一致性风险。
