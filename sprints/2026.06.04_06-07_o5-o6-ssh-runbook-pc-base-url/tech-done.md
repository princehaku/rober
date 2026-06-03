# O5/O6 SSH Runbook PC Base URL Micro Sprint

## sprint_type

micro

## 本轮目标

修复 `GET /api/real-material/acceptance` 暴露给 operator 的 O5/O6 collection runbook：PC 侧 SSH collector 示例不能继续展示 `--pc-base-url http://127.0.0.1:8787`，必须展示上位机可达的 PC workstation 地址 `--pc-base-url http://<pc-workstation-host>:8787`。本轮不 SSH、不联网、不 POST、不访问 `/robots/*` 或 `/cmd_vel`，不读硬件，不发送 robot command。

## 实际改动

- `pc-tools/workstation/src/server/realMaterialAcceptance.ts`
  - 修正 `collection_runbook.suggested_commands[]` 中 `pc_upper_ssh_collector` 的 API-facing recipe，改为 `--pc-base-url http://<pc-workstation-host>:8787`。
  - 在 `collection_runbook.collection_paths[]` 中补齐第三条结构化路径 `pc_upper_ssh_collector`，包含 SSH target/port、PC base URL、cloud base URL、远端 bearer token 环境、artifact 写回方式、成功门槛和安全边界。
  - 保留 PC workstation 本地 Node path 的 `127.0.0.1:8787`，因为该路径运行在 PC 本机；只禁止上位机 SSH path 使用远端 loopback。
- `pc-tools/workstation/test/catalog.test.ts`
  - 增加 regression assertion，确认 SSH collector `suggested_commands[2]` 和结构化 `collection_paths[]` command 都包含 `http://<pc-workstation-host>:8787`。
  - 增加 assertion，确认 SSH collector command 不包含 `--pc-base-url http://127.0.0.1:8787`。
  - 将 collection path id 期望从两条扩展为三条：`pc_node_npm`、`upper_computer_python_stdlib`、`pc_upper_ssh_collector`。
- `docs/interfaces/real_material_acceptance_queue.md`
  - 追加 2026-06-04 06-07 记录，明确 acceptance API runbook 的 SSH collector 示例不得展示远端 loopback。
- `OKR.md`
  - 追加本轮当前最高优先级抓手说明，不调整 O5/O6 百分比。
- `sprints/2026.06.04_06-07_o5-o6-ssh-runbook-pc-base-url/tech-done.md`
  - 新增本 micro sprint 留档。

## 接口影响

- `GET /api/real-material/acceptance` 的顶层 schema 不变。
- O5/O6 `collection_runbook.suggested_commands[]` 中，`pc_upper_ssh_collector` 示例现在要求 `--pc-base-url http://<pc-workstation-host>:8787`。
- O5/O6 `collection_runbook.collection_paths[]` 从两条结构化路径扩展为三条，新增：
  - `id=pc_upper_ssh_collector`
  - `runtime=node_ssh`
  - `host_role=pc_to_upper_computer`
  - `artifact_write_mode=writes_output_file`
- 该变更只影响 operator-facing recipe 和 acceptance queue 展示，不执行 collector，不改变 robot command/ACK 合同。

## 用户旅程变化和触点收益

- Operator 在 PC 上位机采集 runbook 里能直接看到正确的 PC workstation 可达地址占位符，不会按 API 示例让上位机访问自己的 `127.0.0.1:8787`。
- 失败恢复路径更明确：若未配置上位机可达 PC base URL，应补 `--pc-base-url http://<pc-workstation-host>:8787` 或 `ROBER_O5_O6_EXTERNAL_PROBE_PC_BASE_URL`，而不是排查误导性的 HTTP/schema 现象。
- PC UI 若展示结构化 `collection_paths[]`，现在也能展示 SSH collector，而不是只靠 legacy `suggested_commands[]`。

## 验证结果

1. Catalog regression test
   - 命令：`cd pc-tools/workstation && npm test -- --run test/catalog.test.ts`
   - 结果：通过，exit code 0。
   - 关键输出：`Test Files 1 passed (1)`，`Tests 64 passed (64)`。

2. Lint
   - 命令：`cd pc-tools/workstation && npm run lint`
   - 结果：通过，exit code 0。
   - 关键输出：`eslint .` 无报错输出。

3. Diff hygiene
   - 命令：`git diff --check -- pc-tools/workstation/src/server/realMaterialAcceptance.ts pc-tools/workstation/test/catalog.test.ts docs/interfaces/real_material_acceptance_queue.md OKR.md sprints/2026.06.04_06-07_o5-o6-ssh-runbook-pc-base-url/tech-done.md`
   - 结果：通过，exit code 0。
   - 关键输出：无输出。

## 失败定位

- 本轮验收未出现新的测试或 lint 失败。
- regression assertion 覆盖旧风险：API-facing `suggested_commands[]` 和结构化 `collection_paths[]` 都必须包含 `--pc-base-url http://<pc-workstation-host>:8787`，且不得包含 SSH collector 的远端 loopback 示例 `--pc-base-url http://127.0.0.1:8787`。

## 前后端 / ROS2 联调结果

- 本轮只修改 PC workstation acceptance API runbook、测试、接口文档、OKR 抓手和 sprint 留档。
- 未访问 SSH，未联网，未 POST，未访问 `/robots/*` 或 `/cmd_vel`，未读取硬件/串口/ROS2/Nav2/WAVE ROVER，未发送 robot command。
- 未做 ROS2 联调；该变更不涉及 ROS2 topic/service/action。

## Product / OKR 收口

- 映射 Objective：O5 云中转控制面、O6 云端核心后端。
- 本轮是否影响 OKR 百分比：不影响。
- 不涨分原因：本轮只修正采集入口 runbook 和 API 展示合同，没有 accepted live artifact；未证明真实公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、OSS/CDN live traffic、真实 phone/browser、真实上车数据或 production archive/query 回放。

## 剩余风险

- `pc-tools/workstation/src/shared/contracts.ts` 的 `RealMaterialCollectionPath` 字面量类型仍只枚举旧两条路径；该文件不在本轮允许范围内，因此本轮只保证运行时 API 输出和 catalog regression。后续若开放共享类型文件范围，应同步把 `pc_upper_ssh_collector`、`node_ssh` 和 `pc_to_upper_computer` 纳入类型契约。
- 仍需要 operator 提供真实上位机可达的 PC workstation host、有效 cloud base URL，以及上位机运行环境中的 bearer token。
- 本轮没有采集 accepted live artifact，不能证明真实生产云、真实蜂窝链路、真实 OSS/CDN、真实 PC/手机或完整上车数据闭环。
