# PC Tools Workstation Product Boundary

## 定位

`pc-tools/workstation` 是 PC-only Node.js + Vue 工作站，也是 `pc-tools` 的主架构入口。它服务开发、调试、证据复盘、路线 JSON 摘要展示以及训练/标注准备，不服务普通手机用户，也不直接控制机器人。

CEO 最新要求是删除 `pc-tools` 下旧 Python。当前产品边界中，旧 Python 脚本、Python helper、Python unittest 和 Python gate 入口均不再作为 `pc-tools` 资产保留。必要的非 Python 材料保留为 README、JSON fixture 或 Node/Vue 工作站测试资产。

## 主架构

```text
pc-tools/workstation/
```

主技术栈：

- Node.js API
- Vue UI
- TypeScript
- Vitest / ESLint / Vite build

`pc-tools/evidence/fixtures/**` 是 Evidence Tools 的 JSON fixture 来源。`pc-tools/route/` 只保留说明；Route Debug 的实际读取能力在 `pc-tools/workstation/src/server/routeDebugLoader.ts`。

## 功能入口

- Route Debug：通过 Node Route JSON Loader 读取本地 status/task/reconciliation JSON，生成 safe summary。
- Evidence Tools：索引 `pc-tools/evidence/fixtures/**/*.json`，展示 JSON fixture 资产分组。
- Training/Labeling：保留占位入口，明确未接真实训练或标注流水线。
- Proof Boundary：集中展示软件证明能覆盖什么、不能覆盖什么，避免误读为真实硬件或交付证明。

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
