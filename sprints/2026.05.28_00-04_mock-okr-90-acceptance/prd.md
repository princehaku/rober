# Mock OKR 90 Acceptance PRD

## 用户价值和北极星

北极星仍是：把 `rober` 做成普通手机用户可用的低成本 ROS2 自主垃圾投递机器人。

本轮用户价值不是证明真实世界已经完成，而是在真实硬件、真实公网、真实 4G、production DB、OSS/CDN 和真实手机/browser 仍缺席时，先把 O1/O5/O6/O7 的软件链路用 mock evidence 做到可复验、可重复、可交给后续真实材料替换。这样工程队不会停在“等真实材料”，同时 CEO 可以看到每个 Objective 距离真实上线还差哪些材料。

## 需求背景

CEO 新口径要求：`继续完成迭代 所有的okr必须完成到90%以上 允许用mock数据替代真实效果`。

因此本轮验收不再要求 O1/O5/O6/O7 全部具备真实材料后才能达到 90%+。新的完成度判断是：

- 当 mock 数据覆盖 KR 主路径、失败路径、状态标记、回放或 smoke 验证，并且证据可复验时，可以计入 `mock/software completion`。
- 当缺少真实硬件、真实公网、真实 4G、production DB/queue、OSS/CDN live traffic 或真实手机/browser 时，必须继续标为 `real material not_proven`。

## OKR 映射和方向判断

方向判断：继续推进当前 O1/O5/O6/O7，但临时把本轮进度表述限定为 `mock/software completion 90%+`。

| Objective | 当前状态 | 本轮目标 | 不能声称 |
| --- | --- | --- | --- |
| Objective 1 | ~83% | 90%+ mock/software completion | 真实 WAVE ROVER、真实 UART/HIL、真实 IMU/battery/odom 标定已完成 |
| Objective 5 | ~80% | 90%+ mock/software completion | 真实公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、OSS/CDN live traffic、真实手机/browser 已完成 |
| Objective 6 | ~62% software proof | 90%+ mock/software completion | 真实安全隧道、production DB/queue、真实 OSS upload、真实模型 runtime、live O6 API 已完成 |
| Objective 7 | ~48% software proof | 90%+ mock/software completion | 真实 RTC/视频、真实 ASR/TTS、真实手控/寻路、真实地图/电梯数据流、真实 browser/手机验收已完成 |

## 验收口径

### Objective 1 90%+ mock/software completion

必须提供：

- mock serial 或 virtual HIL input 覆盖 WAVE ROVER newline-delimited JSON 编码、坏帧容错、`T=1` wheel command、反馈解析、IMU/battery 发布路径。
- 明确 vendor 来源引用来自 `docs/vendor/VENDOR_INDEX.md` 指向资料；真实集成阶段仍需重新查阅 vendor 文件。
- 证据里必须出现 `software proof`、`not_proven_real_wave_rover` 或等价边界字段。
- 不允许把 mock serial 说成真实 UART 或真实 WAVE ROVER feedback。

### Objective 5 90%+ mock/software completion

必须提供：

- `trashbot.remote.v1` commands/status/ack 业务 contract 的 mock/cloud-local smoke。
- mock 4G interruption、mock production DB/queue、mock OSS/CDN failure graceful degradation 证据。
- bearer/env credential 边界，不把 `.env` 或真实凭证写入仓库。
- 证据里必须保留真实公网、真实 4G、production DB/queue、OSS/CDN live traffic、真实手机/browser 的 `not_proven` 边界。

### Objective 6 90%+ mock/software completion

必须提供：

- O6 archive task/event/annotation/inference/query 的端到端 mock evidence。
- 机器人侧 event publisher、algorithm feed、cloud archive API 至少形成一个可复验 bundle 或 smoke。
- `o6_cloud_archive_state.json` 或同类 runtime state 不落仓库根目录；验证必须覆盖默认路径、环境变量路径或临时目录路径。
- production DB/queue、真实 OSS upload、真实推理 runtime、live API 继续 `not_proven`。

### Objective 7 90%+ mock/software completion

必须提供：

- PC 端六区能力的 mock/live-like evidence：实时地图、机器人位置、电梯状态、历史路线回放、数据标注、推理摘要、ASR/TTS stub、手控/寻路 stub。
- 安全字段必须 fail-closed：如 `safe_to_control=false`、`robot_control_executed=false`，除非只在 mock sandbox 中证明指令 contract。
- 真实 RTC/视频、真实 ASR/TTS、真实手控/Nav2、真实地图/电梯数据流、真实 browser/手机验收继续 `not_proven`。

## Task 分工

### Task A - O1 Mock Hardware Evidence

Owner：`robot-software-engineer` 主责，`rober-hardware-engineer` 做 vendor/boundary 复核。

交付：

- O1 mock serial/HIL packet evidence runner 或测试增强。
- 文档说明 mock 与真实 WAVE ROVER 的边界。
- 验证输出包含 Objective 1、90、software proof、not_proven。

### Task B - O5 Mock Cloud Control Evidence

Owner：`full-stack-software-engineer`。

交付：

- O5 commands/status/ack mock production-like smoke。
- mock 4G/DB/queue/OSS/CDN failure degradation evidence。
- 验证输出包含 Objective 5、90、software proof、not_proven。

### Task C - O6 Mock Archive 90 Evidence and Runtime State Fence

Owner：`full-stack-software-engineer` 主责，`robot-software-engineer` 只处理 onboard publisher 接口事实。

交付：

- O6 archive/annotation/inference/query end-to-end mock smoke。
- 明确 `o6_cloud_archive_state.json` 不落仓库根目录的测试或 smoke。
- 验证输出包含 Objective 6、90、software proof、not_proven、`o6_cloud_archive_state`。

### Task D - O7 Mock Operations Console 90 Evidence

Owner：`full-stack-software-engineer` 主责，`robot-algorithm-engineer` 提供 O6/O7 mock archive feed。

交付：

- O7 六区 mock/live-like console evidence。
- PC adapter 或 UI contract 对 mock O6 API/bundle 的测试。
- 验证输出包含 Objective 7、90、software proof、not_proven。

### Task E - Product Acceptance and OKR Closeout

Owner：`product-okr-owner`。

交付：

- `tech-done.md`、`side2side_check.md`、`final.md` 和必要的 `OKR.md` / progress log 更新。
- 将完成度表述为 `mock/software completion`，真实材料仍保留 `not_proven`。

## 风险边界

- 本轮可以把 O1/O5/O6/O7 推到 90%+ mock/software completion，但不能证明真实生产效果。
- 若工程证据只覆盖 happy path，不覆盖失败路径和边界字段，不得判 90%+。
- 若 runtime state 继续落仓库根目录，O6 不能判 90%+，必须先修复路径或 `.gitignore`/运行参数边界。
- 若 PC 或 cloud 测试需要真实浏览器、真实公网或真实手机才能运行，则本轮应改用 mock/browser-like 或 API-level smoke，不阻塞软件证明。
