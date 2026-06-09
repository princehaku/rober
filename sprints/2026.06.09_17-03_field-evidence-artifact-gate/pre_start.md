# Pre-start - Field Evidence Artifact Gate

## Sprint 类型

sprint_type: epic

本轮启动时间：2026-06-09 17:03。  
主责 owner：`robot-algorithm-engineer`。  
产品 owner：`product-okr-owner` 仅负责 sprint 设计、范围边界和验收口径，不写产品代码、测试代码或硬件配置。

## CEO 输入

CEO 当前要求：

> Automation: 1小时OKR；上位机入口为 `ssh root@192.168.1.11 -p 37878`；开始新一轮迭代，继续完成代码和功能；设计好才能开始写功能点；功能点不完善不允许开始写代码；代码不完美不允许提交；结束后 git commit 和 push。

本轮设计结论：

- 必须先尝试真实 SSH 入口 `ssh root@192.168.1.11 -p 37878`，但不能再次只以 SSH 不通作为 sprint 收口。
- 本轮必须把已有 `field_route_evidence_preflight` 输出推进成可测试的 evidence manifest / artifact gate。
- SSH 恢复时，同一入口应能校验真实远端材料；SSH 不通时，也必须用本地 fixture 或临时目录跑通 manifest 生成、缺失材料 fail-closed、状态落盘和文档验收。

## 最近两轮 blocker 扫描

已扫描最近两轮现场 O3 验证相关 sprint：

- `sprints/2026.06.09_14-15_board-live-route-preflight-and-capture/final.md`：真实上位机 SSH 不可达，未产出 `map.yaml` / `route.csv` / keyframe / rosbag / replay JSONL。
- `sprints/2026.06.09_15-04_board-field-evidence-preflight/final.md`：已交付 preflight CLI，但 SSH 状态仍为 `blocked_ssh_unreachable`，未证明真实现场材料。

红线处理：

- 同一 SSH blocker 已连续两轮消费，本轮不允许第三次仅以 `blocked_ssh_unreachable` 结束。
- CEO 已再次给出 SSH 入口，因此本轮仍要先试真实 SSH。
- 如 SSH 仍不通，本轮必须切换到本地 fixture / 临时目录完成 artifact gate 软件证据，明确输出“不再次只消费同一 SSH blocker”。

## 本轮目标

围绕临时激活的现场 O3 验证 lane，新增“现场证据 artifact gate / evidence manifest”能力：

- 输入：已有 field preflight JSON、本地 artifact 目录或 SSH 远端 artifact 目录。
- 必需 artifact：`map.yaml`、`route.csv`、keyframe 文件、rosbag 目录或文件、fixed-route replay JSONL。
- 输出：统一 evidence manifest JSON，包含 artifact 清单、存在性、大小、mtime、sha256、来源、run id、preflight 状态、fail-closed 总状态和缺失原因。
- 失败语义：材料不完整时必须 `delivery_success=false`、`not_proven=true`、`primary_actions_enabled=false`，不能把模板、空文件或 SSH 不通误判为现场路线成功。
- 验证：无真实 SSH 时必须通过本地 fixture / 临时目录单元测试和 CLI dry-run；SSH 恢复时同一 CLI 可用 `ssh root@192.168.1.11 -p 37878` 校验远端材料。

## Owner 与协作边界

主责：`robot-algorithm-engineer` 单 owner 闭环。

原因：

- 功能属于导航/路线证据链与 fixed-route replay 证据 gate。
- 文件范围集中在 algorithm owner 可改的 `onboard/scripts/`、`onboard/tests/`、`docs/navigation/` 和本 sprint 留档。
- 本轮不改硬件配置、不改 WAVE ROVER / ESP32 / UART / 串口 / 速度映射 / launch 默认硬件参数，因此不需要 `rober-hardware-engineer` 介入。
- 本轮不改 PC/mobile/cloud 产品 UI 或 API，因此不需要 `full-stack-software-engineer` 介入。

## 验收口径

本轮完成后，必须同时满足：

- 已尝试真实 SSH 入口，且无论成功失败都留下 JSON / 日志证据。
- 本地 fixture / 临时目录能证明 manifest CLI 可生成完整状态和 fail-closed 状态。
- 单元测试覆盖完整 artifact、缺失 artifact、空文件或坏 preflight 至少三类路径。
- 文档写清楚 manifest contract、真实 SSH 用法、本地 fixture 用法和“不等于现场路线成功”的边界。
- 完成 `tech-done.md`、`side2side_check.md`、`final.md`，并由 engineer 完成 git commit / push 前检查。

## 本轮不做

- 不启动真实机器人运动、不发布 `/cmd_vel`、不修改底盘协议。
- 不声称完成真实路线、真实送达或 Nav2 实跑，除非产出真实 `map.yaml` / `route.csv` / keyframe / rosbag / replay JSONL 并通过 manifest gate。
- 不把 SSH 不通作为唯一交付结果。
- 不提交未验证代码。

