# Sprint 2026.05.18_08-09 Route Task Field Retest Drill Console - PRD

sprint_type: epic

## 1. 产品问题

上一轮 `route_task_field_retest_operator_drill` 已把 material callback review decision 变成 operator commands、callback checklist、required outputs 和 rerun commands，但现场 operator 仍缺一个统一控制台来执行、查看、导出和回填这些演练材料。

如果继续只堆材料包或回执清单，现场人员仍可能不知道下一步该按哪个顺序收集 route/elevator 证据；如果把演练清单说成完成，则会误导 Objective 2 / 3 / 4 的真实进度。因此本轮要做 `route_task_field_retest_drill_console`：把 operator drill 变成可执行、可导出的演练控制台 software proof。

## 2. 用户价值和产品北极星

北极星：普通手机用户最终能完成一次低成本送垃圾任务，并在失败或需要人工协助时知道该做什么。

本轮面向的是现场 operator / support user，不是普通用户直接发车。价值是让 operator 在 Docker-only 主机上提前获得一套一致的演练控制台，现场拿到真实材料后可以按同一 `evidence_ref` 回填，而不会把软件演练误认为真实送达闭环。

## 3. OKR 映射

主要映射：

- Objective 2：可送垃圾任务 + 电梯 assisted delivery 必达闭环。本轮把电梯门状态、目标楼层确认、人工协助、失败/接管材料转成 operator drill console 的必填和导出字段。
- Objective 3：可验证导航与固定路线。本轮把 Nav2/fixed-route runtime log、route completion signal、task record、dropoff/cancel completion、delivery result 的材料要求转成可复跑、可导出的演练控制台。
- Objective 4：手机用户体验与低成本量产边界。本轮让 mobile/web 和 diagnostics 只读呈现 drill console 摘要，让 support 可以收集材料，但不改变普通用户主操作 gating。

不作为本轮进度主线：

- Objective 5：虽是最低约 68%，但缺真实 external proof；本轮没有公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external material。
- Objective 1：约 81%，但缺真实 WAVE ROVER/UART/HIL、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report 和 PR #5 2D LiDAR / ToF 实物材料。

## 4. 证据依据

- `OKR.md` 4.1：Objective 5 约 68%，Objective 1 约 81%；两者在当前 Docker-only 主机分别受 external proof 和 HIL/hardware material 阻塞。
- PR #4：elevator-assisted delivery 已成为主链路必达能力；PR #4 testing 说明没有 runtime integration tests，因此不能把 PR #4 视为真实运行闭环完成。
- PR #5 review P1：`docs/product/production_hardware_boundary.md` default hardware set 与 `monocular + 2D LiDAR + ToF` mandatory baseline 矛盾。
- PR #5 review P2：mandatory sensor assumptions 缺少 `docs/vendor/` evidence citation，说明 2D LiDAR / ToF 仍是真实材料缺口。
- 最新 sprint `2026.05.18_07-08_route-task-material-review-operator-drill/final.md`：operator drill 已消费 material callback review decision，但没有真实 field pass；下一步建议带到 PR #4 现场材料回填或继续做现场演练层。

## 5. 本轮核心抓手

交付 `route_task_field_retest_drill_console`：

- 输入：上一轮 `route_task_field_retest_operator_drill` artifact / summary / diagnostics-compatible wrapper。
- 输出：`trashbot.route_task_field_retest_drill_console.v1` artifact 与 phone-safe summary。
- 证据边界：`software_proof_docker_route_task_field_retest_drill_console_gate`。
- 必备字段：schema/status/source drill schema、safe `evidence_ref`、operator command groups、callback checklist、required outputs、export summary、rerun commands、blocked/missing/rejected material summary、not-proven list、`delivery_success=false`、`primary_actions_enabled=false`。
- 导出边界：只导出 whitelist-safe metadata，不导出 raw artifacts、local paths、checksums、credentials、ROS topics、serial/UART details、完整 JSON 或成功宣称。

## 6. 需要做什么

Autonomy：

- 新增 PC/CLI gate，把 `route_task_field_retest_operator_drill` 转为 drill console artifact / summary。
- 保持 evidence ref 安全校验、fail-closed 状态和 software proof 文案。
- 增加最小单元测试和 py_compile 围栏。

Robot：

- 在 diagnostics / operator gateway metadata 中只读发现 drill console summary。
- 支持 top-level、nested diagnostics 或 status summary discovery。
- 保证任何 missing/invalid/unsafe/success claim 都 fail closed，不启用动作。

Full-stack：

- 在 `mobile/web` 增加只读“现场复测演练控制台”面板。
- 展示 safe evidence ref、console status、command groups、checklist、required outputs、rerun summary、not_proven、`delivery_success=false`、`primary_actions_enabled=false`。
- copy/export 只能使用 backend safe copy 或 whitelist-safe summary；不得改变 Start Delivery、Confirm Dropoff、Cancel gating。

Product closeout：

- 实现完成后更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md`。
- 核对 docs/ 是否同步描述新 console 的证据边界；如未同步，要求对应 Engineer 补。
- 核对代码技术注释是否为中文且满足 >20% 的项目规范；如不满足，要求对应 Engineer 修复。

## 7. 优先级和验收口径

P0：

- `route_task_field_retest_drill_console` 必须消费上一轮 `route_task_field_retest_operator_drill`。
- 必须产出 `software_proof_docker_route_task_field_retest_drill_console_gate`。
- 必须保留 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- mobile/web、diagnostics 只能只读消费，不启用 Start / Confirm / Cancel。

P1：

- 支持 wrapper / nested summary discovery，减少不同 surface 的接线漂移。
- 导出内容必须 whitelist-only，缺 safe copy 时显示 blocked copy unavailable。
- 所有 owner 的验证命令只跑围栏，不做大范围无关回归。

P2：

- Product final 对照 `OKR.md` 4.1 和 PR #4 / PR #5 证据，保守更新 OKR，不因 software proof 提升 O5 或 O1。

验收通过定义：

- Autonomy、Robot、Full-stack 三个 worker 各自完成文件范围内实现和 fenced 验证。
- Product closeout 的 `rg` 覆盖 `route_task_field_retest_operator_drill`、`route_task_field_retest_drill_console`、`software_proof_docker_route_task_field_retest_drill_console_gate`、`Objective 5`、`Objective 1`、`PR #4`、`PR #5`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- `git diff --check` 仅对本 sprint / touched files 通过。

## 8. 风险和阻塞

- 本轮不会解除 Objective 5 external proof 阻塞。
- 本轮不会解除 Objective 1 HIL / WAVE ROVER / UART / PR #5 sensor material 阻塞。
- 本轮不会补 PR #4 runtime integration tests，只能产生 Docker-local software proof 和受控现场演练材料准备。
- 如果后续实现把 console 文案写成 pass、success、completed、delivery done、field validated，需要立即阻断并要求修复。

## 9. 责任 Engineer

- Autonomy Engineer：PC/CLI gate 与 artifact contract。
- Robot Platform Engineer：diagnostics/operator gateway 只读消费与 fail-closed 集成。
- User Touchpoint Full-Stack Engineer：mobile/web 只读 console 面板和 copy/export。
- Product Manager / OKR Owner：阶段验收、OKR 更新、sprint final 和证据边界复核。
