# Tech Done

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/client/workstationApi.ts`
  - 为 `getRobotControlSummary()` 增加浏览器侧 3.5s AbortController 超时。
  - 超时后抛出 `client_timeout_3500ms`，交给现有普通首屏 fail-closed 错误/旧读数提示处理。
  - 只影响只读 summary GET；不修改 POST、Nav2 执行、地图刷新或自由移动 start/stop 的等待窗口。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 PC Node summary fetch 永不返回时的组件测试。
  - 断言页面退出 loading、显示连接失败事实、保留控制 endpoint 零触发。
- `docs/product/pc_free_roam_mapping_design.md`
  - 补充 2026-06-28 07:50 的 PC summary 客户端超时规则。

## 验证结果

- 已通过：`cd pc-tools/workstation && npm test -- --testNamePattern "browser-side summary|plain timeout|stale facts|Robot Control V1" --maxWorkers=1 --no-fileParallelism`
  - 结果：1 个 test file 通过，4 passed，322 skipped。
- 已通过：`cd pc-tools/workstation && npm test -- --maxWorkers=1 --no-fileParallelism`
  - 结果：2 个 test files，326 passed。
- 已通过：`cd pc-tools/workstation && npm run lint`
- 已通过：`cd pc-tools/workstation && npm run build`
  - 备注：Vite 输出既有 `Some chunks are larger than 500 kB` 警告；构建命令退出码为 0。
- 已通过：`git diff --check`

## 剩余风险

- 本轮只修浏览器等待 PC Node summary 的无界 loading 问题，不修复 7001 或上位机服务本身的间歇卡顿。
- 如果 summary 客户端超时发生，页面会进入 fail-closed；真实相机、雷达、地图、Nav2 状态仍需要下一次成功刷新证明。
- 真实运动、完整 Nav2 路线执行和自由移动仍需要操作员明确安全确认后另行验证。
