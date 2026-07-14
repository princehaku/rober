# Side2Side Check - O7 Voice Runtime Preflight

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.14_11-35_o7_voice_runtime_preflight/`
- Product closeout time: 2026-07-14 11-35 CST
- Product owner: `product-okr-owner`
- Implementation owner: `full-stack-software-engineer`
- Proof boundary: `software_proof_o7_voice_runtime_preflight_only`
- Product status: accepted as O7 voice runtime preflight software proof only.

## 用户价值和产品北极星

用户价值：普通用户最终需要通过语音、喇叭和手机/PC 状态理解小车是否能继续送垃圾任务。本轮没有交付真实语音能力，但把 PC/O7 voice runtime 的配置和准入检查做成可复验合同，避免后续接入 ASR/TTS、speaker dispatch 或现场语音提示时混入危险真值。

产品北极星：rober 要成为普通用户可理解、可操作、可复盘的送垃圾机器人。voice runtime preflight 是用户触点的准入检查，不是送达闭环本身；只有后续真实 voice runtime、现场任务、route execution、delivery/operator acceptance 或 HIL 证据到位后，才可能贡献主 OKR 增量。

## 输入核对

- `pre_start.md` / `prd.md` / `tech-plan.md` 均要求本轮只证明 `voice runtime preflight`，并固定拒绝真实 ASR/TTS、麦克风、喇叭、TTS 发送、speaker dispatch、机器人控制、生产云、delivery、HIL 和 safe-to-control。
- `tech-done.md` 记录 Full-stack owner 已新增 `GET /api/o7/voice-runtime/preflight`、schema `trashbot.pc_tools_workstation.o7_voice_runtime_preflight_result.v1`、proof boundary `software_proof_o7_voice_runtime_preflight_only`。
- `docs/product/pc_tools_workstation.md` 已同步工作站产品边界：该 endpoint 只读取本地/离线 mode 或本地配置 JSON，不连接生产云，不访问 voice provider，不打开麦克风/喇叭，不写 O6 archive events，不控制机器人。

## Side-by-Side Acceptance

| 验收项 | 计划要求 | 实现证据 | Product 判断 |
| --- | --- | --- | --- |
| Endpoint | 增加 PC/O7 voice runtime preflight | `GET /api/o7/voice-runtime/preflight` | 接受 |
| Schema | 返回稳定 receipt/schema | `trashbot.pc_tools_workstation.o7_voice_runtime_preflight_result.v1` | 接受 |
| Proof boundary | 只允许软件证明 | `software_proof_o7_voice_runtime_preflight_only` | 接受 |
| Missing config | 缺少配置必须阻塞/失败关闭 | `blocked_missing_voice_runtime_config` | 接受 |
| Safe local/offline config | 只可标记配置检查 ready | `ready_for_configured_runtime_check_only` | 接受 |
| Dangerous true claims | 真实能力声明必须 fail closed | `fail_closed` | 接受 |
| O6 event write | 默认不需要 O6 archive events | `tech-done.md` 明确没有 O6 event write | 接受 |
| False fields | 固定安全/真实能力 false | `real_voice_api_connected=false`、`real_asr_tts_runtime_connected=false`、`tts_send_enabled=false`、`speaker_dispatch_enabled=false`、`safe_to_control=false`、`delivery_success=false` | 接受 |

## 拒绝声明

本轮不证明 real ASR/TTS、真实 voice API、麦克风输入、喇叭播放、speaker dispatch、real speaker ACK、TTS 发送、production cloud、production DB/queue、OSS/CDN、4G/SIM、真实手机/browser、route execution、delivery/operator acceptance、HIL、safe-to-control、O5 external evidence、`/cmd_vel`、`/api/base/manual`、NavigateToPose、WAVE ROVER UART 或 robot movement。

## OKR 映射和方向判断

- O5：继续约 `85%`。本轮未产生 success-class production/cloud evidence，也没有真实 4G/SIM、production DB/queue、OSS/CDN live traffic 或真实手机/browser 证据。
- O1：继续约 `94%`。本轮不涉及 WAVE ROVER、current live HIL、route execution、delivery/operator acceptance 或 safe-to-control。
- O6/O7：继续约 `93%`。本轮是 O7 voice runtime preflight 软件证明，能提升回归守护和配置准入清晰度，但不是真实语音运行时或送达证据。
- 方向判断：`调整后继续`。在 O5 support-only blocker 无法计分时，接受一个 distinct O7 preflight slice；但主百分比 flat，KR 不归档。

## Product Acceptance 结论

Product 接受本轮为 O7 voice runtime preflight software proof only。证据边界是 `software_proof_o7_voice_runtime_preflight_only`，状态仅覆盖 missing config blocked、本地/离线配置 ready-for-configured-check-only 和 dangerous true claim fail-closed。主百分比不调整，KR `不归档`。

## 剩余风险和下一步

- 剩余风险：没有真实 ASR/TTS provider、麦克风、喇叭、speaker ACK、production cloud、delivery、HIL 或 safe-to-control 证据。
- 下一步证据链：只有 explicit authorization 后的真实 voice runtime smoke，或者同窗口 live route execution / delivery record / operator acceptance / HIL / success-class O5 production evidence，才可进入计分口径。
- 不重复规则：下一轮不得把 voice runtime preflight、voice TTS draft、voice speaker ACK/failure、operator/browser artifact、terminal/readback/export wrapper 或 O5 support-only packet 再包装为新 OKR 增量。
