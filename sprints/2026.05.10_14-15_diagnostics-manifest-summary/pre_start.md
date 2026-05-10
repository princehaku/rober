# Sprint 2026.05.10 14-15 Diagnostics Manifest Summary - Pre Start

## 状态

- 阶段：pre_start 已完成，进入 tech-plan。
- Sprint 类型：Objective 5 功能消费链迭代，承接上一轮 Objective 4 manifest checker。
- 本轮原则：功能往前走，测试只做护栏；把已有离线 checker 接到用户/售后 diagnostics，而不是继续只做离线工具。

## 用户价值

普通手机用户不需要理解 manifest、样本目录或 ROS2。远程支持查看 `/api/diagnostics` 时，应能直接知道视觉样本链是否完整、是否有缺图/缺 JSON、是否有异常/负样本，而不是只看到一个 manifest 路径。

## OKR 映射

- 主目标：Objective 5 手机体验与量产边界。
- 直接 KR：
  - KR5.4：远程诊断最小数据包包含摄像头快照/样本引用和可判定状态。
- 间接受益：
  - Objective 4：离线 manifest checker 的结果被产品诊断链消费。

## Owner

- 主责 Engineer：User Touchpoint Full-Stack Engineer。
- Autonomy Algorithm Engineer：本轮只作为 checker contract 事实来源，不改其生产代码，除非发现无法复用。
- Robot Platform Engineer：本轮不主责；如 diagnostics payload 与行为层状态冲突再介入。
- Hardware Infra Engineer：本轮不涉及硬件参数、UART、WAVE ROVER、ESP32、Orange Pi、电气或机械尺寸。

## 本轮核心抓手

让 `operator_gateway_diagnostics.summarize_vision_manifest()` 复用 `ros2_trashbot_vision.vision_sample_manifest.summarize_manifest()` 的结构化检查结果，并在 `/api/diagnostics` 的 `vision_samples` 字段中暴露可消费的 `integrity_summary`、error/warning 计数和 review queue。

## 做什么 / 不做什么

做：

- 接入已有 manifest checker，不重新手写一套路径/字段校验。
- 保持旧 diagnostics 字段兼容：`sample_count`、`event_counts`、latest sample 和 review queue 不能消失。
- 增加 focused tests 覆盖完整 manifest、缺文件 manifest、未配置/不存在 manifest。
- 更新 `tech-done.md`、`side2side_check.md`、`final.md` 和 OKR 进度。

不做：

- 不改手机页面样式或新增前端框架。
- 不启动默认散落垃圾 detector。
- 不声明真实 camera/odom 数据集已完成。
- 不改硬件/vendor、串口、launch 硬件参数。

## 风险

- `ros2_trashbot_behavior` 对 `ros2_trashbot_vision` 的 Python import 在源码树测试下可用；若 packaging 依赖不完整，本轮需在代码中保守 fallback 并在风险里记录。
- 仍没有真实采集 manifest；只能证明 diagnostics 消费 contract 和 fixture 行为。
