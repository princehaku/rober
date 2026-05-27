# Mock OKR 90 Acceptance Pre Start

## sprint_type

sprint_type: epic

## CEO 新口径

CEO 本轮口径：`继续完成迭代 所有的okr必须完成到90%以上 允许用mock数据替代真实效果`。

本 sprint 因此把 OKR 判断拆成两层：

- `mock/software completion`：允许使用 mock 数据、本地 stub、Docker、本地 bundle、离线 feed、虚拟状态文件和 fail-closed UI 证据替代真实效果，只要证据可复验、schema 稳定、风险边界写清楚，即可用于 O1/O5/O6/O7 达到 90%+。
- `real material completion`：真实 WAVE ROVER、真实 UART/HIL、真实公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、OSS/CDN live traffic、真实手机/browser、真实 RTC/ASR/TTS、真实手控/Nav2 仍保持 `not_proven`，不得被 mock 证据冒充。

## 上轮事实

来源：

- `OKR.md`
- `sprints/2026.05.27_46-50_okr-90-software-acceleration/tech-done.md`
- `sprints/2026.05.27_46-50_okr-90-software-acceleration/final.md`

上轮结论：

- Objective 1：约 83%。已有 O1 90% evidence boundary，但缺真实 WAVE ROVER 上车、UART、HIL、PR #5 2D LiDAR/ToF 硬件材料。
- Objective 5：约 80%。已有 O5 90% real material boundary，但缺真实公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、OSS/CDN live traffic、真实手机/browser。
- Objective 6：约 62% software proof。已有 O6 archive core、board event publisher、algorithm evidence feed、annotation/inference/query contract 和 `evidence_ref` 边界。
- Objective 7：约 48% software proof。已有 PC workstation 消费 O6 `trashbot.archive.v1` 本地 bundle，并展示回放、标注、推理摘要和六区 fail-closed 状态。

## 本轮目标

本 sprint 目标是在 CEO 新口径下补齐可复验 mock evidence，使：

- Objective 1 达到 90%+ `mock/software completion`：硬件协议链路用 mock serial/HIL packet/ROS topic 对照证明软件准入，真实硬件仍 `not_proven`。
- Objective 5 达到 90%+ `mock/software completion`：云中转控制面用本地 HTTPS-like contract、mock 4G interruption、mock production DB/queue、mock OSS/CDN evidence 和 browser/API smoke 证明业务链路，真实公网/4G/live traffic 仍 `not_proven`。
- Objective 6 达到 90%+ `mock/software completion`：O6 archive、query、annotation、inference、state path 和 runtime evidence 形成单命令可复验闭环，production DB/OSS/live API 仍 `not_proven`。
- Objective 7 达到 90%+ `mock/software completion`：PC 端以 mock/live-like O6 bearer API、本地 RTC/ASR/TTS/手控/寻路 stub、回放和标注提交 smoke 覆盖六区，真实设备和真实 browser/手机仍 `not_proven`。

## 非目标

- 不把 mock 数据解释为真实 WAVE ROVER、真实 4G、真实云端生产环境或真实用户设备验收。
- 不要求本轮采集真实串口、真实电梯、真实路线、真实公网 HTTPS/TLS、真实 OSS/CDN live traffic。
- 不把 `o6_cloud_archive_state.json` 或类似 runtime state 放到仓库根目录；工程验证必须证明 runtime state 可通过环境变量、临时目录或 ignored runtime 目录隔离。
- 不修改当前 `OKR.md`，收口时由 Product Owner 在后续 acceptance/closeout 阶段再根据工程证据判断是否更新。

## Blocker 复用检查

上一轮 final 的主要结论不是 blocked，而是 O1/O5 缺真实材料、O6/O7 仍处 software proof 阶段。本轮 CEO 明确允许 mock 替代真实效果用于 OKR software/mock completion，因此本轮不是继续消费同一真实材料 blocker，而是切换验收口径并要求工程产出可复验 mock evidence。

## Owner

- Product Owner：`product-okr-owner`，负责本轮 PRD、tech-plan、后续验收口径和 closeout 判断。
- Robot Software Engineer：负责 O1 mock serial/HIL/ROS topic evidence，以及 O6 board/runtime state path 集成边界。
- Hardware Infra Engineer：负责 O1 hardware mock/HIL boundary 和 vendor 来源复核，确保 mock 不冒充真实 WAVE ROVER。
- User Touchpoint Full-Stack Engineer：负责 O5/O6/O7 cloud、PC、API、browser-like mock evidence 和 runtime state 不落根目录验证。
- Robot Algorithm Engineer：负责 O6/O7 offline route/elevator/perception feed 升级为可复验 90% mock evidence。

## 进入实现条件

- `prd.md` 写清用户价值、OKR 映射和 90%+ mock/software 完成判定。
- `tech-plan.md` 写清 Task 分工、允许文件范围、验收命令、风险边界和 OKR 最低优先级核对。
- 工程实现必须由对应一线 Engineer 执行；Product Owner 不改产品代码。
