# PC 自由移动/自动扫图模式文案拆分

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏自由移动 readiness 标题改为跟随当前模式显示：缺少摄像头/雷达/建图任一建图验收条件时显示 `自由移动准备`，完整 ready 时显示 `自动扫图准备`。
  - `刷新自动扫图状态（只读）` 改为模式感知：自由移动状态下显示 `刷新自由移动状态（只读）`。
  - 向导尾部按钮从固定 `检查自动扫图条件` 改为自由移动状态下显示 `检查自由移动条件`。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖默认缺少完整建图条件时显示 `自由移动准备`，并确保不会误显示 `自动扫图准备`。
  - 覆盖建图条件 ready 时仍显示 `自动扫图准备`。
  - 覆盖只读 latest 按钮在自由移动状态下显示 `刷新自由移动状态（只读）`。
- `docs/product/pc_tools_workstation.md`
  - 同步记录自由移动和自动扫图验收的文案边界：小车可低速自由移动不依赖雷达；完整自动扫图/建图验收才依赖地图记录、摄像头与雷达同时 ready。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts`
  - `Test Files 1 passed (1)`
  - `Tests 153 passed (153)`
- 通过：`cd pc-tools/workstation && npm run lint`
  - `eslint .`
- 通过：`cd pc-tools/workstation && npm run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
  - Vite 保留既有 chunk size warning，本轮无新增构建失败。
- 通过：重启 PC Node 到 `0.0.0.0:7001`
  - `lsof` 显示 `node` PID `45212` 监听 `TCP *:7001`。
  - `curl http://127.0.0.1:7001/api/health` 返回 `mode=pc_only_readonly_workstation`、`safe_to_control=false`、`pc_only=true`。
  - `curl http://127.0.0.1:7001/api/robot-control/summary` 返回 live 事实：摄像头 `source_first_frame_failed` 且 `source_usage_owner_count=0`，雷达 `lifecycle_running=false`、`point_count=0`，Nav2 `next_execution_base_command_mode=ros`，自由移动 `free_roam_autonomy_start_ready=true`、label 为 `自由移动（勾确认后可启动）`。

## 剩余风险

- 本轮只修 PC 首屏 WYSIWYG 文案和只读状态按钮，不执行真车自由移动、Nav2 或摄像头硬件抢占修复。
- 当前 live 摄像头首帧仍需按后续硬件/驱动链路排查；该风险不会阻塞低速自由移动文案拆分。
