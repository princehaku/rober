# 2026.06.04 10-11 O5/O6 Upper SSH Installed Probe Tech Done

## sprint_type

micro

## Owner

full-stack-software-engineer

## 本轮目标

继续推进 O5/O6（约 96%）当前未完成的真实材料采集通路，但避免继续消费同一个纯 runbook/status blocker。按当前 OKR 口径，O5/O6 不是最低完成度 Objective；本轮目标只是把 `pc_upper_ssh_collector` 从远端缺 probe 脚本时只能 `stdin_fallback`，推进到可显式同步并运行上位机已安装 probe 脚本。

安全边界：只允许同步 `/root/rober/cloud-relay/scripts/o5_o6_external_live_probe.py` 这一份 probe 文件；不传 secret、不 POST、不访问 `/robots/*`、不访问 `/cmd_vel`、不读串口/ROS2/Nav2/硬件、不发送 robot/base control。

## 实际改动

- `pc-tools/workstation/scripts/o5-o6-upper-ssh-collector.mjs`
  - 新增显式 `--sync-remote-probe` / `--install-remote-probe` 入口。
  - dry-run 只输出同步计划、预检分类和安全边界，不 SSH、不写远端、不写 artifact。
  - verifier 修正后，live 模式只允许把本地 `cloud-relay/scripts/o5_o6_external_live_probe.py` 通过 SSH stdin 直接写到固定远端最终路径 `/root/rober/cloud-relay/scripts/o5_o6_external_live_probe.py`；不写临时文件、不创建远端目录、不运行 `py_compile`，避免 `.tmp` 或 `__pycache__` 让写入边界外溢。
  - artifact 新增 `remote_probe_sync`、`remote_probe_sync.exact_final_path_only=true` 和 `command_boundary.remote_write_scope=single_probe_script_only`，把最终 probe 文件写入和机器人控制动作严格区分。
  - 补充修正 top-level `viewpoint`：未同步时仍为 `upper_computer_via_pc_ssh_readonly`；同步成功后改为 `upper_computer_via_pc_ssh_probe_sync_then_readonly_probe`，避免把固定 probe 文件写入误标为纯只读。
- `pc-tools/workstation/test/o5o6UpperSshCollector.test.ts`
  - 增加同步 dry-run 测试，确认不 SSH、不写远端、不泄漏 token、不触碰控制路径。
  - 增加 sync 后走 `installed_script` 的采集测试，确认不再落 `remote_repo_present_but_probe_script_missing`。
  - 增加 `viewpoint` 断言：默认 installed script 保持只读视角；sync 成功必须暴露 `probe_sync_then_readonly_probe` 视角。
- `docs/interfaces/real_material_acceptance_queue.md`
  - 同步 O5/O6 acceptance queue 文档，记录 `sync_remote_probe` 模式、关键 artifact 字段、失败分类、dry-run 命令和安全边界。
  - 补充 `viewpoint` 字段语义，区分 readonly、sync attempt、sync success 三种 collector 视角。
- `pc-tools/workstation/.workstation-runtime/o5-o6-external-live-probe.json`
  - 真实 SSH collector 已写回最新 fail-closed runtime artifact。
  - 补正 artifact top-level `viewpoint=upper_computer_via_pc_ssh_probe_sync_then_readonly_probe`，与 `remote_probe_sync.status=synced` 和 `remote_write_scope=single_probe_script_only` 对齐。

## 用户旅程变化和触点收益

- operator 可以用一个显式命令把 PC 本地 probe 安装到上位机固定位置，再采集上位机视角 O5/O6 材料。
- 上一轮的 `remote_repo_present_but_probe_script_missing` 已被消除：当前 runtime artifact 显示 `collector_execution_mode=installed_script`，`remote_probe_sync.status=synced`。
- 普通手机用户无直接 UI 变化；本轮推进的是 O5/O6 真实材料采集通路。

## 接口影响

- 无 HTTP API/schema 破坏性变更。
- `trashbot.o5_o6.upper_ssh_collector.v1` artifact 新增同步相关字段：
  - `ssh_collection.remote_probe_sync.*`
  - `ssh_collection.remote_probe_sync.exact_final_path_only`
  - `ssh_collection.command_boundary.remote_file_write_attempted`
  - `ssh_collection.command_boundary.remote_file_write_executed`
  - `ssh_collection.command_boundary.remote_write_scope`
- `stdin_fallback` 仍保留，未显式传 `--sync-remote-probe` 时默认行为仍是 installed script -> stdin fallback。

## 验证结果

Full-Stack Engineer 已运行：

```bash
cd pc-tools/workstation && npm test -- --run test/o5o6UpperSshCollector.test.ts
```

补充 `viewpoint` 断言前，目标测试先复现失败：

```text
AssertionError: expected 'upper_computer_via_pc_ssh_readonly' to be 'upper_computer_via_pc_ssh_probe_sync_then_readonly_probe'
```

修复后重跑结果：退出码 0，`Test Files 1 passed (1)`，`Tests 9 passed (9)`，`Duration 18.05s`。

```bash
cd pc-tools/workstation && npm run lint
```

结果：退出码 0，无 ESLint error。

