# 2026-06-26 01:25 PC 自动扫图下一步收口

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 增加自动扫图 start/stop 已转发的本地状态判断。
  - 自动扫图 start 成功后，`下一步` 改为 `下一步：监看或停止自动扫图`，点击只聚焦 `停止自动扫图`。
  - 自动扫图 stop 转发后，`下一步` 按地图画面是否已刷新回到 `保存当前地图` 或 `刷新扫图画面`，不再把 operator 带回人工键盘流程。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展自动扫图固定代理组件测试，覆盖 start 后下一步聚焦 stop、stop 后下一步聚焦保存地图。
  - 验证下一步按钮只做焦点移动，不额外调用 manual、Nav2、delivery 或 `/cmd_vel`。
- `docs/product/pc_free_roam_mapping_design.md`
  - 记录自动扫图运行后的下一步流程：监看/停止，再刷新或保存地图。
- `docs/product/pc_tools_workstation.md`
  - 同步普通首屏自动扫图下一步和安全边界。

## 验证结果

- 通过：`npm test -- -t "starts free-roam autonomy through the fixed proxy only after ready readback and safety confirmation"`
  - `Test Files 1 passed | 1 skipped (2)`
  - `Tests 1 passed | 178 skipped (179)`
- 通过：`npm run lint`
- 通过：`npm run build`
  - `vite v7.3.3 building client environment for production`
  - `dist/assets/index-CX0dcRkO.js 474.85 kB`
- 通过：`npm test`
  - `Test Files 2 passed (2)`
  - `Tests 179 passed (179)`
- 通过：`git diff --check`
  - 无输出，未发现空白或 diff 格式问题。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`
  - `node ... TCP *:7001 (LISTEN)`

## 剩余风险

- 本轮只覆盖 PC 前端流程指引和 mock 组件测试，不触发真实自动扫图、真实 manual、keyboard pulse、Nav2、delivery、stop 或 `/cmd_vel`。
- 真实现场仍需在 `0.0.0.0:7001` 上验证自动扫图 start 后的焦点、stop 收口和保存地图流程是否符合 operator 预期。
