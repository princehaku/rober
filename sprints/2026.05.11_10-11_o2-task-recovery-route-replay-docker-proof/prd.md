# PRD: O2 Task Recovery Route Replay Docker Proof

## 目标

补齐 O2 任务恢复记录与 O3 fixed-route replay 的同源证据链。任务结束后，operator/diagnostics/crosscheck 应能用同一个 `evidence_ref` 对齐：

- fixed-route status payload
- task record 顶层 `route_progress`
- `nav_results[-1].evidence.route_progress`
- replay JSONL 最新记录

## 用户价值

当机器人任务失败或超时，普通用户/售后不应只看到“失败”。本轮让失败记录能指向具体 route checkpoint、target、failure_code 和 evidence_ref，便于手机端解释、docker proof 复账和后续上车 HIL 追证。

## 非目标

- 不新增硬件 smoke。
- 不修改 WAVE ROVER/Orange Pi vendor 文档或硬件脚本。
- 不声明真实 `hil_pass`。
- 不新增大测试套件。

## 验收标准

1. fixed-route status 只有嵌套 `route_progress` 时，behavior evidence 仍提升兼容字段。
2. task record 始终保留顶层 `route_progress`。
3. diagnostics 在 top-level `route_progress={}` 时仍从 nav evidence 回退。
4. crosscheck 在 `--task-record-dir` 找不到匹配 task record 时返回非 0。
5. crosscheck 在 task record 缺顶层和 nav evidence route_progress 时返回非 0。
6. OKR 4.1 只上调 O2/O3 software proof 到约 77%，O1 保持约 75% blocked。
