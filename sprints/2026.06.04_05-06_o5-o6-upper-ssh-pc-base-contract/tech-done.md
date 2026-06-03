# O5/O6 upper SSH PC base URL contract Micro Sprint

## sprint_type

micro

## 本轮目标

接手上一位 Full-Stack 子 agent 的 INCOMPLETE 收尾，完成 `pc_upper_ssh_collector` 的 O5/O6 上位机 SSH 采集合同验收和 sprint 留档。本轮不扩大范围，不提交 git，不访问 `/robots/*`，不访问 `/cmd_vel`，不 POST，不读硬件，不发送 robot command。

## 实际改动

本次收尾新增文件：

- `sprints/2026.06.04_05-06_o5-o6-upper-ssh-pc-base-contract/tech-done.md`

本 micro sprint 已验收的既有改动：

- `pc-tools/workstation/scripts/o5-o6-upper-ssh-collector.mjs`
  - 移除上位机 SSH collector 的缺省 `http://127.0.0.1:8787` PC base URL。
  - 未显式传 `--pc-base-url` 或 `ROBER_O5_O6_EXTERNAL_PROBE_PC_BASE_URL` 时，远端 probe 收到空 PC base URL，artifact 追加 `pc_base_url_not_configured_for_upper_ssh`。
  - `dry-run` 新增 `pc_base_url_contract`，明确 `configured_for_upper_ssh=false`、source、blocked reason 和 operator next action。
  - 真实 SSH 收集路径继续支持 `installed_script` 与 `stdin_fallback`，但 PC aggregate 在未配置 PC workstation 可达地址前保持 fail-closed。
- `pc-tools/workstation/test/o5o6UpperSshCollector.test.ts`
  - 新增未配置 PC base URL 时的 dry-run 和 artifact 合同覆盖。
  - 成功/fallback 测试显式传入 `http://192.168.1.50:8787`，避免测试路径继续隐含远端 loopback。
- `docs/interfaces/real_material_acceptance_queue.md`
  - 记录上位机 SSH collector 的 PC base URL 合同：operator 必须传上位机可达的 PC workstation 地址，不再默认使用 `127.0.0.1`。
  - 记录 `pc_base_url_not_configured_for_upper_ssh` blocked reason、operator next action 和安全边界。
- `OKR.md`
  - 更新当前最高优先级抓手说明：本轮只修正 O5/O6 真实材料采集入口合同，不调整 O5/O6 百分比。
- `pc-tools/workstation/.workstation-runtime/o5-o6-external-live-probe.json`
  - 已由真实 SSH collector 重写为结构化 fail-closed artifact。

## 验证结果

1. Targeted collector tests
   - 命令：`cd pc-tools/workstation && npm test -- --run test/o5o6UpperSshCollector.test.ts`
   - 结果：通过，exit code 0。
   - 关键输出：`Test Files 1 passed (1)`，`Tests 6 passed (6)`。

2. Acceptance/catalog tests
   - 命令：`cd pc-tools/workstation && npm test -- --run test/catalog.test.ts`
   - 结果：通过，exit code 0。
   - 关键输出：`Test Files 1 passed (1)`，`Tests 64 passed (64)`。

3. Lint
   - 命令：`cd pc-tools/workstation && npm run lint`
   - 结果：通过，exit code 0。
   - 关键输出：`eslint .` 无报错输出。

4. Dry-run safety / contract
   - 命令：`node pc-tools/workstation/scripts/o5-o6-upper-ssh-collector.mjs --dry-run --ssh-target root@192.168.1.11 --ssh-port 37878 --cloud-base-url https://example.invalid`
   - 结果：通过，exit code 0；不 SSH、不联网、不写 artifact。
   - 关键输出：
     - `artifact_written=false`
     - `ssh_command.args` 与 `stdin_fallback.ssh_args` 均包含 `--pc-base-url ''`
     - `pc_base_url_contract.configured_for_upper_ssh=false`
     - `pc_base_url_contract.blocked_reason=pc_base_url_not_configured_for_upper_ssh`
     - `safety_policy.no_post=true`
     - `safety_policy.no_robot_control=true`
     - `safety_policy.no_hardware_read=true`
     - `forbidden_paths=["/robots/*","/cmd_vel"]`

5. Real upper SSH collector
   - 命令：`cd pc-tools/workstation && npm run o5o6:upper-ssh-collector -- --ssh-target root@192.168.1.11 --ssh-port 37878 --timeout-seconds 8 --probe-timeout-ms 2500`
   - 结果：exit code 2，按验收口径可接受；已写结构化 fail-closed artifact。
   - 关键输出：
     - `probe_status=fail_closed`
     - `viewpoint=upper_computer_via_pc_ssh_readonly`
     - `pc_base_url=not_configured_for_upper_ssh`
     - `cloud_base_url=not_configured`
     - `token_status=absent`
     - `collector_execution_mode=stdin_fallback`
     - `ssh_collection.status=collected`
     - `ssh_collection.execution_mode=stdin_fallback`
     - `ssh_collection.fallback_reason=remote_repo_present_but_probe_script_missing`
     - `ssh_collection.remote_exit_code=2`
     - `ssh_collection.pc_base_url_configured_for_upper_ssh=false`
     - `ssh_collection.pc_base_url_source=absent`
     - `ssh_collection.stdin_fallback_remote_write=false`
     - `command_boundary.post_executed=false`
     - `command_boundary.robots_path_accessed=false`
     - `command_boundary.cmd_vel_accessed=false`
     - `command_boundary.hardware_read_executed=false`
     - `command_boundary.robot_control_executed=false`

