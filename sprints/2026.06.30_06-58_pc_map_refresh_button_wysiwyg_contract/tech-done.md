# PC 地图刷新按钮 WYSIWYG 合同

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 为普通首屏地图卡的 `plain-map-proof-refresh` 和 `plain-map-preview-refresh` 补齐按钮级 DOM 合同。
  - `刷新地图` 明确是 `refresh_proof_then_preview`：固定调用 map proof refresh，并在 proof 后刷新 map preview。
  - `刷新地图画面` 明确是 `refresh_preview`：固定调用 map preview，并同步读取雷达状态。
  - 两个按钮都声明刷新影响 `map-image-route-robot-radar`，且点击不发送运动、不启动建图 runtime、不执行 Nav2。
- `pc-tools/workstation/test/App.test.ts`
  - 在地图刷新与行程执行围栏测试中补充按钮级 WYSIWYG 合同断言。
- `pc-tools/README.md`
  - 记录地图刷新按钮的只读 endpoint、影响图层和非发车边界。
- `docs/product/pc_tools_workstation.md`
  - 同步普通 PC 工作站产品文档，明确地图刷新只更新当前画面/路线/小车位置/雷达层显示材料。

## 验证结果

- 已通过目标用例：
  - `npm test -- test/App.test.ts -t "blocks visible-route execution while the map preview is refreshing"`
  - 结果：`Test Files 1 passed (1)`，`Tests 1 passed | 218 skipped (219)`。
- 已通过全量工作站测试：
  - `npm test -- --run`
  - 结果：`Test Files 2 passed (2)`，`Tests 389 passed (389)`。
- 已通过生产构建：
  - `npm run build`
  - 结果：`vite build` 成功，新 bundle 为 `dist/assets/index-CvYXM8du.js`。
- 已通过 diff 格式检查：
  - `git diff --check`
  - 结果：无输出，检查通过。
- 已重启 PC Node 工作站：
  - `0.0.0.0:7001` 当前由 `node` 监听，PID `1279`。
  - `curl http://127.0.0.1:7001/` 返回 `index-CvYXM8du.js` 和 `index-BmaNglvi.css`。

## 剩余风险

- 本轮只补 PC Web DOM 合同和单元测试，没有连接真实小车执行地图刷新 HIL，也没有发送 manual、free-roam、map lifecycle、Nav2、delivery、stop 或 `/cmd_vel`。
- 真实地图、雷达点和 Nav2 路线的现场 WYSIWYG 仍需在 7001 页面连接上位机后复验。
