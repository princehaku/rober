# PC Tools Remove Python Migration PRD

## sprint_type

epic

## 背景

`pc-tools/workstation` 已经作为 PC-only Node.js + Vue 工作站落地，但上一轮产品边界仍把 `pc-tools/evidence/**` 和 `pc-tools/route/**` 的旧 Python gate 视为保留资产，并继续要求 Python unittest 作为验收命令。

CEO 最新要求“继续 并删除旧python”后，产品边界需要调整：PC 工具不再是旧 Python gate 的可视化外壳，而是以 Node.js + Vue 为主架构的工作站。旧 Python 脚本和 Python 测试入口应退出 `pc-tools`。

## 用户价值

本轮服务对象是开发、调试、路线学习、标注准备和证据复盘使用者，不是普通手机端用户。迁移后的价值是：

- 降低 `pc-tools` 双栈维护成本，避免 Node/Vue 与 Python gate 两套入口长期并存。
- 让后续 route debug、训练/标注入口、proof boundary 都统一走 Node/Vue build/test/lint 验证。
- 保留 JSON fixture/data 等可复用资产，避免因为删除 Python 而丢失可回放样例。

## 需求范围

### 必须完成

1. `pc-tools` 主入口以 `pc-tools/workstation` 为准。
2. 删除 `pc-tools` 下旧 Python 脚本和 Python 测试入口，包括但不限于 `*.py`、`test_*.py`、Python-only runner 或 Python unittest 说明。
3. 将仍有产品价值的 JSON、README、示例数据、脱敏 fixture 保留为 Node 测试或工作站示例资产。
4. Node/Vue 工作站必须继续保留 fail-closed 产品语义：
   - `source=software_proof`
   - `proof_status=not_proven`
   - `safe_to_control=false`
   - `delivery_success=false`
   - `primary_actions_enabled=false`
   - `pc_only=true`
5. 验证命令切换为 Node/Vue：
   - `cd pc-tools/workstation && npm run build`
   - `cd pc-tools/workstation && npm run test`
   - `cd pc-tools/workstation && npm run lint`
   - PowerShell 检查 `pc-tools` 下不再残留 Python 文件。

### 明确不做

- 不删除 repo 其他目录 Python 文件。
- 不触碰 `onboard/**`、`mobile/**`、`cloud-relay/**`。
- 不接入真实 ROS2 runtime、Nav2、fixed-route runtime、串口、WAVE ROVER、HIL 或硬件控制。
- 不把 PC 工作站改造成手机端控制台。
- 不宣称 delivery success、dropoff/cancel completion、真实路线采集或真实训练/标注成功。

## 验收口径

后续实现完成后，必须满足：

1. Node/Vue build/test/lint 全部通过。
2. PowerShell 检查返回空结果：

```powershell
Get-ChildItem -Path pc-tools -Recurse -File -Include *.py | Where-Object { $_.FullName -notmatch '\\workstation\\node_modules\\' }
```

3. `docs/product/pc_tools_workstation.md` 不再要求运行 Python unittest，不再把旧 Python gate 列为保留资产。
4. 若保留 JSON 或其他 fixture/data，必须能说明它们被 Node 测试、Node API 或工作站示例消费。
5. `tech-done.md` 必须记录实际删除的 Python 文件类别、保留的非 Python 资产、验证输出和剩余风险。

## OKR 对齐

本轮主要对齐 Objective 3 的 PC route debug、路径学习、展示、训练/标注准备工具链。它也降低 Objective 4/5 相关工作台的维护复杂度，但本轮不产生真实手机、4G、云中转、OSS/CDN、HIL、WAVE ROVER 或交付成功证据，因此不得提升相关 Objective 完成度。
