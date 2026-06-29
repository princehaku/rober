# PC 雷达启动后地图预览自动同步

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏启动雷达、重启雷达成功后，显式要求 `refreshRadarProof({ mapPreviewAfter: true })`，让雷达 proof 返回后继续读取同轮地图预览，避免地图继续显示旧雷达层。
- `pc-tools/workstation/test/App.test.ts`：补强“启动雷达后自动刷新 proof”回归，验证返回后会额外读取 `/api/robot-control/map/preview`，并按同轮 `radar_overlay` 显示已贴图雷达点。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`：同步记录普通首屏雷达启动/重启后的 WYSIWYG 地图刷新合同。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "auto-refreshes radar proof after plain radar start reports ok"`，1 个目标测试通过。
- 通过：`npm --prefix pc-tools/workstation test`，2 个测试文件、381 个测试全部通过。
- 通过：`npm --prefix pc-tools/workstation run build`，TypeScript app/server 编译和 Vite build 通过；仅保留既有大 chunk 提示。
- 通过：`git diff --check`，未发现 whitespace/error。

## 剩余风险

- 这轮只修 PC 前端刷新链路和回归测试，未实际点击 live 上位机 `启动雷达`；真实雷达硬件、定位和地图 overlay 仍以后续现场只读/安全确认后的验证为准。
