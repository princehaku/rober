# sprint_type: micro

## 实际改动

- 将 PC 普通首屏 `执行图上路线` 的小车 map 位姿缺失从硬阻塞降级为 WYSIWYG 警告：地图上已有当前路线且已勾选现场安全确认时，按钮保持 `执行图上路线` 并允许调用 `/api/robot-control/nav2/goal/execute`。
- 更新行程事实、行程状态、最小确认、进度卡和主进度按钮聚焦文案：缺少小车位置时提示“仍可执行，结果以上车端返回为准”，不再引导先重新定位。
- 更新 PC 工作站测试，覆盖“路线可见 + 小车位姿缺失 + 安全确认”仍会触发 Nav2 execute，且不会调用 manual。
- 同步更新 `docs/product/pc_tools_workstation.md`，记录定位显示缺失不再作为发车前硬挡。

## 验证结果

- `npm test -- --run App.test.ts -t "draws no-motion route markers and still executes"`：通过，1 个测试通过。
- `npm test`：通过，2 个测试文件、287 个测试通过。
- `npm run build`：通过，Vite 保留既有 chunk size warning。

## 剩余风险

- 本轮只改 PC 前端 gate 与文案，没有触发真实小车运动；真实 Nav2 执行仍需要 operator 在现场勾选安全确认并点击执行。
- 上车端当前行程是否真正带动车轮，仍以后端严格轮速 L/R 同窗口反馈为准；上一轮 live 证据显示 Nav2 返回成功但轮速 L/R 仍未证明非零。
- 摄像头源仍处于 `source_first_frame_failed / uvc_no_frame_not_exclusive` 诊断状态，本轮未继续处理摄像头驱动层。
