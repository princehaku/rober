# O5/O6 上位机 SSH Collector Micro Sprint

## sprint_type

micro

## 实际改动

- 新增 `pc-tools/workstation/scripts/o5-o6-upper-ssh-collector.mjs`：
  - PC workstation 侧通过 SSH 执行上位机 `cloud-relay/scripts/o5_o6_external_live_probe.py --once-json`。
  - 默认 SSH 入口为 `root@192.168.1.11 -p 37878`，默认远端仓库为 `/root/rober`，默认 artifact 写回 `.workstation-runtime/o5-o6-external-live-probe.json`。
  - 支持 `--ssh-target`、`--ssh-port`、`--remote-root`、`--remote-script`、`--pc-base-url`、`--cloud-base-url`、`--output`、`--timeout-seconds`、`--probe-timeout-ms` 和对应 env 覆盖。
  - `--dry-run` 只输出 SSH 命令计划与安全边界，不 SSH、不联网、不写 artifact。
  - 不通过 CLI 或 SSH args 传 bearer token；真实 token 只允许由上位机环境变量提供。
  - SSH 不可达、远端仓库缺失、远端 probe 缺失、远端 stdout 非 JSON、schema 不匹配时，写入结构化 `fail_closed` artifact，而不是无结构失败。
- 更新 `pc-tools/workstation/package.json`，新增 `npm run o5o6:upper-ssh-collector`。
- 新增 `pc-tools/workstation/test/o5o6UpperSshCollector.test.ts`，覆盖 SSH 命令构造、dry-run 安全边界、成功 artifact 写入、远端脚本缺失 blocked artifact。
- 更新 `docs/interfaces/real_material_acceptance_queue.md`，把 `pc_upper_ssh_collector` 纳入 O5/O6 collection path，并明确它写回 acceptance queue 已消费的默认 artifact。

## 验证结果

1. `cd pc-tools/workstation && npm test -- --run test/o5o6UpperSshCollector.test.ts`
   - 结果：通过，1 个 test file / 4 tests passed。
   - 覆盖：命令构造不含 bearer、不访问 `/robots/*`/`/cmd_vel`、dry-run 不写 artifact、成功远端 JSON 写回 artifact、远端脚本缺失写 structured blocked artifact。
2. `cd pc-tools/workstation && npm test -- --run`
   - 结果：通过，3 个 test files / 85 tests passed。
3. `cd pc-tools/workstation && npm run lint`
   - 结果：通过，`eslint .` exit code 0。
4. `node pc-tools/workstation/scripts/o5-o6-upper-ssh-collector.mjs --dry-run --ssh-target root@192.168.1.11 --ssh-port 37878 --cloud-base-url https://example.invalid --pc-base-url http://127.0.0.1:8787`
   - 结果：通过，exit code 0。
   - 关键输出：`schema=trashbot.o5_o6.upper_ssh_collector.v1`、`status=dry_run`、`artifact_written=false`、`contains_bearer_token=false`、`blocked_reasons=["dry_run_no_ssh_no_network_no_artifact"]`、`safe_to_control=false`、`sends_commands=false`、`reads_hardware=false`、`robot_control_executed=false`。

## 剩余风险

- 本 sprint 只交付可复跑采集入口和 structured artifact，不证明真实公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、OSS/CDN live traffic、真实 phone/browser 或真实上车数据。
- 真实涨分仍依赖上位机 SSH 实连、远端仓库/脚本存在、上位机环境变量配置 cloud base URL 与 bearer token，并拿到可被 acceptance queue 判定 accepted 的 artifact。
- collector 只运行 Python stdlib probe 的只读 GET allowlist；不 POST、不访问 `/robots/*`、不访问 `/cmd_vel`、不读取串口/ROS2/硬件、不发送机器人控制命令。

## OKR 口径

本 sprint 针对当前最低完成度 O5/O6 的真实材料入口，核心抓手是 `pc_upper_ssh_collector`
把上位机 external live probe 变成 PC workstation 可复跑采集动作。

Product/OKR 收口结论：O5/O6 继续约 96%，本轮不涨分。原因是截至实现完成前只交付
上位机 SSH collector 和 acceptance queue 采集入口，没有产生可计入涨分的真实生产材料：
真实公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、OSS/CDN live traffic、真实
phone/browser、真实上车数据和 accepted live artifact 均仍未完成。

下一步真正涨分的验收口径：用本 collector 完成 SSH 实连，在上位机真实 cloud base URL、
bearer token 环境变量和生产依赖配置到位后，采到可回放、可被 real material acceptance
queue 判定 accepted 的 live artifact；该 artifact 必须覆盖 O5 的公网/TLS/4G/queue/phone-browser
或 O6 的真实隧道/production DB/queue/OSS/推理/上车数据链之一。
