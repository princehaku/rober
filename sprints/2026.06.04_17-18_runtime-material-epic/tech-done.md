# Tech Done: Runtime Material Epic Closeout

## sprint_type

sprint_type: epic

## 用户价值和产品北极星

普通手机用户要的是把垃圾交给小车后，小车能在真实上位机、真实传感器、真实 operator 工具和安全边界下推进送达闭环；异常时必须停在安全态、给出原因，并留下可复盘证据。本轮价值不是新增入口，而是把 16:05 OKR 打回后的 O2/O3/O7/O1 从 `software_guard` 拉向 `robot_runtime_material`、`field_hil_material` 或明确 `blocked_with_root_cause`。

北极星不变：低成本小车沿固定路线送垃圾，必要时 assisted elevator 跨楼层，并让不会 ROS2/SSH/串口的用户通过手机/PC 安全理解状态。

## 实际改动

本轮 Product / OKR Owner 只更新 sprint 收口和 OKR 文档，不触碰产品代码、测试代码、硬件配置、launch 参数、PC 工具、接口文档或 owner notes。

| 文件 | 改动 |
| --- | --- |
| `sprints/2026.06.04_17-18_runtime-material-epic/tech-done.md` | 聚合全部 owner notes，写明 evidence type、OKR 影响、失败定位和剩余风险。 |
| `sprints/2026.06.04_17-18_runtime-material-epic/side2side_check.md` | 对照 PRD 验收项做 side-to-side check。 |
| `sprints/2026.06.04_17-18_runtime-material-epic/final.md` | 完成 Epic 复盘、OKR 方向判断、下一轮抓手和 CEO 决策点。 |
| `OKR.md` | 更新当前快照、最高优先级和完成度边界。 |
| `docs/process/okr_progress_log.md` | 更新本轮历史记录、证据来源、验收结论和剩余风险。 |

## Owner 证据聚合

| Owner | 核心证据 | evidence_type | Product 判定 |
| --- | --- | --- | --- |
| Robot Software Engineer | SSH 到 `op-z3-b6.home` 可达，8787 live，ROS2 Humble 与 trashbot packages 安装，launch parseable；但 ROS graph 只有 `/parameter_events`、`/rosout`，`/scan`、`/map`、`/amcl_pose`、TF、Nav2 lifecycle 缺失。 | `blocked_with_root_cause` + supporting `robot_runtime_material` | 支持 O3/O7 runtime reachability，但 O3 不涨分；缺 runtime nodes 和 map/localize/Nav2 artifact。 |
| Robot Software Engineer | 修复并部署真实上位机 8787 `POST/GET /api/operator/report`；部署前 405，部署后 POST/GET 均 HTTP 200，artifact 可写可读，安全字段保持 fail-closed。 | `robot_runtime_material` + `software_guard` | `upper_http_405` blocker 已解决；可计为 O7 operator report runtime 入口进展，但不证明控车、HIL、ACK 或 delivery success。 |
| User Touchpoint Full-Stack Engineer | PC 同源代理复测 `/api/o7/direct-upper/operator-report` 成功写入真实 8787：HTTP 200、`accepted_by_workstation=true`、`upper_request.ok=true`、`failure_reason=none`，evidence_ref=`2026.06.04_17-18_operator_report_pc_same_origin_retest`。 | `robot_runtime_material` + `software_guard` | 支持 O7 从约 88% 小幅到约 89%；仍不证明 PC WASD 控车、现场 workflow、robot ACK、`T=1001` 或 HIL。 |
| User Touchpoint Full-Stack Engineer | PC 同源代理 status/map/list 可读真实 8787；PC tests 97 passed，build/lint 通过。 | `robot_runtime_material` + `software_guard` | 只证明真实 8787 operator 状态面和 map/list readback，可作为 operator workflow 前置材料。 |
| Robot Algorithm Engineer | 本地和上位机均无真实/受控 elevator image manifest；fixture eval 可复跑但 `real_or_controlled=0`，`field_eval.pass=false`，状态为 `needs_real_image_manifest`。 | `blocked_with_root_cause` + `software_guard` | O2 不涨分；下一步必须采集真实/受控图片和 manifest。 |
| Hardware Infra Engineer | Vendor-sourced `/dev/ttyS5 @115200` 非运动 `T=130 -> T=1001` 3/3 新鲜观察；`safe_to_control=false`，未执行 forward/back/left/right/stop pulse。 | `robot_runtime_material` + `software_guard`；无 `field_hil_material` | O1 只记录材料增强，保持约 95%；不等于 HIL、ROS `/odom`/`/imu/data`/`/battery`、robot ACK 或 `safe_to_control=true`。 |

