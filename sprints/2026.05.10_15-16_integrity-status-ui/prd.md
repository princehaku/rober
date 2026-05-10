# Sprint 2026.05.10 15-16 Integrity Status UI - PRD

## 状态

- 阶段：PRD completed，进入 tech-plan。
- 时间：2026-05-10 15:00 Asia/Shanghai。
- Product Owner：`product-okr-owner`。
- 主责 Engineer：`full-stack-software-engineer`。

## 背景

`/api/diagnostics.vision_samples` 已经能返回 manifest 完整性字段，但手机本地 operator 页面仍偏向展示原始 diagnostics 内容。用户在现场遇到视觉证据链问题时，不应该需要理解 manifest checker、missing file refs 或 context coverage 的工程语义。

本轮把这些字段变成手机页面的可读诊断灯和恢复建议，让 O5 的“普通用户可理解异常”前进一步，同时消费 O4 的视觉样本链 checker 结果。

## 用户价值和产品北极星

用户价值：用户或现场支持打开手机 operator 页面后，可以直接判断视觉证据链是否健康、缺了什么、下一步该做什么，减少 SSH/ROS2/文件系统排查。

产品北极星：普通用户只靠手机完成垃圾投递任务，并在异常时看到清楚的人话提示和恢复路径。

## OKR 映射

| OKR | 本轮贡献 | 验收证据 |
| --- | --- | --- |
| Objective 5 KR4 远程诊断最小数据包 | 将视觉证据链健康度转为 operator 页面诊断灯、原因和建议 | 页面 DOM/JS 和 HTTP 静态测试覆盖 |
| Objective 5 KR5 普通用户验收标准 | 用户不需要命令行即可知道视觉证据链异常下一步 | 手机页面文案、恢复建议和状态映射 |
| Objective 4 KR3 视觉样本目录和 manifest contract | 消费 manifest checker 输出，不新增默认 detector 承诺 | 不改 vision 生产代码，只读现有 diagnostics 字段 |

## KR 拆解

- KR1：operator 页面在 diagnostics 区新增视觉证据链状态块，展示 `integrity_summary.status` 和 error/warning/missing counts。
- KR2：状态块支持 `ok`、`warning`、`error`、`not_configured`、`checker_unavailable`、`checker_failed` 的用户文案映射。
- KR3：页面显示最重要的缺失原因：优先 `missing_file_refs`，其次 `integrity_errors`，再次 `integrity_warnings`，最后 `read_error`。
- KR4：页面给出恢复建议，避免只贴工程字符串。
- KR5：`test_operator_gateway_http.py` 增加护栏，确认页面包含新增 DOM id、状态映射函数、恢复建议函数和现有 diagnostics 字段。

## 本轮核心抓手

把“后端有字段”推进为“手机页面能用”：

- 诊断灯：一眼识别 `ok/warning/error/not_configured/checker_unavailable/checker_failed`。
- 缺失原因：展示最多 3 条优先级最高的问题，避免长列表淹没用户。
- 恢复建议：每种状态给出一句明确建议。
- 保持旧入口：现有 raw diagnostics JSON、latest sample、review queue、map/status 控件继续保留。

## 做什么

- 修改 `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py` 内联 HTML/JS。
- 修改 `src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`，增加页面静态断言。
- 实现后更新本 sprint `tech-done.md`。

## 不做什么

- 不改 `operator_gateway_diagnostics.py`。
- 不改 `docs/interfaces/ros_contracts.md`，除非实现发现 UI 需要消费字段但现有 contract 不清；本轮计划默认不需要。
- 不改 `OKR.md`。
- 不新增前端构建链、CSS 框架或外部依赖。
- 不新增真实 camera/odom/manifest 数据。
- 不做硬件、UART、WAVE ROVER、Orange Pi 或 launch 参数改动。

## 优先级

P0：这是一轮 hourly `daily-bug-scan` 的功能推进项，目标是补 O5 的手机可读诊断缺口，同时让上一轮 O4 manifest checker 结果被用户触点消费。

## 验收口径

用户侧：

- 打开 operator 页面，Support Diagnostics 能看到视觉证据链健康状态。
- 当 `integrity_summary.status=ok` 时，页面表达为健康/可用。
- 当状态为 `warning/error/not_configured/checker_unavailable/checker_failed` 时，页面展示明确原因和恢复建议。
- 页面不要求用户理解 ROS2、manifest checker 或文件系统。

工程侧：

- `/api/diagnostics` HTTP 响应不变。
- 现有 operator 控制能力不回退。
- `test_operator_gateway_http.py` 覆盖新增页面元素和脚本函数名。
- 目标验证命令通过。

## 对应责任 Engineer

- 主责：`full-stack-software-engineer`。
- 其他角色：本轮不需要并行介入；若发现 diagnostics 字段缺失或 contract 不一致，由 `full-stack-software-engineer` 在 `tech-done.md` 记录并请求下一轮 Product/Robot 介入。

## 风险、阻塞和证据链

- 页面是 Python 字符串内联 HTML，测试只能做静态护栏，不能替代真实浏览器/手机视觉验收。
- `integrity_errors` 和 `missing_file_refs` 可能包含路径，页面应控制展示长度，避免手机端难读。
- `checker_unavailable` 是部署依赖风险，不应让用户误以为摄像头一定坏了。
- 本轮计划文档完成后仍缺 `tech-done.md`、`side2side_check.md` 和 `final.md`，实现与验收后补齐。
