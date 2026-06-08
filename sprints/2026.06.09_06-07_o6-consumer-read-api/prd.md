# O6 Consumer Read API PRD

## 需求概述

本 sprint 要把 O6 已有 local/mock archive 低层接口整理成统一的消费侧读 API，优先服务 PC 运营调试和后续手机查询。目标不是新增新的写入能力，而是提供一个稳定、可扩展、可 fail-closed 的统一查询面，覆盖：

- 历史任务列表
- 任务详情
- 轨迹数据
- 事件流
- 证据引用
- 标注状态
- 推理状态
- 机器人 tunnel 在线状态

本 PRD 明确 O6-KR6 的产品定义，不证明真实云 DB、真实 OSS、真实 WebSocket、真实手机设备、真实公网、真实机器人控制或真实交付成功。

## 目标用户

- PC 运营/研发用户：需要按任务回放和排障，不想在前端分别拉 task/events/evidence/labels/tunnel 多条接口再做 join。
- 手机查询用户：需要简单看到最近任务、当前在线状态、最近失败或证据摘要，不需要暴露复杂内部字段。
- 工程实现与 QA：需要一个单一 contract 做单元测试和后续 UI 接入，而不是继续围绕 fixture 拼装。

## 用户价值

1. 降低消费端复杂度：PC 和手机通过统一查询面读取 O6 数据，不再重复聚合底层接口。
2. 降低后续返工：当 O6 从 local/mock 迁到真实云 DB 时，只需守住同一个 read contract。
3. 提高状态解释一致性：`online/offline`、`pending/partial/labeled`、`inference_present`、`latest_event_at_ms` 等语义由后端统一输出。
4. 保持安全边界：所有读接口继续固定 `proof_status=not_proven` 和 `safe_to_control=false`，避免把 software proof 误报为线上能力。

## 范围内功能

### P0：统一任务列表

新增一个 O6 consumer read list endpoint，用于返回任务卡片级摘要。列表必须至少包含：

- `task_id`
- `robot_id`
- `started_at_ms`
- `finished_at_ms`
- `task_status_summary`
- `latest_event_at_ms`
- `trajectory_frame_count`
- `event_count`
- `evidence_count`
- `labeling_status`
- `inference_status`
- `tunnel_status_summary`
- `selected=false|true` 或等价字段

列表必须支持最小查询参数：

- `robot_id`
- `task_id`
- `date`
- `status`
- `limit`
- `cursor` 或等价的 offset/after 方案二选一

本轮建议优先用简单 `limit + before_task_id` 或 `limit + before_started_at_ms` 方案，避免为 local/mock store 引入复杂分页游标。

### P0：统一任务详情

新增一个 O6 consumer read detail endpoint，返回单个任务的聚合视图。详情必须把已有 O6 数据按读模型重组为：

- `task_summary`
- `trajectory`
- `events`
- `evidence`
- `labeling`
- `inference`
- `tunnel_status`
- `proof_boundary`

其中：

- `trajectory` 可返回完整小数组或受限数组 + `has_more=false`
- `events` 必须按时间升序
- `evidence` 只返回白名单摘要，不返回原始 object 内容
- `labeling` 返回 task 级 summary 和限量 item summary
- `inference` 返回从 event 中提取出的推理摘要，不要求单独新建 store
- `tunnel_status` 返回与该 `robot_id` 对应的最新 tunnel snapshot

### P0：统一筛选和瘦身模式

为了兼顾 PC 和手机，detail endpoint 必须支持轻量化查询模式，例如：

- `view=summary`
- `include=trajectory,events,evidence,labeling,inference,tunnel`

设计要求：

- 未显式请求的重字段可以省略或返回空数组
- 手机默认可走 `view=summary`
- PC 可按需请求明细

### P0：状态归一

后端必须统一输出以下消费侧状态，而不是把底层 store 原样透传给前端：

- `task_status_summary`
  - 例如 `completed_mock`, `failed_mock`, `in_progress_mock`, `unknown_not_proven`
- `labeling_status`
  - `pending`, `partial`, `labeled`, `not_available`
