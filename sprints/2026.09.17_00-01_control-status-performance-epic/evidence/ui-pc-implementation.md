# PC 控制与状态性能实施证据

- Owner：full-stack-software-engineer；验证时间：2026-09-18 00:09（Asia/Shanghai）。
- 环境：Windows 10.0.22631 x64，Node v24.12.0；Vue 3.5.34、Vitest 4.1.7、Vite 7.3.3（`npm ci` 恢复现有锁定依赖后复验；package.json / package-lock.json 未改）。
- 实施：Stop/Space 独立请求；迟到 manual/operator 回执不覆盖 Stop；ACK 后后台单实例状态回读；App 刷新保留 WebRTC；两个摘要共用一次上位机状态采样；保留 409 serial_busy / preempted 业务结果。

## 验证结果

在 `pc-tools/workstation/` 执行：

| 命令 | 实际结果 |
| --- | --- |
| `npm.cmd ci` | 成功，352 packages；恢复锁定依赖 |
| `npm.cmd test -- --run` | 4 test files，110/110 passed；3.91s |
| `npm.cmd run build` | TypeScript + Vite + server TypeScript 全部成功；14 modules，834ms |
| `npm.cmd run lint` | exit 0，无 lint 错误 |
| `node scripts/control-status-performance-probe.mjs --output ../../sprints/2026.09.17_00-01_control-status-performance-epic/evidence/ui-pc-performance.json` | 7/7 passed；1.93s |
| 限定本轮 PC 和相关文档的 `git diff --check` | exit 0 |

新增/修改非空代码行中的有意义中文技术注释为 92/456，约 20.18%。

## 可复跑证据与结果

- `ui-pc-baseline.json`：修改前实际 fake-fetch 执行，live panel + direct status 合计远端 `/api/status` 2 次。
- `ui-pc-performance.json`：probe 调用真实 Vue DOM 和生产代理，记录更新后一轮 status 1 次、刷新媒体卸载/close 0、后台状态回读最大在途 1；manual/operator 在途时 Stop 已派发，Space 独立停车，迟到回执未覆盖 Stop，ACK 不等待状态，409/preempted 保留。
- 统一 collector：输出文件名为 `ui-performance.json` 时，probe 在 PC 测试通过后运行 `node --test mobile/web/test_mobile_performance.mjs`，读取本轮手机产物并生成 `trashbot.control_status_ui_performance.v1` 聚合证据；`ui-pc-*` 继续只输出 PC。追加分支已通过 `node --check` 和定向 ESLint，完整聚合由父节点统一执行。
- 已修复：原 node_modules 平台不匹配、可选布尔类型、Vue 测试包装代理身份比较、既有未使用测试参数 lint；修复后用锁定依赖完整复验通过。

## 剩余风险与验证边界

全部为 jsdom + fake fetch + fake WebRTC 的离线软件证据，没有访问真实设备或部署。保留原人工确认、点动限幅和固定安全字段；HTTP 接受及 preempted 不代表物理运动或停车成功。真实 WebRTC、HIL、4G、CPU 降幅与物理停车时延仍需现场验证。未修改 mobile、Robot、旧 sprint 或本轮收口文档。
