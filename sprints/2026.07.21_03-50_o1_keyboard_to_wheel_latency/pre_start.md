# O1 Keyboard-to-Wheel Latency - Pre Start

## Sprint metadata

- `sprint_type: epic`
- 启动时间：`2026-07-21 03:50 CST`
- 状态：`planning_complete_pending_engineer_dispatch`
- Product owner：`product-okr-owner`
- 主责/集成 owner：`full-stack-software-engineer`（Full-Stack）
- 并行事实与条件式现场测量 owner：`rober-hardware-engineer`（Hardware）
- 目标 Objective：O1，兼顾 O7 用户触点体验
- planning proof boundary：`planning_only_plus_preexisting_consumed_first_jog_not_latency_measurement`

## 用户原话与用户价值

用户要求：`优化按键按下到轮子动的延迟，现在很明显，要尽可能短。`

用户价值不是让 HTTP 更快返回，而是按下 W/A/S/D 或方向键后，轮子尽快开始产生可观察运动，同时松键、窗口失焦、页面隐藏、停止按钮和 watchdog 仍能可靠停车。产品北极星是“手感立即响应且失控边界不退化”：优化必须覆盖从浏览器 `keydown` 到物理轮子 onset 的整条链路，不能只优化某一段日志或把 response time 当成运动时间。

## 当前真实控制链路

本轮基线链路固定为：

`PC Vue keydown -> Node POST /api/robot-control/base/manual -> upper POST /api/base/manual -> 进程内 /cmd_vel burst -> esp32_bridge callback -> 当前配置 transport write -> WAVE ROVER firmware -> wheel onset`

- Vue 当前在首次 `keydown` 直接进入 `sendKeyboardManualPulse()`，长按后续 pulse 按上一次回包自调度。
- PC Node 只转发固定 `/api/base/manual`，限速、限时并保留 `realtime_hold`、session、sequence 和 watchdog。
- Upper 的低延迟主路径是复用进程内 `rclpy` publisher；当前首次初始化/DDS subscription wait、burst 发送及回包聚合都可能贡献可感延迟或后续脉冲空档。
- `esp32_bridge` 在 `/cmd_vel` callback 内构造 vendor command；现场当前默认使用 ESP32 HTTP `/js` 规避 UART TX 断点，禁止未经 HIL 擅自切回 serial。若配置为 serial，才按 vendor UTF-8 newline JSON 写入 UART。
- vendor source 明确 `ugv_rpi/base_ctrl.py` 以 `json.dumps(data) + '\n'` 写 UART；`uart_ctrl.h` 按完整换行 JSON 解析；`json_cmd.h` 定义 `T=1`、`T=11`、`T=13`；`movtion_module.h` 最终进入左右电机控制。

