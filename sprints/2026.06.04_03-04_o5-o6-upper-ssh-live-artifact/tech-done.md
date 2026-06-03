# O5/O6 上位机 SSH Live Artifact Micro Sprint

## sprint_type

micro

## 实际改动

- 真实执行 `pc_upper_ssh_collector` 连接 `root@192.168.1.11 -p 37878`，保持只读 GET probe 边界，不通过 CLI/SSH args 传 bearer token，不 POST、不访问 `/robots/*`、不访问 `/cmd_vel`、不读硬件。
- 更新 `pc-tools/workstation/scripts/o5-o6-upper-ssh-collector.mjs`：
  - 将远端 repo root 已存在但 probe 脚本缺失的 exit 42 细分为 `remote_repo_present_but_probe_script_missing`。
  - 在 `ssh_collection` 中新增 `next_action` 与 `remote_path_override_supported=true`，让 operator 直接知道应同步 `cloud-relay/scripts/o5_o6_external_live_probe.py`，或用 `--remote-root` / `--remote-script` 指向真实脚本位置。
- 更新 `pc-tools/workstation/src/server/realMaterialAcceptance.ts`：
  - O5/O6 blocked reason 优先展示 endpoint / collector 的机器原因，避免被 `tls_not_configured_not_accepted` 掩盖。
  - runbook suggested commands 增加脱敏的 PC SSH collector 入口，SSH target/port 用占位符，不向 UI/API 暴露真实 IP。
- 更新测试：
  - `pc-tools/workstation/test/o5o6UpperSshCollector.test.ts` 覆盖新的 script-missing blocker、next action 和 remote path override。
  - `pc-tools/workstation/test/catalog.test.ts` 覆盖 acceptance queue 显示 `remote_repo_present_but_probe_script_missing`，并保持 API 不泄漏真实 SSH target/IP。
- 更新 `docs/interfaces/real_material_acceptance_queue.md`，记录本轮真实 SSH 只读采集事实、阻塞分类和下一步。
- 保留安全脱敏 artifact：`pc-tools/workstation/.workstation-runtime/o5-o6-external-live-probe.json`。

## 真实 SSH collector 结果

- 结果：`blocked`，不是 `accepted`。
- artifact path：`pc-tools/workstation/.workstation-runtime/o5-o6-external-live-probe.json`。
- 关键 blocked reason：`remote_repo_present_but_probe_script_missing`。
- 只读路径探测结论：SSH 可达，远端 hostname 为上位机角色；`/root/rober` 存在，但主要是 `onboard/`、`docs/`、`scripts/`、`sprints/` 与历史 runtime，未发现 `cloud-relay/scripts/o5_o6_external_live_probe.py`。
- 远端修改：无。只执行 SSH 只读命令和目录/脚本存在性检查。

## 验证结果

1. 真实 collector：
   - 命令：`cd pc-tools/workstation && npm run o5o6:upper-ssh-collector -- --ssh-target root@192.168.1.11 --ssh-port 37878 --pc-base-url http://127.0.0.1:8787 --timeout-seconds 6 --probe-timeout-ms 2500`
   - 结果：exit code 2，写入 blocked artifact。
   - 关键输出：`probe_status=fail_closed`、`blocked_reasons=["remote_repo_present_but_probe_script_missing"]`、`ssh_collection.remote_path_override_supported=true`、`safe_to_control=false`、`sends_commands=false`、`reads_hardware=false`、`robot_control_executed=false`。
2. Acceptance 只读解析：
   - 命令：`TMPDIR=/tmp npx tsx -e 'import { buildRealMaterialAcceptance } from "./src/server/realMaterialAcceptance.ts"; ...'`
   - 结果：exit code 0。
   - 关键输出：`queue_status=action_required`、`summary.accepted=1`、`summary.blocked=2`、O5/O6 均 `status=blocked`、`blocking_reason=remote_repo_present_but_probe_script_missing`、artifact ref 为 `.workstation-runtime/o5-o6-external-live-probe.json`。
3. Targeted tests：
   - 命令：`cd pc-tools/workstation && npm test -- --run test/o5o6UpperSshCollector.test.ts`
   - 结果：通过，`Test Files 1 passed`，`Tests 4 passed`。
4. Acceptance parsing tests：
   - 命令：`cd pc-tools/workstation && npm test -- --run test/catalog.test.ts`
   - 结果：通过，`Test Files 1 passed`，`Tests 64 passed`。
   - 备注：首轮失败暴露 runbook 泄漏真实 `192.168.1.11`，已修正为 `<upper-ssh-target>` / `<ssh-port>` 占位符后复跑通过。
5. Lint：
   - 命令：`cd pc-tools/workstation && npm run lint`
   - 结果：通过，`eslint .` exit code 0。
6. Dry-run safety：
   - 命令：`node pc-tools/workstation/scripts/o5-o6-upper-ssh-collector.mjs --dry-run --ssh-target root@192.168.1.11 --ssh-port 37878 --cloud-base-url https://example.invalid --pc-base-url http://127.0.0.1:8787`
   - 结果：通过，`artifact_written=false`、`contains_bearer_token=false`、`no_post=true`、`no_robot_control=true`、`no_hardware_read=true`。
7. Whitespace/scope：
   - 命令：`git diff --check`
   - 结果：通过，无输出。

## OKR 口径

本轮针对当前最低完成度 O5/O6，推进了真实上位机 SSH 采集链路：SSH reachability 已观察到，blocked artifact 已能被 acceptance queue 直接消费，并且 operator 下一步已从“泛 TLS 未配置”收敛为“远端 repo 缺 external probe 脚本或路径 override”。

O5/O6 仍保持约 96%，本轮不更新 `OKR.md`。原因是 artifact 没有达到 accepted 条件：未观察到真实公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、OSS/CDN live traffic、真实 phone/browser、真实上车数据或生产 archive/query 回放。

## 剩余风险

- 上位机 `/root/rober` 当前缺 `cloud-relay/scripts/o5_o6_external_live_probe.py`，需要同步脚本或用 `--remote-root` / `--remote-script` 指向真实 probe 位置后重跑。
- 本轮未向远端配置 cloud base URL 或 bearer token；collector 仍只显示 `cloud_base_url=not_configured` 与 `token_status=absent`。
- `pc-tools/workstation/.workstation-runtime/o5-o6-external-live-probe.json` 是 blocked artifact，可作为 acceptance queue 材料，但不能作为 O5/O6 涨分证据。
- 未执行真实公网、4G/SIM、production DB/queue、OSS/CDN、真实 phone/browser 或机器人任务闭环验证。
