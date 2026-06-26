# Free Roam Mapping Quality Confirm Gate

sprint_type: micro

## 实际改动

- 修改 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：新增 `plainFreeRoamMappingQualityReady`，把自动扫图 start 的 `confirm_mapping_active` 收紧为“地图记录已启动 + 摄像头 ready + 雷达 ready”。
- 自动扫图 fallback 响应也使用同一判断，避免失败展示里把降级自由移动误写成建图 active。
- 修改 `pc-tools/workstation/test/App.test.ts`：在摄像头缺首帧场景里显式让 map start 返回 runtime started，并断言自动扫图 start 仍发送 `confirm_mapping_active=false`。
- 更新 `docs/product/pc_tools_workstation.md`：记录 2026-06-26 23:25 起建图质量确认位的语义。

## 验证结果

- `cd pc-tools/workstation && npm test -- App.test.ts`：通过，`141 passed`。
- `cd pc-tools/workstation && npm run build`：通过，仅保留既有 Vite chunk size warning。
- `git diff --check`：通过。

## 剩余风险

- 本轮只修正 PC 请求体语义和测试边界，没有真实上车 HIL。
- 上车端是否在 runtime artifact 中完整标注自由移动/不可验收建图，仍需现场 start 后读取 `/api/free-roam/autonomy/latest` 复测。
