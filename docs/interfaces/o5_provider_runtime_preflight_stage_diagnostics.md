# O5 Provider Runtime Preflight Stage Diagnostics 接口

## 1. 用途与稳定标识

该接口为 provider runtime 前置检查提供脱敏、可复验的阶段诊断，稳定 schema 为 `trashbot.o5.provider_runtime_preflight_stage_diagnostics.v1`。当前唯一 proof boundary 为 `software_proof_o5_provider_runtime_preflight_stage_diagnostics_offline_only`。

该 artifact 只证明本地 fixture、official-release-shaped metadata 合同与阶段机通过离线 dry gate。它不证明真实 official binary 下载、真实 SHA/权限/version 执行、SSH/remote runtime、public HTTPS、production ready、Mission Objective 0、route execution、delivery、HIL 或 safe-to-control。

## 2. 固定阶段顺序

阶段只能按以下顺序单调前进：

```text
download_started -> download_completed -> sha_command_completed -> sha_matched
-> chmod_completed -> version_executed -> version_matched
```

- `completed_stages` 必须是上面固定列表的精确有序前缀；空列表合法，只表示尚未开始安全步骤。
- `last_reached_stage` 是前缀最后一项；空前缀时为 `null`。
- `next_expected_stage` 是前缀之后紧邻的 stage；七阶段全部完成时为 `null`。
- 重复、跳级、回退、未知 stage、完成后继续推进均 fail closed 为 `invalid_stage_transition`，并且不能把调用方原始输入写入 artifact。

阶段语义：

1. `download_started`：本地 download stub 调用前已记录。
2. `download_completed`：本地 fixture 已成功落入受控临时目录。
3. `sha_command_completed`：本地 SHA 计算成功且结果符合 64 位小写十六进制形状。
4. `sha_matched`：实际摘要与 metadata 摘要完成常量时间匹配。
5. `chmod_completed`：临时 fixture 权限调整成功。
6. `version_executed`：受控 version stub 成功返回。
7. `version_matched`：version 输出包含 metadata version。

## 3. 字段合同

所有字段均为必填。实现必须从白名单构造完整对象，不能合并调用方字典、命令上下文或异常对象。

| 字段 | 类型 | 成功值 | fail-closed 默认值/语义 |
| --- | --- | --- | --- |
| `schema` | string | `trashbot.o5.provider_runtime_preflight_stage_diagnostics.v1` | 同成功值 |
| `provider_runtime_preflight_status` | string | `passed_offline_dry_gate` | `blocked_offline_dry_gate` |
| `completed_stages` | array[string] | 完整七阶段 | 已安全到达的有序前缀；合同输入非法时为空 |
| `last_reached_stage` | string or null | `version_matched` | 前缀末项；空前缀为 `null` |
| `next_expected_stage` | string or null | `null` | 前缀之后的紧邻 stage |
| `failure_reason` | string or null | `null` | 下节固定安全枚举之一 |
| `proof_boundary` | string | `software_proof_o5_provider_runtime_preflight_stage_diagnostics_offline_only` | 同成功值 |
| `official_provenance_contract_checked` | boolean | `true` | metadata/runner 前置合同失败时为 `false` |
| `network_access_attempted` | boolean | `false` | 固定 `false` |
| `ssh_attempted` | boolean | `false` | 固定 `false` |
| `tunnel_start_attempt_count` | integer | `0` | 固定 `0` |
| `public_capture_count` | integer | `0` | 固定 `0` |
| `public_probe_attempt_count` | integer | `0` | 固定 `0` |
| `current_run_artifact_delta` | boolean | `false` | 固定 `false` |
| `external_artifact_delta` | boolean | `false` | 固定 `false` |
| `live_control_delta` | boolean | `false` | 固定 `false` |
| `user_action_delta` | boolean | `false` | 固定 `false` |
| `production_ready` | boolean | `false` | 固定 `false` |
| `mission_objective_0_satisfied` | boolean | `false` | 固定 `false` |
| `route_execution_success` | boolean | `false` | 固定 `false` |
| `delivery_success` | boolean | `false` | 固定 `false` |
| `hil_pass` | boolean | `false` | 固定 `false` |
| `safe_to_control` | boolean | `false` | 固定 `false` |

