# Sprint 2026.05.10 15-16 Integrity Status UI - Pre Start

## 状态

- 阶段：pre_start completed，进入 PRD。
- 时间：2026-05-10 15:00 Asia/Shanghai。
- 本轮类型：hourly `daily-bug-scan`，功能往前走，测试只做护栏。
- Product Owner：`product-okr-owner`。
- 主责 Engineer：`full-stack-software-engineer`。

## 上轮输入

上一轮 `2026.05.10_14-15_diagnostics-manifest-summary` 已把 vision sample manifest checker 结果接入 `/api/diagnostics.vision_samples`：

- 新增 `integrity_summary.status`、error/warning count、缺失文件引用、上下文字段覆盖和 file counts。
- 旧 diagnostics 字段保持兼容。
- 明确剩余缺口：真实手机页面尚未消费这些字段。

## 本轮用户价值

普通用户和现场支持同学不应看到一坨后端 JSON 后再猜视觉证据链是否可用。本轮要把 `/api/diagnostics.vision_samples.integrity_summary` 推进到手机本地 operator 页面：用诊断灯、缺失原因和恢复建议告诉用户“视觉证据链是否可信、为什么不可信、下一步怎么恢复”。

## 产品北极星

普通用户只靠手机就能完成垃圾投递任务，并在失败或证据缺失时知道该怎么处理；不要求用户理解 SSH、ROS2、manifest、文件路径或视觉算法。

## OKR 映射

- 主推进：Objective 5 手机体验与量产边界。把远程诊断字段转化为手机端可读状态，是 KR4 远程诊断最小数据包和 KR5 普通用户验收标准的直接增量。
- 消费：Objective 4 感知模块产品化。复用 manifest checker 的 `integrity_summary`，让视觉样本链从离线诊断进入 operator UI。
- 不更新：本轮只创建计划文档，不修改 `OKR.md` 进度快照；OKR 进度和收口证据留到实现后更新。

## 本轮核心抓手

把 operator 页面当前的 Support Diagnostics 从“显示字段”升级为“可行动的诊断卡片”：

- 视觉证据链诊断灯：`ok`、`warning`、`error`、`not_configured`、`checker_unavailable`、`checker_failed` 映射到用户可理解状态。
- 缺失原因：优先展示 missing file refs、checker errors/warnings、read error。
- 恢复建议：按状态给出普通用户/现场支持可执行的下一步，例如检查相机采集、恢复 manifest 路径、重新跑学习路线或联系支持。

## 做什么 / 不做什么

做：

- 在本地 operator HTML/JS 中消费现有 `/api/diagnostics.vision_samples` 字段。
- 保持 dependency-free HTML，不引入前端框架。
- 给 `test_operator_gateway_http.py` 增加页面静态断言，保证关键 DOM id、状态映射和字段名存在。
- 更新实现后的 `tech-done.md`，记录实际改动和验证。

不做：

- 不改 `/api/diagnostics` 后端字段契约。
- 不改 ROS2 msg/srv/action。
- 不改 manifest checker、vision 生产代码或样本写入逻辑。
- 不更新 `OKR.md` 进度快照。
- 不做真实手机浏览器或真实 camera/odom 数据证明；这属于实现后风险/后续验收。

## 优先级和验收口径

优先级：P0。理由：O5 仍缺手机 UI 展示，上一轮 O4/O5 后端诊断证据需要被普通用户入口消费，否则仍停在支持工程师字段层。

验收口径：

- `/` operator 页面能在 diagnostics 区显示视觉证据链健康状态、缺失/警告原因和恢复建议。
- `ok` 状态不制造恐慌，`warning/error/not_configured/checker_unavailable/checker_failed` 给出明确下一步。
- 旧页面控制按钮、状态、地图、diagnostics JSON 仍可用。
- 目标测试 `test_operator_gateway_http.py` 通过；`operator_gateway_http.py` 能 py_compile；`git diff --check` 通过。

## 风险、阻塞和证据链

- 风险：当前页面是内联 HTML/JS，容易因字符串改动破坏页面；需要测试锁住关键 DOM 和脚本函数名。
- 风险：`integrity_errors` 可能是工程诊断字符串，不应原样当成唯一用户文案；UI 应有状态级恢复建议。
- 风险：真实手机浏览器、真实 manifest 与真实摄像头样本不在本轮证明范围内。
- 阻塞：无产品方向阻塞；实现可以由 `full-stack-software-engineer` 单线闭环。
- 证据链缺口：实现后需在 `tech-done.md` 写明测试输出，并在后续 `side2side_check.md` 记录人工/手机页面验收情况。

## 需要创建或更新的 sprint 文档

本轮计划阶段创建：

- `sprints/2026.05.10_15-16_integrity-status-ui/pre_start.md`
- `sprints/2026.05.10_15-16_integrity-status-ui/prd.md`
- `sprints/2026.05.10_15-16_integrity-status-ui/tech-plan.md`

实现阶段后续必须更新：

- `sprints/2026.05.10_15-16_integrity-status-ui/tech-done.md`

验收/复盘阶段后续按结果更新：

- `sprints/2026.05.10_15-16_integrity-status-ui/side2side_check.md`
- `sprints/2026.05.10_15-16_integrity-status-ui/final.md`
