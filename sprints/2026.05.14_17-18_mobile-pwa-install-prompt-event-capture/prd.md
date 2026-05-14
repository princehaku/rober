# Sprint 2026.05.14_17-18 Mobile PWA Install Prompt Event Capture - PRD

sprint_type: epic

## 用户价值和产品北极星

手机端是普通用户和现场验收人员唯一应接触的操作入口。当前 `mobile/web` 已有 `mobile_pwa_install_prompt_evidence*` 面板和 `mobile_real_device_field_trial_acceptance_session*` 会话材料，但这些能力主要消费或展示上游 metadata；代码层面尚未监听真实浏览器 PWA install prompt 事件。`rg -n "beforeinstallprompt|appinstalled|userChoice" mobile/web` 无命中，是本轮要补的核心缺口。

本轮北极星是：现场人员打开 `mobile/web` PWA 后，手机端能直接捕获并展示 `beforeinstallprompt`、`userChoice`、`appinstalled` 三类浏览器安装提示事件，生成可复制的 whitelist-only 证据包；没有事件时也能明确记录 blocked/not_proven，而不是把已有 evidence 面板误读为真实 prompt 通过。所有控制动作继续 fail closed，所有 copy 都保持 `safe_to_control=false`、`accepted_processing_only_not_delivery_success` 和 `not_proven`。

## OKR 映射

- Objective 4：直接推进。对应 KR1/KR5/KR7：手机最小流程、普通用户验收标准、手机端美观可用与主流尺寸适配。本轮把 PWA install prompt 证据从材料展示推进到浏览器事件捕获。
- Objective 5：不推进 completion。当前仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration；本轮只记录 stop rule，不把 install prompt event capture 写成 O5 external proof。
- Objective 1/2/3：不推进 completion。Robot 侧只围栏 metadata，不证明底盘、导航、任务闭环、真实投放或 HIL。

## KR 拆解或更新

1. KR-A：手机端新增 `mobile_pwa_install_prompt_event_capture*` 事件捕获包。
   - schema 建议为 `trashbot.mobile_pwa_install_prompt_event_capture.v1`。
   - summary/copy 字段建议为 `mobile_pwa_install_prompt_event_capture_summary` 和 `mobile_pwa_install_prompt_event_capture_copy`。
   - 本地证据边界统一为 `software_proof_docker_mobile_pwa_install_prompt_event_capture_gate`。
2. KR-B：PWA 静态入口必须监听真实浏览器事件。
   - `beforeinstallprompt`：捕获事件出现、client timestamp、display mode、platform/user agent summary 和 prompt availability；如保存 deferred prompt，必须只保存在前端 runtime，不写入 copy package。
   - `userChoice`：捕获 outcome、platform、choice timestamp；只记录 allowlisted outcome，不保存 raw event。
   - `appinstalled`：捕获 installed event、timestamp、display mode；不得写成 production app readiness 或真实送达。
3. KR-C：证据包必须 phone-safe、whitelist-only。
   - 允许字段只包括 schema、event status、event timestamps、display mode、platform/browser summary、installability state、user choice outcome、appinstalled observed、safe phone copy、ACK 语义、evidence boundary、source boundary、`safe_to_control=false`、`not_proven`。
   - 禁止 token、Authorization、OSS AK/SK、DB/queue URL、credential-bearing URL、raw ROS topic、`/cmd_vel`、serial/UART、baudrate、WAVE ROVER 参数、本地路径、traceback、checksum、完整 artifacts、raw browser event、raw robot response、raw intake JSON 或 robot/internal 技术字段。
4. KR-D：安全和语义边界必须保持。
   - `safe_to_control=false`。
   - `ack_semantics=accepted_processing_only_not_delivery_success`。
   - `not_proven` 必须包括真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice 外部验收、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL、dropoff/cancel completion、delivery success。
   - Start Delivery、Confirm Dropoff、Cancel 继续 fail closed。
