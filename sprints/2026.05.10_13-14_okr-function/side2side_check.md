# Sprint 2026.05.10 13-14 OKR Function - Side2Side Check

## 状态

- 阶段：side2side_check 已完成。
- 验收角色：Product Manager / OKR Owner。
- 验收时间：2026-05-10 13:35 CST。
- 结论：通过产品验收，可进入 final 收口。

## 用户价值和产品北极星

北极星仍是低成本 ROS2 自主垃圾投递机器人：普通手机用户把垃圾交给小车后，小车沿固定路线送达垃圾站，并留下可复盘证据。

本轮价值不是把摄像头变成默认散落垃圾 detector，而是让 route/camera 样本 manifest 能被离线检查、汇总和复盘。这样后续 diagnostics、人工标注和售后支持可以先判断样本链是否完整，而不是人工翻目录猜测缺图、缺 JSON 或缺 route/checkpoint 上下文。

## OKR 映射

- 主目标：Objective 4 感知模块产品化，从约 63% 提升到约 66%。
- 间接受益：Objective 5 手机体验与量产边界，从约 69% 小幅提升到约 70%。
- Objective 1、Objective 2、Objective 3 不因本轮抬进度。

## KR 验收

- KR4.3：通过。vision sample manifest 已具备离线检查/汇总 helper 和模块 CLI，能输出结构化 summary。
- KR4.4：通过。summary 依赖 manifest contract，不绑定具体 detector 或模型。
- KR5.4：部分推进。离线 summary 可作为远程诊断最小数据包的上游证据，但尚未接入 `/api/diagnostics` 或手机界面。

## 本轮核心抓手

- 已把样本 manifest 从“能落盘”推进到“能被离线检查和汇总”。
- 已覆盖 valid manifest、缺引用文件、空 manifest/schema 问题、缺关键字段、坏 manifest shape、route_data_recorder 风格 manifest 兼容。
- 已在 `docs/vision/perception_upgrade_evaluation.md` 写入后续 diagnostics/人工复盘使用方式。

## 做什么 / 不做什么

已做：

- 新增离线 manifest summary 能力。
- 新增 focused tests。
- 更新感知升级评估文档。
- 更新 `tech-done.md` 并补齐 OKR 收口证据。

未做且不计入本轮完成：

- 不接入手机 UI 或 `/api/diagnostics`。
- 不声明真实 camera/odom 数据集已经完成。
- 不默认启动散落垃圾 detector。
- 不修改硬件、WAVE ROVER、ESP32、Orange Pi、UART、launch 硬件参数或 vendor 文件。

## 优先级和验收口径

- P0：离线 manifest parse/check/summary 可运行，坏数据可判定。验收通过。
- P1：summary 字段可被 diagnostics/人工复盘后续消费。验收通过。
- P2：CLI 美化、手机展示和 API 接入。留给后续 sprint。

验收证据来自 `tech-done.md`：

- vision tests 13 OK。
- `py_compile` OK。
- `git diff --check` OK。
- full smoke OK：interfaces 6 / hardware 14 / nav 27 / bringup 9 / behavior 110 / vision 13。

## 责任 Engineer

- 主责：Autonomy Algorithm Engineer。
- Product Manager / OKR Owner：负责本轮验收、OKR 进度更新和收口文档。
- Full-Stack Engineer：后续 diagnostics/API 接入时介入。
- Robot Platform Engineer：后续行为层消费 summary 或 task record 对齐时介入。
- Hardware Infra Engineer：本轮不涉及硬件事实，不介入。

## 风险、阻塞和证据链缺口

- 仍缺真实上车采集 manifest，本轮只能证明离线 contract 和 fixtures。
- 仍缺真实 ROS2 camera/odom 采集后的 manifest 复盘。
- 仍缺持续标注/人工复核闭环。
- 仍缺 `/api/diagnostics` 和手机界面对 summary 的消费。
- 本轮未触碰硬件事实，因此未新增硬件风险；硬件相关判断仍必须回到 `docs/vendor/VENDOR_INDEX.md`。
