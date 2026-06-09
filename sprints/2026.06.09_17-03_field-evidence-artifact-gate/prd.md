# PRD - Field Evidence Artifact Gate

## 背景

当前 `OKR.md` 最高优先级是现场 O3 验证 lane：CEO 已提供真实上位机入口 `ssh root@192.168.1.11 -p 37878`，项目必须从软件 proof 切到真实路线材料证据链。

最近两轮已经交付了现场 preflight 入口，但真实 SSH 仍不可达，导致没有产出 `map.yaml`、`route.csv`、keyframe、rosbag 或 fixed-route replay JSONL。继续只做 SSH 探测会第三次消费同一 blocker，不符合 `AGENTS.md` 的 repeated blocker 红线。

本轮 PRD 目标是补齐“材料是否真的够验收”的 artifact gate，而不是再新增一个只报告 SSH 不通的 preflight。

## 用户价值

面向 CEO / 现场验收：

- 能一眼知道这次现场运行是否真的留下了地图、路线、关键帧、bag 和 replay 证据。
- SSH 恢复时，能用同一入口检查真实上位机材料，减少人工 SSH 后逐个找文件的成本。
- SSH 不通时，仍能通过本地 fixture 验证代码路径，避免研发停滞。

面向后续 O6 / O7：

- O6 云端 archive 后续可消费 manifest，把真实 artifact 作为存档对象引用。
- O7 PC 历史路线回放后续可消费 replay JSONL / keyframe 清单，而不是依赖手工口头说明。

## 功能范围

### P0：Evidence manifest CLI

新增或扩展一个可测试 CLI，基于已有 `field_route_evidence_preflight` 输出和 artifact 目录生成 manifest JSON。

建议入口由 `robot-algorithm-engineer` 在实现时择优确定，但必须满足：

- 支持本地模式，读取本地目录。
- 支持 SSH 模式或为 SSH 模式预留同一参数入口，可使用 `ssh root@192.168.1.11 -p 37878` 从远端执行只读检查。
- 支持输出到指定 JSON 文件。
- 支持以非零退出码表达 gate fail，或至少在 JSON 中明确 `gate_pass=false` 与 `status`。

### P0：Artifact 清单

Manifest 至少覆盖：

- `map.yaml`
- `route.csv`
- `keyframes/` 下至少一个图片或 JSON 关键帧文件
- `rosbag` 目录或文件
- `replay.jsonl` 或 fixed-route replay JSONL

每个 artifact 至少记录：

- `required`
- `present`
- `path`
- `size_bytes`
- `mtime_utc`
- `sha256`（目录可记录目录摘要或文件列表摘要）
- `reason`（缺失或无效时填写）

### P0：Fail-closed 状态

Manifest 顶层必须记录：

- `schema`
- `run_id`
- `generated_at`
- `source`
- `mode`
- `preflight_status`
- `gate_pass`
- `status`
- `blocked_reason`
- `not_proven`
- `delivery_success=false`，除非真实材料完整且 gate 通过
- `primary_actions_enabled=false`，除非真实材料完整且 gate 通过

缺任意必需 artifact、artifact 为空、preflight 为 dry-run 或 SSH 不可达时，必须 fail closed。

### P1：文档与复跑

更新导航文档，写清：

- 本地 fixture 验证方式。
- 真实 SSH 验证方式：`ssh root@192.168.1.11 -p 37878`。
- manifest JSON contract。
- 证据边界：manifest gate 通过只能证明材料完整，不自动证明真实送达成功；如果输入来自 dry-run，则必须保持 `not_proven=true`。

## 非目标

- 不做 ROS2 launch 或 Nav2 行为改造。
- 不做底盘控制、串口、UART、WAVE ROVER 或 ESP32 参数改造。
- 不做云端上传、OSS 存档、PC UI 展示。
- 不把本地 fixture 伪装成真实路线材料。

## 验收标准

本轮实现完成后，Engineer 必须提供：

- 真实 SSH 尝试结果：使用 `ssh root@192.168.1.11 -p 37878` 或 manifest CLI 的 SSH 模式，输出成功、失败或 timeout 的结构化证据。
- 本地完整 fixture：manifest 输出 `gate_pass=true`，artifact 全部 present。
- 本地缺失 fixture：manifest 输出 `gate_pass=false`，列出缺失 artifact，且 `not_proven=true`。
- 单元测试：覆盖完整、缺失、dry-run/preflight 未证明路径。
- 文档更新：`docs/navigation/` 中能按步骤复跑。
- Git 状态：只包含本轮允许范围内的有意改动，提交前通过 `git diff --check`。

## 成功指标

- 若真实 SSH 可达：产出或校验真实远端 artifact manifest，并明确是否已经具备 O3 现场路线证据。
- 若真实 SSH 不可达：仍产出本地 fixture manifest 测试证据，并把 SSH 仅作为一个字段记录，不再次只消费同一 SSH blocker。

