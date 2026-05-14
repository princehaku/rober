# Sprint 2026.05.14_09-10 Mobile Real Device Field Trial Package - PRD

## 1. 用户价值和产品北极星

产品北极星：普通手机用户只通过手机就能理解任务是否可启动、如何处理异常、如何把安全的诊断/验收材料交给支持人员，而不需要 SSH、ROS2、串口、日志路径或硬件知识。

本轮用户价值：为真实 iPhone/Android 或 production app 的现场试跑准备一个可复制、可脱敏、phone-safe 的 field trial package。它让现场人员按同一口径记录当前设备环境和人工观察结果，减少“截图散落、口头描述不一致、ACK 被误解成送达成功”的风险。

## 2. OKR 映射

- 直接映射：Objective 4，KR1 手机端最小流程、KR5 普通用户验收标准、KR7 手机端 UI 美观且能直接使用。
- 支撑映射：Objective 5 仅保留外部材料缺口说明，不在本轮提升。field trial package 可以为未来真实公网/4G/OSS/CDN/DB/queue 试跑材料提供入口，但本轮不证明这些外部材料。
- 不映射提升：Objective 1/2/3 不因本轮 metadata package 提升；本轮不涉及硬件协议、任务闭环或导航实跑。

## 3. KR 拆解或更新

本轮只新增 Objective 4 的软件证明抓手，不改写 OKR 原始 KR：

- KR4 远程诊断最小数据包：新增真实设备现场试跑包，包含 phone-safe viewport、touch、display-mode、service-worker/offline、client-time 和人工 observation fields。
- KR5 用户验收标准：现场人员可以复制同一份材料进入验收/复盘链路，但该材料本身不是验收通过。
- KR7 手机端 UI：field trial package 必须在主流移动 viewport 下可读、可复制、触控目标不低于 44pt，并保持 Start/Confirm/Cancel fail closed。

## 4. 本轮核心抓手

在 `mobile/web` 首屏新增“真实设备现场试跑包 / field trial package”能力：

- 自动采集当前浏览器可安全暴露的环境：viewport CSS width/height、device pixel ratio、orientation、touch capability、display-mode、manifest link presence、service worker registration/support、offline shell hint、client timestamp、entry URL summary。
- 提供人工 observation fields：device type、OS/browser、production app observed、PWA install prompt observed、user choice、offline reload observed、touch target issue、visual issue、operator note、support note。
- 生成 whitelist-only copy package，schema 使用 `trashbot.mobile_real_device_field_trial_package.v1`，boundary 使用 `software_proof_docker_mobile_real_device_field_trial_package_gate`。
- 复制包必须明确 `safe_to_control=false`，ACK/HTTP accepted/package copy 只是 accepted/processing/support metadata，不是 delivery success。

## 5. 需要做什么

### Task A Full-stack

Owner：`full-stack-software-engineer`

需要实现：

- 修改 `mobile/web/index.html`，新增 field trial package panel、人工 observation inputs 和 copy action。
- 修改 `mobile/web/app.js`，生成/派生 `mobile_real_device_field_trial_package`、`mobile_real_device_field_trial_package_summary`、`mobile_real_device_field_trial_package_copy`。
- 修改 `mobile/web/styles.css`，保持首屏密度、移动 viewport、44pt touch target 和不重叠。
- 修改 `mobile/test_mobile_web_entrypoint.py`，覆盖 package schema、safe fields、manual observation fields、敏感字段过滤、ACK 非 delivery success、primary actions fail closed。
- 修改 `mobile/README.md` 与 `docs/product/mobile_user_flow.md`，同步 field trial package 的产品边界。

### Task B Robot

Owner：`robot-software-engineer`

需要实现：

- 修改 `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py` 和 `test_remote_bridge_protocol.py`。
- 证明 `mobile_real_device_field_trial_package*` metadata-only response 不触发 collect、confirm_dropoff、cancel、ACK POST、cursor advance/persistence、terminal ACK、production readiness、HIL、dropoff/cancel completion 或 delivery success。
- 证明 mixed valid-command 场景仍只执行 `trashbot.remote.v1` command envelope，field trial package metadata 不进入 normalized command、ACK、status、cursor 或 terminal result。
- 修改 `docs/interfaces/ros_contracts.md`，明确该 metadata 只服务 phone/support/product field trial handoff。

### Task C Product closeout

Owner：`product-okr-owner`

需要实现：

- 等 Task A/B 返回后更新 `tech-done.md`、`side2side_check.md`、`final.md`。
- 若 Task A/B 验证通过，保守调整 Objective 4；Objective 5 不动。
- 更新 `OKR.md` 与 `docs/process/okr_progress_log.md`，把证据边界写为 `software_proof_docker_mobile_real_device_field_trial_package_gate`。

## 6. 优先级和验收口径

优先级：

1. P0：复制包 phone-safe whitelist 和 evidence boundary 正确。
2. P0：Start/Confirm/Cancel 不因 field trial package 启用。
3. P0：Robot metadata-only fence 通过，mixed valid command 只执行合法 command envelope。
4. P1：移动 viewport 视觉可读、触控目标不低于 44pt、文案中文优先。
5. P1：文档同步，说明本轮不是真实手机验收通过。

验收口径：

- `mobile.test_mobile_web_entrypoint` targeted tests 通过。
- `node --check mobile/web/app.js` 通过。
- Robot remote bridge/protocol targeted tests 通过。
- `py_compile` 只覆盖本轮测试文件。
- scoped `git diff --check` 只覆盖本轮改动文件。
- 文档中必须出现 `software_proof_docker_mobile_real_device_field_trial_package_gate`、`not_proven` 和 ACK 非 delivery success 边界。

## 7. 对应责任 Engineer

- `full-stack-software-engineer`：用户触点、Web/UI、mobile package、mobile docs。
- `robot-software-engineer`：ROS2 remote bridge/protocol fence、接口合同。
- `product-okr-owner`：OKR/KR 映射、阶段验收、sprint closeout。

本轮不需要 `hardware-engineer` 或 `autonomy-engineer` 修改文件，因为不触碰 WAVE ROVER、UART、Orange Pi、Nav2、fixed route、HIL 或真实硬件配置。

## 8. 风险、阻塞和证据链

风险：

- 现场人员可能把 field trial package 误解为真实设备验收通过；UI 和文档必须反复写明 package 只是 support/reproduction metadata。
- 浏览器暴露的 service worker/offline/display-mode 信息在本地 Chromium、真实 Safari、Android Chrome 和 production app webview 中可能不同；本轮只能记录观测值，不能替代真实设备验证。
- 人工 observation fields 可能被填错；package 必须保留 `not_proven` 和 `safe_to_control=false`。

阻塞：

- 无真实 iPhone/Android。
- 无 production app。
- 无真实 PWA install prompt/user choice。
- 无 Objective 5 外部材料。
- 无真实硬件/HIL。

需要补齐的证据链：

- 真实设备现场试跑截图/录屏/observations。
- production app 或真实浏览器入口 URL。
- 真实 PWA install prompt/user choice。
- 如未来回到 Objective 5，还需要公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration。

## 9. 需要创建或更新的 sprint 文档

- 当前已创建：`pre_start.md`、`prd.md`、`tech-plan.md`。
- Task A/B 完成后必须更新：`tech-done.md`。
- Product 验收后必须更新：`side2side_check.md`。
- OKR closeout 后必须更新：`final.md`、`OKR.md`、`docs/process/okr_progress_log.md`。
