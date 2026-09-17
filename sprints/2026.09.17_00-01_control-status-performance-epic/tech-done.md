# 控制与状态性能交付记录

## 状态与证据范围

- sprint_type: epic
- 状态：implemented_and_verified，2026-09-18；pre_start、PRD、tech-plan 已完成。
- 第一批性能实现已交付，验收级别为 `software_mock_only`。Product 核对两个责任 owner 的最终报告与 JSON，未代替工程 owner 执行测试。
- 基线固定为 `869dfe5aaf95bcd1759583752a1a433b9ff1e83c`；最终 Robot JSON 生成时间 `2026-09-17T16:15:38Z`，最终 UI 聚合时间 `2026-09-17T16:14:13.569Z`。
- 无真实串口/相机/4G/ROS/手机 CPU/用户物理验收，未控车、未部署。未修改旧的未跟踪 AMCL/Nav2 sprint。

## 实际改动

| Owner | 实际文件 | 交付行为 |
| --- | --- | --- |
| Robot | `onboard/scripts/upper_robot_api.py`、新增 `upper_robot_io.py` | 单实例串口专用线程；非 Stop 忙时拒绝并返回 409；Stop 打断读窗和 pulse；取消/异常仍 finally 停车，旧运动不排队恢复。有效 `T=1001` 反馈早返回，显式 samples 保留完整观察；配置子进程移出事件循环，单次状态内文件读取去重。 |
| Robot | `onboard/scripts/local_webrtc_camera_smoke.py` | CPU Process 复用、预热与有效窗口区分；异常、PID 或线程变化正确重新建立基线。 |
| Robot | `remote_cloud_relay.py` 的 `MOBILE_WEB_STATIC_FILES` | 仅新增 `diagnostics.js` 静态托管。 |
| Robot | `test_upper_robot_api.py`、`test_local_webrtc_camera_smoke.py`、新增 `test_upper_robot_performance.py`、`control_status_performance_probe.py`；`ros2_trashbot_behavior/test/test_remote_cloud_relay.py` | 控制/取消/Stop/状态缓存回归、可复跑 baseline/after probe、实际本机 HTTP 静态入口验证。完整路径见 [Robot 文件记录](evidence/robot-implementation.md)。 |
| Full-stack | `pc-tools/workstation/src/App.vue`、`components/O7LiveOperatorPanel.vue`、`server/o7LiveOperatorPanel.ts`、`server/o7DirectUpperApi.ts`、`shared/contracts.ts` | Stop/Space 独立派发，旧回执不能覆盖 Stop；ACK 不等待状态回读；刷新保留视频；live/direct 摘要共享一次采样，无 TTL 或跨请求状态缓存。 |
| Full-stack | `pc-tools/workstation/test/App.test.ts`、新增 `test/controlStatusPerformance.test.ts`、`scripts/control-status-performance-probe.mjs` | PC 真实 Vue DOM + fake fetch/媒体测试及 PC/手机聚合证据。 |
| Full-stack | `mobile/web/app.js`、新增 `diagnostics.js`、`index.html`、`service-worker.js`；两套 `test_mobile_web_entrypoint.py`、新增 `test_mobile_performance.mjs` | 主路径与诊断依赖拆分，诊断按需加载；前台单飞读取、后台暂停、旧响应失效；未变状态跳过渲染，POST 在途保持动作锁。 |
| 两工程 owner | `docs/interfaces/o7_upper_robot_api.md`、`o1_upper_robot_api_base_feedback.md`、`o7_local_webrtc_camera_smoke.md`、`o7_live_operator_panel.md`、`o7_direct_upper_pc_api.md`；`docs/product/mobile_user_flow.md`、`pc_tools_workstation.md`；`mobile/README.md` | 文档与实际接口、加载方式、验证边界同步。 |

相机缓存首次或过期返回 unknown，实际完成采样后记录 `sampled_at_ms/sample_age_ms/stale/refreshing`；1 秒后允许刷新，3 秒或无样本时标 stale。CPU 预热为 `available=false/reason=warming_up`，有效样本新增窗口与单调时钟信息。PC 可选 `upper_accepted/preempted/upper_error` 保留 busy/抢占语义，控制 payload 与原有安全限制保持。

## 验证结果

最终命令及原始摘要分别见 [Robot 实施证据](evidence/robot-implementation.md)、[CPU 采样证据](evidence/robot-cpu-sampling.md)、[触点实施证据](evidence/ui-implementation.md)。

| 实际验证 | 最终结果 |
| --- | --- |
| WSL Ubuntu 24.04，`PYTHONPATH=/tmp/rober-control-performance-deps python3 -m unittest discover -s onboard/scripts -p "test_*.py"` | **108 tests OK，0 skip**，4.497s；新增性能/并发回归 13 项。 |
| `test_remote_cloud_relay.RemoteCloudRelayHttpTest` 的 shell、路由优先和 missing/traversal 三项 | **3 tests OK**；`/diagnostics.js` 本机 HTTP 200、正确 MIME/内容，API 路由和穿越防线保持。 |
| `npm.cmd test -- --run`、`npm.cmd run build`、`npm.cmd run lint`，workstation 目录 | **110/110 passed**；TypeScript/Vite/服务端构建及 lint 通过。 |
| 统一 UI collector，输出 `evidence/ui-performance.json` | **PC 7/7 + Mobile 9/9 passed**。 |
| `node --test mobile/web/test_mobile_performance.mjs` | **9/9 passed，0 skipped**。 |
| `python -m unittest mobile.test_mobile_web_entrypoint mobile.web.test_mobile_web_entrypoint` | **415 条中 405 passed、10 errors**；改前基线相同，未删除安全断言或跳过失败。 |
| 工程 owner 的 `git diff --check` | 通过；换行转换提示已与空白错误区分。 |

