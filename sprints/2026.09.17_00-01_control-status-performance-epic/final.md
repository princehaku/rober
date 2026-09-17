# 首批控制与状态性能优化收口

## 结论

- 状态：completed_software_scope，2026-09-18；tech-done 与 side2side_check 已完成。
- 第一批已交付：CPU 采样、异步串口仲裁/Stop、安全取消、相机缓存、PC 去重与媒体保活、手机诊断懒加载与轻量刷新。
- 证据边界：`software_mock_only`；用户物理验收未做，无真实串口/相机/4G/ROS/手机 CPU/HIL，无控车或部署。
- 方向判断：**继续**北极星；完成 CEO 本轮指定性能工作，保留 O10 导航与受控送达主线验收要求。

## 结果与代价

[最终 Robot probe](evidence/robot-performance.json) 在固定基线 `869dfe5aaf95bcd1759583752a1a433b9ff1e83c` 与最终代码上使用同一 fake 条件，每组 10 次、直接 API 调用。p50：有效反馈 **1202.019→1.388ms**，计划 Stop→写入 **130.615→30.474ms**，每轮最大事件循环延迟 **145.642→0.419ms**，预热状态 **150.909→0.510ms**。p95/p99、原始样本与方法均在 [tech-done](tech-done.md) 和 artifact 中，不能外推生产端到端尾延迟。

CPU 采样对象创建 **10→1**，差分窗口有效；总体 CPU 改善未证明。Stop 组累计 CPU **7.755→16.191ms**，新增线程/抢占有成本。首次状态请求 **88.029ms/CPU 59.307ms**、后台采样预热 **150.330ms** 均保留，未用稳态替代冷启动。

[UI artifact](evidence/ui-performance.json)：PC 状态读取 **2→1**，刷新媒体卸载/关闭 **0**；手机首屏脚本 **3,931,297→253,304B**，**3,682,451B** 诊断按需加载。默认重面板执行 **0**、核心 **14**，未变状态不重绘，轮询最大并发 **1**、后台请求 **0**。这是首屏加载与执行量减少，总代码量未减少；手机改前动态 baseline 未测量。

验证：Robot **108 tests**、静态托管 **3 tests**，PC **110 tests/build/lint**、UI collector **7 PC + 9 Mobile** 均通过。手机旧套件 **415 条中 405通过、10 errors**，与基线一致，源于两个缺失的历史 gate 文件；没有全套全绿结论。

## KR 软件阶段归档

| KR | Owner | 用户价值与完成证据 | 历史位置及剩余风险 |
| --- | --- | --- | --- |
| KR-O7-Control-Responsiveness-Software | Robot + Full-stack | Stop 优先、取消仍停车、旧动作不恢复；并发回归与 Robot/UI artifact | 本 sprint tech-done/side2side_check；真实 UART 竞争、物理停止、看门狗仍待验收。 |
| KR-O7-CPU-Sampling-Baseline | Robot | 预热与差分窗口可信，CPU 对象复用 | robot-cpu-sampling.md、robot-performance.json；真实板端 CPU 仍待测。 |
| KR-O7-Status-Refresh-Cost | Robot + Full-stack | 相机后台缓存、PC 一次状态采样与媒体保活 | Robot/UI artifact；冷启动与真实视频会话、网络性能待测。 |
| KR-O7-Mobile-Primary-Path-Cost | Full-stack | 默认轻量路径、诊断按需、轮询不重叠并守住动作锁 | ui-implementation.md/ui-performance.json；真机 CPU/RSS、压缩传输、历史缺文件错误仍待处理。 |

以上四项从本 sprint 候选进入**软件阶段完成历史**，不作为新增产品能力完成率。`OKR.md` 仅补事实和历史条目，所有百分比保持：O1 约95.5%、O2约72%、O3约77%、O5约84%、O6约82%、O7约94%、O8约51%、O9约22%、O10约12%。

## 最低 Objective 与阻塞复核

最低 Objective 仍为 **O10，约12%**。本轮优先 O7 控制与触点质量的理由仍成立：CEO 明确授权性能首批；本地软件工作可独立交付，无须再消费前两轮 Nav2/runtime、真实图片或现场 HIL 阻塞。此次性能证据不替代 O10 新链式实机材料，不上调任何产品 Objective。

## 遗留与下一步

- Robot：在真实部署保证 UART 独占，测按键到真实写入/物理停止、长时间 CPU/RSS、冷启动、掉线与看门狗。50ms 读片/200ms 写 timeout 仅为调度配置。
- Full-stack：真机测首屏、持续轮询 CPU、视频保活与4G；发布需同步 core、diagnostics、HTML、service worker；重诊断仍可继续按用户价值精简。
- 手机两个缺失的历史 gate 的 10 个错误单列测试资产技术债，避免在性能改动中重建范围外工具。
- 算法视觉按需、路线转换等待、重复写盘、remote bridge 退避、DB 等尚未实施；按部署启用情况与性能采样选择后续范围。

本轮无新增未处理 TODO、无范围外回滚、无硬件配置变化。工程 owner 已完成失败定位与复验；Product 完成阶段验收与历史归档，不提交 Git。部署与物理验收尚未执行。
