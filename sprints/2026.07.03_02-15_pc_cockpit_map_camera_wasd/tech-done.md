# PC 首页驾驶台地图/图传/WASD收口

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/styles.css`
  - 普通 PC 首页 `visual-first` 布局改成左侧大地图、右侧实时图传和 WASD/方向键手控，避免地图独占首屏。
  - 雷达独立卡、连接状态、自由移动和长验收说明下沉到详情区；首页键盘卡隐藏冗长 proof 文案，把空间让给方向键。
  - 移动端顺序保持为地图、图传、WASD、详情。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通页可见安全文案统一为 `现场默认安全`，保留停止、松开停、失焦停和后端兼容确认字段。
  - 键盘 DOM 合同的 `keyboard_safety_confirm_required` 缺省值改为 `false`，普通用户不再看到或需要执行勾选确认动作。
- `pc-tools/workstation/test/App.test.ts`
  - 更新普通首页样式合同测试，明确首页必须同时包含大地图、图传和键盘手控区。
  - 更新打开即用文案和键盘 safety confirm 合同断言。
- `docs/product/pc_tools_workstation.md`
  - 记录 2026-07-03 02:15 CST 后 PC 首页驾驶台布局、`/map` 大屏边界、相机 USB 风险和 WAVE ROVER 当前控制路径。

## 验证结果

- `npm test -- --run test/App.test.ts`
  - 通过：1 个测试文件，237 个测试。
- `npm run build`
  - 通过：TypeScript app/server 编译和 Vite build 完成；仅保留既有 chunk size warning。
- `npm run lint`
  - 通过：`eslint .` 无报错。
- `git diff --check`
  - 通过：无空白错误输出。
- `HOST=0.0.0.0 PORT=7001 ROBOT_API_BASE_URL=http://192.168.1.11:8787 npm run api`
  - 通过：`lsof` 显示 Node 监听 `*:7001`；`/api/health` 回读 `workstation_listen_address=http://0.0.0.0:7001`、默认小车 API 为 `http://192.168.1.11:8787`。
- Chrome headless 实测 `http://127.0.0.1:7001/?baseUrl=http%3A%2F%2F192.168.1.11%3A8787`
  - 1280x720 首屏坐标：地图 `top=89,left=11,width=782,height=624`；图传 `top=89,left=803,width=426,height=346`；手控面板 `top=445,left=803,width=426,height=346`。
  - 方向按钮 `top=520..638`，首屏可见；summary 加载后 `keyboard_ready=true`、`keyboard_safety_confirm_required=false`、方向按钮可用。
  - 截图证据：`/tmp/rober_pc_cockpit_1280x720_proof.png`。

## 剩余风险

- 现场摄像头仍可能因 USB `12M` full-speed 导致首帧失败；本轮只改善 PC 页面布局和多人预览入口，不解决物理 USB 带宽/线缆问题。
- wheel raw `L/R` 非零仍取决于上车 `esp32_bridge` 和底盘反馈实际状态；当前 PC 手控路径继续走 `/cmd_vel` 到 bridge，再由 bridge 映射 vendor `T=11/PWM164`。
- Chrome 实测时相机仍为失败态，和当前 USB full-speed/首帧失败现场事实一致；该风险不阻塞地图和键盘手控。

## 资料来源

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
