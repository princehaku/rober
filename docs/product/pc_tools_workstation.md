# PC Tools Workstation Product Boundary

## 定位

`pc-tools/workstation` 是 PC-only Node.js + Vue 工作站，也是 `pc-tools` 的主架构入口。它服务开发、调试、证据复盘、路线 JSON 摘要展示以及训练/标注准备，不服务普通手机用户，也不直接控制机器人。

CEO 最新要求是删除 `pc-tools` 下旧 Python。当前产品边界中，旧 Python 脚本、Python helper、Python unittest 和 Python gate 入口均不再作为 `pc-tools` 资产保留。必要的非 Python 材料保留为 README、JSON fixture 或 Node/Vue 工作站测试资产。

## 主架构

```text
pc-tools/workstation/
  src/App.vue                         # 全局状态、布局和页面组合
  src/client/workstationApi.ts        # /api/* client 与 query 参数拼接
  src/components/*.vue                # Route/Evidence/Training/Proof 页面组件
  src/server/index.ts                 # Express API 与静态 UI 托管入口
  src/server/catalog.ts               # Route Debug 响应聚合
  src/server/evidenceAssets.ts        # Evidence JSON fixture 索引
  src/server/waveRoverMaterialCoverage.ts # WAVE ROVER material coverage 只读扫描
  src/server/proofBoundary.ts         # Health、Training/Labeling、Proof Boundary 契约
  src/server/paths.ts                 # 仓库内路径和安全展示路径
  src/server/routeDebugLoader.ts      # 本地 route/status/task/reconciliation JSON safe summary
  src/shared/contracts.ts             # 前后端共享 fail-closed 契约
```

主技术栈：
- Node.js / Express API
- Vue / Vite UI
- TypeScript
- Vitest / ESLint / Vite build

前端分层约束：
- `App.vue` 只保留全局状态、刷新流程、错误处理和页面组合。
- `src/client/workstationApi.ts` 集中封装 `/api/*` 路径、fetch 和 route debug query 参数拼接。
- `src/components/` 只做展示与本地交互，不直接拼 API URL，不发明机器人状态。

后端分层约束：
- `index.ts` 只挂载本地 PC API 和构建后的静态 UI，不挂载 ROS2、串口、控制或云端生产客户端。
- `catalog.ts` 只保留 Route Debug summary 聚合。
- `evidenceAssets.ts` 只索引 `pc-tools/evidence/fixtures/**/*.json`，不扫描或执行 `.py`。
- `proofBoundary.ts` 集中输出 health、训练/标注占位和 proof boundary。
- `routeDebugLoader.ts` 只读本地 JSON 并生成 safe summary；坏 JSON、缺文件、成功声明、控制声明、敏感复制和 evidence_ref 错配均 fail-closed。

`pc-tools/evidence/fixtures/**` 是 Evidence Tools 的 JSON fixture 来源。`pc-tools/route/` 只保留说明；Route Debug 的实际读取能力在 `pc-tools/workstation/src/server/routeDebugLoader.ts`。

## 功能入口

- Route Debug：通过 Node Route JSON Loader 读取本地 status/task/reconciliation JSON，生成 safe summary。
- Evidence Tools：索引 `pc-tools/evidence/fixtures/**/*.json`，展示 JSON fixture 资产分组。
- Hardware Materials：`GET /api/tools/hardware-materials` 扫描 `pc-tools/evidence/fixtures/wave_rover_*` 下的 WAVE ROVER 材料组，识别 `feedback_T1001.log`、`odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl`、`operator_hil_report` / `operator_hil_report.json` 的 present/missing coverage，并在 Vue 面板中展示缺口。
- Training/Labeling：保留占位入口，明确未接真实训练或标注流水线。
- Proof Boundary：集中展示软件证明能覆盖什么、不能覆盖什么，避免误读为真实硬件或交付证明。

## WAVE ROVER Material Coverage 边界

Hardware Materials 是 Node-native 只读入口，不恢复旧 Python evidence gate，不执行 ROS2、串口、HIL 或任何控制动作。它只统计本地 fixture 材料覆盖：

- 顶层 API 固定继承 `source=software_proof`、`proof_status=not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`pc_only=true`。
- 每个 `wave_rover_*` 材料组输出 `group`、`fixture_relative_path`、present/missing materials、coverage counts 和 material coverage status。
- UI 文案必须明确 `coverage is not HIL pass`。文件齐备只说明材料 coverage，不说明 WAVE ROVER 上电、真实 UART 连通、轮向正确、反馈频率达标、IMU/battery 标定通过或真实 delivery success。
- 允许展示的 bounded vendor facts 来自 `docs/vendor/VENDOR_INDEX.md` 指向的本地资料：UART newline-delimited JSON、`json.dumps(data)+'\n'` 写串口、`readline()` 读、ESP32 newline 后 `deserializeJson()`、`FEEDBACK_BASE_INFO=1001`、`T=1/T=13/T=130/T=131/T=142/T=143`、`T=1001` feedback 字段 `L/R/r/p/y/v`。
- 必须保留的 fail-closed token 包括：`hil_pass=false`、`hardware_connected=false`、`serial_path_not_proven`、`baudrate_link_not_proven`、`wheel_direction_not_proven`、`cmd_ros_ctrl_not_proven_on_chassis`、`feedback_frequency_not_proven`、`imu_calibration_not_proven`、`battery_calibration_not_proven`、`delivery_success_not_proven`。

## Fail-Closed 契约

所有 API/UI 必须可追溯到以下字段：
- `source=software_proof`
- `proof_status=not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `pc_only=true`

即使本地 JSON 读取成功，`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false` 仍固定不变。工作站不得因为存在 route/evidence fixture 而声明真实路线通过、真实投放完成或机器人可控制。

## 禁止声明

第一阶段不得声明完成：
- 真实 ROS2 runtime
- 真实 Nav2/fixed-route runtime pass
- 真实路线采集或关键帧实景验证
- 真实电梯、WAVE ROVER 运动、串口反馈或 HIL pass
- dropoff/cancel completion、delivery success 或安全控制
- 真实手机/browser proof
- 4G、云端、OSS/CDN 生产链路
- 真实训练、真实标注、真实投放或真实交付成功

UI 不提供 Start、Confirm、Cancel、Dropoff、Collect 或任何真实控制入口。

## 运行与验证

工作站验证只使用 Node/Vue gate：

```bash
cd pc-tools/workstation && npm run build
cd pc-tools/workstation && npm run test
cd pc-tools/workstation && npm run lint
```

删除旧 Python 的范围检查使用 PowerShell：

```powershell
Get-ChildItem -Path pc-tools -Recurse -File -Include *.py | Where-Object { $_.FullName -notmatch '\\workstation\\node_modules\\' }
```

该检查应返回空结果。上述验证只证明 PC 工作站软件链路，不证明真实机器人、真实硬件、真实手机、真实云链路或真实交付成功。
