# PC Tools WAVE ROVER Source Boundary Micro Sprint

## sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/waveRoverMaterialCoverage.ts`
  - 为 Hardware Materials API 增加 `vendor_sources: [{ path, fact_ids }]`，来源覆盖 `docs/vendor/VENDOR_INDEX.md`、`base_ctrl.py`、`config.yaml`、`json_cmd.h`、`uart_ctrl.h`、`ugv_advance.h`。
  - 增加 `hardware_claim_level=software_material_coverage`、`serial_reference`、`command_facts`、`feedback_schema.T1001`，并保持所有命令事实 `hardware_verified=false`。
  - 明确 `T=1001` 字段来自 `ugv_advance.h` 的 `baseInfoFeedback()`，并标注 `moduleType=1` 时 `y` 可能被机械臂 `lastY` 覆盖。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 增加 Hardware Materials 新字段的前后端共享类型。
- `pc-tools/workstation/src/components/WaveRoverMaterialCoveragePanel.vue`
  - 展示 vendor sources、串口参考、命令事实、反馈 schema。
  - 将 `complete coverage` 改为 `complete file/material coverage`。
  - `safe_to_control`、`delivery_success` 改为从 API 字段渲染。
- `pc-tools/workstation/test/catalog.test.ts`、`pc-tools/workstation/test/App.test.ts`
  - 覆盖 `vendor_sources`、`serial_reference`、`command_facts`、`feedback_schema`、fail-closed tokens、`hardware_claim_level`、complete material coverage 仍 `proof_status=not_proven`。
  - 继续禁止 `/cmd_vel`、`/dev/ttyUSB`、`/dev/ttyACM`、`hardware_connected=true`、`hil_pass=true`、`hardware connected`、`ready to control` 等越界声明。
  - 允许展示 vendor Raspberry Pi 示例 `/dev/ttyAMA0`、`/dev/serial0`，但 API/UI 同时固定 `orange_pi_device_status=not_proven`。
- `docs/product/pc_tools_workstation.md`
  - 同步 Hardware Materials 边界、vendor source、串口参考、命令事实、T1001 反馈字段和项目侧 evidence material 说明。

## 验证结果

```text
cd pc-tools/workstation && npm run build
> tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json
✓ built in 700ms
```

```text
cd pc-tools/workstation && npm run test
Test Files  2 passed (2)
Tests  11 passed (11)
```

```text
cd pc-tools/workstation && npm run lint
> eslint .
```

```text
Get-ChildItem -Path pc-tools -Recurse -File -Include *.py | Where-Object { $_.FullName -notmatch '\\workstation\\node_modules\\' }
<empty>
```

## 失败定位

- Python 残留检查第一次运行时，PowerShell 正则反斜杠被传成单反斜杠，报 `Illegal \ at end of pattern`；已按验收命令的双反斜杠正则重新执行，结果为空。
- 产品构建、测试、lint 未发现代码失败。

## 剩余风险

- 本轮只验证 PC-only Node/Vue 软件契约和本地 fixture 文件名覆盖；未进行 HIL、真实串口、真实 WAVE ROVER feedback、轮向、反馈频率、IMU/电池标定或 `T=13 CMD_ROS_CTRL` 上车验证。
- `/dev/ttyAMA0`、`/dev/serial0`、`115200` 仅作为 vendor Raspberry Pi 示例展示；Orange Pi 串口设备仍是 `not_proven`。
