# 2026-07-03 19:12 PC 隐藏旧安全勾选入口

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/styles.css`
  - 将 `.plain-hidden-safety-input` 从 1px 视觉隐藏改为 `display: none !important;`。
  - 保留旧 input 节点给测试和现场脚本读取，但普通用户界面不再渲染 safety checkbox。
- `pc-tools/workstation/test/App.test.ts`
  - 补充样式断言，锁定普通用户界面不能再渲染旧安全勾选框。
- `docs/product/pc_tools_workstation.md`
  - 同步 PC 普通首页/高级区的旧 safety input 兼容口径：现场安全默认已确认，用户不需要勾选，且隐藏 input 不触发任何运动动作。

## 验证结果

- `npm test -- App.test.ts`
  - 通过：`Test Files 1 passed (1)`，`Tests 239 passed (239)`。
- `npm run build`
  - 通过：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 成功。
- `git diff --check`
  - 通过：无 whitespace/error 输出。
- PC Node 重启
  - `HOST=0.0.0.0 PORT=7001 DEFAULT_ROBOT_API_BASE_URL=http://192.168.1.11:8787 npm run api`
  - `lsof` 显示 `node` 监听 `*:7001`。
- 浏览器 DOM smoke
  - 首页 `.plain-hidden-safety-input`：5 个节点全部 `display=none`、`visible=false`、`checked=true`，`visibleSafetyCount=0`。
  - `/map` 直达页 `.plain-hidden-safety-input`：7 个节点全部 `display=none`、`visible=false`，`visibleSafetyCount=0`。
  - `/map` 地图画布仍为 `1272x787`，未因本轮隐藏 checkbox 改小。
- PC health
  - `workstation_host=0.0.0.0`
  - `workstation_port=7001`
  - `default_robot_api_base_url=http://192.168.1.11:8787`
- 上位机 smoke
  - `ssh root@192.168.1.11 -p 7878` 通过。
  - `trashbot-upper-robot-api.service` 与 `trashbot-local-webrtc-camera.service` 均为 `active`。
  - `0.0.0.0:8787` 与 `0.0.0.0:8088` 均在监听。
- PC summary 抽样
  - `map_current_visible=true`
  - `path_current_visible=true`
  - `radar_map_points_visible=true`
  - `keyboard_status=start_ready`
  - `delivery_success=false`

## 剩余风险

- 本轮只修复 PC 页面残留 safety checkbox 的可见性，不改变 Nav2/manual/keyboard/free-roam 的真实运动链路。
- 当前 summary 仍显示 `delivery_success=false`，完整送达闭环未完成。
- 当前相机仍需要现场检查摄像头输入/供电或换 known-good UVC 后复测；本轮没有改变相机采集链路。
- `sprints/2026.06.11_18-00_pc_simple_user_console_repair/artifacts/` 下两个旧 DOM smoke artifact 已在工作区中脏改，本轮未读取、未修改、未 stage。
