# PC 扫地式建图路线草图 WYSIWYG

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏地图 overlay 新增 `扫地图草图`：真实地图画面已读取且存在可通行区域时，显示蛇形覆盖草图。
  - 当 summary 提供 map-frame 机器人位姿时，地图上额外显示 `扫图起点`，并把草图文案改为从当前位置接入。
  - 扫地式建图卡片新增 `扫地图草图` 状态行，明确这是只读计划草图，不会自动移动。
- `pc-tools/workstation/src/styles.css`
  - 新增扫地图草图和起点 marker 样式，层级低于 Nav2 路线，高于地图底图，不覆盖雷达/机器人标记。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖默认真实地图画面显示蛇形草图。
  - 覆盖 map-frame 机器人位姿存在时显示 `扫图起点` 并从当前位置接入。
- `docs/product/pc_tools_workstation.md`
  - 同步记录扫地图草图的 WYSIWYG 口径和控制边界。

## 验证结果

- `npm test -- --testNamePattern "Robot Control V1|free-roam|radar pulse|local radar|route path|扫地式建图"`：通过，1 个测试文件执行，6 个相关测试通过。
- `npm run lint`：通过。
- `npm test`：通过，2 个测试文件，167 个测试通过。
- `npm run build`：通过，完成 TypeScript 和 Vite production build。

## 剩余风险

- 本轮实现的是 PC 端只读路线草图，不是上车端自动扫图状态机；不会自动移动小车。
- 本轮未做真实 HIL 扫图验证，真实自由跑动建图仍需后续接入上车端 watchdog、雷达避障和 operator stop 兜底后验证。
