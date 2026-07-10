# O6/O7 Current Field Evidence Material PRD

## 用户价值

运营和研发需要把真实上位机 current evidence 从散落的 smoke artifact，变成 O6/O7 能按同一 `task_id` 查询、审计和展示的材料摘要。这样下一轮现场复跑时，团队可以直接看到 camera/radar/map/Nav2 path/manual gate 哪些已经具备，哪些仍卡在 wheel L/R、HIL、delivery/operator material，而不是人工翻 70 多个 artifact。

## OKR 对齐

- O6 KR2/KR6：任务记录、感知事件和失败原因 archive/readback 能消费更强的现场材料。
- O7 KR1/KR3/KR4：PC consumer detail 能展示实时地图/历史回放相关的 current evidence material，帮助 operator 补齐下一步材料。
- O5/O1：本轮明确不调整，因为缺真实 production cloud 和真实 WAVE ROVER nonzero/HIL 材料。

## 范围内

- Algorithm manifest 新增 current field evidence material packet。
- O6 archive/readback 新增 additive section 与 consumer include。
- O7 consumer/UI 新增 read-only summary。
- 文档同步更新接口说明和 sprint 留档。

## 范围外

- 不新跑真实上位机命令。
- 不连接 production cloud、DB/queue、OSS/CDN。
- 不发送 `/cmd_vel`、NavigateToPose、`/api/base/manual` 或任何运动控制。
- 不声明 delivery success、safe_to_control、primary_actions_enabled、robot_control_executed。

## 验收口径

1. Algorithm 能从 fixture/current evidence summary 生成安全摘要，且 hostile payload fail-closed。
2. O6 能 ingest/readback/include 该 section，危险 true、绝对路径、URL/token/traceback 不回显。
3. O7 能在 consumer detail 展示该 section 的 status、present materials、blocked reasons 和 next required evidence。
4. 全链路保持 fixed false safety fields。
