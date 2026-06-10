# PC Simple User UI Restore

## sprint_type

micro

## 背景

- Owner：`full-stack-software-engineer`。
- 时间：2026-06-11 01:18:02 CST。
- 用户反馈：PC Robot Control 首屏被改成偏工程/诊断风格，需要恢复之前面向普通用户的简洁体验。
- 本轮边界：只做体验降噪和普通用户化，不改后端 proxy 合同，不降低安全边界，不启用真实自动导航、`cmd_vel` 或持续手控。

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 首屏标题改回 `Rober 小车控制台`。
  - 首屏保留 5 个简单卡片：`小车连接`、`实时画面`、`雷达`、`地图`、`移动/导航`。
  - 地图卡片只保留 `刷新地图`、`查看地图列表` 和短状态；`保存地图`、`map_name`、`artifact_path` 移入高级诊断。
  - 移动/导航卡片只保留状态说明、`停止`、自动导航未开放和最近证据摘要。
  - 非 stop 点动方向、速度/时长输入、现场确认 checklist、readback 和控制边界字段全部移入高级诊断的 `现场点动设置 / 控制边界`。
  - 保存类 lifecycle 结果不再把 `mode/executed` 细节回流到地图首屏，只提示高级操作已返回。
- `pc-tools/workstation/src/styles.css`
  - 新增首屏 `停止` 按钮的紧凑样式，保持按钮尺寸稳定。
- `pc-tools/workstation/test/App.test.ts`
  - 更新 Robot Control 默认页断言，确保首屏不再出现点动方向、速度/时长输入、现场 checklist 或保存地图。
  - 更新 map lifecycle 测试，确认保存地图仍可在高级诊断触发并保留诊断结果。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 2026-06-11 UI 回归修正：首屏普通用户化，高级诊断保留工程字段和安全门槛，后端合同不变。
- `sprints/2026.06.11_01-25_pc_simple_user_ui_restore/tech-done.md`
  - 新增本 micro sprint 留档。

## 设计取舍

- 首屏保留：连接/刷新、打开/关闭实时画面、刷新雷达、刷新地图、查看地图列表、停止。
- 首屏下沉：`source=software_proof`、`proof_status=not_proven`、`safe_to_control=false`、raw evidence/readback、HIL checklist、速度/时长输入、四向点动、保存地图、map lifecycle start/reset。
- 安全边界不变：非 stop 点动仍需要完整现场确认；stop 仍可单独发送；自动导航、键盘控制、map click goal、`cmd_vel` 和真实 map start 仍不开放。

## 验证结果

- `cd pc-tools/workstation && npm run build`
  - 通过。
  - 关键输出：`✓ built in 919ms`。
- `cd pc-tools/workstation && npm run test`
  - 通过。
  - 关键输出：`Test Files  2 passed (2)`，`Tests  71 passed (71)`。
  - 第一轮失败定位：地图首屏默认提示仍包含“保存地图”；修复后重跑通过。
  - 第二轮失败定位：测试断言误期望 `mode=dry_run_stub`，而当前 fixture 合同是 `software_guard_command_not_configured`；对齐断言后重跑通过。
- `cd pc-tools/workstation && npm run lint`
  - 通过。
  - 关键输出：`eslint .` 无报错。
- `git diff --check`
  - 通过，无 whitespace error。
- 本地 UI smoke：
  - 启动：`PORT=8794 npm run api`。
  - 浏览器 URL：`http://127.0.0.1:8794/`。
  - 默认打开是 `Robot Control` 普通用户页，页面标题与面板标题均为 `Rober 小车控制台`。
  - 首屏 5 个卡片齐全：`小车连接`、`实时画面`、`雷达`、`地图`、`移动/导航`。
  - 首屏检查通过：不含 `source=software_proof`、`proof_status=not_proven`、`safe_to_control=false`、raw readback、HIL checklist、速度/时长输入、保存地图、四向点动；保留 `停止`。
  - 展开 `高级诊断` 后检查通过：能找到 `现场点动设置 / 控制边界`、四向点动、速度/时长输入、现场确认 gate、保存地图、readback、安全字段和 disabled 的 map start/reset。
  - 证据 artifact：`sprints/2026.06.11_01-25_pc_simple_user_ui_restore/artifacts/ui_smoke_2026-06-11.json`。
- 主节点补充验收：
  - 复用本机 workstation 服务 `http://127.0.0.1:8787/` 做浏览器 DOM 验收。
  - 首屏标题为 `Rober 小车控制台`，5 个卡片齐全。
  - 首屏不含 `保存地图`、四向点动、HIL checklist、速度/时长、`source=software_proof`、`proof_status=not_proven`、`safe_to_control=false` 或 `readback`。
  - 浏览器 console `warn/error` 为空。
  - 补充截图 artifact：`sprints/2026.06.11_01-25_pc_simple_user_ui_restore/artifacts/browser_simple_ui_acceptance.png`。
  - `python3 -m json.tool sprints/2026.06.11_01-25_pc_simple_user_ui_restore/artifacts/ui_smoke_2026-06-11.json >/dev/null` 通过。

## 剩余风险

- 本轮只做 PC 首屏体验回归和测试更新，没有改上位机、onboard、后端 proxy 合同或硬件配置。
- UI smoke 使用本地 workstation 页面和默认空 baseUrl，不代表真实上位机摄像头、雷达、地图或底盘现场联调通过。
- 高级诊断仍保留工程字段和受控点动能力；这是有意保留的排障入口，不应作为普通用户首屏操作路径。
