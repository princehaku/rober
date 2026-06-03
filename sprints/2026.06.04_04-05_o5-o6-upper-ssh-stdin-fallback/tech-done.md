# O5/O6 上位机 SSH stdin fallback Micro Sprint

## sprint_type

micro

## 实际改动

- 更新 `pc-tools/workstation/scripts/o5-o6-upper-ssh-collector.mjs`：
  - 保留原有 `installed_script` 路径：远端存在 `cloud-relay/scripts/o5_o6_external_live_probe.py` 时，继续通过 SSH 执行已安装 probe。
  - 新增 `stdin_fallback`：当远端 `remote_root` 可进入但缺 probe 脚本时，collector 自动把 PC 本地 `cloud-relay/scripts/o5_o6_external_live_probe.py` 通过 SSH stdin 喂给 `python3 - --once-json` 执行。
  - fallback 不 scp、不写远端文件、不持久修改 `/root/rober`；仍只允许 GET allowlist，不 POST、不访问 `/robots/*`、不访问 `/cmd_vel`、不读硬件、不发送控制命令、不把 bearer/token 放入 CLI/SSH args/artifact。
  - `ssh_collection` 新增并落盘 `execution_mode`、`attempted_execution_modes`、`fallback_used`、`fallback_reason`、`remote_exit_code`、`stdin_fallback_supported`、`stdin_fallback_remote_write=false`。
  - Python probe 若输出合法 `trashbot.o5_o6.external_live_probe.v1` JSON，即使 exit code 为 2（`probe_status=fail_closed`），collector 也会保留为 `ssh_collection.status=collected`，避免丢失真实 fail-closed 材料。
- 更新 `pc-tools/workstation/test/o5o6UpperSshCollector.test.ts`：
  - 覆盖 dry-run 展示 stdin fallback 计划但不写 artifact。
  - 覆盖远端缺 probe 脚本时自动走 stdin fallback，并确认 stdin 不包含测试 token。
  - 覆盖 stdin fallback 自身失败时写结构化 blocked artifact 和 operator `next_action`。
- 更新 `docs/interfaces/real_material_acceptance_queue.md`：
  - 记录 `pc_upper_ssh_collector` 的 `installed_script` / `stdin_fallback` 两种执行模式。
  - 记录新增 artifact 字段、fallback 安全边界，以及 2026-06-04 04-05 的 stdin fallback 更新口径。
- 更新 live artifact：
  - `pc-tools/workstation/.workstation-runtime/o5-o6-external-live-probe.json` 已由真实 SSH collector 重采，当前为 `stdin_fallback` 采集到的 fail-closed artifact。

## 验证结果

1. Targeted collector tests：
   - 命令：`cd pc-tools/workstation && npm test -- --run test/o5o6UpperSshCollector.test.ts`
   - 结果：通过。
   - 关键输出：`Test Files 1 passed (1)`，`Tests 5 passed (5)`。
2. Acceptance/catalog tests：
   - 命令：`cd pc-tools/workstation && npm test -- --run test/catalog.test.ts`
   - 结果：通过。
   - 关键输出：`Test Files 1 passed (1)`，`Tests 64 passed (64)`。
3. Lint：
   - 命令：`cd pc-tools/workstation && npm run lint`
   - 结果：通过，`eslint .` exit code 0。
4. 真实 SSH collector：
   - 命令：`cd pc-tools/workstation && npm run o5o6:upper-ssh-collector -- --ssh-target root@192.168.1.11 --ssh-port 37878 --pc-base-url http://127.0.0.1:8787 --timeout-seconds 8 --probe-timeout-ms 2500`
   - 结果：exit code 2，但已按验收口径写入结构化 fail-closed artifact；没有卡住。
   - 关键输出：`probe_status=fail_closed`、`ssh_collection.status=collected`、`ssh_collection.execution_mode=stdin_fallback`、`attempted_execution_modes=["installed_script","stdin_fallback"]`、`fallback_reason=remote_repo_present_but_probe_script_missing`、`remote_exit_code=2`、`stdin_fallback_remote_write=false`。
   - 当前 blocked reasons：`base_url_not_configured`、`bad_json`、`http_405`、`schema_mismatch`、`remote_bearer_token_absent`、`cloud_base_url_not_configured`。
5. Dry-run safety：
   - 命令：`node pc-tools/workstation/scripts/o5-o6-upper-ssh-collector.mjs --dry-run --ssh-target root@192.168.1.11 --ssh-port 37878 --cloud-base-url https://example.invalid --pc-base-url http://127.0.0.1:8787`
   - 结果：通过，exit code 0。
   - 关键输出：`artifact_written=false`、`ssh_command.contains_bearer_token=false`、`stdin_fallback.contains_bearer_token=false`、`stdin_fallback.remote_file_write_executed=false`、`no_post=true`、`no_robot_control=true`、`no_hardware_read=true`。
6. Whitespace/scope：
   - 命令：`git diff --check`
   - 结果：通过，无输出。

## 新 artifact 关键字段

```json
{
  "probe_status": "fail_closed",
  "blocked_reasons": [
    "base_url_not_configured",
    "bad_json",
    "http_405",
    "schema_mismatch",
    "remote_bearer_token_absent",
    "cloud_base_url_not_configured"
  ],
  "ssh_collection": {
    "status": "collected",
    "execution_mode": "stdin_fallback",
    "attempted_execution_modes": ["installed_script", "stdin_fallback"],
    "fallback_used": true,
    "fallback_reason": "remote_repo_present_but_probe_script_missing",
    "remote_exit_code": 2,
    "stdin_fallback_remote_write": false
  },
  "safe_to_control": false,
  "sends_commands": false,
  "reads_hardware": false,
  "robot_control_executed": false
}
```

