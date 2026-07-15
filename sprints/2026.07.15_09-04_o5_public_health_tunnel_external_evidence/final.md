# Final - O5 Public Health Tunnel External Evidence

## Sprint Metadata

- `sprint_type: epic`
- Sprint：`sprints/2026.07.15_09-04_o5_public_health_tunnel_external_evidence/`
- Closeout date：`2026-07-15 Asia/Shanghai`
- Product status：`accepted_local_safety_and_honest_failed_live_preflight_no_external_credit`
- Proof boundary：`software_and_failed_live_preflight_o5_public_health_tunnel_external_evidence`

## Product Acceptance 结论

本轮接受本地 health-only 安全收口和一次真实 provider runtime preflight 的诚实失败，拒绝 external artifact、public HTTPS success、production ready、Mission Objective 0、任何 OKR score lift 与 KR 归档。

唯一 live invocation 事实为：`capture_invocation_count=1`、`tunnel_start_attempt_count=0`、`public_capture_count=0`、`public_probe_attempt_count=0`。Cloudflare 官方 metadata HTTPS 成功，release version=`2026.7.1`，上位机架构=`aarch64`；随后 remote `provider_runtime_preflight` 在完整 SHA/version gate 前 exit=`1`。这不是已证明的 SHA mismatch，当前脱敏分类不足以判定 download、SHA command、chmod 或 binary version 哪个子步骤失败。

没有 public URL，没有 TLS/certificate、GET/HEAD `2xx/3xx`、公网负向矩阵或 state checksum 结果。`tls_certificate_valid=false`、`state_unchanged=false` 在本 artifact 中都表示 not run，不得解释成证书无效或 state 已变化。cleanup residual=`0`，远端复核无本轮进程或临时目录。

## 实际改动与验证

- Full-stack 新增纯标准库 `healthz_allowlist_proxy.py`，只允许原始 target 精确 GET/HEAD `/healthz`；其他 path/query/encoding/absolute-form 返回 `404`，精确 path 的其他 method 返回 `405` 和 `Allow: GET, HEAD`。
- 6 个测试覆盖正向 GET/HEAD、负向 path/query/encoding、method gate、Authorization/Cookie/Host/Forwarded 隔离、upstream timeout/error 和非 loopback 配置拒绝；负向用例同时断言 upstream request count 不变。
- compose host publish 收紧到 `127.0.0.1`；bearer token 仍是显式必填，没有默认空鉴权；README 同步 tunnel 直连 relay `NO-GO` 与迁移说明。
- 本地验证通过：`py_compile` exit `0`；两次 targeted unittest 均 `Ran 6 tests ... OK`，discover 复验同样 `Ran 6 tests ... OK`；显式一次性非生产 token 下 compose config exit `0`；artifact `json.tool`、结构/脱敏断言与 scoped `git diff --check` 通过。
- 唯一 live invocation 在公网前 fail closed；本轮没有执行 command/task/archive write/manual/`cmd_vel`/UART/route/delivery/HIL。

## 用户价值与非重复说明

开发/运维现在有明确、可测试的 health-only 暴露边界，relay 不再默认发布到 LAN/all-interface，quick tunnel 也被禁止直连整个 relay。该安全收益是真实实现，不是又一份 readback/export/browser wrapper。

本轮还真实执行了 Cloudflare 官方 metadata 与远端 provider runtime preflight，因此不等同于重复 loopback wrapper；但因为 tunnel 和公网 probe 都没有启动，仍未形成用户可消费的 external availability evidence，不能计入 O5 百分比。

## Mission / OKR / KR 决策

- `current_run_artifact_delta=false`
- `external_artifact_delta=false`
- `live_control_delta=false`
- `user_action_delta=false`
- `production_ready=false`
- `mission_objective_0_satisfied=false`
- `okr_credit=false`
- O5 保持约 `85%`，O1 保持约 `94%`，O6/O7 各保持约 `93%`。
- KR `不归档`；无已完成 KR 移入历史区。

固定安全字段：`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`safe_to_control=false`。

## 方向判断

方向为 `O5 flat，禁止重跑当前 sprint；下一次先离线修 provenance 可诊断性`。

1. 当前 sprint **不得重跑**，也不得把 proxy/README/失败 artifact/cleanup 重新包装。
2. 若继续 O5，由 `full-stack-software-engineer` 在新 sprint 先让 helper 输出枚举化、非敏感的 `download_started/download_completed/sha_command_completed/sha_matched/chmod_completed/version_executed/version_matched` stage；不得保存 stderr、URL、路径或 checksum 原文。
3. 在本地/离线 official provenance dry gate 通过后，Product/CEO 再明确授权是否执行新的唯一 public capture。
4. 同一 `provider_runtime_preflight` blocker 最多再消费一轮；若仍失败，切换到不重复 blocker 的次低 Objective 或升级 CEO。不得回到 O6/O7 support wrapper。

## 剩余风险

1. cloudflared binary 的 download/SHA/chmod/version 子步骤尚不可定位，官方 runtime provenance 未闭环。
2. 没有 tunnel/public URL、TLS/certificate、GET/HEAD success class 或公网负向隔离证据。
3. state checksum gate 未运行，不能声明 unchanged；当前也没有证据表明发生 mutation。
4. temporary tunnel 即使后续成功，也仍不等于稳定 DNS、生产凭证、4G、production DB/queue、worker、OSS/CDN、真手机、route、delivery 或 HIL。
