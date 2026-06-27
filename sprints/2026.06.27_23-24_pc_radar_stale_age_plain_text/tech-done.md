# PC Radar Stale Age Plain Text

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增秒级年龄格式器，把 stale runtime `/scan` age 从机器秒数转换为普通用户能判断的新旧程度。
  - `latestRadarRuntimeScanStaleLabel()` 现在显示 `约 12 秒前`、`约 2 小时 51 分前` 等人话，不再直出 `10234.64s`。
- `pc-tools/workstation/test/App.test.ts`
  - 更新短 stale age 断言。
  - 新增 live 级别长 stale age 回归，确保页面显示 `约 2 小时 51 分前`，且不出现原始 `10234.64s`。
- `docs/product/pc_tools_workstation.md`
  - 记录 stale runtime `/scan` 年龄的人话格式。
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步记录该格式不改变 freshness、建图 ready 或地图贴点判定。

## 验证结果

- `npm test -- test/App.test.ts -t "stale runtime scan|long stale runtime scan age" --maxWorkers=1 --no-fileParallelism`
  - 通过：1 个测试文件，2 个相关用例通过。
- `npm test -- --maxWorkers=1 --no-fileParallelism`
  - 通过：2 个测试文件，318 个用例通过。
- `npm run lint`
  - 通过。
- `npm run build`
  - 通过；Vite 仍提示 bundle 超过 500 kB，这是既有体积 warning。

## 剩余风险

- 本轮只改 PC 可读性，不刷新雷达、不改变自由移动门禁、不恢复摄像头或 Nav2。
- live 当前仍是 stale runtime `/scan`、camera first frame failed、Nav2 planner/controller inactive；这些真实状态还需后续继续推进。
