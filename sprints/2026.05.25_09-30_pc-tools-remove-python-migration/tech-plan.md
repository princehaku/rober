# PC Tools Remove Python Migration Tech Plan

## sprint_type

epic

## 技术目标

把 `pc-tools` 收敛为 Node.js + Vue 工作站主架构。旧 Python gate、Python helper、Python unittest 入口从 `pc-tools` 删除；仍有复用价值的 JSON、README、样例数据、脱敏 fixture 保留，并迁移为 Node 测试或工作站示例资产。

本轮不是硬件任务，不涉及 WAVE ROVER、ESP32、Orange Pi、UART、波特率、JSON 指令、速度映射、反馈协议、引脚、电压、固件或机械尺寸事实。

## 文件范围

后续 `full-stack-software-engineer` 允许改动：

- `pc-tools/**`
- `docs/product/pc_tools_workstation.md`
- `sprints/2026.05.25_09-30_pc-tools-remove-python-migration/tech-done.md`
- `sprints/2026.05.25_09-30_pc-tools-remove-python-migration/side2side_check.md`
- `sprints/2026.05.25_09-30_pc-tools-remove-python-migration/final.md`

后续咨询子 agent 只读范围：

- `pc-tools/route/**`
- `pc-tools/evidence/**`
- `docs/product/pc_tools_workstation.md`

禁止改动：

- `onboard/**`
- `mobile/**`
- `cloud-relay/**`
- repo 其他目录 Python 文件
- 硬件配置、ROS2 launch、串口参数、vendor 文档

## 迁移方案

1. 盘点 `pc-tools` 下所有 `*.py` 文件，按用途分为 route gate、evidence gate、training/labeling helper、Python tests、其他脚本。
2. 删除 Python 脚本和 Python 测试入口，不保留 Python runner、不保留 `python -m unittest discover pc-tools/route` 作为 gate。
3. 对仍有价值的非 Python 资产做迁移：
   - JSON fixture/data：保留到原位置或迁移到 `pc-tools/workstation/test/fixtures/`，但必须由 Node 测试或 API 示例读取。
   - README 或说明：保留时必须改写为 Node/Vue 工作站口径。
   - 脱敏 proof/route 样例：保留 `software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false` 语义。
4. 更新 Node API/UI：
   - 不再扫描 Python 文件清单作为工具索引。
   - Route Debug、Evidence Tools、Training/Labeling、Proof Boundary 改为展示 Node-native 资产和 fail-closed 摘要。
   - UI 不提供真实控制入口，不暴露 `/cmd_vel`、Start、Confirm、Cancel、Dropoff、Collect 等真实控制动作。
5. 更新 Node 测试：
   - 覆盖 health/proof boundary fail-closed 字段。
   - 覆盖 route/evidence fixture 的读取与坏数据 fail-closed。
   - 覆盖删除 Python 后的空状态或 Node-native 索引状态。
6. 更新文档与 sprint 收口：
   - `docs/product/pc_tools_workstation.md` 删除旧 Python gate 保留声明。
   - `tech-done.md` 记录删除列表、保留资产、验证结果。

## 验收命令

后续 `full-stack-software-engineer` 必须执行并记录输出：

```powershell
cd pc-tools/workstation && npm run build
cd pc-tools/workstation && npm run test
cd pc-tools/workstation && npm run lint
Get-ChildItem -Path pc-tools -Recurse -File -Include *.py | Where-Object { $_.FullName -notmatch '\\workstation\\node_modules\\' }
```

验收说明：

- 不再运行 `python -m unittest discover pc-tools/route -p "test_*.py"`。
- 最后一条 PowerShell 检查必须返回空结果；若返回任何 `pc-tools` 下的 Python 文件，必须继续定位并删除或说明它不在本轮范围内。
- 若 build/test/lint 任一失败，执行 owner 必须定位根因、修复并重新验证，不能把第一轮失败作为最终结果。

## 并行执行计划

本轮建议在实现阶段并行派发 3 个子 agent：

1. `full-stack-software-engineer`：主责写入与删除，范围为 `pc-tools/**`、`docs/product/pc_tools_workstation.md` 和本 sprint 收口文档。
2. `robot-algorithm-engineer`：只读咨询 route JSON/route debug fixture 保留建议，不改文件。
3. `robot-software-engineer`：只读咨询 proof boundary/fail-closed 字段保留建议，不改文件。

主责 owner 收到咨询事实后负责集成，不得把只读咨询结果当作完成证据。

## OKR 最低优先级核对

当前 `OKR.md` 4.1 节内容存在历史编码显示问题，无法在计划阶段可靠读取每个 Objective 的完成度数字。本轮不无证据提升任何 OKR 完成度。

本 sprint 是否针对最低 Objective：不做完成度承诺。CEO 明确指定继续推进 `pc-tools` 并删除旧 Python，本轮按该方向收敛 PC 工具链。若后续 Product Manager 需要更新完成度，必须先基于有效编码的 `OKR.md` 和实现验证证据重新核对。

## 风险与边界

- 删除 Python 后可能丢失历史测试覆盖；必须用 Node 测试承接仍有价值的 fixture/data。
- 如果 `pc-tools/workstation` 当前 API 依赖 Python 文件索引，删除后可能出现 UI 空态或测试失败，必须同步调整。
- 本轮验证只证明 PC 工作站 Node/Vue 软件链路，不证明真实 ROS2、Nav2、fixed-route runtime、路线采集、真实训练/标注、硬件串口、WAVE ROVER、HIL、手机浏览器或交付成功。
