# 2026.06.30 15:05 PC visual-first WYSIWYG layout

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `.robot-console-grid` 增加 `data-layout="visual-first"`，让测试和 smoke 能证明当前页面是画面/地图优先布局。
  - 实时画面卡增加 `data-wysiwyg-surface="primary-camera"`。
  - 地图卡增加 `data-wysiwyg-surface="primary-map"` 与 `data-default-size="large"`；地图 viewport 也暴露同一 WYSIWYG surface。
  - 修正自由移动建图区几行 tab 缩进，避免后续 `diff --check` 噪声。
- `pc-tools/workstation/src/styles.css`
  - 普通首屏桌面布局改为 12 栅格，画面卡占 7 栅格、雷达卡占 5 栅格，连接/自由移动/移动导航各占 6 栅格。
  - 相机预览框增加 `min-height: 260px`，避免桌面端真实画面被压成小条。
  - 地图默认大图高度从 `clamp(420px, 68vh, 760px)` 提升为 `clamp(560px, 78vh, 980px)`；普通收起态也提升到 `clamp(360px, 52vh, 560px)`；全屏地图可用高度提升为 `calc(100vh - 190px)`。
- `pc-tools/workstation/test/App.test.ts`
  - 锁定 `visual-first` 布局、primary camera/map WYSIWYG surface、地图默认 large 和新的尺寸 CSS。
- `docs/product/pc_tools_workstation.md`、`pc-tools/README.md`
  - 同步普通首屏 visual-first 布局和只读安全边界。

## 验证结果

- `cd pc-tools/workstation && npm test -- test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`
  - 通过：`Test Files 1 passed (1)`，`Tests 1 passed | 218 skipped (219)`。
- `cd pc-tools/workstation && npm test -- --run`
  - 通过：`Test Files 2 passed (2)`，`Tests 389 passed (389)`。
- `cd pc-tools/workstation && npm run build`
  - 通过：Vite build 成功；保留既有 `Some chunks are larger than 500 kB after minification` warning。
- `git diff --check`
  - 通过：无 whitespace error。
- 7001 live 更新：
  - 已重启：`npm run api -- --host 0.0.0.0 --port 7001`，`lsof` 显示 `TCP *:7001 (LISTEN)`。
  - `curl -fsS http://127.0.0.1:7001/` 通过，首页加载当前构建产物。
  - `GET http://127.0.0.1:7001/api/robot-control/summary` 只读通过：HTTP 200，`schema=trashbot.pc_tools_workstation.robot_control_summary.v1`，`map_status=visible`，`card_count=7`。
  - `curl` 当前 CSS 产物可匹配 `visual-first`、`clamp(560px,78vh,980px)`、`calc(100vh - 190px)` 和 `min-height:260px`。

## 剩余风险

- 本轮只改 PC Web 侧布局和 DOM 证据，没有做真实浏览器截图 smoke，也没有触发真实雷达、相机、Nav2、manual、keyboard、free-roam 或 `/cmd_vel`。
- 目标仍未完全完成：完整 Nav2 路线执行、真实键盘连续控制、真实雷达贴图和建图仍需要继续按硬件/现场验证推进。
