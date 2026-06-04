# 2026.06.04 08-09 O5/O6 Upper SSH Preflight Tech Done

## sprint_type

micro

## Owner

full-stack-software-engineer

## 本轮目标

继续推进 O5/O6 当前最低 OKR 的真实材料采集入口，不做真实底盘/硬件控制，不访问 `/cmd_vel`、`/robots/*` 控制路径，不读串口，只增强 PC->上位机 SSH collector 的 GET-only / metadata / preflight / fail-closed 合同。

本轮不产出 accepted live artifact，因此不提升 O5/O6 百分比。

## 实际改动

- `pc-tools/workstation/scripts/o5-o6-upper-ssh-collector.mjs`
  - 新增 `--ssh-command "ssh root@192.168.1.11 -p 37878"` 解析入口，operator 可直接粘贴上位机 SSH 入口；脚本只提取 target/port，不执行 shell 解析、不 SSH、不联网。
  - dry-run / artifact `ssh_collection.preflight` 新增 `trashbot.o5_o6.upper_ssh_collector_preflight.v1`，分类 `ssh_target`、`ssh_port`、`pc_base_url`、`cloud_base_url`、`remote_bearer_token`、`remote_root`、`remote_probe_script`。
  - `failure_classification[]` 明确区分 `pc_base_url_not_configured_for_upper_ssh`、`cloud_base_url_not_configured`、`remote_bearer_token_not_verified_by_pc_preflight`、`remote_repo_root_missing`、`remote_repo_present_but_probe_script_missing`、stdin fallback 失败等机器原因。
- `pc-tools/workstation/src/shared/contracts.ts`
  - `RealMaterialCollectionPath` 新增 `preflight_checks[]` 与 `failure_classification[]`，让 acceptance API/UI typed consumers 可断言预检合同。
- `pc-tools/workstation/src/server/realMaterialAcceptance.ts`
  - O5/O6 三条 collection path 同步暴露预检项和失败分类。
  - SSH collector runbook 示例改为 `--ssh-command "ssh <upper-ssh-target> -p <ssh-port>"`，API 不回显真实 IP/账号。
- `pc-tools/workstation/test/o5o6UpperSshCollector.test.ts`
  - 新增 SSH command 粘贴入口与 preflight fail-closed 分类测试。
- `pc-tools/workstation/test/catalog.test.ts`
  - 更新 real-material acceptance queue 合同断言，覆盖 `preflight_checks[]`、`failure_classification[]` 和脱敏 SSH command 示例。
- `docs/interfaces/real_material_acceptance_queue.md`
  - 同步 preflight/failure classification 字段、dry-run 示例和本轮 08-09 记录。
- `OKR.md`
  - 在当前最高优先级段记录本轮推进，但明确没有 accepted live artifact，不提升 O5/O6 百分比。

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

第一轮验证发现并已修复：

- catalog 测试发现 acceptance API 响应包含真实示例 IP `192.168.1.11`，违反脱敏合同；已改成 `<upper-ssh-target>` 占位符，collector 自身仍支持 operator 粘贴真实 SSH command。
- collector 单测误把安全策略中的 forbidden path 声明当成实际访问；已改为只断言 SSH argv 不包含 `/robots/` 或 `/cmd_vel`。

最终收口已继续通过：

```bash
cd pc-tools/workstation && npm run build
```

关键结果：`vite v7.3.3 building client environment for production...`，`✓ built in 2.25s`，server TypeScript build 退出码 0。

```bash
cd pc-tools/workstation && npm run lint
```

关键结果：ESLint 退出码 0，无输出错误。

```bash
git diff --check -- pc-tools/workstation docs/interfaces/real_material_acceptance_queue.md OKR.md sprints/2026.06.04_08-09_o5-o6-upper-ssh-preflight/tech-done.md
```

关键结果：退出码 0，无 whitespace error。

## 剩余风险

- 本轮只证明 workstation 软件合同和测试，不证明真实 SSH live collection、真实公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、OSS/CDN、真实 phone/browser 或真实上车数据。
- `remote_bearer_token` 在 PC preflight 中只能标为 remote runtime requirement；collector 不会也不应通过 PC CLI/SSH argv/stdin/artifact 验证或传递 token。
- `remote_root` / `remote_probe_script` 在 dry-run 中只标为 `requires_ssh_probe`；真实存在性仍需 operator 显式运行 collector 后由只读 SSH `cd`/`test -f` 分类。
- 本轮不访问硬件、不读串口、不访问 ROS2/Nav2、不发送机器人控制命令，因此不能作为 O1/O7 或真实运动证据。

## Product / OKR 收口核对

- 用户价值和北极星：本轮只降低 operator 从 PC 采集 O5/O6 真实材料的操作门槛，服务"普通手机用户只看结果、运营同学负责采集证据"的产品分工；不把 SSH 入口暴露成普通用户体验。
- sprint_type 判定：`micro` 成立，范围是 full-stack-software-engineer 单 owner 的 SSH collector preflight/failure classification 合同增强；`tech-done.md` 已包含实际改动、验证结果和剩余风险，不需要升级为 epic。
- OKR 映射和方向判断：O5/O6 继续，仍是当前最低完成度；本轮没有 accepted live artifact，O5/O6 保持约 96%，不因 runbook、dry-run、preflight 或 failure classification 增强涨分。
- KR 处理：本轮没有完成可归档 KR；`preflight_checks[]` 与 `failure_classification[]` 只作为下一轮采集真实公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、OSS/CDN、真实 phone/browser 或真实上车数据的前置抓手。
- 优先级和验收口径：下一步仍优先由 full-stack-software-engineer 继续采集 O5/O6 accepted live artifact；验收必须看到可回放 artifact，且不能只用 dry-run、blocked artifact 或只读摘要替代。
- 文档同步和边界：`OKR.md` 已记录本轮不涨分，`docs/interfaces/real_material_acceptance_queue.md` 已同步 operator runbook、`preflight_checks[]`、`failure_classification[]` 和 no POST/no `/robots/*`/no `/cmd_vel`/no hardware/no robot command 边界。
- 证据链缺口：仍缺真实 SSH live collection accepted artifact、真实生产云、公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、OSS/CDN live traffic、真实 phone/browser、真实上车数据和机器人控制闭环证据。
