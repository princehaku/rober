# O7 PC Consumer Read Integration Tech Plan

## 计划状态

本轮设计与实现已经完成并收口。此文件保留设计依据、验收口径和风险边界，当前状态以 `tech-done.md` / `final.md` 为准，不再表示“仅设计未执行”。

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：**O6**
- 本 sprint 是否针对该 Objective：**是**
- 选择理由：O6 已完成 local/mock 的 write/query 分层，但消费侧仍未被 O7/手机真正接管；若不先做统一消费入口，O7 接口面会继续在多个 tab 重复做聚合，阻碍下一步 O7 与 O6 真实化迁移。
- `final.md` 复盘时需核对：本轮是否在 O7 端有效降低了重复消费与 fail-closed 解释成本；若未达成，应升级为接口契约不完整或范围遗漏。

## 本轮目标与功能点定义（For Implementation）

### FP1: O7 主入口消费改造

- 统一入口：`GET /api/o6/consumer/tasks`
- 场景：PC O7 “任务列表/任务池”页面
- 必须行为：不再默认 `GET /api/o6/archive/tasks` + 多路再拼接
- 成功标准：
  - 可展示任务状态摘要与证据字段
  - `task_status_summary` 与 `labeling_status` 与后端一致
  - 缺失子视图返回 `pending/absent/not_available` 而不是空白成功

### FP2: O7 任务详情统一入口

- 统一入口：`GET /api/o6/consumer/tasks/<task_id>`
- 场景：O7 任务详情、路线回放入口、标注预览入口、ASR/TTS 诊断入口
- 成功标准：
  - `task_summary`、`events`、`evidence`、`labeling`、`inference`、`tunnel_status` 一致返回
  - `tunnel_status.latest_known_status` 在说明中标明 “latest known snapshot, not task-time aligned”
  - 手机摘要场景可走 `view=summary`

### FP3: O7 fail-closed 与边界文案

- 场景：任务缺失、query 非法、未知 include、limit 越界、危险字段
- 成功标准：
  - 返回结构化 blocked/not_proven，不伪造状态
  - `proof_status=not_proven`、`safe_to_control=false`、`connects_cloud_production=false`、`robot_control_executed=false`
  - UI 文案不出现“可下发”“可控制”“已交付”类语义

### FP4: O7 文档与运行指引

- 在产品文档中新增 “PC 端接入 O6 consumer read 作为首选”规则
- 保持对已有低层 endpoint 的兼容说明，但禁止新增实现中“默认必须多接口 join”假设

## 文件范围

本 sprint 仅设计与文档，允许改动：

- `docs/product/pc_tools_workstation.md`
- `sprints/2026.06.09_07-08_o7-pc-consumer-read-integration/pre_start.md`
- `sprints/2026.06.09_07-08_o7-pc-consumer-read-integration/prd.md`
- `sprints/2026.06.09_07-08_o7-pc-consumer-read-integration/tech-plan.md`

不允许改动（本 sprint）：  
- 其它 sprint 文档  
- `docs/interfaces/o6_cloud_archive_api.md`（本轮不扩展接口，已在上一轮完成）  
- ROS2 主链路、串口参数、WAVE ROVER、Nav2、launch 配置

## Owner 与执行方式

- 主责实现 owner：`full-stack-software-engineer`（PC 消费层与边界定义）
- 只读咨询：`robot-software-engineer`（确认 O6 consumer read payload 与状态口径）
- 产品 owner：`product-okr-owner`（验收与方向调整）

## 关键验收命令（只读）

```bash
test -f sprints/2026.06.09_07-08_o7-pc-consumer-read-integration/pre_start.md && \
test -f sprints/2026.06.09_07-08_o7-pc-consumer-read-integration/prd.md && \
test -f sprints/2026.06.09_07-08_o7-pc-consumer-read-integration/tech-plan.md
```

```bash
sed -n '1,220p' sprints/2026.06.09_07-08_o7-pc-consumer-read-integration/pre_start.md && \
sed -n '1,260p' sprints/2026.06.09_07-08_o7-pc-consumer-read-integration/prd.md && \
sed -n '1,260p' sprints/2026.06.09_07-08_o7-pc-consumer-read-integration/tech-plan.md
```

```bash
rg -n "consumer/tasks|view=summary|include=|fail-closed|safe_to_control=false|proof_status=not_proven|connects_cloud_production=false|robot_control_executed=false|O6-KR6|O7" docs/product/pc_tools_workstation.md sprints/2026.06.09_07-08_o7-pc-consumer-read-integration
```

```bash
git status --short
```

```bash
git diff --check -- sprints/2026.06.09_07-08_o7-pc-consumer-read-integration docs/product/pc_tools_workstation.md
```

## 验收边界（开始写代码前）

以下全部达成后，允许工程进入实现：

1. PRD 与技术点清晰列出 F1~F4，包含每个功能的输入/输出字段与失败语义
2. `docs/product/pc_tools_workstation.md` 增补“PC 首选消费 O6 consumer read”规则
3. 未出现跨 sprint 的 blocker 重复消费问题
4. 设计文档中明确不继续本轮 O6 production 化的边界与下一轮回归触发条件

## 风险与失败定位预案

- 风险 1：工程实现混用 `archive` 与 `consumer` 双路径，导致状态解释不一致。  
  处理：在代码评审和 side2side 时要求仅将 O7 任务列表/详情的 primary path 定义为 consumer read。
- 风险 2：PC 端直接将 `pending/absent` 等同于真空状态，误发成功告警。  
  处理：统一状态层增加 fail-closed 文案模板。
- 风险 3：在没有 O6 production 化条件下误将 local/mock 标注为 production。  
  处理：前端文案检查点固定 `proof_status`/`safe_to_control`/`robot_control_executed` 三段式，不允许缺失。
- 风险 4：方向偏移为 O6 生产化而忽视 O7 推进。  
  处理：以“本轮不可变目标”锁定 F1~F4，不新增 O6 infra scope。

## 成功退出条件

- 设计文档可被 `full-stack-software-engineer` 直接执行，无需再次澄清消费入口、字段、失败边界。
- O7 在本地消费链路中具备统一读取前置，不再默认拼装底层多 endpoint。
- 未触发新的“重复 blocker”与并行职责冲突。
