# Sprint 2026.05.13_05-06 Mobile Task Start Confirmation Gate - Pre Start

## Sprint Type

- sprint_type: epic
- Evidence boundary target: `software_proof_docker_mobile_task_start_confirmation_gate`
- Start time: 2026-05-13 Asia/Shanghai

## Product 北极星

本轮继续服务 rober 北极星：让普通手机用户把垃圾交给小车后，不接触 ROS2、SSH、串口或 raw JSON，也能按清晰步骤发起送垃圾任务，并知道当前只是 accepted/processing、blocked、offline 还是需要人工处理。

本轮不追求真实 production app、真实手机设备、真实云、4G、HIL 或送达成功；只把手机静态入口从"能打开并消费 readiness"推进到"发车前必须确认目标垃圾站和已放入垃圾，并提交 phone-safe JSON payload"。

## 启动依据

- `OKR.md` 4.1 当前快照显示 Objective 4 手机用户体验与低成本量产边界约 56%，是当前最低可推进目标；Objective 5 约 57%，已经被上一轮 cloud deployment readiness gate 推到略高。
- `sprints/2026.05.13_03-04_mobile-web-entrypoint-gate/final.md` 记录 Objective 4 从约 54% 提升到约 56%，证据边界是 `software_proof_docker_mobile_web_entrypoint_gate`，且明确不是 production app、真实手机设备/浏览器、真实 PWA install prompt、云、4G、HIL 或真实送达证明。
- `sprints/2026.05.13_03-04_mobile-web-entrypoint-gate/tech-done.md` 记录 `mobile/web/` 已有 dependency-free PWA 静态入口，按钮必须同时满足 `command_safety` 和旧权限 gate，但当前只是 consumer，不改变 `/api/status`、`/api/diagnostics` 或 `trashbot.remote.v1`。
- `sprints/2026.05.13_04-05_cloud-deployment-readiness-gate/final.md` 记录 Objective 5 从约 55% 到约 57%，Objective 4 保持约 56%，因为本轮没有 real phone app/device 或 production app 新证据。
- `sprints/2026.05.13_04-05_cloud-deployment-readiness-gate/tech-done.md` 记录 cloud deployment readiness 只是 Docker/local blocked readiness，ACK 仍只能解释为 command accepted/processing，不是 delivery success。
- `docs/product/mobile_user_flow.md` Minimum User Journey 的第 3-5 步要求用户选择或确认垃圾站、放入垃圾、确认装载后点击开始；KR1/KR5/KR7 对应的产品口径是普通用户不接触命令行/ROS2/硬件调试，主路径要手机可用、美观、中文优先、主操作步骤不超过 3 步。
- `docs/product/mobile_user_flow.md` Mobile Web Entrypoint 还要求 Start Delivery、Confirm Dropoff、Cancel 默认禁用，只有 `command_safety.actions.<action>.enabled=true` 且旧权限字段也允许时才能启用；blocked/offline/pending ACK/manual takeover 均要 fail closed。
- `mobile/web/app.js` 当前 `submitAction()` 对 `POST /api/collect` 只传 `{ method: "POST" }`，没有 body，也没有把垃圾站选择和"已放入垃圾"确认写入 phone-safe payload。

## 本轮核心抓手

`software_proof_docker_mobile_task_start_confirmation_gate`：

1. 手机入口发车前明确展示或选择垃圾站。
2. 发车前必须显式确认"已放入垃圾"。
3. `POST /api/collect` 提交 phone-safe JSON payload，不暴露 ROS topic、`/cmd_vel`、串口、WAVE ROVER 或硬件细节。
4. 继续保持 `command_safety` + 旧权限字段双 gate。
5. blocked、offline、pending ACK、manual takeover、后端缺字段或选择/确认缺失时 fail closed。
6. ACK 文案继续保持 accepted/processing evidence only，不能变成送达成功证明。

## Owner 与分工

- `full-stack-software-engineer`：主责手机静态入口、phone-safe collect payload、UI 步骤、静态 smoke、产品文档同步。
- `robot-software-engineer`：主责 robot/remote bridge compatibility fence，证明新 payload metadata 不触发非预期 robot action、不改变 ACK/delivery 语义、不污染 `trashbot.remote.v1` command envelope。
- `product-okr-owner`：本轮只负责产品口径、计划、验收边界和最终 OKR 更新；不写产品代码或测试代码。

## 阻塞扫描

最近两轮没有连续消费同一 blocker：

- 03-04 结论是 mobile web entrypoint 软件证明完成，但真实手机、production app、云、4G、HIL、真实送达未证明。
- 04-05 结论是 cloud deployment readiness 软件证明完成，但 Objective 4 未提升。

本轮切回 Objective 4，不继续消费 Objective 5 的 cloud blocker；当前没有真实手机、真实云、真实硬件，因此验收限定为 Docker/local software proof。

## 计划文档

本轮需要创建并维护：

- `sprints/2026.05.13_05-06_mobile-task-start-confirmation-gate/pre_start.md`
- `sprints/2026.05.13_05-06_mobile-task-start-confirmation-gate/prd.md`
- `sprints/2026.05.13_05-06_mobile-task-start-confirmation-gate/tech-plan.md`

实现完成后还必须继续更新同目录下：

- `tech-done.md`
- `side2side_check.md`
- `final.md`

并在最终收口时更新 `OKR.md` 与相关 `docs/`，但本计划任务不修改这些文件。
