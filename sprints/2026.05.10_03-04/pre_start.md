# Sprint 2026.05.10_03-04 Pre Start

## 目标

- 开始新一轮 hourly iteration，优先推进 OKR 完成度较低且不依赖硬件的功能。
- 本轮 owner：`User Touchpoint Full-Stack Engineer`。
- 本轮聚焦：把 operator gateway 从 API/极简页面推进为手机用户可直接操作的本地控制台。

## 上轮未完成项

- Objective 5 仍缺完整手机 UI、普通用户验收和真实手机浏览器验证。
- Objective 1/3 仍缺 Docker/Humble build、WAVE ROVER HIL、真实 Nav2/摄像头路线验证。
- Objective 2 仍有 legacy server 与部分学习阶段模拟口径债务。

## 验收口径

- 手机页面必须展示普通用户流程状态、主操作按钮、异常/诊断入口和支持包摘要。
- 不要求用户理解 ROS2、SSH、串口或命令行。
- 不改硬件事实，不声明硬件验证完成。

## 风险

- 本轮在无 ROS/hardware 环境下推进浏览器入口，只能做静态/HTTP contract 和软件 smoke 验证。
- 页面仍是本地 HTTP 控制台，不是生产账号体系或原生手机 App。
