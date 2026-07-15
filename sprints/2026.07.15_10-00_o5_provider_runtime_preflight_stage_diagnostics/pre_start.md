# Pre Start - O5 Provider Runtime Preflight Stage Diagnostics

## Sprint Metadata

- `sprint_type: epic`
- Sprint：`sprints/2026.07.15_10-00_o5_provider_runtime_preflight_stage_diagnostics/`
- Product owner：`product-okr-owner`
- Delivery owner：`full-stack-software-engineer`
- 目标 Objective：O5（约 `85%`，当前最低）
- 当前阶段：计划完成后等待 Engineer 实现；本文件不代表交付完成。

## 用户价值与产品北极星

北极星仍是让普通手机用户获得可验证、可靠的垃圾送达服务。本轮不宣称公网已可用，而是把阻塞公网健康证据的 provider runtime 前置失败从“整体 exit 1”收敛为可安全定位的子阶段，使下一次决策基于确定事实，不再靠重跑 tunnel 猜测。

## 上轮事实与方向判断

上一轮 `sprints/2026.07.15_09-04_o5_public_health_tunnel_external_evidence/` 已接受本地 health-only proxy、6 tests、loopback publish、bearer token fail-closed 和一次真实 Cloudflare metadata/runtime preflight 的诚实失败。唯一 invocation 中 official metadata HTTPS/version `2026.7.1` 成功，但 remote `provider_runtime_preflight` 在完整 SHA/version gate 前 exit `1`；`tunnel_start_attempt_count=0`、`public_capture_count=0`、`public_probe_attempt_count=0`，不能判定 download、SHA command、chmod 或 version 哪个子步骤失败，也不能称为 SHA mismatch。

方向判断：`继续 O5，但只允许最后一轮 provider_runtime_preflight blocker 诊断`。本轮唯一抓手是让 preflight 输出脱敏、有序的阶段枚举，并通过本地/离线 official provenance contract dry gate。不得 SSH/live、不得启动 tunnel、不得公网 capture/probe、不得机器人控制。

## Blocker 消费红线

- 上轮已消费该 blocker 一轮，本轮是最多允许的第二轮，也是最后一轮。
- 本轮不得重跑上一 sprint，不得把 proxy、README、cleanup 或旧失败 artifact 包装成新增量。
- 若枚举 stage 仍不能把失败定位到明确边界，或本地/离线 dry gate 失败，本 sprint 必须 fail closed；下一轮必须切换 Objective，或升级 CEO 决策，不得继续第三轮消费同一 blocker。

## 本轮核心抓手与范围

由 `full-stack-software-engineer` 单 owner 闭环：

1. 输出且只输出以下有序脱敏 stage：`download_started`、`download_completed`、`sha_command_completed`、`sha_matched`、`chmod_completed`、`version_executed`、`version_matched`。
2. 使用本地临时目录、受控 fixture/stub 和注入式 command runner 完成离线 official provenance contract dry gate；验证 stage 单调前进、失败停在最后安全边界、SHA/version mismatch fail closed。
3. artifact 不保存 raw URL、checksum 原文、stderr/stdout、绝对路径、credential、header、body 或 tunnel log。

## 明确禁止

- 不得执行 SSH、SCP、远端命令或 live provider runtime。
- 不得启动 tunnel/cloudflared daemon，不得生成或保存 public URL。
- 不得公网 capture/probe，不得发 TLS/GET/HEAD/negative matrix 请求。
- 不得启动 relay/proxy，不得读写 production DB/queue/OSS/CDN。
- 不得执行 command/task/archive write、`/cmd_vel`、`/api/base/manual`、UART、route、delivery、HIL 或任何机器人控制。
- 不得修改工程代码、测试、`OKR.md` 或 `docs/process/okr_progress_log.md`；实现阶段只按 `tech-plan.md` 的精确范围工作。

## OKR / KR 决策

- O5 保持约 `85%`；本轮计划阶段不调整任何 Objective 百分比。
- 当前 O5 KR 继续推进但 `不归档`；没有已完成 KR 移入历史区。
- 即使离线 dry gate 通过，也只证明诊断合同，不证明 official provider binary 当前真实下载/执行成功、public HTTPS、production ready 或 Mission Objective 0。
- 只有后续新的明确授权和 success-class external evidence 才可能触发 O5 计分判断；本轮不得自行推导增量。

## 需要创建或更新的 sprint 文档

本阶段只创建 `pre_start.md`、`prd.md`、`tech-plan.md`。不得创建 `tech-done.md`、`side2side_check.md` 或 `final.md`；它们只能在后续真实实现、验证和 Product 验收发生后按顺序产生。
