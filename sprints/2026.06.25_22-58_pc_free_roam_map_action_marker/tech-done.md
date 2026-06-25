# PC 扫图流程地图 marker

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏地图新增 `plain-map-free-roam-action-marker`，把扫地式建图流程状态直接叠到地图上。
  - marker 覆盖 `地图记录中`、`键盘已启用`、`扫图移动中`、`已停止，可保存`、`地图保存中` 等状态。
  - 缺少 map-frame 机器人位置时固定在角落，并在 aria 中声明“不代表坐标”；有机器人位置时贴近当前位置。
- `pc-tools/workstation/src/styles.css`
  - 为扫图流程 marker 增加记录/移动、等待刷新、可保存、保存中等状态样式。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展 free-roam 流程测试，验证流程 marker 从未显示到记录、启用、移动、停止可保存、保存中的完整变化。
- `docs/product/pc_tools_workstation.md`
  - 同步记录地图扫图流程 marker 的用户口径和安全边界。

## 验证结果

- 通过：`npm test -- -t "free-roam keyboard locked"`，1 个目标用例通过，170 个用例跳过。
- 通过：`npm run lint`。
- 通过：`npm test`，2 个测试文件、171 个用例全部通过。
- 通过：`npm run build`，TypeScript app/server 编译与 Vite production build 通过。
- 通过：`git diff --check`。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`，确认 `node` 监听 `TCP *:7001`。
- 已恢复全量 `npm test` 自动刷新的旧 smoke artifact `checked_at`，避免把历史验证时间戳混入本轮提交。

## 剩余风险

- 本轮是 PC/mock 层 WYSIWYG 状态增量，没有触发真实 map start/save、manual、keyboard pulse、Nav2 execute、delivery complete、stop 或 `/cmd_vel`。
- 自动自由跑动仍依赖上车端 `free_roam_autonomy` 真车验证；当前 marker 只让人工扫图流程在地图上更可见。
