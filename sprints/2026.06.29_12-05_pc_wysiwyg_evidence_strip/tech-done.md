# PC 当前所见只读条

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏在“当前事实”下新增“当前所见”只读条，把画面、地图、雷达点三类 WYSIWYG 事实分开展示；每行 `去处理` 只调用既有页面内聚焦逻辑。
- `pc-tools/workstation/src/styles.css`：新增“当前所见”响应式布局，桌面展示为紧凑状态行，移动端自动换行。
- `pc-tools/workstation/test/App.test.ts`：补充首屏断言，确认当前所见条展示 3 行、雷达点数量明确、不出现工程诊断词，并确认按钮只聚焦不发请求。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`：同步记录“当前所见”条的只读边界。

## 验证结果

- 已通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "renders Robot Control V1 by default"`。
- 已通过：`npm --prefix pc-tools/workstation test`，2 个测试文件、376 个测试通过。
- 已通过：`npm --prefix pc-tools/workstation run build`；仍有既有 Vite chunk size warning。
- 已通过：PC API 已重启到 `0.0.0.0:7001`，监听 PID `50964`；只读读取 `GET /api/health` 成功，mode 为 `pc_only_readonly_workstation`。
- 已通过：只读读取 `GET /api/robot-control/summary`，live 显示地图画面、图上路线和小车位置已显示；雷达当前图上 0 点、旧来源点 81 个只作诊断；摄像头仍为非独占但 UVC 无视频帧。

## 剩余风险

- 这次只改善 PC 首屏 WYSIWYG 可读性，不调用相机 offer、雷达启动、地图刷新、Nav2 执行、自由移动或键盘运动接口。
- live 真实状态仍需现场处理：摄像头 UVC 无首帧、雷达未运行或扫描已停、Nav2 需要安全确认后重跑并复验轮速 L/R 非零。
