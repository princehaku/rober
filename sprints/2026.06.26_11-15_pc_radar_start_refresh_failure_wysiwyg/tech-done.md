# 2026-06-26 11:15 PC 雷达启动后刷新失败 WYSIWYG

sprint_type: micro

## 实际改动

- `pc-tools/workstation/test/App.test.ts`
  - 新增 `启动雷达` 成功返回后自动 scan proof refresh 失败的回归。
  - 锁定该场景下雷达卡片保持 `刷新失败`、地图 marker 显示 `雷达刷新失败：fetch_timeout`、扫描范围隐藏、freshness 说明未显示新点位。
  - 继续断言该失败态不调用 manual、Nav2、delivery complete 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`
  - 同步记录雷达启动后自动刷新失败的 WYSIWYG 口径和安全边界。

## 验证结果

- `npm test -- -t "auto-refreshes radar proof after plain radar start reports ok|keeps radar start fail-closed when the automatic proof refresh fails"`：通过，2 passed / 193 skipped。
- `npm run lint`：通过。
- `npm run build`：通过，Vite production build 完成。
- `npm test`：通过，2 files / 195 tests passed。
- `git diff --check`：通过。
- `lsof -nP -iTCP:7001 -sTCP:LISTEN`：确认 Node 监听 `TCP *:7001 (LISTEN)`。

## 剩余风险

- 本轮只做 PC 前端 mock/静态验证，不触发真实雷达 lifecycle、真实 scan proof 或 HIL。
- `雷达刷新失败` 只表示 PC 自动刷新没有拿到新点位；真实雷达是否运行仍需上位机 readback、现场传感器日志和 HIL 材料确认。
- Node 当前应继续监听 `0.0.0.0:7001`；本轮不修改 Clash、代理或系统网络配置。
