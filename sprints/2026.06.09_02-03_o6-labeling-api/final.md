# O6 Labeling API Final

## 收口状态

本轮 O6 Labeling API 已完成软件闭环（本地/mock proof）：

- 新增 `POST /api/o6/archive/labels`、`GET /api/o6/archive/labels`、`GET /api/o6/archive/labels/<task_id>`。
- 仅允许在现有 archive task 上打标，越权/未知 task fail-closed。
- 成功响应固定 boundary 字段，明确不证明真实标注生产链路。
- 文档已同步到接口说明、PC 触点说明与 cloud-relay README。

## 验收结论

- 主体验收通过：py_compile、unitest 与 diff/rg 校验通过。
- 与 `tech-plan.md` 的验收命令一致；未出现未修复的构建/测试失败。
- `task_status` 使用 `pending / partial / labeled` 表达内部进度，`status=pending` 查询同时覆盖 `pending` 与 `partial`，与本轮定义一致。
- O6 labeling 幂等语义已修正为 key 级：新 key 无论 task 下既有 labels 数量如何都返回 `201/created`，混合批次只要含任一既有 key 即返回 `200/updated` + `duplicate=true`。

## OKR 进度与边界

- 该 sprint 未改变 O6 真实生产能力，仅补齐 O6-KR4 标注链路 local/mock 软件证据。
- 不证明：真实 O6 标注 API 上线、真实 annotation review API、真实训练集导出、真实 robot control。

## 剩余风险

- 仍未接真实标注平台、审核版本管理和训练导出闭环，`labeling` 仅用于 O7 本地工程验证与文档化。
- `task_status` 的 `partial` 语义需在 PC 页面与脚本中保持一致解释。
- 该接口仍依赖本机 `TRASHBOT_O6_CLOUD_ARCHIVE_STATE`，多实例/多机器人并发场景未做冲突治理。

## 提交提示

建议提交消息：

- `Add O6 local/mock labeling API and contract proof`

并保留证据边界：`local_mock_labeling`、`not_proven`、`proof_status=not_proven`。
