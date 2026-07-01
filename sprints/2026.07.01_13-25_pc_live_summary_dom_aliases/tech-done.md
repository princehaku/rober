# PC 首屏 Live Summary DOM Alias

sprint_type: micro

## 实际改动

- `plain-live-closure-summary` DOM 同步暴露易读 alias：`data-nav2-route-ready`、`data-live-wysiwyg-camera-visible`、`data-live-wysiwyg-map-visible`、`data-primary-action-id`、`data-keyboard-continuous-ready`、`data-keyboard-continuous-motion-verified`、`data-keyboard-continuous-forwarded-pulses`。
- 这些字段只复用已有 summary alias 和权威字段，不改变按钮行为、不新增请求、不触发任何运动控制。
- 更新 PC 主测试和产品文档，明确 DOM alias 仅用于页面 smoke/现场脚本读取。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`，结果 `1 passed | 230 skipped`。
- 通过：`npm run lint`。
- 通过：`npm run build`，Vite build 成功；仍提示既有 chunk 大小 warning。
- 通过：`npm test`，结果 `3 passed` test files，`417 passed` tests。
- 通过：`git diff --check`。

## 剩余风险

- 本轮只改 DOM 只读属性；不执行 Nav2、manual、keyboard、free-roam、建图、delivery、stop 或 `/cmd_vel`。
- 工作区仍有两个历史 artifact 脏文件，本轮不纳入提交。
