# 2026-06-26 04:05 PC 保存后地图刷新中可见状态

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 保存地图成功后、自动触发的只读 `map/preview` 尚未返回时，普通首屏显示明确的“保存后刷新中”状态。
  - 对齐扫图 hint、扫图状态、下一步、地图画面新鲜度、地图 marker、步骤条和覆盖提示，避免保存成功后让 operator 误以为刷新已经结束。
  - 该中间态只等待 `/api/robot-control/map/preview`，不新增控制接口，不发送 manual、Nav2、delivery、stop 或 `/cmd_vel`。
- `pc-tools/workstation/src/styles.css`
  - 为 `saved_refreshing` 地图流程 marker 复用处理中样式。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展 free-roam keyboard/save 流程测试：延迟保存后的地图 preview，验证“保存后刷新中”中间态和最终“已自动刷新”状态，并断言不触发 manual、Nav2 execute、delivery complete。
- `docs/product/pc_free_roam_mapping_design.md`
- `docs/product/pc_tools_workstation.md`
  - 同步保存后 preview pending 的产品口径和非运动边界。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- -t "keeps free-roam keyboard locked until map recording starts"`，1 passed / 188 skipped。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`。
- 通过：`cd pc-tools/workstation && npm test`，2 files / 189 passed。
- 通过：`git diff --check`。
- 确认：`lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 PC node 监听 `*:7001`。

## 剩余风险

- 本轮只覆盖 PC mock/前端状态与固定代理回归；没有在真实小车上触发保存地图或做 HIL。
