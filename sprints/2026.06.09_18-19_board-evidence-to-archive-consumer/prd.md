# PRD - 板载 Evidence 到 O6 Archive/Consumer Detail

## 一句话目标

本轮把 `trashbot.field_evidence_manifest.v1` 从“artifact gate”变成可消费入口，继续接到 O6 archive + O7 consumer detail，形成“manifest -> archive/task -> consumer detail -> 可读证明摘要”的闭环。

## 用户价值

1. 现场材料产出后，PC 端不再只在 `Field evidence consumer ingest` 停留，而能看到任务轨迹、事件、标注和推理摘要的统一入口。
2. 在 SSH 恢复前，团队仍可继续做软件回归，避免再次卡在单点 blocker。
3. 运营侧能确认每份 evidence 的 `not_proven` 与 `delivery_success` 约束，减少“当成真实现场成功”的误判。

## 背景

- 上一轮已完成 manifest 产物能力，仍缺一条明确消费路径：
  - 如何从 manifest 入场；
  - 如何转入 O6 archive 或 consumer detail；
  - 如何在 O7/PC 显示 `artifact status` 与 `manifest gate`。
- 上位机真实 SSH 入口虽提供（`root@192.168.1.11 -p 37878`），但当前不可达不能作为唯一验收条件。

## 需求范围（In Scope）

### F1 读取 manifest 输入

- 读取 `trashbot.field_evidence_manifest.v1`，输出 `manifest_entry`，至少提取：
  - `status / gate_pass / not_proven / blocked_reason / blocked_reasons`
  - `source / schema / generated_at / artifact_summary`
  - `next_required_evidence`
- manifest schema mismatch、missing file、bad JSON、unsafe 内容必须 fail-closed。

## F2 转换/注入 O6 archive 或 consumer mock 模型

- 在 O6 local/mock 数据模型下，以可追溯方式构建：
  - archive task 或 consumer detail 来源链条（task_id/evidence_ref/artifact refs）
  - `artifact_status`（gated/missing/blocked）与 `gate_pass` 一致映射
- 必须保持 `source=software_proof` 或已存在的 O6 contract source，不新增真实生产云语义。
- 若可用字段不足，必须保留 blocked reason，不允许虚构成功。

## F3 O7/PC 通过 consumer detail 可见入口

- O7 列表与详情读取优先走 `consumer` 语义而非手工拼接 archive fragment。
- `consumer detail` 中必须能观察到：
  - manifest 来源归属（manifest status/manifest schema/evidence_ref）
  - `artifact_status` 与 `artifact_missing` 解释
  - `not_proven`、`delivery_success`、`primary_actions_enabled`
  - `proof_status` 与控制边界（`safe_to_control=false`、`robot_control_executed=false` 等）

## F4 边界与失败语义

- 任何阶段都必须保持 fail-closed：
  - `unknown_task` / `unknown_task_id` / `artifact_missing` / `schema_not_match` / `not_proven=true` / `blocked_reason` 非空
  - 输出 `ingest_status=blocked_not_proven` 或等效失败状态。
- 不允许任何界面或 API 声明：
  - `delivery_success=true`
  - `safe_to_control=true`
  - `primary_actions_enabled=true`
  - 实时 robot control / 真实送达完成。

## 非目标（Out of Scope）

- 不做真实控制、真实云部署、真实 OSS 上传、真实 4G 接入、真实数据库持久化。
- 不做硬件底层协议/底盘参数/串口路径/供应商材料重写。
- 不新增移动端新控制面，仅保证消费模型一致性。

## KR 映射与优先级

- 本轮直接推进：
  - `O7-KR3`
  - `O7-KR4`
  - `O6-KR2`
  - `O6-KR6`
- O6 与 O7 目标都需要：manifest 一旦产生即可落地到统一读模型，否则重复复用不同入口会反复产生人工清洗开销。

## 验收前置（设计闭合）

- 完成以下文档字段冻结后，允许 `full-stack-software-engineer` 写实现：
  - manifest 入口字段映射定义
  - archive/consumer detail 目标字段与 fail-closed 约束
  - SSH 可达与不可达两类命令分支
  - 下一位 owner 的可执行命令列表

