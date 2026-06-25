# Free Roam Mapping Keyboard Gate

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - “扫地式建图”的键盘扫图入口新增流程 gate：必须先完成现场安全确认，并且地图记录已经启动成功，才能启用键盘扫图。
  - 按钮文案按流程显示 `先勾安全确认 -> 先开始记录 -> 启用键盘扫图/键盘条件未满足`。
  - 普通键盘手控自身仍保持最小安全确认入口；本次只限制“扫地式建图”卡片里避免未记录地图时先移动。
- `pc-tools/workstation/test/App.test.ts`
  - 补齐 map/start fixture 路由。
  - 新增回归测试：安全确认后但地图记录未启动时，扫图键盘仍禁用；map/start 明确成功后才启用；点击启用不发送 manual。
- `docs/product/pc_tools_workstation.md`
  - 同步扫地式建图顺序和安全边界。

## 验证结果

- `npm test`
  - 通过：2 个 test files，159 个 tests 全部通过。
- `npm run build`
  - 通过：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`。
- 只读 7001 smoke：
  - `GET http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http://192.168.1.11:8787`
  - 返回 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。
  - 当前 `free_roam=locked`、`lidar_state=stopped`、`path_generated=false`，未触发任何真实运动。

## 剩余风险

- 本轮只修正 PC 建图向导顺序，没有证明真实 map/start 在当前上位机已配置成功。
- 自动扫图仍保持 locked；自由移动仍依赖 operator 显式启用键盘并按住方向键。
- 当前未证明完整 Nav2 路线执行、wheel raw L/R 非零或 delivery success。