## OKR 映射和方向判断

| Objective | 本轮结论 | 百分比决策 | 证据边界 |
| --- | --- | --- | --- |
| O7：PC 端运营调试平台 | 继续。`upper_http_405` 已被真实上位机部署和 PC 同源代理复测解除，operator report 可写入并回放同一 evidence ref。 | 约 88% -> 约 89% | 这是 `robot_runtime_material` + `software_guard`；不证明 PC WASD 控车、现场 stop/急停、robot ACK、HIL 或完整 operator workflow。 |
| O8：Epic 交付节奏与证据治理 | 继续。首轮跨 owner Epic 形成 pre_start/prd/tech-plan/owner notes/tech-done/side2side/final 链，证据类型和 blocker 都被明确标注。 | 约 35% -> 约 40% | 这是组织治理进展，不证明产品能力完成。 |
| O1：硬件协议可信底盘 | 继续。非运动 `T=1001` 新鲜材料有效，但缺现场安全前提、低速 pulse、stop/post-status 和 ROS feedback topic。 | 保持约 95% | 只记录材料增强；无 `field_hil_material`，`safe_to_control=false`。 |
| O3：建图、定位、Nav2 与固定路线 | 继续。上位机 ROS2 环境存在，但没有 ROS graph runtime topic 和 map/localize/Nav2 artifact。 | 保持约 73% | 主结论是 `blocked_with_root_cause`。 |
| O2：送垃圾任务 + 电梯 assisted delivery | 继续。算法链路可复跑，但没有真实/受控图片 manifest。 | 保持约 72% | fixture eval 不可替代 field eval。 |
| O5/O6：云中转/云端核心后端 | 保持 16:05 打回口径，继续作为支线。 | O5 约 84%，O6 约 82% | 本轮未触达 production live material。 |

方向判断：**继续**。本轮没有证据推翻北极星，也没有理由暂停 O2/O3/O7/O1；但推进方式必须继续按 O8 约束，用真实 runtime、field/HIL、production 或用户验收材料支撑产品 Objective，不再用 mock、fixture、runbook 或只读状态面涨产品分。

## KR 更新和历史归档

| KR | 处理 | 历史记录位置 | 剩余风险 |
| --- | --- | --- | --- |
| KR-O7-Operator-Report-Route | 本轮解决旧 blocker `upper_http_405`，真实上位机 8787 POST/GET 200，PC 同源代理 POST 200 且 `accepted_by_workstation=true`。进入 O7 历史进展。 | `owner_notes/robot-software-engineer-operator-report-deploy.md`、`owner_notes/full-stack-software-engineer-operator-report-retest.md`、`docs/process/okr_progress_log.md` 17-18 节。 | 仍缺 PC WASD 控车、stop/急停、robot ACK、`T=1001` 同场、长期 artifact retention 和 production archive ingestion。 |
| KR-O8-Epic-Cadence | 本轮完成首轮有效 Epic 治理证据，进入历史进展记录。 | `docs/process/okr_progress_log.md` 17-18 节；本 sprint `final.md`。 | 只证明治理链路执行，不证明 O1/O2/O3/O7 产品闭环。 |
| KR-O8-Evidence-Type-Gate | 本轮所有 owner evidence 均被标成 `software_guard`、`robot_runtime_material`、`field_hil_material` 或 `blocked_with_root_cause`，进入历史进展记录。 | `docs/process/okr_progress_log.md` 17-18 节；本文件。 | 后续仍需防止把 runtime liveness 误写成 field HIL。 |
| KR-O8-Owner-Health | 本轮识别 owner 健康状态：Software 缺 runtime nodes，Algorithm 缺图片材料，Hardware 缺 HIL 安全前提，Full-Stack 已完成 operator report PC 同源复测但缺现场控车。 | `final.md` 风险与下一步。 | 需要下一轮 owner 直接补材料，不再扩 fixture/runbook。 |