- `inference_status`
  - `present`, `absent`, `not_available`
- `tunnel_status_summary`
  - `online`, `offline`, `unknown_not_proven`
- `proof_boundary`
  - 固定说明 local/mock、non-production、no-control

### P0：fail-closed 读接口规则

以下情况必须返回结构化 blocked/not_proven，而不是伪造成功数据：

- store 文件坏 JSON
- task 不存在
- query 非法
- `limit` 超上限
- `include` 包含未知字段
- 聚合过程中发现 unsafe content
- tunnel 状态不存在
- label / inference / evidence 子视图缺失

缺子视图时允许局部 `not_available`，但顶层必须显式说明，不得让消费方误解为“真实没有发生”。

## 范围外功能

- 不新增任何真实云写链路
- 不新增 WebSocket / SSE 实时事件流
- 不新增真实数据库分页 cursor
- 不新增真实鉴权体系调整
- 不修改 PC UI 或手机 UI
- 不接入真实 WAVE ROVER、串口、硬件、ROS2 实时图
- 不把 tunnel 在线状态解释成真实公网隧道已通

## KR 拆解与历史归档判断

### 本轮直接推进

- `O6-KR6`：统一 REST 查询面

### 本轮消费既有证据

- `O6-KR1`：复用 `tunnel online status` local/mock 数据
- `O6-KR2`：复用 archive task / events
- `O6-KR3`：复用 evidence refs 摘要
- `O6-KR4`：复用 labeling status
- `O6-KR5`：复用 inference event 摘要

### 历史归档判断

当前没有任何 O6 KR 达到“可归档到历史区”的条件。原因：

- 都只有 local/mock software proof
- 缺少真实生产链路、真实设备或真实用户验收
- 本轮只新增统一读模型，不构成真实闭环完成

因此本轮只设计，不移动任何 KR 到历史区。

## 本轮核心抓手

把“多个低层 endpoint 的事实”转成“一个消费层 contract”。核心抓手是：

- 定义统一列表卡片字段
- 定义统一详情结构
- 定义 include/view 的轻量查询模式
- 定义状态归一和 fail-closed 规则
- 把 PC/手机都需要的最小字段一次写清

## 优先级和验收口径

### P0 验收

以下全部满足，Engineer 才允许开始实现并在完成后进入收口：

- 已有 O6 task / event / evidence / label / inference / tunnel 数据源都有明确消费位置
- 统一列表 contract 定义完成
- 统一详情 contract 定义完成
- query 参数、状态归一、边界字段和 fail-closed 规则定义完成
- 明确主责 Engineer、文件范围和验收命令

### 工程完成后验收口径

- 至少 1 个统一列表 endpoint 和 1 个统一详情 endpoint 可通过 unittest 验证
- `docs/interfaces/o6_cloud_archive_api.md`、`docs/product/pc_tools_workstation.md`、`cloud-relay/README.md` 同步更新
- 读接口响应中明确包含：
  - `proof_status=not_proven`
  - `safe_to_control=false`
  - `connects_cloud_production=false`
  - `robot_control_executed=false`
- 任何缺失子视图或非法 query 都能 fail-closed，而不是返回伪造成功态

## 责任 Engineer

主责 Engineer：`full-stack-software-engineer`

原因：

- 改动核心是 cloud relay REST API contract 与消费侧文档
- 这是 PC/手机共享的后端查询面，不是 ROS2 主链路改造
- `robot-software-engineer` 只需在必要时做只读接口事实确认，不需要并行实现

## 风险、阻塞和需要补齐的证据链

- local/mock store 适合本轮 contract proof，但不代表未来真实 DB 查询成本和分页行为
- 如果本轮不定义 `view/include` 瘦身机制，后续手机消费可能拿到过重 payload
- 如果直接把底层 schema 透传给前端，后续迁移真实云时会造成二次破坏
- 仍缺真实手机界面、真实公网和真实任务现场证据
- 仍缺统一审计字段是否足够支撑未来回放/标注/客服排障的验证