5. KR-E：Robot metadata-only fence 覆盖新 family。
   - metadata-only payload 不触发 collect/dropoff/cancel。
   - 不触发 ACK POST、cursor advance/persistence、terminal ACK、production readiness、HIL、dropoff/cancel completion 或 delivery success。
   - mixed valid-command 场景只执行合法 `trashbot.remote.v1` envelope，install prompt event capture metadata 不改变 action、target、idempotency、ACK 或 cursor。

## 本轮核心抓手

把 “install prompt evidence 面板” 推进到 “install prompt 浏览器事件捕获”。这个 sprint 的成功标准是 `mobile/web` 能实际绑定 `beforeinstallprompt`、`appinstalled` 和 `userChoice` 事件，并将事件状态收敛成 phone-safe 证据包；不是证明真实手机验收已经通过，也不是让机器人可控。

## 需要做什么

- Full-stack：在 `mobile/web` 中新增事件监听、状态归一化、首屏面板和 copy package；更新 fixture/test、`mobile/README.md`、`docs/product/mobile_user_flow.md`。
- Robot：新增/更新 remote bridge/protocol metadata-only fence，保证 `mobile_pwa_install_prompt_event_capture*` family 对机器人侧没有控制副作用，并更新 `docs/interfaces/ros_contracts.md`。
- Product：工程完成后补齐 `tech-done.md`、`side2side_check.md`、`final.md`，并在 closeout 后更新 `OKR.md` 与 `docs/process/okr_progress_log.md`。

## 优先级和验收口径

P0：`mobile/web` 必须出现 `beforeinstallprompt`、`appinstalled` 和 `userChoice` 监听；事件缺失时仍生成 blocked/not_proven evidence package，而不是静默成功。

P0：evidence package 必须固定 `safe_to_control=false`、ACK 非 delivery success、`not_proven`、whitelist-only；Start/Confirm/Cancel 继续 fail closed。

P0：Robot metadata-only fence 证明新 family 不触发控制、副作用或成功语义；mixed valid-command 只执行合法 command envelope。

P1：`mobile/README.md`、`docs/product/mobile_user_flow.md`、`docs/interfaces/ros_contracts.md` 同步更新，避免 Product/Support 把 event capture package 误读为真实手机验收、production app、O5 external proof 或 delivery success。

P2：验证保持围栏：复用现有 mobile unittest、`node --check`、py_compile、remote bridge targeted unittest、required `rg` 和 scoped `git diff --check`；不新增大批泛化测试。

## 对应责任 Engineer

- `full-stack-software-engineer`：Task A，负责 `mobile/web` install prompt event capture、fixture/test、mobile/product 文档和手机端 evidence boundary。
- `robot-software-engineer`：Task B，负责 remote bridge/protocol metadata-only fence 和 ROS contract 文档。
- `product-okr-owner`：Task C，负责后续 closeout、OKR/process log/sprint final，不写产品代码或测试代码。

## 风险、阻塞和需要补齐的证据链

- 本轮不会自动产生真实手机验收；真实 iPhone/Android、production app、真实 PWA prompt/user choice 仍需现场设备材料。
- 浏览器可能因为已安装、manifest/service worker 条件、用户手势或平台策略不触发 `beforeinstallprompt`；这种情况必须保留 not_proven，而不是判定通过。
- 本轮不会产生 Objective 5 external proof；真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration 仍缺。
- 本轮不会产生 HIL、Nav2/fixed-route、WAVE ROVER、dropoff/cancel completion 或 delivery success。
- 需要补齐的证据链：后续现场人员用真实 iPhone/Android 或 production app 入口执行并保留截图/浏览器事件摘要/user choice/appinstalled/offline/touch/visual/redaction 材料后，才能进入真实设备验收判定。

## 需要创建或更新的 sprint 文档

- 已创建/本阶段创建：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 工程完成后：`tech-done.md` 记录 Task A/B 实际改动、验证结果、失败定位和剩余风险。
- 验收收口后：`side2side_check.md` 对照 PRD/tech-plan；`final.md` 更新 OKR 边界和下一步；Product closeout 后更新 `OKR.md` 与 `docs/process/okr_progress_log.md`。
