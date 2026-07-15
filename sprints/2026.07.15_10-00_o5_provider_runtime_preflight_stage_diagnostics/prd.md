# PRD - O5 Provider Runtime Preflight Stage Diagnostics

## 1. 产品问题

上一轮 provider runtime preflight 只有整体 exit `1`，为保护 URL/路径/stderr 而没有保留非敏感子阶段。Product 因而无法判断失败发生在 download、SHA command、SHA compare、chmod 还是 version execution/match，也不能安全批准下一次公网 capture。继续盲目重跑会重复消费同一 blocker。

## 2. 用户价值与北极星关系

直接用户是负责部署与验收的开发/运维人员：他们需要一个不泄密、可复验的 preflight 诊断结果，才能决定修复、暂停或申请下一次 live。对普通手机用户的价值是减少不可靠公网控制面进入交付链的概率；本轮不改变手机体验，也不宣称云端已在线。

## 3. 产品目标

在完全本地/离线、无 SSH、无 tunnel、无公网 probe、无机器人控制的条件下，完成 `provider_runtime_preflight` 阶段诊断合同与 official provenance contract dry gate：

- 成功路径按固定顺序输出 `download_started`、`download_completed`、`sha_command_completed`、`sha_matched`、`chmod_completed`、`version_executed`、`version_matched`。
- 失败路径只保留已经到达的有序前缀、最后到达 stage、下一预期 stage 和安全 reason enum；不得保存原始命令输出。
- SHA mismatch 不得进入 chmod/version；version mismatch 不得标记 `version_matched`。
- dry gate 使用本地临时 fixture/stub 验证 official metadata/asset/digest/version 的合同形状与阶段机，不访问远端或公网。

## 4. 输出合同

建议 schema：`trashbot.o5.provider_runtime_preflight_stage_diagnostics.v1`。

必须包含：

- `provider_runtime_preflight_status`: `passed_offline_dry_gate` 或 `blocked_offline_dry_gate`
- `completed_stages`: 只允许上述七项的有序前缀
- `last_reached_stage`
- `next_expected_stage`
- `failure_reason`: 固定安全枚举，不含异常文本
- `proof_boundary=software_proof_o5_provider_runtime_preflight_stage_diagnostics_offline_only`
- `official_provenance_contract_checked=true|false`
- `network_access_attempted=false`
- `ssh_attempted=false`
- `tunnel_start_attempt_count=0`
- `public_capture_count=0`
- `public_probe_attempt_count=0`

固定安全字段：`current_run_artifact_delta=false`、`external_artifact_delta=false`、`live_control_delta=false`、`user_action_delta=false`、`production_ready=false`、`mission_objective_0_satisfied=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`safe_to_control=false`。

禁止输出：raw URL、hostname、credential/token、checksum 原文、stderr/stdout、shell command、绝对路径、header/body、tunnel log、public URL。

### 4.1 稳定接口文档同步

`full-stack-software-engineer` 必须新增稳定接口文档 `docs/interfaces/o5_provider_runtime_preflight_stage_diagnostics.md`，不得只在 sprint artifact 或测试中隐含合同。文档同步至少写清：

- schema `trashbot.o5.provider_runtime_preflight_stage_diagnostics.v1` 及每个字段的类型、必填性和 fail-closed 默认值；
- 七个 stage 的固定顺序、`completed_stages` 有序前缀规则、`last_reached_stage` 与 `next_expected_stage` 语义；
- failure enums：`download_failed`、`sha_command_failed`、`sha_mismatch`、`chmod_failed`、`version_execution_failed`、`version_mismatch`、`invalid_stage_transition`；
- 脱敏白名单与禁止字段：不得保存 raw URL、hostname、credential/token、checksum 原文、stderr/stdout、命令、绝对路径、header/body 或 tunnel log；
- proof boundary `software_proof_o5_provider_runtime_preflight_stage_diagnostics_offline_only`，明确 dry gate 只证明本地合同；
- offline-only 运行边界，以及禁止 SSH/live、禁止启动 tunnel、禁止 public capture/probe、禁止任何 robot control。

接口文档必须与实现、测试和 dry artifact 同轮验证；缺失或与 schema/stage/failure contract 不一致时，本轮不得验收。

## 5. 验收场景

1. happy path：七个 stage 精确、无重复、按顺序完成，status 为 `passed_offline_dry_gate`。
2. download failure：只到 `download_started`，后续全部未完成。
3. SHA command failure：停在 `download_completed`，不进入 match/chmod/version。
4. SHA mismatch：包含 `sha_command_completed`，不包含 `sha_matched` 及后续 stage。
5. chmod failure：包含 `sha_matched`，不包含 `chmod_completed` 及后续 stage。
6. version execution failure：包含 `chmod_completed`，不包含 `version_executed/version_matched`。
7. version mismatch：包含 `version_executed`，不包含 `version_matched`。
8. hostile/invalid metadata、乱序/跳级/重复 stage、危险 true claim、非本地 runner 均 fail closed。
9. artifact 脱敏扫描、JSON 结构、中文注释比例 `>20%`、targeted unittest、scoped diff check 全通过。

## 6. 非目标与 proof boundary

本轮不证明真实 cloudflared binary 下载、真实 official SHA match、真实 chmod/version execution、SSH/remote runtime、tunnel/public URL、TLS/certificate、GET/HEAD、negative matrix、state checksum、稳定 DNS、4G、production DB/queue/worker/OSS/CDN、真实手机/browser、route execution、delivery、HIL 或 safe-to-control。

本轮不得启动 tunnel，不得公网 capture/probe，不得机器人控制。离线 dry gate 通过只允许 Product 得出“stage diagnostics contract ready”；不得上调 O5，不得归档 KR。

## 7. 优先级、Owner 与退出条件

- 优先级：P0，仅因 O5 为最低 Objective 且 CEO 已明确允许同 blocker 最后一轮诊断。
- 唯一责任 Engineer：`full-stack-software-engineer`。
- 文档责任：同一 Engineer 必须新增并同步 `docs/interfaces/o5_provider_runtime_preflight_stage_diagnostics.md`。
- 成功退出：阶段机、失败矩阵、dry artifact、脱敏与全部本地验收通过。
- 失败退出：任一 gate 失败即 fail closed，不做 live 补证。
- 后续路由：若 stage 仍不可定位或离线 gate 失败，下一轮必须切换 Objective 或升级 CEO；不得继续第三轮 provider runtime preflight blocker。

## 8. KR 历史归档

无已完成 KR，不新增历史记录。证据来源仅为上一轮 `tech-done.md`、`side2side_check.md`、`final.md` 与本 sprint 后续可能产生的真实 `tech-done.md`；计划文档不能作为 KR 完成证据。
