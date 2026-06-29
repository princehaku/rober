# PC 意图快捷入口改用结构化 WYSIWYG 状态

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏“下一步选一个”里的 `补画面/雷达` 缺口判断，改为优先读取 `action_status_cards.camera_preview.status` 与 `action_status_cards.radar_map_points.status`，不再依赖 `camera_wysiwyg_status_plain` 中文前缀。
- `pc-tools/workstation/test/App.test.ts`：新增回归，覆盖画面文案改成“已经看到画面...”但结构化卡片为 `visible` 的情况；快捷入口只提示补雷达点，并聚焦雷达卡，不调用任何运动接口。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`：同步记录快捷入口只消费结构化 WYSIWYG 状态的口径。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "routes the sensor shortcut"`，1 个目标测试通过。
- 通过：`npm --prefix pc-tools/workstation test`，2 个测试文件、382 个测试全部通过。
- 通过：`npm --prefix pc-tools/workstation run build`，TypeScript app/server 编译和 Vite build 通过；仅保留既有大 chunk 提示。
- 通过：`git diff --check`，未发现 whitespace/error。

## 剩余风险

- 这轮只修 PC 前端页面内聚焦和展示，不改变真实相机、雷达或底盘状态；live 仍需要相机首帧和雷达新鲜后才能完成建图启动条件。