`passed_offline_dry_gate` 只有在 metadata 合同已检查、七阶段完整且 `failure_reason=null` 时成立。其他组合必须输出 `blocked_offline_dry_gate`。

## 4. Failure enum 与允许前缀

| `failure_reason` | 允许的 `completed_stages` | 含义 |
| --- | --- | --- |
| `download_failed` | `download_started` | 本地 download stub 未完成 |
| `sha_command_failed` | 到 `download_completed` | SHA 计算失败或输出形状非法 |
| `sha_mismatch` | 到 `sha_command_completed` | SHA 计算完成但比对不匹配；不得进入 chmod/version |
| `chmod_failed` | 到 `sha_matched` | SHA 已匹配但权限调整失败 |
| `version_execution_failed` | 到 `chmod_completed` | version stub 未成功返回 |
| `version_mismatch` | 到 `version_executed` | version 已执行但内容不匹配；不得标记 `version_matched` |
| `invalid_stage_transition` | 通常为空；非法内部转换时为最后安全前缀 | metadata、runner 或阶段转换不满足合同 |

失败原因不得拼接 Python 异常、exit 文本或任何原始输入。调用方只能依赖上述枚举与阶段前缀定位失败边界。

## 5. Metadata 与本地 runner 合同

metadata 必须同时满足：provider 精确为 Cloudflare、version 符合年月版本形状、architecture 精确为 ARM64、asset name 精确为 standalone ARM64 名称、asset reference 精确符合官方 GitHub HTTPS owner/prefix 和 version/name 组合、digest 符合 `sha256:<64hex>` 形状。

reference 与 digest 只允许在进程内参与合同检查，不能进入 primary artifact。runner 必须是实现提供的 `LocalFixtureRunner`，root 必须位于系统临时目录；所有文件操作都要再次验证没有逃逸 root。runner 不启动 shell、不执行 fixture 二进制、不读取环境 credential，也没有 SSH、SCP、HTTP、tunnel、relay、proxy 或 public probe 能力。

稳定调用接口：

```python
run_provider_runtime_preflight(release_metadata, runner) -> dict
advance_stage(completed_stages, stage) -> tuple[str, ...]
build_artifact(completed_stages, failure_reason, official_provenance_contract_checked) -> dict
```

CLI 仅允许：

```bash
python3 provider_runtime_preflight_stage_diagnostics.py \
  --offline-dry-gate \
  --output provider-runtime-preflight-dry-gate.json
```

CLI 不提供 SSH target、public URL、tunnel、relay、proxy 或 robot control 参数。

## 6. 脱敏白名单与禁止字段

artifact 只能包含第 3 节字段。不得保存 raw URL、hostname、credential/token、authorization、checksum 原文、digest 原文、stderr/stdout、shell command、绝对路径、header/body、response body、tunnel log 或 public URL；也不得保存 fixture/version 命令的原始输出。

失败处理只能选择固定 `failure_reason`。禁止将异常字符串、runner 输入、metadata 值或路径插入 status、stage、reason 或新增字段。

## 7. Offline-only 禁止边界

- 不得 SSH/live，不得执行上一 sprint 的 live helper。
- 不得启动 tunnel 或 cloudflared daemon，不得生成 public URL。
- 不得公网 capture/probe，不得发 TLS/GET/HEAD/negative matrix 请求。
- 不得启动 relay/proxy，不得读写 production DB/queue/worker/OSS/CDN。
- 不得执行 command/task/archive write、`/cmd_vel`、`/api/base/manual`、UART、route、delivery、HIL 或任何 robot control。

即使 dry gate 全部通过，`current_run_artifact_delta`、`external_artifact_delta`、`live_control_delta` 与 `user_action_delta` 仍固定为 `false`，且不得据此上调 O5 或归档 KR。
