# PC summary 路线首屏地图预览回归

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/test/App.test.ts`
  - 将原“summary 已有路线”用例改名为“只有路线点数但缺坐标数组”的场景，明确 PC 不能凭空画路线。
  - 新增 live 形状回归：summary 已带 `path_preview_points`、`path_preview_frame_id=map` 且首屏只读地图预览成功时，普通首屏直接显示路线 polyline、`路线已显示 N/M 个点`、图上路线说明；勾选安全确认后主按钮进入 `执行图上路线`，且不调用 Nav2 proof refresh、Nav2 execute、manual 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 2026-06-27 18:33 口径：初载 summary 已有路线坐标时，地图预览成功后不再要求普通用户额外点击 `刷新图上路线`；只有点数没有坐标时仍保持不画假路线。

## 验证结果

- 已通过：`npm test -- --run test/App.test.ts -t "summary route|prepared trip count"`，2 passed / 171 skipped。
- 已通过：`npm test -- --run`，2 test files passed，302 tests passed。
- 已通过：`npm run build`。Vite 仍输出既有 chunk >500 kB 警告，不影响本轮通过。
- 已通过：`npm run lint`。
- 已通过：`git diff --check`。

## 剩余风险

- 本轮没有触发真实 Nav2 execute、manual、keyboard、delivery、stop 或 `/cmd_vel`；真实发车仍需要现场勾选安全确认并由 operator 显式点击。
- 摄像头 live 当前仍显示 UVC 首帧超时且非占用，下一步仍是检查 USB/input/供电或换已知可用 UVC；本轮只锁定路线首屏 WYSIWYG 回归。
