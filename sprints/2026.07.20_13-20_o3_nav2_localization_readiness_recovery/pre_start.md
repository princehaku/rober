# O3 Nav2 Localization Readiness Recovery - Pre Start

## Sprint metadata

- `sprint_type: epic`
- Sprint：`sprints/2026.07.20_13-20_o3_nav2_localization_readiness_recovery/`
- 状态：`plan_contract_correction_implementation_ready`
- Product owner：`product-okr-owner`
- Robot Software owner：`robot-software-engineer`
- Algorithm owner：`robot-algorithm-engineer`
- 目标链路：Objective 3 current readiness → Objective 1 current-run HIL 前置
- proof boundary：`strict_no_motion_persistent_lifecycle_fresh_pose_planner_only_path_readiness`

## 用户价值和产品北极星

产品北极星是让每次真实路线 action 都建立在同一 current window 的安全 lifecycle、可信定位、TF、planner-only path 和可审计零控制证据之上。本 sprint 必须真正解锁 current readiness，不再重复 managed no-initialpose diagnostic、cleanup 后 no-go、health wrapper 或 readback surface。

## 原计划合同错误与修订原因

本文件组最初版本存在 `plan_contract_correction`，现按 Robot Software / Algorithm 的只读代码证据纠正：

1. `/api/nav2/start` handler 当前不读取 body；原计划传入的安全字段实际被忽略。默认命令使用 `--base-enabled auto`，在无 holder 时可能打开 `/dev/ttyS5`，与本轮 UART invocation 必须为 0 冲突。
2. `/api/nav2/proof/refresh` 的真实 opt-in 字段是 `managed_runtime_opt_in`、`initialpose_opt_in`、`path_generation_opt_in`；原计划字段不会生效。
3. O10 managed helper 不开 base UART，但默认可能按 230400 新开 LiDAR，与 current holder / 150000 冲突；其 runtime 只含 map/amcl/可选 planner，不含 controller，并在返回前 cleanup，不能证明 persistent stack readiness。
4. 当前 path precondition 硬要求 initialpose opt-in；在本轮禁止 `/initialpose` 的条件下，原 GO 对 persistent lifecycle、controller、path 的组合不可达。
5. helper 的真实测试文件是 `onboard/tests/test_nav2_runtime_proof_helper.py`，不是原计划中的不存在路径。
6. HTTP 200 只表示 handler 返回；成功必须解析 `command_result`、`status`、`evidence`、`root_causes`、cleanup 和 publish attempts。

因此 sprint 升级为真正的两 owner 跨 owner Epic：Robot Software 交付安全、可测试、persistent 的 lifecycle API 合同；Algorithm 交付零次 initialpose 前提下基于 current fresh persisted pose/TF 的 planner-only path gate。

## OKR 与 blocker 路由

- 当前最低 Objective 5 约 85%，但 external provider/runtime blocker 已连续消费 `2/2`，本轮按 blocker 红线暂停，不再包装同一阻塞。
- Objective 6 / Objective 7 均约 93%，在 readiness 未成立前暂停 action 重跑；Objective 1 约 94%，等待 current readiness 后再建立独立 HIL/motion window。
- 本轮切换到可推进的 Objective 3 current readiness。只接受代码合同、current artifact 和结构断言，不用计划文档计分。
- KR 本轮不归档，历史区无新增；只有 `tech-done.md`、artifacts 和后续 Product closeout 达标后才评估进度。

## CEO 授权与本轮边界

CEO 原话：`小车运动已经授权，我已经限制了它物理位置，不会有风险。我已授权有 operator 看护、路线清空；持续推进 OKR`。

该授权是后续 motion gate 的真实变化，但本 sprint 不消费运动授权。允许：persistent stack-only lifecycle start/status/stop、复用现有 `/scan`、读取 current `/amcl_pose` / TF、调用 planner-only `ComputePathToPose`。禁止：`NavigateToPose`、`/cmd_vel`、`/api/base/manual`、发布 `/initialpose`、WAVE ROVER UART、打开新的 base/LiDAR serial holder、路线 execute 和任何轮子运动。

## Owner 与跨 owner Epic

- `robot-software-engineer`：主责 API/start/stop 合同、现有 `o11_nav2_lifecycle.sh` 安全参数拼装、API 单测、lifecycle live integration 和总 `tech-done.md`。
- `robot-algorithm-engineer`：主责 O10 current persisted pose/TF gate、planner-only path、helper 单测与 proof artifacts。
- 两 owner 实现与本地测试并行，文件范围互不重叠；真机集成严格串行：Robot Software 安全 start → Algorithm no-motion proof → Robot Software fixed stop/cleanup。
- `o11_nav2_lifecycle.sh` 已支持显式 `--base-enabled false --lidar-enabled false`，本计划不修改该脚本；如 Engineer 发现现有参数不能兑现安全合同，必须暂停并返回 Product 修订范围。

## Go / No-Go 产品结果

GO 要求同一 current window：strict contract 实际生效；base UART 与 LiDAR new-open 计数均为 0；persistent map/amcl/planner/controller active；fresh `/amcl_pose`、fresh dynamic `map->odom`、`map->base_link` 且来源可审计；`initialpose_publish_attempts=0`；planner-only path 成功且点数大于 0；最后 owned lifecycle stop/cleanup 成功。

`obstacle_clear` 不阻断本轮 planner-only readiness，但必须作为下一 motion gate blocker 记录。任一 current pose/TF freshness 或 attribution 缺失时必须 NO-GO，且不得发布 `/initialpose`。

无论 GO/NO-GO，固定 `safe_to_control=false`、`route_execution_success=false`、`hil_pass=false`、`delivery_success=false`、`okr_credit=false`。

## 风险与证据缺口

- current AMCL pose/TF 可能不存在或 stale；本轮必须 NO-GO，不能借旧证据补齐。
- persistent stack 即使 start command exit 0，也可能 lifecycle 未 active；必须解析 status/evidence/root causes。
- stop 只允许终止 `o11_nav2_lifecycle.sh` 自有进程组；若归属无法确认，不得扫杀其它 ROS2 runtime。
- 本轮不创建 `side2side_check.md` / `final.md`，不修改 `OKR.md` / progress log。
