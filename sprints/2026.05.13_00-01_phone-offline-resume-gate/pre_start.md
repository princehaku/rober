# Sprint 2026.05.13_00-01 Phone Offline Resume Gate - Pre Start

## 状态

- 阶段：pre_start
- 创建时间：2026-05-13 00:01 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 主线 Objective：O5 手机体验与量产边界
- Evidence boundary：计划目标为 `software_proof_docker_phone_offline_resume_gate`
- 本轮约束：本机没有真实手机、真实云/4G、真实硬件或 HIL，只能推进 local/Docker fallback phone proof。

## 当前 evidence rerank

`OKR.md` 当前显示：

- O5 手机体验与量产边界：约 52%，最新证据是 `software_proof_docker_phone_voice_prompt_readiness_gate`。
- O6 4G 云中转 + OSS/CDN：约 53%，最新证据是 `software_proof_docker_production_recovery_gate`。

因此在 Docker-only 环境下，当前最低且可推进 Objective 是 O5。O1/O2/O3/O4 的剩余缺口依赖真实硬件、真实路线、真实相机或 HIL，本轮不抢这些范围。

## 近期证据

- `sprints/2026.05.12_24-25_phone-voice-prompt-readiness-gate/final.md`：O5 voice prompt readiness 已落地，首屏/API/diagnostics 能解释 prompt、human help、`playback_ready=false` 与 ACK 语义；仍没有真实手机设备、production app、真实喇叭/TTS。
- `sprints/2026.05.12_25-26_remote-production-recovery-gate/final.md`：O6 production recovery gate 已落地，O6 约 53%；仍是 local/Docker software proof，不等于真实云、4G、production DB/queue 或灾备完成。
- `docs/product/mobile_user_flow.md`：PWA/offline shell 已存在，且已声明 API 不应被 service worker 缓存；但还没有面向 phone/offline resume 的 readiness gate，把离线、恢复、command safety、support handoff 和 ACK 语义合成一个可执行验收口径。

## 用户价值和产品北极星

用户价值：普通用户在手机本地 fallback 页面离线、恢复连接或等待 ACK 时，能知道现在能不能继续、为什么不能发车、该等恢复还是联系支持，而不是看到 raw JSON、空白页面或误以为 ACK 等于送达成功。

产品北极星：普通用户只用手机完成垃圾交付。本轮不是做 production app，而是把已有 PWA/offline shell 推进成离线/恢复场景下可解释、可测试、可交接的 O5 readiness gate。

## 上轮未完成项

- 真实手机设备 Safari/Chrome、production app、普通用户实机验收仍缺。
- 真实喇叭/TTS、麦克风或真实播放证据仍缺。
- 真实云/4G、HTTPS/TLS、公网入口、production account、OSS/CDN 实流量仍缺。
- Nav2/fixed-route、WAVE ROVER、真实串口反馈、HIL 或真实送达仍缺。

## 本轮核心抓手

把 local/Docker fallback phone UI/API 增加 `phone_offline_resume_readiness` gate：

- 离线：offline shell 和 status/API summary 能明确“手机离线或控制面不可用，不能发车/确认/取消，Diagnostics/Support Handoff 可保留只读入口”。
- 恢复：恢复连接后，页面/API 能解释是否等待最新 robot status、是否有 pending ACK、是否需要重新拉取 diagnostics。
- command safety：Start/Confirm/Cancel 在离线、stale、pending ACK、manual takeover、support required 时保持 disabled，Diagnostics/Support Handoff 保持可进入。
- support handoff：离线/恢复失败时能给用户和售后一个 phone-safe handoff summary，不暴露 token、Authorization、OSS AK/SK、DB/queue URL、ROS topic、`/cmd_vel`、串口、波特率、本地路径、checksum 或完整 artifact。
- ACK 语义：所有 offline/resume copy 明确 ACK 只是 accepted/processing evidence，不是 delivery success、Nav2/fixed-route success、WAVE ROVER motion、真实云/4G 或 HIL。

## Scope

本轮 planning 只创建：

- `sprints/2026.05.13_00-01_phone-offline-resume-gate/pre_start.md`
- `sprints/2026.05.13_00-01_phone-offline-resume-gate/prd.md`
- `sprints/2026.05.13_00-01_phone-offline-resume-gate/tech-plan.md`

本轮不更新 `OKR.md`。只有实现、验证和收口证据落地后，才能在 final 阶段保守更新 OKR。

## Owner

- Product Owner：`product-okr-owner`，负责本轮 PRD、验收口径、证据边界和收口判断。
- 主责 Engineer：`full-stack-software-engineer`，负责 phone/operator API、fallback HTML、offline shell、service worker/API bypass、diagnostics/support handoff 的实现与验证。
- 兼容性咨询/围栏：`robot-software-engineer`，只在 remote command/status/ACK envelope 或 robot action 语义可能受影响时执行兼容性测试，不改 phone UI 主实现。

## 风险和阻塞

- 本机只有 Docker：不能声明真实手机设备、真实浏览器安装、真实云/4G、真实硬件或 HIL。
- Offline shell 容易被误读成“离线可继续控制机器人”：必须明确离线只能展示恢复提示和只读支持入口，不能发控制命令。
- Resume gate 容易把 stale status 或 pending ACK 当成 ready：必须让 command safety 做最终按钮级阻断。
- Support handoff 必须继续 phone-safe redaction，不得泄露凭证、硬件细节、ROS topic、路径或完整 artifacts。

## 进入下一阶段条件

- `prd.md` 写清用户价值、OKR/KR 映射、范围边界、验收口径和 not-proven 列表。
- `tech-plan.md` 写清主责 Engineer、允许改动文件、接口影响、验证命令和风险边界。
- planning 文件存在且 scoped `git diff --check` 通过。
