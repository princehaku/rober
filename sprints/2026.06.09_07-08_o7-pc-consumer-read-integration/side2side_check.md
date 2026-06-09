# O7 PC Consumer Read Integration Side2Side Check

## 对照范围

- 设计输入：`pre_start.md`、`prd.md`、`tech-plan.md`
- 实现输出：workstation consumer read adapter、O7 预览页 primary path、测试与产品文档

## Side-by-side 结果

### FP1 任务列表 primary path

- 设计要求：O7/PC 任务列表 primary path 使用 `GET /api/o6/consumer/tasks`
- 实现结果：已通过 workstation 后端 `/api/o7/consumer-read/tasks` 固定转发到 `GET /api/o6/consumer/tasks?view=summary&limit=50`
- 结论：符合

### FP2 任务详情 primary path

- 设计要求：O7/PC 任务详情 primary path 使用 `GET /api/o6/consumer/tasks/<task_id>`
- 实现结果：已通过 workstation 后端 `/api/o7/consumer-read/tasks/:taskId` 固定转发到 `GET /api/o6/consumer/tasks/<task_id>?view=default&include=trajectory,events,evidence,labeling,inference,tunnel`
- 结论：符合

### FP3 `view=summary` 与 detail `include=` 策略

- 设计要求：summary/detail 策略可见，字段映射与 fail-closed 语义可见
- 实现结果：
  - UI 明确展示 `view=summary`
  - UI 明确展示 detail `include=trajectory,events,evidence,labeling,inference,tunnel`
  - UI 明确展示 `safe_to_control=false`、`connects_cloud_production=false`、`robot_control_executed=false`
  - UI 明确展示 `blocked reasons`、`not proven`、`tunnel temporal alignment`
- 结论：符合

### FP4 文档与 sprint 收口

- 设计要求：同步文档与 sprint 留档，且不声明真实云/真实控制/真实交付
- 实现结果：
  - `docs/product/pc_tools_workstation.md` 已更新
  - `tech-done.md` / `side2side_check.md` / `final.md` 已补齐
  - 全部说明均保持 software proof 边界
- 结论：符合

## 差异项

- 无功能性偏差。
- 旧 `Cloud Archive Tasks` fixture 区块未删除，保留为 secondary path 预览，作为本地 fixture debug 补充。

## 验收意见

- 本轮可按 software proof 收口。
- 下一轮若要推进 O7 更深的 route replay/labeling/voice/command 真正运行链路，应继续以 O6 consumer read 为 primary path，不回退到前端多接口 join。
