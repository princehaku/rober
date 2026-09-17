# 需求与工程结果对照

## 验收状态

- 状态：accepted_with_documented_limits，2026-09-18；前置 tech-done 已记录最终工程结果。
- 验收人：Product / OKR Owner，基于 Robot 与 Full-stack 冻结的实施报告、测试摘要及 JSON。
- 证据类型：`software_mock_only`；用户物理验收 `not_performed`。以下通过仅限本轮软件范围。

| 需求 | 实际证据 | 结论 |
| --- | --- | --- |
| Stop 不受普通反馈等待阻塞，取消与异常仍停车 | 13 项并发回归；专用串口 owner、busy 拒绝、finally 停车、Stop 后无旧运动；直接 API fake 探针计划 Stop→写入 p50 130.615→30.474ms | 软件通过；物理停止未测。 |
| 修正 CPU 测量 | 对象创建 10→1，1 次预热与 9 次有效窗口，恢复/线程/PID/争用测试通过 | 测量正确性通过；无整体 CPU 降幅结论。 |
| 总状态不等待相机网络采样 | 冷态 unknown，后台单飞，缓存带真实采样时间和 stale；稳态 p50 150.909→0.510ms | 软件通过；冷首请求 88.029ms 仍保留。 |
| PC 状态去重与视频保活 | 改前实际 fake fetch 两次 status，改后一次；媒体 unmount/close 各 0；旧回执不覆盖 Stop | DOM/mock 通过；真实 WebRTC 未测。 |
| 手机默认轻量、诊断可展开 | 首屏源码 253,304B，重面板执行 0、核心 14；诊断只加载一次，无未捕获异常 | 软件通过；总代码量未减少。 |
| 状态自动刷新守住安全语义 | 最大并发 1、后台 0、前台立即更新；状态未变不重绘，POST 在途不解锁、旧 GET 失效 | 9 项动态测试通过；真实手机/4G 未测。 |
| 拆分后静态托管可用 | Robot 3 项实际本机 HTTP 测试含 diagnostics.js 200/MIME/内容、路由及穿越防线 | 本机托管通过；尚未部署。 |
| 原有回归与构建 | Robot 108 tests、PC 110 tests/build/lint、UI collector 7+9通过；手机历史415中405通过/10既存缺文件错误 | 本轮回归通过；历史全套非全绿。 |

## 证据核对

- [Robot 最终实施](evidence/robot-implementation.md)、[CPU 实施](evidence/robot-cpu-sampling.md)、[Robot v2 JSON](evidence/robot-performance.json)；最终 probe 在最终代码上重跑，owner 核对源码和 probe 的归一化文本 hash 一致。
- [触点最终实施](evidence/ui-implementation.md)、[PC 实施](evidence/ui-pc-implementation.md)、[UI 聚合](evidence/ui-performance.json)。手机 `baseline_observed=false`，改前 render 只作源码结构计数。
- 测试取消、异常、抢占、相机过期和错误回读均有独立覆盖；软件 ACK、HTTP 200、cache fresh 不提升 `safe_to_control` 或 delivery success。
- 改动文档与职责范围一致；旧未跟踪 sprint 保持不动。未把环境首次失败、跳过或缺失历史工具写成通过。

## 产品决定与验收缺口

第一批软件性能优化验收通过，保留历史测试错误与实机性能缺口。交付价值是控制请求更及时、默认页面计算和重复请求更少、CPU 读数可信。当前证据不足以认定生产端到端或总体 CPU 已达标；冷启动及 Stop CPU 增量需要真实负载复核。

硬件 UART 独占、看门狗、真实手机/4G/相机/ROS/HIL 留后续现场验收。算法、remote bridge、DB 和高频写盘尚未实施，保持独立待办。本轮不以既有硬件阻塞收口，不消耗新的重复 blocker 轮次。
