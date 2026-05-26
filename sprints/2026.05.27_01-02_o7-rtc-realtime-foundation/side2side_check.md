# O7 RTC Realtime Foundation Side-by-Side Check

## 1. CEO 问题对照

| 问题 | 本轮验收结论 | 证据 |
| --- | --- | --- |
| 视频 RTC 不需要机器上协议打通吗？ | 需要。至少需要 board media agent、设备状态、云端信令/status、PC viewer 状态和错误回执。 | `docs/interfaces/o7_realtime_hardware_sources.md`、`docs/interfaces/o7_board_realtime_status.md`、`docs/interfaces/o7_realtime_operator_console.md` |
| 板子上的代码够了？ | 不够。vendor Raspberry Pi app 可作参考，但不证明 rober Orange Pi + ROS2 + cloud + PC 已打通。 | `o7_realtime_hardware_sources.md` 明确 vendor Raspberry Pi source boundary |
| PC 端能不能先做？ | 可以先做 cloud-contract driven、fail-closed、observe-only 的 O7 Console；不能说成真实 RTC 或真实控制。 | PC `GET /api/o7/operator-console` 与 `O7 Console` tab |

## 2. O7 KR 对照

| O7 KR | 本轮真实进展 | 仍未完成 |
| --- | --- | --- |
| KR1 实时地图与机器人位置 | PC O7 Console 有 map/pose 视图入口和 blocked/not_proven contract。 | 未证明真实 `/tf` 或云端位置流，未证明刷新延迟 < 2 秒。 |
| KR2 电梯状态展示 | PC O7 Console 有 elevator state 视图入口和所需字段方向。 | 未证明真实电梯状态链、楼层证据或人工接管链路。 |
| KR3 历史路线回放 | PC O7 Console 有 route replay draft 入口。 | 未证明云端历史任务库、轨迹帧和状态转移回放。 |
| KR4 数据标注/打标界面 | PC O7 Console 有 labeling queue draft 入口。 | 未证明真实标注服务、提交审计或训练数据导出。 |
| KR5 实时 ASR 监听 + TTS 发言控制 | board/cloud/PC contract 表达 ASR/TTS 状态、TTS draft 和缺口。 | 未证明真实 ASR stream、真实 TTS 播放或喇叭链路。 |
| KR6 手动转向控制 + 自动寻路下发 | board/cloud/PC contract 明确 manual/nav policy blocked，未来 command preview 不发送到机器人。 | 未证明真实手控、速度控制、Nav2 goal、safe stop、cancel、timeout 或 HIL。 |

## 3. Product 验收结论

本轮可以验收为 O7 realtime foundation 的软件契约起步完成：Hardware 给出 vendor-source 边界，Robot 给出 board realtime status producer，Full-Stack 给出 cloud/PC operator console contract 和 PC O7 tab。

本轮不能验收为真实 RTC、真实视频、真实 ASR/TTS、真实手控、真实寻路、真实地图、电梯状态、历史回放、标注服务或上车链路完成。`source=software_proof`、`proof_status=not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false` 必须继续保留。

## 4. OKR 判断

O7 从 0% 保守提升到约 5%。理由是本轮从“新 Objective 无平台入口”推进到“board/cloud/PC 三段契约 + PC O7 Console software proof”，这是可复用基础。

该 5% 不包含真实能力完成度。O6 保持 0%，O5 保持约 80%，O1 保持约 83%。
