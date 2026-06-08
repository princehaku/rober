# O6 Consumer Read API Tech Plan

## 计划状态

本文件完成后，本轮设计已达到可交给 Engineer 开始写代码的程度。Product 设计阶段到此收口，不写产品代码。

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：O6（0%）
- 本 sprint 是否针对该 Objective：是
- 选择理由：最近 5 轮已补齐 O6 的 archive / labeling / inference / tunnel / event-evidence local/mock 写与分散查询 proof，但 O6-KR6 的统一消费侧查询面仍缺位。若不先做 KR6，O7 和手机消费层会继续围绕多个底层 endpoint 重复造聚合逻辑。
- `final.md` 收口时需复核：本轮统一读模型是否真的降低了 O7/手机消费复杂度，还是只新增了另一层分散接口。

## 主责 Engineer

- 主责：`full-stack-software-engineer`
- 只读咨询：`robot-software-engineer`
- 执行方式：单 owner 单线闭环

单线原因：

- 文件范围集中在 `remote_cloud_relay.py`、对应测试和接口/产品文档
- 不涉及硬件协议、WAVE ROVER、Nav2、真实 ROS2 runtime 或前端 UI 实装
- 这是云查询面的 contract 设计与实现，不需要拆成多 owner 并行

## 目标接口

本轮要求 Engineer 在既有 O6 local/mock store 之上新增统一消费侧查询面。推荐 endpoint 形态如下：

### 1. 统一任务列表

- `GET /api/o6/consumer/tasks`

作用：

- 返回给 PC/手机消费的任务卡片列表
- 聚合 task 基本信息、事件摘要、证据计数、标注状态、推理状态和 tunnel 在线状态

最小 query：

- `robot_id`
- `task_id`
- `date`
- `status`
- `limit`
- `before_started_at_ms` 或等价轻量分页参数
- `view=summary|default`

### 2. 统一任务详情

- `GET /api/o6/consumer/tasks/<task_id>`

作用：

- 返回单任务聚合详情
- 默认给 PC 使用
- 手机可通过 `view=summary` 获取裁剪版本

最小 query：

- `robot_id`
- `view=summary|default`
- `include=trajectory,events,evidence,labeling,inference,tunnel`

## 统一读模型

### 列表响应

列表每个 task item 至少提供：

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
- `selected`

顶层还必须提供：

- `schema`
- `source`
- `proof_status`
- `safe_to_control`
- `connects_cloud_production`
- `robot_control_executed`
- `query`
- `task_list.total_tasks`
- `task_list.tasks[]`

### 详情响应

详情至少提供以下 section：

- `task_summary`
- `trajectory`
- `events`
- `evidence`
- `labeling`
- `inference`
- `tunnel_status`
- `proof_boundary`

聚合规则：

1. `task_summary`
   - 来自 archive task 主记录
2. `trajectory`
   - 来自 task `trajectory_frames[]`
   - 可限量输出 sample + `total_count`
3. `events`
   - 来自 archive events 和 task 已内嵌 events
   - 按 `occurred_at_ms` 升序
4. `evidence`
   - 来自 evidence archive 摘要
   - 只保留白名单字段
5. `labeling`
   - 来自 labeling summary
   - 返回 `task_status`、`label_count` 和限量 item summary
6. `inference`
   - 从事件中抽出 `model_inference.*` 摘要
   - 返回 `inference_status` 与限量 result summary
7. `tunnel_status`
   - 按 `robot_id` 取最新 tunnel snapshot
   - 不要求和 task 时间完全对齐，但必须写明是 latest known status

## 状态归一规则

后端统一负责把底层数据归一为消费侧状态：

- `task_status_summary`
  - `completed_mock`
  - `failed_mock`
  - `in_progress_mock`
  - `unknown_not_proven`
- `labeling_status`
  - `pending`
  - `partial`
  - `labeled`
  - `not_available`
- `inference_status`
  - `present`
  - `absent`
  - `not_available`
- `tunnel_status_summary`
  - `online`
  - `offline`
  - `unknown_not_proven`

要求：

- 不能把没有数据直接解释成真实 negative
- 必须区分 `absent` 和 `not_available`
- 所有 summary 名称要适合 PC/手机直接消费

## fail-closed 规则

以下情况必须 fail-closed：

- store 文件坏 JSON
- `task_id` 不存在
- `robot_id` 与 task 不匹配
- `limit` 非法或超过上限
- `include` 含未知 section
- query 中出现 `Authorization`、`Bearer`、`token`、`password`、`secret`、`/cmd_vel`、串口路径、`baudrate`、traceback、credential URL
- 子视图含 unsafe content 或危险 true 声明

