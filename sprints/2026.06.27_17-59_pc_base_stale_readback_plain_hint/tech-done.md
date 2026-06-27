# PC 底盘 stale 读回普通提示

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增底盘读回 freshness 判断：`latest_feedback_status=stale` 或 `latest_t1001_observed_count=0` 时，普通首屏不再把 `L/R=0/0` 说成“已读到 0 帧”。
  - 轮速记录卡片会显示“当前没有新鲜底盘反馈帧，最近轮速占位为 L/R=0/0”，并引导先 `刷新当前轮速（只读）`，再低速试动或键盘按住读取非零 L/R。
  - 本轮只改只读文案和目标提示，不改变 manual、keyboard、Nav2、free-roam、delivery 或 stop 控制边界。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 live 形态回归：stale/0 帧底盘读回必须显示刷新优先提示，且不得触发 manual 或 Nav2 execute。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 stale/0 帧底盘读回的普通首屏口径。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run App.test.ts -t "stale or empty base readback"`
  - 结果：`1 passed | 171 skipped`
- 通过：`cd pc-tools/workstation && npm test -- --run`
  - 结果：`2 passed` test files，`301 passed`
- 通过：`cd pc-tools/workstation && npm run build`
  - 结果：TypeScript 与 Vite build 通过；保留既有 chunk size warning。
- 通过：`cd pc-tools/workstation && npm run lint`
  - 结果：`eslint .` 通过。
- 通过：`git diff --check`

## 剩余风险

- 本轮不触发真实键盘手控、低速试动或 Nav2 重跑；只让普通首屏把当前 live 的 stale/0 帧底盘读回说清楚。
- 当前 live Nav2 仍是旧 PWM action 成功但同窗口 wheel raw L/R=0/0；完整路线仍需现场安全确认后用 ROS 模式重跑。
- 当前 live 摄像头仍是非独占 UVC 无首帧；雷达 runtime 可读近障碍，但地图 scan 点仍为 0。