6. Whitespace / diff hygiene
   - 命令：`git diff --check`
   - 结果：通过，无输出，exit code 0。

## 新 artifact 关键字段

```json
{
  "probe_status": "fail_closed",
  "pc_base_url": "not_configured_for_upper_ssh",
  "cloud_base_url": "not_configured",
  "token_status": "absent",
  "blocked_reasons": [
    "base_url_not_configured",
    "pc_base_url_not_configured_for_upper_ssh",
    "remote_bearer_token_absent",
    "cloud_base_url_not_configured"
  ],
  "endpoints": [
    {
      "name": "pc_aggregate",
      "failure_category": "pc_base_url_not_configured_for_upper_ssh",
      "blocked_reasons": [
        "pc_base_url_not_configured_for_upper_ssh",
        "base_url_not_configured"
      ]
    }
  ],
  "ssh_collection": {
    "status": "collected",
    "execution_mode": "stdin_fallback",
    "fallback_reason": "remote_repo_present_but_probe_script_missing",
    "pc_base_url_configured_for_upper_ssh": false,
    "pc_base_url_source": "absent",
    "stdin_fallback_remote_write": false
  },
  "safe_to_control": false,
  "sends_commands": false,
  "reads_hardware": false,
  "robot_control_executed": false
}
```

## 接口影响

- `trashbot.o5_o6.external_live_probe.v1` 顶层 schema 不变，acceptance queue 仍消费同一 artifact。
- `ssh_collection` 增加或稳定使用以下字段：
  - `pc_base_url_configured_for_upper_ssh`
  - `pc_base_url_source`
  - `pc_base_url_next_action`
- `dry-run` 输出增加 `pc_base_url_contract`，用于 operator 在不联网、不写 artifact 前确认上位机视角 PC base URL 是否已配置。
- 该接口变更只影响 O5/O6 真实材料采集合同和 blocked 分类，不改变 robot command/ACK 合同。

## 用户旅程变化和触点收益

- Operator 不会再被误导去让上位机访问 `http://127.0.0.1:8787` 并把上位机自身 loopback 当成 PC workstation。
- 失败原因从 `bad_json/http_405/schema_mismatch` 这类误导性 HTTP/schema 现象，收敛为真实可执行动作：配置上位机可达的 PC workstation base URL、cloud base URL 和远端 bearer token。
- PC 端真实材料采集入口保持 fail-closed、可回放、可被 acceptance queue 分类，不隐藏失败原因。

## 前后端 / ROS2 联调结果

- 本轮只涉及 PC workstation collector、acceptance queue 文档、OKR 当前抓手和上位机 SSH 只读采集 artifact。
- 未接触 ROS2 topic/service/action、硬件串口、WAVE ROVER、Nav2、`/cmd_vel` 或真实运动控制。
- 真实 SSH 到 `root@192.168.1.11 -p 37878` 可达，collector 通过 `stdin_fallback` 在远端一次性执行 Python stdlib probe；远端文件未写入，bearer/token 未通过 CLI、SSH args、stdin 或 artifact 暴露。

## Product / OKR 收口

- 映射 Objective：O5 云中转控制面、O6 云端核心后端。
- 当前 OKR 百分比：O5 约 96%，O6 约 96%。
- 本轮是否涨分：不涨。
- 不涨原因：本轮只修正真实材料采集入口的 PC base URL 合同，artifact 仍为 `probe_status=fail_closed`，且没有采到 accepted live material；未证明真实公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、OSS/CDN live traffic、真实 phone/browser、真实上车数据或生产 archive/query 回放。
- 下一步涨分门槛：显式配置 `--pc-base-url http://<pc-workstation-host>:8787` 或 `ROBER_O5_O6_EXTERNAL_PROBE_PC_BASE_URL`，配置有效 cloud base URL 和远端 bearer token，并采到 acceptance queue 可判定 accepted 的 live artifact。

## 失败定位

- 真实 SSH collector 的 exit code 2 是预期 fail-closed，不是测试失败。
- 当前 blocked reasons：
  - `base_url_not_configured`
  - `pc_base_url_not_configured_for_upper_ssh`
  - `remote_bearer_token_absent`
  - `cloud_base_url_not_configured`
- 当前 artifact 已不再出现上一轮误导性 `bad_json`、`http_405`、`schema_mismatch` blocked reasons。
- `remote_repo_present_but_probe_script_missing` 仍作为 `stdin_fallback` 的 fallback reason 存在，表示远端 repo 缺 probe 文件；collector 已用 stdin fallback 绕过该入口缺口，但这不等于 live material accepted。

## 剩余风险

- `pc-tools/workstation/.workstation-runtime/o5-o6-external-live-probe.json` 仍是 fail-closed artifact，不能用于 OKR 涨分。
- 需要 operator 提供上位机可达的 PC workstation base URL，不能用远端 `127.0.0.1` 假设 PC 可达。
- 需要配置真实 cloud base URL 和上位机远端环境里的 bearer token。
- 未验证 production DB/queue、OSS/CDN live traffic、真实公网 HTTPS/TLS、真实 4G/SIM、真实 phone/browser、真实上车数据或 archive/query 回放。
- 本轮没有提交 git，等待协调者统一提交。