本轮没有任何 O1/O2/O3 产品 KR 完成归档；O1 只有非运动 runtime material 增强，不进入 HIL 完成归档。O7 只归档 `upper_http_405` route blocker 解除，不归档完整 operator workflow。

## 失败定位

| blocker | root cause | owner | 下一步 |
| --- | --- | --- | --- |
| O3 ROS graph topics missing | 上位机 ROS2 包安装完成，但未启动 application ROS2 nodes；8787 radar/map/localize/Nav2 hooks 仍是 dry-run stub 或未形成 artifact。 | Robot Software Engineer | 启动受监督 non-motion LiDAR/SLAM runtime，采 `/scan`、`/map`、TF、AMCL 或明确 process supervisor blocker。 |
| O2 no real elevator manifest | 真实/受控电梯图片未落到本地或上位机可搜索路径，只有 fixture 和模板。 | Robot Algorithm Engineer + 现场 owner | 采集 `trashbot.elevator_image_manifest.v1`，满足 field gate 后再跑 OpenCV eval。 |
| O1 no field HIL | 没有现场看护、物理净空、人工急停和 CEO/现场授权材料。 | Hardware Infra Engineer | 先写 operator preflight report，再执行 stop-first 低速 pulse；否则继续 `safe_to_control=false`。 |
| O7 operator report not field workflow | route 已通，但 report 是非运动 evidence artifact，不包含 observed motion、stop、ACK 或现场视频。 | Full-Stack Engineer + Hardware Infra Engineer | 与 O1 stop-first HIL 使用同一 evidence ref，把 operator report、manual response、stop response、post-status 和 `T=1001` 同场对齐。 |

## 验证结果

Product 收口验收命令将在文档更新后运行并回填到 `final.md`。当前 owner 侧验证摘要如下：

- Full-Stack operator report retest：真实 upper 8787 direct POST/GET HTTP 200；PC same-origin proxy POST HTTP 200，`accepted_by_workstation=true`、`upper_request.ok=true`、`failure_reason=none`、evidence_ref=`2026.06.04_17-18_operator_report_pc_same_origin_retest`。
- Full-Stack package：`cd pc-tools/workstation && npm test -- --run`，97 tests passed；`npm run build` 通过；`npm run lint` exit code 0。
- Robot Software：部署前 `/api/operator/report` HTTP 405；部署后真实 upper 8787 POST/GET HTTP 200；`python3 -m unittest onboard.scripts.test_upper_robot_api`，26 tests OK，1 skipped；`python3 -m compileall onboard/scripts` 通过。
- Robot Software ROS2 runtime：SSH/8787/ROS2 packages live，但 `/scan`、`/lidar/raw_packet`、`/map`、`/amcl_pose`、TF、Nav2 lifecycle 均缺。
- Robot Algorithm：`needs_real_image_manifest`；`python3 -m compileall onboard/src/ros2_trashbot_vision` 通过；`python3 -m unittest discover -s onboard/src/ros2_trashbot_vision/test`，18 tests OK。
- Hardware：SSH/8787 非运动 serial feedback samples 3/3 观察到 `T=1001`，并明确 `sends_motion_commands=false`、`hil_pass=false`、`safe_to_control=false`。

## 剩余风险

- 没有真实 PC WASD 控车、底盘运动、急停演练、HIL pass、`safe_to_control=true`。
- 没有 fresh `/scan` continuity、`/map`、`/amcl_pose`、TF、Nav2 lifecycle、地图 artifact。
- 没有真实/受控 elevator image manifest、field eval pass、楼层 OCR 或电梯实景流程。
- `operator_report` 只是人工/operator evidence artifact，不替代 base status、stop、feedback samples、HIL 或现场视频。
- 本轮不触达 O5/O6 production live material，不改变云端支线打回口径。
