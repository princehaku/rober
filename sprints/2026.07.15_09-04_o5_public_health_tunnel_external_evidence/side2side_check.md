# Side-to-side Check - O5 Public Health Tunnel External Evidence

## Sprint Metadata

- `sprint_type: epic`
- Sprint：`sprints/2026.07.15_09-04_o5_public_health_tunnel_external_evidence/`
- Product owner：`product-okr-owner`
- Delivery owner：`full-stack-software-engineer`
- Product status：`accepted_local_safety_and_honest_failed_live_preflight_no_external_credit`
- Proof boundary：`software_and_failed_live_preflight_o5_public_health_tunnel_external_evidence`

## 事实源核对

Product 已逐项核对 `pre_start.md`、`prd.md`、`tech-plan.md`、`tech-done.md`、脱敏 JSON artifact、proxy/test/compose/README 与 helper diff、最近 O5/O3 `final.md`、`OKR.md` 和进度日志。验收只采信这些当前文件中的一致事实，不把计划目标回写成已完成结果。

## 计划与实绩对照

| Gate | 计划口径 | 当前事实 | Product 判断 |
| --- | --- | --- | --- |
| health-only proxy | 纯标准库、只允许精确 GET/HEAD `/healthz` | 已实现；其他 path/query/encoding/absolute-form `404`，精确路径其他 method `405` | 接受本地安全增量 |
| upstream 隔离 | 负向请求不得触达 relay | 6 tests 覆盖正向、完整负向矩阵、敏感 header、timeout/error 与非 loopback；负向断言 upstream count 不变 | 接受本地合同与测试证据 |
| loopback publish | relay/proxy 仅 `127.0.0.1` | compose host publish 已收紧；README 标明 tunnel 直连 relay `NO-GO` | 接受 |
| bearer contract | token 必须 fail-closed | compose 仍要求显式非空 `TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN`；没有引入默认 token | 接受 |
| provider metadata | Cloudflare 官方 HTTPS/version/ARM64 | metadata HTTPS 成功，version=`2026.7.1`，remote arch=`aarch64` | 接受为 preflight 部分事实 |
| provider runtime | 下载、SHA256、chmod、binary version 全 gate | remote provider runtime preflight command exit `1`，发生在完整 SHA/version gate 前 | 拒绝 runtime provenance 完成 |
| tunnel | 只能指向 loopback proxy | `capture_invocation_count=1`，但 `tunnel_start_attempt_count=0` | 未执行，拒绝 tunnel success |
| public capture | TLS/certificate + GET/HEAD `2xx/3xx` | `public_capture_count=0`、`public_probe_attempt_count=0`，无 public URL、TLS/certificate 或 GET/HEAD | 拒绝 external artifact 与 public HTTPS success |
| public negative matrix | 所有公网负向 case fail closed | 未运行，cases 为空；本地测试不能替代公网 edge/tunnel 证据 | 拒绝公网隔离完成 |
| relay state | capture 前后 checksum 相同 | state check 未运行；`state_unchanged=false` 表示 not run，不代表观察到 mutation | 不接受也不推断 state change |
| cleanup | helper residual=`0` | `cleanup_residual_count=0`；远端只读 residual 复核无进程、无临时目录 | 接受清理完成 |
| redaction | artifact 不含 raw URL/credential/header/body | 无 public URL 产生；artifact 为枚举化失败摘要，未提交 raw credential | 接受，但当前分类过窄导致子阶段不可判 |

## 失败定位

- 唯一 live invocation=`1`，official metadata HTTPS 与 version `2026.7.1` 已成功。
- exact accepted stage 是 `provider_runtime_preflight`；remote command exit=`1` 发生在 `sha256_verified=true` 与 binary version gate 完成之前。
- 这不是已证明的 SHA mismatch。当前 helper 为避免泄露路径/URL而未保留非敏感子阶段，所以不能从 artifact 判断是 download、SHA command、chmod 还是 binary version 子步骤退出。
- `tunnel_start_attempt_count=0`、`public_capture_count=0`、`public_probe_attempt_count=0`；因此没有证书失败、GET/HEAD 失败或公网负向矩阵失败，只是这些步骤均未运行。
- cleanup residual=`0`，失败没有留下公网入口或 helper-owned 远端资源。

## Product 接受项

1. 接受本地 health-only proxy、6 tests、loopback compose publish、README 安全说明和 bearer token 仍必填。
2. 接受一次真实 Cloudflare provider metadata/runtime preflight invocation 及其 honest fail-closed artifact。
3. 接受 `software_and_failed_live_preflight_o5_public_health_tunnel_external_evidence` 边界和 cleanup residual=`0`。
4. 接受本轮不同于既有 loopback wrapper：它真实触达官方 provider metadata 与远端 runtime preflight，并实质收紧 relay 暴露面；但该差异不足以跨过 external gate。

## Product 拒绝项

- 拒绝 `external_artifact_delta=true`、`current_run_artifact_delta=true`。
- 拒绝 public HTTPS/TLS/certificate success、GET/HEAD `2xx/3xx`、公网 negative matrix 和 state checksum unchanged claim。
- 拒绝 `production_ready=true`、Mission Objective 0、O5 score lift 或 KR 归档。
- 拒绝 route/control/delivery/HIL/safe-to-control 的任何推导。

固定结论：

- `current_run_artifact_delta=false`
- `external_artifact_delta=false`
- `live_control_delta=false`
- `user_action_delta=false`
- `production_ready=false`
- `mission_objective_0_satisfied=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `safe_to_control=false`

## OKR 与非重复判断

- O5 保持约 `85%`；O1 保持约 `94%`；O6/O7 各保持约 `93%`。
- 本轮 KR `不归档`，没有完成 KR 移入历史区；详细失败事实进入 `docs/process/okr_progress_log.md`。
- 当前 sprint **不得重跑**，不得把本地 proxy、README、失败 artifact 或 cleanup 再包装成增量。
- 若继续 O5，必须进入新 sprint：先离线给 helper 增加非敏感枚举 stage（download/sha/chmod/version），完成 official provenance dry gate，再由新的明确授权决定是否消费一次 public capture。
- 同一 `provider_runtime_preflight` blocker 最多再消费一轮；再失败必须切换到不重复 blocker 的次低 Objective 或升级 CEO 决策。不得回到 O6/O7 wrapper。
