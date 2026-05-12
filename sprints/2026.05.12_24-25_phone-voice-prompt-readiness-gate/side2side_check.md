# Sprint 2026.05.12_24-25 Phone Voice Prompt Readiness Gate - Side2Side Check

## 状态

- 阶段：side2side_check
- Product Owner：`product-okr-owner`
- 主线 Objective：O5 手机体验与量产边界
- Evidence boundary：`software_proof_docker_phone_voice_prompt_readiness_gate`
- 收口结论：通过本轮产品验收，可进入 final。

## 用户价值和产品北极星

用户价值：手机首屏现在能解释“小车当前应该说什么、为什么说、是否需要人工帮助、是否已经证明真实播放”。这让电梯 assisted delivery、失败、人工接管等场景从散落字段变成普通用户可理解的提示 readiness。

产品北极星：普通用户只用手机交付垃圾；语音/喇叭路径先完成稳定 prompt contract 和手机可见 readiness，再补真实喇叭/TTS、真实手机设备和 production app 验收。

## OKR 映射

- O5 / KR2：`trashbot.voice_prompt_readiness.v1` 明确提示词、触发状态、播放证明边界和 ACK 语义。
- O5 / KR6：电梯 `requesting_floor_help` 指定中文提示进入首屏和 diagnostics，同步保留人工帮助边界。
- O5 / KR7：fallback 手机首屏以 phone-safe 中文文案展示提示 readiness，不暴露 raw JSON、ROS topic、串口或硬件参数。
- O6：仅验证 metadata 不污染 remote command/status/ACK envelope，不提升 O6 进度。

## 对照 PRD / Tech Plan

| 验收项 | 结果 | 证据 |
| --- | --- | --- |
| `/api/status.voice_prompt_readiness`、`phone_readiness.voice_prompt_readiness`、`/api/diagnostics.voice_prompt_readiness` 同口径 | 通过 | Task A `Ran 50 tests in 21.150s OK` |
| fallback HTML 首屏展示 current prompt、trigger、human help、`playback_ready=false`、safe copy、not_proven | 通过 | Task A static/http tests 与 `operator_gateway_static.py` 锚点 |
| 电梯 `requesting_floor_help` 指定提示覆盖 | 通过 | Task A 覆盖 `你好,好心人,.我要去1楼扔垃圾,请帮我按一下电梯,` |
| voice metadata 不污染 `trashbot.remote.v1` command/status/ACK envelope | 通过 | Task B `Ran 82 tests in 20.943s OK` |
| metadata-only blocked response 不触发 action、不 ACK、不推进或持久化 cursor | 通过 | Task B remote bridge compatibility fence |
| ACK 不等于 delivery success，也不等于 voice prompt 已真实播放 | 通过 | Task A + Task B 验证与接口文档 |
| diagnostics 不暴露 raw ROS topic、serial、baudrate、token、Authorization、OSS/DB/queue URL 或 local path | 通过 | Task B diagnostics fence |
| product/interface docs 已同步且路径存在 | 通过 | `docs/product/mobile_user_flow.md`、`docs/interfaces/ros_contracts.md` |

## 优先级和验收口径

- P0 已完成：schema/API/diagnostics/首屏入口、字段脱敏、ACK/not_proven 口径。
- P1 已完成：覆盖电梯 assisted delivery 和人工接管中文提示，`playback_ready=false` 明确保守。
- P2 已完成：support/diagnostics 可引用 voice prompt readiness，但未写成真实售后系统、真实 TTS 或 production app。

## 责任 Engineer

- `full-stack-software-engineer`：完成 Task A API、HTML、测试、product/interface 文档同步。
- `robot-software-engineer`：完成 Task B remote bridge/operator compatibility fence。
- `product-okr-owner`：完成本 side2side、final 和 OKR 保守收口。

## 文档路径核对

- `docs/product/mobile_user_flow.md`：存在，已同步 voice prompt readiness。
- `docs/interfaces/ros_contracts.md`：存在，已同步 schema/remote compatibility contract。

## 剩余风险和证据缺口

- 没有真实喇叭/TTS 播放证据。
- 没有真实手机设备 Safari/Chrome 或 production app 验收。
- 没有真实云/4G、HTTPS/TLS 公网入口、OSS/CDN 实流量或 production account。
- 没有 Nav2/fixed-route 实跑、WAVE ROVER、真实串口、HIL 或真实送达。
- 本轮只支持 O5 从约 50% 保守提升到约 52%；O6 保持约 51%，O1/O2/O3/O4 不提升。
