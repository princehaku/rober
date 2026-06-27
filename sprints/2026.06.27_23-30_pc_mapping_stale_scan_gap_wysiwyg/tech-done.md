# PC Mapping Stale Scan Gap WYSIWYG

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `freeRoamMappingMissingPlainLabelsForVisibleState()` 在建图缺口为 `雷达未刷新` 且存在 stale runtime `/scan` 距离时，显示旧距离和过期年龄。
  - 该说明只进入建图验收/当前事实缺口，不改变自由移动启动门禁。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展 stale runtime scan 回归，断言建图验收和当前事实都显示 `雷达未刷新（旧 /scan 距离 ... 已过期，不贴到地图）`。
- `docs/product/pc_tools_workstation.md`
  - 记录建图缺口消费 stale runtime `/scan` 的 PC 文案口径。
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步记录自由移动仍可启动、建图验收不能用旧雷达距离收口。

## 验证结果

- `npm test -- test/App.test.ts -t "stale runtime scan distance" --maxWorkers=1 --no-fileParallelism`
  - 通过：1 个相关用例通过。
- `npm test -- --maxWorkers=1 --no-fileParallelism`
  - 通过：2 个测试文件，318 个用例通过。
- `npm run lint`
  - 通过。
- `npm run build`
  - 通过；Vite 仍提示 bundle 超过 500 kB，这是既有体积 warning。

## 剩余风险

- 本轮只修 PC 文案，不刷新雷达、不启动自由移动、不恢复摄像头或 Nav2。
- live 当前仍需 camera 首帧、雷达 fresh、地图记录和 fresh map preview 才能按可验收建图收口。