硬件事实必须引用以下本地来源，不凭记忆外推：

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`

Orange Pi 的 UART 设备必须读取当前 runtime 配置，不得照抄 vendor Raspberry Pi 默认路径。

## 已有 first-jog 与授权消费边界

前序 micro sprint `sprints/2026.07.21_01-54_o1_minimal_wheel_jog/` 已经完成一次真实 first-jog：

- 其 `artifacts/hardware/frozen_authorization_identity.json`：authorization `ceo_20260721_0154_minimal_wheel_jog_v6`，只允许 exactly-one forward nonzero，`0.08m/s`、`300ms`、`command_mode=ros`，并禁止 direct UART、direct `/cmd_vel` 与 Nav2。
- 其 `artifacts/hardware/first_jog_proxy_response.json`：PC proxy `command_forwarded`、HTTP `200`，command raw nonzero 与 IMU delta 已观察到，但 `wheel_feedback_lr_nonzero_proven=false`。
- 上述 one-shot authorization 已消费。不得再用它发送任何 nonzero 请求，也不得把现有 artifact 当 latency baseline：其中没有 browser keydown、PC receive/forward、upper receive、`/cmd_vel` publish、bridge callback/write 和 wheel onset 的可关联时间戳。

后续实现、回归和阈值验收先走 software/mock、fake clock、loopback HTTP、fake publisher/fake serial。若要做新的物理 latency 测量，必须另获 fresh bounded authorization，明确 operator、路线清空、速度、单次时长、样本次数、间隔、预/后 stop 和中止条件。用户本句是性能目标，不是无限制真实运动授权。

## OKR、优先级与不重复消费

- `OKR.md` 当前 O5 约 `85%` 最低，但 provider/runtime blocker 已消费 `2/2` 并暂停；本轮不重开 O5 wrapper。
- O6/O7 各约 `93%`，O1 约 `94%`。本轮直接提升 O1 人工底盘控制体验，并由 O7 用户触点承载 keydown 与诊断展示；planning 阶段不调整百分比，KR `不归档`。
- 最近两轮 route closeout 的 blocker 是 Nav2 readiness、transport/运行条件。本 sprint 是新的 human-control latency lane，不重开 Nav2 readiness、deadline、transport 或 route wrapper，也不把 latency trace 包装成 route/delivery/HIL 证明。

## 核心抓手与责任边界

1. Full-Stack 主责单线集成浏览器、PC Node、Upper 和 bridge trace contract：先量各段，再移除 hot path 中可避免的串行等待、冷启动和同步证据聚合；不新增浏览器直连机器人或裸 `/cmd_vel` 入口。
2. Hardware 与 Full-Stack 并行，但只做 vendor 事实确认、独立 fake-serial/latency probe、已有 artifact 只读核对；只有 fresh bounded authorization 到位后才可执行现场 wheel-onset 测量。
3. 接口耦合强，Hardware 不修改 Vue、workstation Node、`upper_robot_api.py`、其测试或 Full-Stack 集成文件；不得并行双写共享文件。
4. 当前工作区的 `onboard/scripts/upper_robot_api.py` 与 `onboard/tests/test_upper_robot_api.py` 已有另一 Nav2 sprint 的未提交改动。若 latency 实现必须触碰，Full-Stack 必须保留并兼容现有 hunks，禁止覆盖、回滚、整文件格式化或用 checkout/reset 清理；优先等现 owner 冻结/提交后再进入共享文件。

## 验收分层

验收至少分为三层，且每层都保留 raw sample、p50、p95、max、样本数和异常原因：

- software/mock：浏览器 keydown、PC proxy receive/forward、upper receive、首帧 `/cmd_vel` publish、bridge callback、fake HTTP/serial transport write 全链路可关联；warm-path `keydown -> fake transport write` p95 目标 `<=60ms`、max `<=100ms`，单段不得出现未声明的 `>=50ms` 同步等待。
- live command-path（无物理 onset 结论）：在 future fresh authorization 下验证真实 PC/upper/bridge timestamps 与 UART write，不能把它叫 wheel-motion latency。
- live physical：用外部高帧率视频/光学/编码器或可信同窗口反馈标定 wheel onset；目标 `keydown -> first wheel motion` p50 `<=100ms`、p95 `<=150ms`、max `<=200ms`，并相对首轮有效 baseline 至少降低 `30%`。如果无法获得可信 wheel onset，只能写 `physical_latency_not_measured`。

阈值是本轮产品目标，不是现状声明；正式 live 样本数及每次运动上限必须由新的 authorization 冻结。

## 安全与证据边界

- 必须保留 keyup、all-keys-released、pointer end/cancel、window blur、page hidden、stop button、upper watchdog 与 bridge/firmware stop 兜底。
- 优化不得延后 stop、放大速度/持续时间、关闭 watchdog、绕过 safety confirmation，或用“先动后校验”换取数字。
- HTTP response latency、command accepted、publisher return、serial write return、T1001 IMU delta 和肉眼主观感觉均不是同一个指标；每项单独命名。
- software/mock 结果不证明真实 UART、物理轮子、HIL、`safe_to_control`、route execution 或 delivery success。

## Sprint 留档顺序

本 Epic 当前只创建 `pre_start.md -> prd.md -> tech-plan.md`。Engineer 实现后才创建 `tech-done.md`，Product 验收后再创建 `side2side_check.md`、`final.md` 并决定是否更新 `OKR.md` 与相关 `docs/`。本 planning 不创建后续三文档、不发送 live/control、不修改产品代码或其他 sprint。
