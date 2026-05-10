# Sprint 2026.05.10 14-15 Diagnostics Manifest Summary - Side2Side Check

## 状态

- 阶段：side2side_check 已完成。
- 验收角色：Product Manager / OKR Owner。
- 验收时间：2026-05-10 14:35 CST。
- 结论：通过产品验收，可进入 final 收口。

## 用户价值验收

本轮把上一轮离线 manifest checker 从工程工具推进到用户/售后诊断链。远程支持读取 `/api/diagnostics` 时，不再只能看到 manifest 路径、最新样本和 review queue；现在可以直接看到视觉样本链健康度、缺失文件引用、error/warning、上下文字段覆盖和文件引用计数。

这符合手机用户北极星：普通用户不用懂 ROS2 或样本目录，支持人员也能从诊断包快速判断“这次任务有没有可信的视觉证据链”。

## OKR 映射

- Objective 5：从约 70% 提升到约 72%。
  - 原因：远程诊断最小数据包现在真正消费 vision checker summary。
- Objective 4：从约 66% 小幅提升到约 67%。
  - 原因：感知样本 contract 不只可离线检查，也进入 diagnostics 消费链。
- Objective 1、Objective 2、Objective 3：本轮不抬进度。

## KR 验收

- KR5.4：通过。`/api/diagnostics.vision_samples` 增加 `integrity_summary`、error/warning 计数、缺失文件引用、context coverage 和 file counts。
- KR4.3：继续有效。离线 checker 输出被复用，没有在 behavior 侧重写另一套 manifest 校验。
- KR4.4：通过。diagnostics 依赖 manifest contract 和 checker summary，不绑定具体 detector 模型。

## 做什么 / 不做什么

已做：

- 接入 `ros2_trashbot_vision.vision_sample_manifest.summarize_manifest()`。
- 保持旧 diagnostics 字段兼容。
- 增加 import/checker 失败时的结构化降级。
- 更新 diagnostics contract 文档和目标测试。

未做且不计入本轮完成：

- 未新增手机 UI 展示。
- 未产生真实 camera/odom manifest。
- 未默认启动散落垃圾 detector。
- 未修改硬件、WAVE ROVER、ESP32、Orange Pi、UART、launch 硬件参数或 vendor 文件。

## 验收证据

来自 `tech-done.md`：

- behavior diagnostics 目标测试 8 OK。
- vision manifest 目标测试 5 OK。
- `operator_gateway_diagnostics.py` `py_compile` OK。
- `git diff --check` OK。
- full smoke OK：interfaces 6 / hardware 14 / nav 27 / bringup 9 / behavior 111 / vision 13。

## 剩余风险

- 仍缺真实上车采集 manifest；当前验证是 diagnostics/API contract 和 fixtures。
- 真实手机页面尚未消费新增字段。
- 下一步应把 `integrity_summary.status` 映射成手机端可读的诊断灯和恢复建议。
