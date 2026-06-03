# O5/O6 collection path shared contract micro sprint

## Sprint 类型

- sprint_type: micro
- 时间：2026-06-04 07-08
- Owner：full-stack-software-engineer
- 对齐 Objective：O5 / O6 当前最低优先级。该轮只修正 typed contract，不产生 accepted live material，不提升 O5/O6 百分比。

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - `RealMaterialCollectionPath.id` 增加 `pc_upper_ssh_collector`。
  - `RealMaterialCollectionPath.runtime` 增加 `node_ssh`。
  - `RealMaterialCollectionPath.host_role` 增加 `pc_to_upper_computer`。
- `pc-tools/workstation/src/server/realMaterialAcceptance.ts`
  - 删除第三条 SSH collector path 的 `unknown` cast，`collection_paths[]` 直接按共享合同类型检查。
- `pc-tools/workstation/test/catalog.test.ts`
  - 增加 `RealMaterialCollectionPath["id"]` 的 `satisfies` 回归断言，证明三条 O5/O6 collection path 都在共享合同内。
  - 保留第三条 SSH collector 的 runtime、host_role、PC base URL 和安全边界断言。
- `docs/interfaces/real_material_acceptance_queue.md`
  - 把 O5/O6 `collection_paths[]` 文档从两条入口修正为三条入口，并记录本轮 shared contract 修正边界。
- `OKR.md`
  - 记录当前 O5/O6 抓手的 typed contract fix；未调整百分比。

## 验证结果

- `cd pc-tools/workstation && npm test -- --run test/catalog.test.ts`
  - exit code: 0
  - key output: `Test Files  1 passed (1)`；`Tests  64 passed (64)`
- `cd pc-tools/workstation && npm run build`
  - exit code: 0
  - key output: `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`；`✓ built in 1.99s`
- `cd pc-tools/workstation && npm run lint`
  - exit code: 0
  - key output: `eslint .`
- `git diff --check -- pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/src/server/realMaterialAcceptance.ts pc-tools/workstation/test/catalog.test.ts docs/interfaces/real_material_acceptance_queue.md OKR.md sprints/2026.06.04_07-08_o5-o6-collection-path-contract/tech-done.md`
  - exit code: 0
  - key output: no whitespace errors

## 剩余风险

- 本轮未执行 SSH collector、未访问真实云、未访问真实 4G/SIM、未采集 production DB/queue/OSS/CDN live traffic，也未产生 accepted live material。
- 本轮不访问 `/cmd_vel`、`/robots/*`、串口、ROS2 硬件或任何机器人控制路径。
- O5/O6 百分比保持约 96%；后续涨分仍只来自 accepted live production material。