## 用户旅程变化和触点收益

- Operator 不再因为上位机 `/root/rober` 缺 `cloud-relay/scripts/o5_o6_external_live_probe.py` 而停在“同步脚本”这一步。
- PC collector 可以在不写远端、不扩大控制面的前提下，把本地只读 probe 临时送到上位机运行，直接形成 acceptance queue 可消费的真实 SSH 采集 artifact。
- 失败原因从上一轮的 `remote_repo_present_but_probe_script_missing` 前移到更真实的 O5/O6 live material 缺口：cloud base URL 未配置、远端 bearer absent、PC aggregate HTTP/schema 未满足。

## Product/OKR 收口

- 用户价值和产品北极星：本轮降低 Operator 采集 O5/O6 真实材料的门槛，让普通用户侧云中转/云后端闭环继续向“可回放 live artifact”推进；北极星仍是手机用户交付垃圾后，机器人经云端可观测、可回放、可运营地完成送达。
- OKR 映射和方向判断：映射 O5 云中转控制面、O6 云端核心后端；方向继续。`remote_repo_present_but_probe_script_missing` 已被 `stdin_fallback` 绕过，说明采集链路有进展，但 `probe_status=fail_closed` 且 blocked reasons 转为 `base_url_not_configured`、`bad_json`、`http_405`、`schema_mismatch`、`remote_bearer_token_absent`、`cloud_base_url_not_configured`，不满足 accepted live material。
- KR 更新：O5/O6 仍为约 96%，不涨分，不做已完成 KR 历史归档；本轮只把当前推进抓手更新为“stdin fallback 后继续采 accepted live artifact”。
- 本轮核心抓手：保留 `pc_upper_ssh_collector` 作为 O5/O6 真实材料采集入口，优先解决 cloud base URL、远端 bearer token、上位机到 PC/云端可达 base URL、HTTP method 和 schema contract。
- 需要做什么：下一轮由 Full-Stack 继续闭环，配置真实 `ROBER_O5_O6_EXTERNAL_PROBE_CLOUD_BASE_URL` / bearer 环境，避免远端 loopback 误指 PC 本机，并让 external probe 产出 queue 可判定 accepted 的 live artifact。
- 优先级和验收口径：当前最高优先级仍是 O5/O6 -> O1 -> O7；验收口径是至少一条公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、OSS/CDN live traffic、真实 phone/browser 或真实上车数据链的可回放 accepted artifact。fail-closed、runbook、只读 readback、状态面继续不涨分。
- 对应责任 Engineer：User Touchpoint Full-Stack Engineer 主责；Robot Software Engineer 只在 robot command/ACK 合同或 8787/上位机接口事实需要复核时配合。
- 风险、阻塞和证据链缺口：缺真实 cloud base URL、远端 bearer token、正确可达 base URL、HTTP/schema contract、production DB/queue、OSS/CDN live traffic、真实 phone/browser、真实 4G/SIM、真实上车数据和生产 archive/query 回放。
- 已完成 KR 历史记录：无新增完成 KR；`stdin_fallback` 是采集入口能力，不是 O5/O6 accepted live material，剩余风险是不应被误写成真实生产云或真实数据闭环完成。
- 需要创建或更新的 sprint 文档：本 micro sprint 已更新本 `tech-done.md`；`OKR.md` 仅更新当前最高优先级抓手，不调整百分比；不重复更新 `docs/interfaces/real_material_acceptance_queue.md`。

## 接口影响

- `trashbot.o5_o6.external_live_probe.v1` 顶层 schema 不变，acceptance queue 可继续读取同一 artifact。
- `ssh_collection` 增加字段：
  - `execution_mode`
  - `attempted_execution_modes`
  - `fallback_used`
  - `fallback_reason`
  - `remote_exit_code`
  - `stdin_fallback_supported`
  - `stdin_fallback_remote_write`
- `buildDryRunResult()` 增加 `stdin_fallback` 计划字段，用于 dry-run 安全核对。

## 前后端/ROS2 联调结果

- 本轮只涉及 PC workstation collector、acceptance queue 文档和真实 SSH 到上位机的只读采集。
- 未接触 ROS2 topic/service/action、硬件串口、Nav2、WAVE ROVER 或真实机器人控制。
- 真实 SSH 已触达 `root@192.168.1.11 -p 37878`，并在远端通过 `python3 -` 执行本地 probe 源；远端未写文件。

## 剩余风险

- 当前 artifact 仍是 fail-closed，不是 O5/O6 accepted live material；不能用于 OKR 涨分。
- 未配置 `--cloud-base-url` / `ROBER_O5_O6_EXTERNAL_PROBE_CLOUD_BASE_URL`，因此 `cloud_base_url_not_configured` 仍然存在。
- 远端运行环境未提供 bearer token，`remote_bearer_token_absent` 仍然存在。
- 远端视角访问 `http://127.0.0.1:8787/api/o5-o6/cloud-relay-health` 返回不满足 contract 的结果，当前表现为 `bad_json`、`http_405`、`schema_mismatch`；需要后续确认上位机到 PC workstation 的可达 base URL，不应默认使用远端 loopback 指向 PC。
- 未验证真实公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、OSS/CDN live traffic、真实 phone/browser、真实上车数据或生产 archive/query 回放。
