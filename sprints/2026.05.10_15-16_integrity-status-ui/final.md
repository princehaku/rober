# Sprint 2026.05.10 15-16 Integrity Status UI - Final

## 状态

- 阶段：final completed。
- 时间：2026-05-10 15:45 Asia/Shanghai。
- Product Owner：`product-okr-owner`。
- 实现主责：`full-stack-software-engineer`。

## 本轮收口结论

本轮目标成立并完成：operator 页面已新增 Vision evidence chain 诊断卡片，把 `/api/diagnostics.vision_samples` 的完整性结果转成用户触点可读的状态灯、原因列表和恢复建议。它让 Objective 5 的手机诊断能力前进一步，也让 Objective 4 的视觉证据链不再只停留在离线 checker 或 raw diagnostics 字段。

这次收口不把 happy path 当成产品闭环完成。本轮没有真实手机浏览器截图，没有真实 camera/odom manifest 上车验证，也没有普通用户现场验收；这些仍是后续必须补齐的证据链。

## 用户价值和产品北极星

用户价值：普通用户或现场支持打开手机本地 operator 页面后，可以直接判断视觉证据链是否健康、缺什么、下一步如何恢复，不需要理解 ROS2、manifest checker 或文件路径。

产品北极星：普通用户只靠手机完成垃圾投递任务，并在失败或证据缺失时知道该怎么处理。

## OKR 进度更新

| Objective | 本轮前 | 本轮后 | 更新理由 |
| --- | --- | --- | --- |
| Objective 1 硬件协议可信底盘 | 约 70% | 约 70% | 本轮未改硬件协议、UART、底盘桥或上车验证 |
| Objective 2 可恢复送垃圾任务闭环 | 约 74% | 约 74% | 本轮未改行为状态机、action 或真实任务闭环 |
| Objective 3 可验证导航与固定路线 | 约 68% | 约 68% | 本轮未改路线、Nav2、keyframe 或学习流程 |
| Objective 4 感知模块产品化 | 约 67% | 约 68% | Vision evidence chain 诊断结果进入 operator 页面，但还没有真实 camera/odom manifest 上车闭环 |
| Objective 5 手机体验与量产边界 | 约 72% | 约 74% | 手机本地 operator 页面新增可读诊断灯、原因和恢复建议，并有自动化验证证据 |

## 本轮核心抓手

- 把后端 diagnostics 的视觉证据链健康度转成手机页面可理解的诊断卡片。
- 保持 dependency-free operator 页面和现有 API contract，不扩大后端字段范围。
- 用测试锁住页面关键 DOM、渲染函数和 diagnostics 字段名，降低内联 HTML/JS 回退风险。

## 做了什么 / 没做什么

做了：

- operator 页面 Support Diagnostics 新增 Vision evidence chain 卡片。
- 页面展示 `Healthy`、`Needs review`、`Broken`、`Not configured`、`Checker unavailable`、`Checker failed` 等状态。
- 页面展示最多 3 条缺失/错误/警告原因，并提供恢复建议。
- `OKR.md` 当前进度快照已更新：Objective 5 约 74%，Objective 4 约 68%，Objective 1/2/3 保持不变。
- 本 sprint 已补齐 `side2side_check.md` 和 `final.md` 收口文档。

没做：

- 没有真实手机浏览器截图。
- 没有真实 camera/odom manifest 上车验证。
- 没有喇叭/TTS 联动验证。
- 没有量产硬件实物验收或普通用户现场测试。

## 验证结果

Full-Stack Engineer 在 `tech-done.md` 记录：

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_behavior/test -p 'test_operator_gateway_http.py'`：16 tests OK。
- `python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`：通过。
- `git diff --check`：通过。
- `PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh`：通过，interfaces 6、hardware 14、nav 27、bringup 9、behavior 111、vision 13 tests OK。

Coordinator 复跑确认：

- HTTP 页面测试：16 tests OK。
- py_compile：通过。
- git diff --check：通过。

## 失败定位

本轮实现阶段出现过一次本地测试导入失败：`ModuleNotFoundError: No module named 'ros2_trashbot_behavior'`。Full-Stack Engineer 已在允许修改的 HTTP 测试文件中补齐源码树 `sys.path`，复跑后通过。该失败不是产品功能失败，也未影响 `/api/diagnostics` contract。

## 剩余风险和下一步

- P0：补一次真实手机宽度浏览器截图或人工浏览器检查，确认 Vision evidence chain 卡片在手机页面不溢出、不遮挡、不误导用户。
- P0：补真实 camera/odom manifest 上车或采集验证，证明 diagnostics 字段不是纯 mock/fixture 链路。
- P1：把 Vision evidence chain 异常和喇叭/TTS 或状态提示词联动，减少用户只看屏幕才知道异常的依赖。
- P1：继续补量产硬件约束实物验收，避免 UI 诊断能力脱离低成本装配边界。

## 需要创建或更新的 sprint 文档

已完成：

- `sprints/2026.05.10_15-16_integrity-status-ui/side2side_check.md`
- `sprints/2026.05.10_15-16_integrity-status-ui/final.md`
- `OKR.md`
