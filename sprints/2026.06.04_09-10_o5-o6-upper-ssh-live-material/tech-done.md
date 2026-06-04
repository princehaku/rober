# 2026.06.04 09-10 O5/O6 Upper SSH Live Material Tech Done

## sprint_type

micro

## Owner

full-stack-software-engineer

## 本轮目标

尝试从 PC workstation 通过 `ssh root@192.168.1.11 -p 37878` 采集 O5/O6 upper-computer 视角真实材料，优先追求 accepted live artifact；测试只作为护栏。

本轮保持只读安全边界：不 POST、不访问 `/robots/*`、不访问 `/cmd_vel`、不读串口/硬件、不发送 robot/base control 命令。

## 实际改动

- `pc-tools/workstation/.workstation-runtime/o5-o6-external-live-probe.json`
  - 运行真实 PC -> 上位机 SSH collector 后更新 runtime artifact。
  - artifact 为 `probe_status=fail_closed`，不是 accepted live material。
  - SSH collector `status=collected`，`execution_mode=stdin_fallback`，说明 SSH 可达、远端 repo root 可进入；默认 installed script 缺失后通过 stdin fallback 一次性运行本地 Python stdlib probe。
  - 阻塞分类落为 `base_url_not_configured`、`pc_base_url_not_configured_for_upper_ssh`、`remote_bearer_token_absent`、`cloud_base_url_not_configured`。
- `sprints/2026.06.04_09-10_o5-o6-upper-ssh-live-material/tech-done.md`
  - 记录本轮 collector 证据、验证结果、OKR 不涨分原因和剩余风险。

本轮未修改 collector、acceptance API、shared contract、Vue UI、接口文档、OKR 或 progress log；未发现会阻碍下一次真实采集的代码缺陷。

## 用户旅程变化和触点收益

- 对 operator 有收益：本轮证明上位机 SSH 入口可达，且 PC 侧 collector 的 stdin fallback 能在远端缺 installed probe script 时继续产生 fail-closed artifact。
- 对普通手机用户无直接 UI 变化：没有新增或更改前端操作入口。
- 对下一次真实采集的收益：下一步不用再优先排查 SSH 连通性，应优先准备上位机可达的 PC base URL、production cloud base URL 和上位机 runtime bearer token。

## 接口影响

- 无 API/schema/UI 合同变更。
- runtime artifact 仍遵循 `trashbot.o5_o6.external_live_probe.v1` 与 `trashbot.o5_o6.upper_ssh_collector.v1`。
- acceptance queue 可继续按现有规则读取 `.workstation-runtime/o5-o6-external-live-probe.json` 并分类为 blocked / not accepted。

## Collector 证据

执行命令：

```bash
cd pc-tools/workstation && node scripts/o5-o6-upper-ssh-collector.mjs --ssh-command "ssh root@192.168.1.11 -p 37878"
```

结果：退出码 `2`，artifact 已写入 `.workstation-runtime/o5-o6-external-live-probe.json`。

关键字段：

```json
{
  "probe_status": "fail_closed",
  "runner": "pc_upper_ssh_collector+python_stdlib",
  "collector_status": "collected",
  "execution_mode": "stdin_fallback",
  "fallback_used": true,
  "fallback_reason": "remote_repo_present_but_probe_script_missing",
  "blocked_reasons": [
    "base_url_not_configured",
    "pc_base_url_not_configured_for_upper_ssh",
    "remote_bearer_token_absent",
    "cloud_base_url_not_configured"
  ]
}
```

安全字段：

```json
{
  "safe_to_control": false,
  "sends_commands": false,
  "robot_control_executed": false,
  "reads_hardware": false,
  "post_executed": false,
  "robots_path_accessed": false,
  "cmd_vel_accessed": false,
  "hardware_read_executed": false
}
```

## 验证结果

已通过：

```bash
cd pc-tools/workstation && npm test -- --run test/o5o6UpperSshCollector.test.ts
```

关键结果：`Test Files 1 passed (1)`，`Tests 7 passed (7)`。

```bash
cd pc-tools/workstation && npm test -- --run test/catalog.test.ts
```

关键结果：`Test Files 1 passed (1)`，`Tests 64 passed (64)`。

```bash
cd pc-tools/workstation && npm run lint
```

关键结果：ESLint 退出码 0，无错误输出。

```bash
git diff --check -- pc-tools/workstation/.workstation-runtime/o5-o6-external-live-probe.json sprints/2026.06.04_09-10_o5-o6-upper-ssh-live-material/tech-done.md
```

关键结果：退出码 0，无 whitespace error。

未运行：

- `cd pc-tools/workstation && npm run build`：本轮没有改 TS/Vue/server contract，按本轮验收口径不强制运行。

## 失败定位

本轮失败不是代码缺陷，而是 accepted live material 所需配置未就绪：

- PC workstation 环境未观察到 `ROBER_O5_O6_EXTERNAL_PROBE_PC_BASE_URL` 或可替代 CLI `--pc-base-url`。
- PC workstation 环境未观察到 `ROBER_O5_O6_EXTERNAL_PROBE_CLOUD_BASE_URL` / `ROBER_CLOUD_RELAY_BASE_URL` 或可替代 CLI `--cloud-base-url`。
- collector 不通过 PC CLI/SSH argv/stdin 传 bearer token；远端 artifact 显示 `remote_bearer_token_absent`。
- 上位机默认 `cloud-relay/scripts/o5_o6_external_live_probe.py` installed script 缺失，但 stdin fallback 已工作，因此该项不是本轮阻塞主因。

## OKR 收口

O5/O6 不涨分，继续保持约 96%。

原因：本轮 artifact 是 `fail_closed` / blocked，不满足 OKR 对真实公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、OSS/CDN live traffic、真实 phone/browser 或真实上车数据链的 accepted live evidence 要求。

## 剩余风险

- 仍缺上位机可达的 PC workstation base URL，例如 `--pc-base-url http://<pc-workstation-host>:8787`。
- 仍缺 production cloud base URL，例如 `--cloud-base-url https://<production-cloud-base>`。
- 仍缺上位机 runtime 中配置的 `TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN` 或 `ROBER_CLOUD_RELAY_BEARER_TOKEN`；不得把 secret 写入命令行、日志、artifact 或文档。
- 本轮未证明公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、OSS/CDN、真实 phone/browser、真实机器人任务或真实上车数据。
- 本轮没有触碰硬件、串口、ROS2、Nav2 或底盘控制，因此不能作为 O1/O7 或真实运动材料。

## 完成前反思

- 需求是否满足：已尝试真实 SSH collector，并把真实 blocked 分类落到 runtime artifact 和 sprint 文档；没有伪造 accepted。
- 是否误改无关文件：本轮只应包含 runtime artifact 与本 sprint `tech-done.md`。
- 是否留下 TODO：没有新增代码 TODO。
- 验证缺口：未运行 build 是因为无 TS/Vue/server contract 改动；真实 accepted 采集仍依赖下一轮准备 PC/cloud URL 与远端 bearer。
