# PC Hardware HIL Material Coverage Tech Done

## 1. Sprint 声明

- sprint_type: epic
- sprint_id: `2026.05.26_06-07_pc-hardware-hil-material-coverage`
- closeout owner: `product-okr-owner`
- closeout time: 2026-05-26 06:50 Asia/Shanghai

## 2. 实际改动

Task B Full-Stack worker 2026-05-26 23:07 Asia/Shanghai 增量补齐：

- `pc-tools/workstation/src/shared/contracts.ts`：扩展 WAVE ROVER material coverage contract，新增 `fixture_groups`、`gaps`、`not_proven_boundaries`，并把主 API 路由登记为 `/api/hardware/wave-rover/material-coverage`。
- `pc-tools/workstation/src/server/waveRoverMaterialCoverage.ts`：补齐 Node-native gap scanner 和 not_proven boundary 输出；仍只扫描 `pc-tools/evidence/fixtures/wave_rover_*`，不执行 Python、不打开串口、不运行 HIL。
- `pc-tools/workstation/src/server/index.ts`：新增 `GET /api/hardware/wave-rover/material-coverage`，保留 `GET /api/tools/hardware-materials` 兼容旧 UI/API 调用。
- `pc-tools/workstation/src/client/workstationApi.ts`：前端切换到新的 material coverage API 路径。
- `pc-tools/workstation/src/components/WaveRoverMaterialCoveragePanel.vue`、`pc-tools/workstation/src/styles.css`：UI 展示 coverage gaps、fixture group 和 `not_proven` 边界，继续禁止任何 Start/Control/Run HIL/Connect Serial/Mark Passed 类动作。
- `pc-tools/workstation/test/catalog.test.ts`、`pc-tools/workstation/test/App.test.ts`：覆盖 scanner contract、API fail-closed flags、UI 文案、缺口和 not_proven boundary。
- `docs/product/pc_tools_workstation.md`、`pc-tools/evidence/README.md`：同步 Node-native coverage contract、五件套材料要求、execution pack/review decision 只能作为辅助上下文。

Full-Stack worker 已完成并验证：

- `pc-tools/workstation` 新增 Node-native Hardware Materials 入口：`GET /api/tools/hardware-materials`。
- 新增 `waveRoverMaterialCoverage.ts`，扫描 `pc-tools/evidence/fixtures/wave_rover_*` 目录。
- Coverage scanner 识别五件套：`feedback_T1001.log`、`odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl`、`operator_hil_report` / `.json`。
- Vue 工作站新增 `Hardware Materials` tab/panel，展示 WAVE ROVER material coverage 和缺口。
- UI/API 明确 `coverage is not HIL pass`，并保持 `source=software_proof`、`proof_status=not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`pc_only=true`。
- `docs/product/pc_tools_workstation.md` 已同步更新，说明 Node-native 工作站入口和不恢复旧 Python gate。

Hardware worker 已只读确认 vendor facts 和边界：

- 已确认 WAVE ROVER 官方 UART newline JSON 语义、`T=1001` feedback、`T=1` / `T=13` / `T=130` / `T=131` / `T=142` / `T=143` 等事实。
- 只读结论不能证明 serial path、baudrate link、wheel direction、feedback frequency、IMU/battery calibration 或 `delivery_success`。

Product closeout 本轮新增/更新：

- `sprints/2026.05.26_06-07_pc-hardware-hil-material-coverage/tech-done.md`
- `sprints/2026.05.26_06-07_pc-hardware-hil-material-coverage/side2side_check.md`
- `sprints/2026.05.26_06-07_pc-hardware-hil-material-coverage/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## 3. 验证结果

Full-Stack worker 验证通过。第一次使用系统 Node `v18.19.1` 运行 build 时失败，原因是 Vite 7 要求 Node `20.19+` 或 `22.12+`，报错为 `crypto.hash is not a function`；随后改用 Codex bundled Node `v24.16.0` / npm `11.13.0` 复跑验收通过：

```bash
export PATH="/mnt/c/Users/haku/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH"
node --version
# v24.16.0
npm --version
# 11.13.0
```

```bash
cd pc-tools/workstation && timeout 120s npm run build
# vite built successfully, 27 modules transformed
```

```bash
cd pc-tools/workstation && timeout 120s npm run test
# Test Files 2 passed (2), Tests 14 passed (14)
```

```bash
cd pc-tools/workstation && timeout 120s npm run lint
# eslint . exited 0
```

```bash
find pc-tools -path 'pc-tools/workstation/node_modules' -prune -o -type f -name '*.py' -print
# no output
```

```bash
git diff --check -- pc-tools/workstation docs/product/pc_tools_workstation.md pc-tools/evidence/README.md sprints/2026.05.26_06-07_pc-hardware-hil-material-coverage
# no output
```

环境说明：

- 当前默认 `node` 为 `v18.19.1`，不能满足 Vite 7 build gate。
- 本轮最终验收使用 Codex bundled Node `v24.16.0`，该路径只影响验证环境，不改仓库脚本。

## 4. 需求满足自检

- P0：Node-native WAVE ROVER material coverage 已落在 `pc-tools/workstation`，通过。
- P0：能扫描 `pc-tools/evidence/fixtures/wave_rover_*`，通过。
- P0：能显示 required materials、缺口和 `not_proven` 边界，通过。
- P0：`npm run build`、`npm run test`、`npm run lint` 通过。
- P0：文档同步到 `docs/product/pc_tools_workstation.md`，通过。
- P0：未恢复 `pc-tools` 旧 Python gate，通过。
- 安全边界：API/UI 保持 fail-closed flags，通过。

## 5. 剩余风险

- 本轮是 `software_proof` PC 工具材料 coverage，不是 HIL pass。
- 不证明真实 WAVE ROVER 上电、真实 UART、serial path、baudrate link、wheel direction、feedback frequency、IMU/battery calibration。
- 不证明 2D LiDAR / ToF SKU、采购、安装、接线、电源或标定。
- 不证明 PR #5 `PRRT_kwDOSWB9286CJ3tX` resolved。
- 不证明真实 Nav2/fixed-route、电梯现场、投放、dropoff/cancel completion、delivery result 或 `delivery_success=true`。
- Product closeout 已核对 worker 验证证据；Node/Vue build/test/lint 的执行边界是 Codex bundled Node `v24.16.0`，不是当前默认系统 Node `v18.19.1`。
