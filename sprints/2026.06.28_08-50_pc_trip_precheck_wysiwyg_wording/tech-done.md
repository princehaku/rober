# PC 行程前确认地图同步文案收敛

sprint_type: micro

## 实际改动

- 将普通首屏 `plain-trip-minimal-precheck` 在地图画面/proof 刷新中时的文案，从“等待刷新后再执行”改为“地图画面同步完成后即可执行（当前等待刷新）”，避免把所见即所得同步误读成额外预检。
- 更新对应 App 断言，分别覆盖地图画面刷新 pending 和地图状态刷新 pending 两种路径。
- 同步更新 `pc-tools/README.md` 与 `docs/product/pc_tools_workstation.md`，记录发车前确认仍只保留现场安全确认，地图刷新等待只是 WYSIWYG 同步条件。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "blocks visible-route execution while the map preview is refreshing"`，1 个测试通过，203 个同文件测试按筛选跳过。
- 通过：`npm test`，2 个 test files、352 个测试全部通过。
- 通过：`npm run lint`。
- 通过：`npm run build`；保留既有 Vite chunk 超过 500 kB 提示，构建成功。
- 通过：`git diff --check`。

## 剩余风险

- 本轮只做 PC 前端文案和测试收敛，不连接真实上位机，不发送 Nav2、manual、keyboard、delivery、stop 或 `/cmd_vel` 控制请求。
