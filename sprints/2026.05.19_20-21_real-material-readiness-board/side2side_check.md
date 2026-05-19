# Sprint 2026.05.19_20-21 Real Material Readiness Board - Side2Side Check

## 1. 验收对象

本轮验收对象是 `real_material_readiness_board` 从产品口径到工程实现的对照：

- PRD 要求：把 Objective 5 external、Objective 1 / PR #5 hardware、PR #4 route/elevator、Objective 4 real phone 四类真实材料缺口统一成一个只读、fail-closed 的 board。
- Tech Plan 要求：PC/evidence gate 生成 artifact，Robot diagnostics 暴露 safe alias，mobile/web 展示只读“真实材料就绪看板”，Product closeout 保守更新 OKR。
- 工程结果：Hardware/Autonomy、Robot、Full-Stack worker 均完成对应文件范围与 targeted validation。

## 2. 用户价值对照

用户价值成立但仍是 software proof：现场 owner 可以从一个 board 看见“下一步缺哪类真实材料、谁负责、什么证据才能推进”，不用在 O5、Objective 1 / PR #5、PR #4 route/elevator、Objective 4 mobile 多条 closeout 链路中查找。

产品北极星仍未达成真实业务闭环：普通手机用户真实完成送垃圾任务仍缺真实手机、真实云/4G、真实 WAVE ROVER/UART/HIL、真实 PR #4 route/elevator field pass、真实 Nav2/fixed-route、dropoff/cancel completion 和 delivery success。

## 3. OKR 映射对照

- Objective 5：仍约 68%。本轮只把 O5 external proof 缺口纳入 `real_material_readiness_board`，没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或 real external proof。
- Objective 1：仍约 81%。board 展示 WAVE ROVER/UART/HIL 与 PR #5 `PRRT_kwDOSWB9286CJ3tX` 所需真实硬件材料，但不关闭 PR #5 thread，不证明 O1 HIL，也不提高百分比。
- Objective 2 / Objective 3：仍约 99%。board 展示 PR #4 route/elevator 缺真实现场材料；Autonomy consult 明确仍缺 elevator door state、target floor confirmation、human assistance record、Nav2/fixed-route runtime log、field task record、route completion signal、dropoff/cancel material 和 delivery_result。
- Objective 4：仍约 99%。board 展示真实 iPhone/Android、production app、PWA prompt/userChoice、true phone/browser acceptance 缺口，但不声明真实手机验收通过。

## 4. OKR 最低优先级核对回顾

`tech-plan.md` 中的 `## OKR 最低优先级核对` 仍成立：

- Objective 5 数字最低，约 68%，但 blocked by real external materials。Docker-only 主机没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或 real external proof。
- Objective 1 下一低，约 81%，但 PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `blocked_pending_real_materials`，真实 WAVE ROVER/UART/HIL 与真实 2D LiDAR / ToF materials 均未到位。
- 本轮不新增第四个 mobile wrapper，不新增第三个 route/elevator wrapper，而是把四类真实材料缺口统一路由成一个 read-only board。

## 5. 证据边界对照

验收通过的边界是：

- `software_proof_docker_real_material_readiness_board_gate`
- `source=software_proof`
- `software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

不得改写为：

- Objective 5 external proof。
- Objective 1 HIL、WAVE ROVER/UART 或 PR #5 hardware material proof。
- PR #5 `PRRT_kwDOSWB9286CJ3tX` 可关闭。
- PR #4 route/elevator field pass。
- Objective 4 real phone/browser acceptance。
- dropoff/cancel completion、delivery success 或 safe-to-control grant。

## 6. 工程验证对照

- Hardware / Autonomy PC gate：vendor sources 已读，`Ran 5 tests OK`，artifact generation passed，required `rg` 与 scoped diff check passed。
- Robot worker：diagnostics unittest `Ran 213 tests OK`，py_compile、required `rg`、scoped diff check passed。
- Full-Stack worker：mobile tests `Ran 137 tests ... OK`，py_compile、`node --check mobile/web/app.js`、required `rg`、scoped diff check passed。
- Product closeout：required file check、required `rg`、scoped `git diff --check` passed。

## 7. 结论

本轮 side-by-side 对照通过：工程实现和产品文档满足 PRD / Tech Plan 的只读真实材料就绪看板要求，并保持证据边界。验收结论是“`real_material_readiness_board` routing readiness / software proof 完成”，不是“真实材料到位”。
