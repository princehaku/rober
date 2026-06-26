# PC 雷达卡片点数口径 WYSIWYG

## sprint_type

micro

## 实际改动

- 普通首屏雷达卡片补充 scan proof 点数和 map/local/recent 口径，避免地图 caption 已说明点数但雷达卡仍只写“看到新的雷达状态”。
- 补充 PC 工作站测试，锁定 map-frame 贴图、缺定位局部轮廓、雷达停止但保留最近点三类文案。
- 同步 `docs/product/pc_tools_workstation.md`，明确该展示只读，不启动雷达、不刷新 proof、不发底盘或 Nav2 指令，不修改 Clash/系统代理，PC 入口保持 `0.0.0.0:7001`。

## 验证结果

- 通过：`npm test -- -t "draws radar pulse on the robot marker only after map-frame pose is observed|shows local radar scan dots instead of fake map dots when pose is missing|keeps recent local radar scan visible when lidar is currently stopped|shows plain radar start only when the readback says lidar is stopped|auto-refreshes radar proof after plain radar start reports ok"`，结果 `Test Files 1 passed | 1 skipped (2)`，`Tests 5 passed | 197 skipped (202)`。
- 通过：`npm run lint`。
- 通过：`npm run build`。Vite 仍提示单个 chunk 超过 500 kB，这是既有体积提醒，不影响本轮功能。
- 通过：`npm test`，结果 `Test Files 2 passed (2)`，`Tests 202 passed (202)`。
- 通过：完整测试改写的两个历史 smoke artifact `checked_at` 已恢复到历史固定值，未纳入本轮提交。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN` 确认 `node` 监听 `*:7001`。

## 剩余风险

- 本轮只做 PC 前端只读文案和测试锁定，未做真实小车 HIL、真实雷达 lifecycle 或 Nav2 执行验证。
