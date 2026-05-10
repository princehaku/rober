# Sprint 2026.05.10 14-15 Diagnostics Manifest Summary - PRD

## 状态

- 阶段：PRD 已完成，进入 tech-plan。
- 产品目标：把 vision manifest 离线检查能力接入 `/api/diagnostics`，让远程支持和后续手机端能直接判断视觉样本链是否可信。

## 背景

上一轮 Objective 4 已经提供 `vision_sample_manifest.py` 离线 checker，可以检查 manifest shape、文件引用、上下文覆盖、异常/负样本和 error/warning。但它还停留在工程工具层，`/api/diagnostics` 仍主要暴露 manifest 路径、latest sample 和 review queue，无法直接告诉手机/远程支持“证据链是否完整”。

## 用户价值

普通用户只用手机，不会翻 ROS2 目录、manifest JSON 或样本文件夹。远程支持拿到 diagnostics 包时，应能快速判断：

- manifest 是否可读。
- raw image / annotated image / JSON 是否缺失。
- route/task/checkpoint/anomaly 上下文是否覆盖。
- 样本链健康度是 `ok`、`warning` 还是 `error`。

这样失败复盘可以先看诊断结论，再决定是否需要重新采集、补图或人工复核。

## OKR 映射

- 主目标：Objective 5 手机体验与量产边界。
  - KR5.4：远程诊断最小数据包包含摄像头快照/样本引用和可判定状态。
- 间接受益：Objective 4 感知模块产品化。
  - KR4.3：manifest contract 不只可离线检查，也能被 diagnostics 消费。
  - KR4.4：消费 manifest contract，不耦合具体 detector 或模型。

## 本轮范围

必须做：

- `/api/diagnostics.vision_samples` 保持旧字段兼容。
- 复用 `ros2_trashbot_vision.vision_sample_manifest.summarize_manifest()`，不要在 behavior 侧重写另一套 checker。
- 新增结构化完整性字段：健康状态、error/warning、缺失文件引用、file counts、context coverage。
- 如果 manifest 未配置、checker 不可 import 或 checker 报错，diagnostics 仍返回结构化降级字段。
- 更新目标测试、接口文档和 sprint `tech-done.md`。

不做：

- 不新增手机 UI。
- 不训练或启用 detector。
- 不声明真实 camera/odom manifest 已完成。
- 不改硬件、vendor、串口、WAVE ROVER、Orange Pi、ESP32 或 launch 硬件参数。

## 验收口径

- 目标测试覆盖完整 manifest、缺文件 manifest、未配置/不存在/corrupt manifest。
- `vision_samples` 旧字段不消失，新字段稳定可消费。
- `git diff --check` 通过。
- 能运行 full smoke 时必须运行；无法运行则写清风险。

## 责任 Engineer

- 主责：User Touchpoint Full-Stack Engineer。
- Autonomy Algorithm Engineer：提供 checker contract 事实来源，本轮不主责。
- Product Manager / OKR Owner：负责验收、OKR 快照和 sprint 收口。

## 风险

- 本轮只能证明 API/fixture contract，不能替代真实上车 camera/odom manifest。
- 新字段还未在真实手机页面展示；后续需要把 `integrity_summary.status` 转成用户可理解的诊断灯和恢复建议。
