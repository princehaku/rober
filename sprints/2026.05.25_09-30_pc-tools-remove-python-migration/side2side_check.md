# PC Tools Remove Python Migration Side2Side Check

## sprint_type

epic

## CEO 要求对照

| 要求 | 对照结果 |
| --- | --- |
| 删除 `pc-tools` 下所有旧 `.py` Python 脚本和 Python 测试文件 | 已删除 270 个 `.py`，最终 PowerShell 检查为空 |
| 不删除 repo 其他目录 Python | 本轮删除范围限定在 `pc-tools/**` |
| 保留非 Python 资产，尤其是 evidence fixtures JSON、README、Node/Vue 工作站 | 已保留 `pc-tools/evidence/fixtures/**`、README 和 `workstation/**` |
| Evidence Tools 不再扫描 Python 文件，改为 Node-native 资产/fixture 索引 | `buildEvidenceToolsResponse()` 改为索引 `fixtures/**/*.json` |
| Route Debug 不再把旧 route Python 文件当 gate 文件，改为 Node Route JSON Loader 能力 | API/UI 改为 `node_route_json_loader` |
| 所有 proof flags 继续 fail-closed | 测试覆盖 `delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false` |
| 更新相关文档 | 已更新 `pc-tools/README.md`、`pc-tools/route/README.md`、`pc-tools/evidence/README.md`、`docs/product/pc_tools_workstation.md` |
| 新增/更新 Node 测试 | `npm run test` 通过，2 个测试文件 8 条用例 |
| 更新 sprint 收口文档 | 已更新 `tech-done.md`、`side2side_check.md`、`final.md` |

## 验收命令对照

- `npm run build`：通过。
- `npm run test`：通过，8 tests passed。
- `npm run lint`：通过。
- `.py` 范围检查：空结果。

## 边界确认

本轮未触碰 `onboard/**`、`mobile/**`、`cloud-relay/**`、硬件配置、ROS2 launch 或 vendor 文档事实。验证范围是 PC 工作站软件证明，不扩展为 HIL、真实串口、真实路线、真实手机或真实交付成功。
