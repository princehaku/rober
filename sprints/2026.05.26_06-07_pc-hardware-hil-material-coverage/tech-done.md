# PC Hardware HIL Material Coverage Tech Done

## 1. Sprint 声明

- sprint_type: epic
- sprint_id: `2026.05.26_06-07_pc-hardware-hil-material-coverage`
- closeout owner: `product-okr-owner`
- closeout time: 2026-05-26 06:50 Asia/Shanghai

## 2. 实际改动

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

Full-Stack worker 验证通过：

```bash
PATH=/tmp/rober-node-v24.11.1-linux-x64/bin:$PATH npm run test
# 2 test files passed, 11 tests passed
```

```bash
PATH=/tmp/rober-node-v24.11.1-linux-x64/bin:$PATH npm run build
# vite built successfully, 27 modules transformed
```

```bash
PATH=/tmp/rober-node-v24.11.1-linux-x64/bin:$PATH npm run lint
# exit 0
```

```bash
git diff --check -- pc-tools/workstation docs/product/pc_tools_workstation.md docs/hardware/wave_rover_feedback_replay_gate.md sprints/2026.05.26_06-07_pc-hardware-hil-material-coverage
# exit 0
```

旧 Python gate 未恢复：

```bash
find pc-tools -path 'pc-tools/workstation/node_modules' -prune -o -type f -name '*.py' -print
# no output
```

环境说明：

- 当前 WSL 的 `/mnt/c/Program Files/nodejs/npm` shim 不可用。
- Worker 使用临时 Linux Node 24：`/tmp/rober-node-v24.11.1-linux-x64` 跑等价 npm 脚本。
- Worker 补齐了 `node_modules` 中缺失的 Linux Rollup/esbuild optional native 包；该改动位于 ignored `node_modules`，不纳入提交。

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
- Product closeout 未重新运行 npm build/test/lint；本文件记录并核对 Full-Stack worker 已提供的验证证据。