手机 10 个历史 errors 来自缺失的 `pc-tools/evidence/phone_browser_acceptance_gate.py` 与 `cloud_hosted_pwa_installability_gate.py`；手机历史套件尚未全绿。Windows Python 初轮另有 POSIX 假设失败及 aiohttp 缺失跳过，最终用 WSL Linux 和隔离依赖完整复验；Docker Engine pipe 不可用，不以未运行 Docker 构建充当通过证据。

## 性能证据

[Robot v2 artifact](evidence/robot-performance.json) 使用同一 fake UART/camera，直接调用 API，每组 10 次；时间单位 ms，以下各列均为 baseline → after。没有 HTTP 传输或真实网络测量。

| 指标 | p50 | p95 | p99 |
| --- | ---: | ---: | ---: |
| 有效反馈请求 | 1202.019 → 1.388 | 1202.128 → 1.590 | 1202.179 → 1.646 |
| 计划 Stop 时刻到写入 | 130.615 → 30.474 | 130.646 → 30.571 | 130.648 → 30.581 |
| 每轮最大 heartbeat 调度延迟 | 145.642 → 0.419 | 145.688 → 0.536 | 145.696 → 0.542 |
| 预热后同实例状态请求 | 150.909 → 0.510 | 151.025 → 0.715 | 151.036 → 0.729 |

Stop 场景注入 150ms 无反馈读窗，在 20ms 时计划提交 Stop；旧代码延迟了提交本身。JSON 分开保留提交迟到量与实际提交后等待，不能混用起点。10 个样本的 p99 仅描述本轮结果。

冷启动单样本保留：优化后首次状态请求 **88.029ms、CPU 59.307ms**，含 aiohttp 首次导入/session 初始化；后台首次采样等待 **150.330ms**。稳态才复用已完成样本，不能把稳态数据套到冷启动。

CPU 没有总体下降结论：反馈组累计 CPU **7.066 → 8.028ms**，Stop 组 **7.755 → 16.191ms**，相机稳态组 **7.285 → 5.519ms**。线程与抢占有额外调度成本。CPU 采样的结构性收益为 Process 创建 **10 → 1**，改后 1 次预热与 9 次有效窗口；修正了原来无差分基线却报 available/0% 的读数。

[UI 聚合 artifact](evidence/ui-performance.json) 证明：

- PC 每轮上位机状态请求 **2 → 1**，刷新媒体 unmount/close **0/0**，状态回读最大在途 **1**；慢普通动作期间 Stop 可派发，迟到动作不覆盖 Stop。
- 手机首屏未压缩 JS 源码 **3,931,297 → 253,304 bytes**，诊断 **3,682,451 bytes** 按需加载。总源码未减少，收益是首屏加载及默认执行量降低。
- 改前 215 次 render 为源码计数，`baseline_observed=false`；改后默认 14 个核心渲染、重面板 **0**、诊断请求 **0**。两次相同状态读取不重绘，变化状态渲染一次。
- 重开诊断脚本仅加载一次；状态最大并发 **1**、后台请求 **0**、返回前台立即刷新；POST 期间变化状态不能解锁动作。

## 偏差、修复与反思

- 最终入口已同步 tech-plan：准确白名单名、`.mjs` 手机测试、PC `test/` 范围、固定基线 SHA 与独立/汇总 artifact 路径。轮询留在 app.js，没有新增 state-poll.js。
- 诊断真实 DOM 展开暴露旧 `normalizeList` 未定义，已修复并重跑；PC 平台可选依赖、类型和 lint 错误经锁定依赖恢复后复验。串口新增部分 samples 被抢占回归后，最终计数从 107 更新为 108，并重跑性能 artifact。
- Robot 已核对触点 409/preempted/camera unknown 契约，懒加载文件已有实际 HTTP 覆盖。工程报告声明未新增 TODO、未覆盖无关改动；新增/修改技术注释均中文，保守计数各实现/测试比例 **20.1%–22.2%**，迁移历史诊断代码未做无关重写。
- 模块迁移和并发安全增加了少量代码与调度成本；本轮交付以关键等待与默认执行量为依据，不宣称净代码量或整体 CPU 已下降。

## 剩余风险

单实例仲裁覆盖不到其他 UART 进程；驱动异常、进程强制终止和硬件看门狗未验收。50ms 读片/200ms 写 timeout 为软件配置，物理停车仍待 HIL。手机详情仍大，发布需同步 core/diagnostics/HTML/service worker；真实压缩传输、手机 CPU/RSS、相机编码与 4G 端到端时延均待测。历史手机缺文件错误保留为技术债。算法、remote bridge 退避、DB/写盘优化留后续，不影响本轮限定软件交付。