固定 false 边界至少包括：

- `proof_status=not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `connects_cloud_production=false`
- `robot_control_executed=false`

## 文件范围

允许 `full-stack-software-engineer` 在实现阶段改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `cloud-relay/README.md`
- `docs/interfaces/o6_cloud_archive_api.md`
- `docs/product/pc_tools_workstation.md`
- `sprints/2026.06.09_06-07_o6-consumer-read-api/tech-done.md`
- 必要时：
  - `sprints/2026.06.09_06-07_o6-consumer-read-api/side2side_check.md`
  - `sprints/2026.06.09_06-07_o6-consumer-read-api/final.md`

不得改动：

- `OKR.md`
- 其他 sprint 文档
- mobile / pc UI 源码
- WAVE ROVER / UART / 硬件配置
- Nav2 / launch / 行为状态机

## 接口影响

### 对既有 O6 低层接口的影响

- 不删除既有 `archive/tasks`、`archive/events`、`archive/evidence`、`archive/labels`、`archive/inference`、`tunnel/robots`
- 新查询面是消费层聚合接口，不替代底层写入口
- 既有 O7 或测试代码可继续用旧接口；新接口作为推荐消费面

### 对 PC/手机消费方的影响

- PC/手机后续可优先从 `consumer/tasks` 和 `consumer/tasks/<task_id>` 读取
- 减少前端 join 逻辑
- 统一空态、blocked 态和 not_proven 语义

### 对文档的影响

- `docs/interfaces/o6_cloud_archive_api.md` 需要新增 consumer read contract
- `docs/product/pc_tools_workstation.md` 需要把 O7 后续消费入口从“直接消费分散 O6 低层接口”更新为“优先消费统一读接口”
- `cloud-relay/README.md` 需要说明该接口只证明 local/mock aggregated read model

## 实现要求

1. 数据来源
   - 复用同一个 `TRASHBOT_O6_CLOUD_ARCHIVE_STATE`
   - 不新增第二套 store
2. 查询瘦身
   - 支持 `view=summary`
   - 支持 `include=...`
   - 防止手机默认拿到过大 payload
3. 时间和排序
   - 列表默认按 `started_at_ms` 或 `updated_at_ms` 倒序
   - 详情事件按发生时间升序
4. 推理摘要
   - 从 `model_inference.*` events 中归纳
   - 不要求新增独立 inference store
5. 注释规范
   - 新增技术注释必须使用中文
   - 对聚合和状态归一逻辑说明“为什么”

## 验收命令

### Product 设计阶段验收命令

```bash
test -f sprints/2026.06.09_06-07_o6-consumer-read-api/pre_start.md && test -f sprints/2026.06.09_06-07_o6-consumer-read-api/prd.md && test -f sprints/2026.06.09_06-07_o6-consumer-read-api/tech-plan.md
```

```bash
rg -n "sprint_type: epic|OKR 最低优先级核对|O6-KR6|验收命令|文件范围|robot-software-engineer|full-stack-software-engineer" sprints/2026.06.09_06-07_o6-consumer-read-api
```

```bash
git diff --check -- sprints/2026.06.09_06-07_o6-consumer-read-api
```

### Engineer 实现阶段验收命令

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
```

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
```

```bash
rg -n "GET /api/o6/consumer/tasks|GET /api/o6/consumer/tasks/<task_id>|proof_status=not_proven|safe_to_control=false|connects_cloud_production=false|robot_control_executed=false|view=summary|include=" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md docs/product/pc_tools_workstation.md cloud-relay/README.md sprints/2026.06.09_06-07_o6-consumer-read-api
```

```bash
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py cloud-relay/README.md docs/interfaces/o6_cloud_archive_api.md docs/product/pc_tools_workstation.md sprints/2026.06.09_06-07_o6-consumer-read-api
```

## 风险边界

- 本轮只设计并计划 local/mock 统一查询面，不证明真实生产读流量
- 不证明真实 WebSocket/SSE 事件流
- 不证明真实 DB 索引、分页性能或多实例一致性
- 不证明真实手机 UI 已接通
- 不证明真实 tunnel、真实 4G、真实公网 TLS 或真实机器人控制

## 开始写代码判定

判定：**允许 Engineer 开始写代码。**

原因：

- 用户价值、目标 KR、主责 owner、接口 contract、文件范围、验收命令和风险边界都已明确
- 没有未解决的产品级阻塞
- 本轮设计已经足够支撑 `full-stack-software-engineer` 进入实现
