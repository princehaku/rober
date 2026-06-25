# PC 自动扫图启动反馈所见即所得

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 自动扫图 start/stop 固定代理返回后，普通首屏地图 `plain-map-free-roam-action-marker` 会显示 `自动扫图已启动`、启动/停止中、停止已发送或失败状态。
  - `扫图状态` 行同步显示 `自动扫图状态机已启动，地图和雷达监看中`，失败时明确写成未证明启动或停止。
  - 这些状态只消费 PC 固定代理结果，不外推真实自主运动成功。
- `pc-tools/workstation/src/styles.css`
  - 为自动扫图 action marker 增加启动中、运行、停止、失败等状态配色。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展自动扫图固定代理用例，验证 start 成功后地图 marker 和扫图状态行同步显示，且仍不调用 manual、`/cmd_vel` 或 Nav2 execute。
- `docs/product/pc_free_roam_mapping_design.md`
  - 记录自动扫图 start/stop 结果贴回地图和扫图状态行的用户口径。
- `docs/product/pc_tools_workstation.md`
  - 同步 PC workstation 边界，并明确不改 Clash 或系统代理配置。

## 验证结果

- `npm test -- -t "free-roam autonomy"`：通过，2 files / 3 passed / 173 skipped。
- `npm run lint`：通过。
- `npm run build`：通过，Vite production build 和 server TypeScript build 均完成。
- `npm test`：通过，2 files / 176 passed。
- `git diff --check`：通过。
- `lsof -nP -iTCP:7001 -sTCP:LISTEN`：`node 90259 ... TCP *:7001 (LISTEN)`。

## 剩余风险

- 本轮不触发真实自动扫图、真实 Nav2、manual、keyboard pulse、delivery complete、stop 或 `/cmd_vel`。
- 自动扫图运动是否真实发生仍以后续上车端 runtime artifact、HIL 和现场确认材料为准；PC 只展示固定代理请求结果。
