# PC Tools Remove Python Migration Pre Start

## sprint_type

epic

## CEO 最新要求

CEO 明确要求：“继续 并删除旧python”。

这推翻上一轮 `pc-tools` Node/Vue 工作站继续保留旧 Python gate 与 `python -m unittest discover pc-tools/route` 验证入口的边界。本轮目标改为：`pc-tools` 以 `pc-tools/workstation` 的 Node.js + Vue 工作站为主架构，删除 `pc-tools` 下旧 Python 脚本和 Python 测试入口，只保留必要的非 Python fixture/data 作为 Node 测试或示例资产。

## 上轮边界变化

上一轮 `2026.05.25_08-40_pc-tools-node-vue-workstation` 的收口结论仍把旧 Python route/evidence gate 作为保留资产，并要求继续运行：

```text
python -m unittest discover pc-tools/route -p "test_*.py"
```

本轮不再采用该验收口径。后续实现必须移除 `pc-tools` 下旧 Python 脚本和 Python 测试入口，并把验证口径切换为 Node/Vue 的 build、test、lint 和 `pc-tools` Python 文件残留检查。

## 本轮目标

1. 将 `pc-tools` 的主架构收敛为 `pc-tools/workstation` Node.js + Vue 工作站。
2. 删除 `pc-tools/evidence/**`、`pc-tools/route/**`、`pc-tools/training/**`、`pc-tools/labeling/**` 等 `pc-tools` 范围内的旧 Python 脚本和 Python 测试入口。
3. 保留必要的 JSON、README、示例数据、测试 fixture 或脱敏样本，但它们必须被 Node 测试或工作站示例消费，不再依赖 Python runner。
4. 更新 `docs/product/pc_tools_workstation.md`，明确旧 Python gate 已退出产品边界。
5. 不删除 repo 其他目录 Python，不触碰 `onboard/**`、`mobile/**`、`cloud-relay/**`。

## Owner 与执行方式

本轮是 Epic sprint，但写入和删除范围主要集中在 `pc-tools/**` 与产品文档。后续实现阶段建议按以下方式派发：

- `full-stack-software-engineer`：主责实现 Node/Vue 工作站迁移、删除 `pc-tools` Python、补 Node 测试、运行验收命令。
- `robot-algorithm-engineer`：只读咨询 `pc-tools/route` 中哪些 JSON/route fixture 应保留为 Node 测试资产，不改文件。
- `robot-software-engineer`：只读咨询 proof boundary/fail-closed 语义是否在 Node 工作站里保留，不改文件。

若实现阶段最终只派 1 个子 agent，必须在 `tech-done.md` 说明原因：本轮写范围高度集中在 `pc-tools` 前端/Node 工具链，其他角色仅提供只读事实补充。

## 范围边界

允许后续实现改动：

- `pc-tools/**`
- `docs/product/pc_tools_workstation.md`
- 当前 sprint 的 `tech-done.md`、`side2side_check.md`、`final.md`

本计划阶段仅允许改动：

- `sprints/2026.05.25_09-30_pc-tools-remove-python-migration/**`
- `docs/product/pc_tools_workstation.md`
- `OKR.md` 仅可新增说明，不得无证据提升完成度

禁止后续实现改动：

- `onboard/**`
- `mobile/**`
- `cloud-relay/**`
- repo 其他目录 Python 文件
- 硬件配置、ROS2 launch、串口参数、vendor 文档事实

## 风险预判

- 删除旧 Python 可能会移除历史 proof/route gate 的唯一测试入口，必须先把仍有价值的 fixture/data 迁移到 Node 测试。
- 当前工作站如果仍扫描旧 Python 文件清单，删除后 UI/API 需要切换成 Node-native 资产索引，不能出现空壳页面。
- 本轮不涉及硬件事实，因此不新增 WAVE ROVER、ESP32、Orange Pi、UART、波特率、JSON 指令、反馈协议、引脚、电压、固件或机械尺寸结论。