```bash
node scripts/o5-o6-upper-ssh-collector.mjs --dry-run --sync-remote-probe --ssh-command "ssh root@192.168.1.11 -p 37878" --cloud-base-url https://example.invalid
```

结果：退出码 0；输出包含 `artifact_written=false`、`ssh_executed=false`、`remote_file_write_executed=false`、`exact_final_path_only=true`、`remote_probe_sync_not_executed_dry_run`；`sync_remote_probe.ssh_args` 只包含 `test -d 'cloud-relay/scripts'`、`cat > 'cloud-relay/scripts/o5_o6_external_live_probe.py'`、`test -s 'cloud-relay/scripts/o5_o6_external_live_probe.py'`，不包含 `.tmp`、`py_compile` 或 `mkdir -p`。

```bash
ssh -o BatchMode=yes -o ConnectTimeout=8 -p 37878 root@192.168.1.11 python3 -
```

结果：退出码 0；仅按允许范围检查并清理 `/root/rober/cloud-relay/scripts/.o5_o6_external_live_probe.py.tmp` 与 `/root/rober/cloud-relay/scripts/__pycache__/o5_o6_external_live_probe.*.pyc`。清理输出：

```json
{
  "cleanup_scope": "o5_o6_probe_tmp_and_matching_pyc_only",
  "removed": [],
  "missing": [
    "/root/rober/cloud-relay/scripts/.o5_o6_external_live_probe.py.tmp"
  ],
  "skipped": []
}
```

```bash
node scripts/o5-o6-upper-ssh-collector.mjs --sync-remote-probe --ssh-command "ssh root@192.168.1.11 -p 37878"
```

结果：退出码 2；真实 SSH 可达，已同步 `/root/rober/cloud-relay/scripts/o5_o6_external_live_probe.py`，随后通过 `installed_script` 写回 fail-closed artifact。关键字段：

```json
{
  "probe_status": "fail_closed",
  "viewpoint": "upper_computer_via_pc_ssh_probe_sync_then_readonly_probe",
  "collector_execution_mode": "installed_script",
  "blocked_reasons": [
    "base_url_not_configured",
    "pc_base_url_not_configured_for_upper_ssh",
    "remote_bearer_token_absent",
    "cloud_base_url_not_configured"
  ],
  "remote_probe_sync": {
    "status": "synced",
    "remote_file_write_executed": true,
    "exact_final_path_only": true
  },
  "command_boundary": {
    "remote_file_write_attempted": true,
    "remote_file_write_executed": true,
    "remote_write_scope": "single_probe_script_only"
  }
}
```

远端复核：退出码 0；`tmp_exists=false`、`matching_pyc_count=0`，即同步后没有遗留 `.tmp` 或本脚本匹配的 `.pyc`。

```bash
git diff --check -- pc-tools/workstation/scripts/o5-o6-upper-ssh-collector.mjs pc-tools/workstation/test/o5o6UpperSshCollector.test.ts docs/interfaces/real_material_acceptance_queue.md pc-tools/workstation/.workstation-runtime/o5-o6-external-live-probe.json sprints/2026.06.04_10-11_o5-o6-upper-ssh-installed-probe/tech-done.md
```

结果：退出码 0，无 whitespace error。

## 失败定位

本轮已经消除 verifier 指出的写入边界 blocker，并保持远端 probe 缺失 blocker 消除状态；但没有产生 accepted live material。

剩余 blocker 是真实材料配置未就绪：

- 缺上位机可达的 PC workstation base URL：`pc_base_url_not_configured_for_upper_ssh`。
- 缺 production cloud base URL：`cloud_base_url_not_configured` / `base_url_not_configured`。
- 缺上位机 runtime bearer token：`remote_bearer_token_absent`。

## OKR 收口

O5/O6 不涨分，继续约 96%。

原因：本轮只把 SSH collector 从 fallback 通路推进到 installed probe 通路；artifact 仍是 `fail_closed`，没有证明公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、OSS/CDN live traffic、真实 phone/browser 或真实上车数据链。

## 剩余风险

- 仍需提供上位机可达的 `--pc-base-url http://<pc-workstation-host>:8787`。
- 仍需提供 production `--cloud-base-url https://<production-cloud-base>`。
- 仍需在上位机运行环境配置 `TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN` 或 `ROBER_CLOUD_RELAY_BEARER_TOKEN`，不得写入 CLI、日志、artifact 或文档。
- 本轮远端写入仅限最终 probe 脚本路径，不证明任何机器人运动、硬件、ROS2、Nav2、WAVE ROVER、底盘 ACK 或任务闭环。

## 完成前反思

- 需求是否满足：已按 O5/O6 当前未完成验收项推进实际采集通路，避免继续只写 runbook；真实远端 probe 缺失 blocker 已解除，verifier 指出的 temp/pycache 写入边界已改为最终路径直写。
- 是否误改无关文件：最终应只提交 O5/O6 collector、collector test、接口文档、runtime artifact 和本 sprint 文档；其他 dirty 文件保持不动。
- 是否留下 TODO：没有新增代码 TODO。
- 验证缺口：accepted live material 还依赖 PC/cloud URL 与远端 token；未进行真实生产 HTTPS/TLS、4G/SIM、production DB/queue、OSS/CDN 或真实 phone/browser 验收。
