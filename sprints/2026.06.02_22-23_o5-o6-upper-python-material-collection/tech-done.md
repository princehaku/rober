# O5/O6 Upper Python Material Collection Micro Sprint

## sprint_type

micro

## 实际改动

- `GET /api/real-material/acceptance` 的 O5/O6 `collection_runbook` 新增结构化 `collection_paths[]`，同时暴露 `pc_node_npm` 与 `upper_computer_python_stdlib` 两条真实材料采集路径。
- PC Node 路径继续使用 `pc-tools/workstation/scripts/o5-o6-external-live-probe.mjs`；上位机路径明确使用 `cloud-relay/scripts/o5_o6_external_live_probe.py --once-json`，只依赖 Python stdlib。
- UI `真实材料验收队列` 现在展示每条采集路径的 runtime、host role、required env、artifact 回传方式、命令和成功门槛，不提供执行按钮。
- 文档同步更新 `docs/interfaces/real_material_acceptance_queue.md`、`docs/product/pc_tools_workstation.md` 和 `docs/interfaces/o6_cloud_archive_core_api.md`，明确 GET-only、no POST、no `/robots/*`、no hardware read、fail-closed 边界。

## 验证结果

执行时间：2026-06-02 23:20:56 CST。已执行：

- `python3 -m py_compile cloud-relay/scripts/o5_o6_external_live_probe.py`：通过。
- `PYTHONDONTWRITEBYTECODE=1 python3 cloud-relay/scripts/o5_o6_external_live_probe.py --once-json || true`：通过并按预期 fail-closed；关键字段为 `schema=trashbot.o5_o6.external_live_probe.v1`、`runner=python_stdlib`、`probe_status=fail_closed`、`pc_base_url=not_configured`、`cloud_base_url=not_configured`、`token_status=absent`、3 个 endpoint 全部 `failure_category=base_url_not_configured`、`safe_to_control=false`、`sends_commands=false`、`reads_hardware=false`、`robot_control_executed=false`、`delivery_success=false`、`method_allowlist=["GET"]`、`forbidden_paths=["/robots/*","/cmd_vel"]`、`no_post=true`、`no_robot_control=true`、`no_hardware_read=true`。
- `cd pc-tools/workstation && npm run test`：通过，`Test Files 2 passed (2)`，`Tests 63 passed (63)`。
- `cd pc-tools/workstation && npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成；Vite 输出 `35 modules transformed`、`built in 2.55s`。
- `cd pc-tools/workstation && npm run lint`：退出码 0；有 2 个范围外既有样式 warning，位置为 `src/components/O7LiveOperatorPanel.vue:126` 和 `:136`，均为 `vue/html-self-closing`，本轮未触碰该文件。
- `git diff --check -- pc-tools/workstation/src/server/realMaterialAcceptance.ts pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/src/components/RealMaterialAcceptancePanel.vue pc-tools/workstation/test/App.test.ts pc-tools/workstation/test/catalog.test.ts docs/interfaces/real_material_acceptance_queue.md docs/product/pc_tools_workstation.md docs/interfaces/o6_cloud_archive_core_api.md sprints/2026.06.02_22-23_o5-o6-upper-python-material-collection/tech-done.md`：通过。

验证中额外自检：`py_compile` 生成的 `cloud-relay/scripts/__pycache__/o5_o6_external_live_probe.cpython-312.pyc` 已清理，避免留下范围外生成物。

## OKR 口径

本轮只推进 O5/O6 真实材料采集链的 operator 可执行入口和 contract 可见性。没有采集到新的真实 production/cloud accepted artifact，因此 O5/O6 百分比不提升，不修改 `OKR.md`。

## 剩余风险

- 上位机 Python runner 的本地 fail-closed baseline 只能证明脚本可执行和未配置环境时安全退出，不证明真实公网 HTTPS、真实 4G/SIM、production DB/queue、OSS/CDN 或上车数据。
- 真实 O5/O6 accepted 仍需要 operator 在配置生产 cloud base URL、PC base URL 和 bearer token 后运行 Node 或 Python collector，并把 artifact 放入 `.workstation-runtime/o5-o6-external-live-probe.json` 或通过 `ROBER_O5_O6_EXTERNAL_PROBE_ARTIFACT` 指向。
- 本轮发现并保留了范围外并发 dirty scope；这些文件不纳入本 micro sprint 验收，也未由本轮修改或回滚。
