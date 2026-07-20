# O3 Nav2 Localization Readiness Recovery - Side2Side Check

## Product acceptance metadata

- `sprint_type: epic`
- Product owner：`product-okr-owner`
- Implementation owners：`robot-software-engineer`、`robot-algorithm-engineer`
- Product decision：`accept_implementation_and_live_safety_contract_reject_current_readiness_go`
- proof boundary：`strict_no_motion_persistent_lifecycle_fresh_pose_planner_only_path_readiness`
- `READINESS_GO=false`
- `PRODUCT_CLOSEOUT_COMPLETE=yes`

## 用户价值与北极星对照

北极星是让真实路线 action 建立在同一 current window 的安全 lifecycle、可信定位/TF、planner-only path 和零控制证据上。本轮交付了真实上位机可执行的 strict-no-motion lifecycle 合同与保守 NO-GO，消除了 `/api/nav2/start` 忽略 body、`auto` 可能新开串口的风险；但 current AMCL pose/TF/path 未在 proof budget 内被证明，因此仍停在 mission attempt 之前。

这不是又一层 wrapper/readback：代码合同、双方回归、导航文档、真实 start/proof/latest/stop 与 8 个 JSON artifact 均已发生。但 NO-GO 也不能包装为 mission success。

## 计划与实际 side-by-side

| 验收项 | 计划口径 | 实际证据 | Product 裁决 |
| --- | --- | --- | --- |
| Start 合同 | body 必须被消费；effective `base=false/lidar=false` | `status=started_strict_no_motion`、`semantic_success=true`、effective false/false | 接受 |
| 串口隔离 | base UART / LiDAR new-open=`0/0` | `/dev/ttyS5` 与 `/dev/ttyACM0` 既存 holder 未变，new-open=`0/0` | 接受 |
| 零运动边界 | goal/manual/cmd_vel/initialpose/UART motion 均 0 | start/proof/latest/stop=`1/1/1/1`；控制与发布 invocation 均 0；无物理运动 | 接受 |
| Safe cleanup | proof 成败都只停 owned lifecycle | stop `semantic_success=true`、cleanup scope=`o11_owned_pid_process_group_only`、Upper API healthy | 接受 |
| Current localization | fresh persisted pose、unique dynamic `map->odom`、`map->base_link` | helper `81243ms` 超过 80s process budget；AMCL/TF probe 未完成 | 拒绝 readiness |
| Planner-only path | requested/attempted/succeeded/generated 且 point count > 0 | requested=true；attempted/succeeded/generated=false；count=0 | 拒绝 readiness |
| OKR/Mission | 只有 readiness 真成立才考虑计分/attempt | `READINESS_GO=false`、所有 route/HIL/delivery/safe/OKR 字段 false | 不计分 |

## 工程交付验收

Robot Software diff 被接受：

- `upper_robot_api.py` 读取并严格验证 start body，默认与 effective argv 均固定 `--base-enabled false --lidar-enabled false`；legacy/未知字段/非法 timeout 在 subprocess 前 fail closed。
- response 把 `command_result`、`status`、`evidence`、`root_causes`、cleanup 和 lifecycle readback 纳入语义成功，HTTP 200 本身不再等于成功。
- stop 只清理由 `o11_nav2_lifecycle.sh` 拥有的 PID/process group，不发送底盘 stop。
- `test_upper_robot_api.py` 最终 `114 tests OK`，其中 strict lifecycle targeted `5` 项通过；Robot 源码+测试中文注释 owner 验收 `20.63%+`，集成 diff 复核 `25.24%`。

Algorithm diff 被接受：

- O10 新增 persisted-pose planner-only precondition gate，要求 current fresh pose、fresh dynamic TF、唯一 AMCL attribution、四 lifecycle active 与零 initialpose publish。
- missing/stale/ambiguous 在 `ComputePathToPose` 前 fail closed，path attempt 保持 0。
- 真实测试路径 `test_nav2_runtime_proof_helper.py` 最终 `167 tests OK`；Algorithm 产品源文件中文注释 `22.38%`。

Product 未重跑 Engineer tests；本阶段只读核对双方 scoped diff、`tech-done.md`、测试留档、导航文档和 JSON evidence。

## Artifact 与结构验收

8 份 JSON 均通过 Engineer `json.tool`，跨 artifact 结构断言 marker 为：

`O3_STRICT_NO_MOTION_FINAL_NO_GO_CLEANUP_OK`

Artifact 是阶段化证据：readiness assertion 在 stop 前记录 stop pending，start safety manifest 记录 lifecycle handoff；最终 stop response 与 `tech-done.md` 补齐 owned cleanup。Product 只接受跨 artifact 一致结论，不要求单一中间 artifact 伪装成最终全序列。

Current proof 的直接根因：

- `amcl_pose_probe_interrupted_before_observation`
- `sigint_before_final_artifact`
- `helper_process_timeout_after_partial_artifact`

因此 lifecycle active、persisted pose audit、fresh unique `map->odom`、`map->base_link` 没有在 timeout 前得到 current proof；`initialpose_publish_attempts=0` 正确保持，path 未尝试。

## OKR、Mission、delta 与 KR 裁决

- O5 保持约 85%，provider/runtime blocker `2/2` 仍成立；跳过最低项的理由仍成立。
- O6 / O7 各保持约 93%；O1 保持约 94%；主百分比 flat。
- `current_run_artifact_delta=true`：只表示真实 current upper 的安全 start 合同、NO-GO partial evidence 和 clean cleanup。
- `external_artifact_delta=false`：证据来自项目自有上位机/runtime，并非独立 external provider、用户交付、production cloud 或第三方验收材料。
- `live_control_delta=false`
- `user_action_delta=false`
- `route_execution_success=false`
- `hil_pass=false`
- `delivery_success=false`
- `safe_to_control=false`
- `okr_credit=false`
- KR：`不归档`；历史区无新增完成记录。

Mission Objective 0 状态为 `blocked_before_attempt_on_current_localization_readiness`。本轮已有 fresh CEO motion authorization，但 strict-no-motion sprint 没有消费它；因此不是 pending authorization，也不是 mission attempt/success。

## 剩余风险与唯一入口

- O10 helper 的 80s process budget、probe order 与 partial artifact 写入仍需修复；当前 timeout 发生在 AMCL pose probe 完成前。
- Upper API graceful shutdown 仍可能卡在 `stop-sigterm`；本轮只证明 unit-scoped recovery 有效，没有根治该既有问题。
- 不得重复本 proof/window，不得再开 wrapper/summary/readback sprint。
- 下一轮唯一入口：先由 Algorithm 在本地修 helper budget/probe order/partial artifact，使 current AMCL pose 与 TF 可在 80s no-motion window 内完成并通过完整回归；然后才允许一个新的 no-motion proof。
- 若优化后仍没有 persisted pose，必须由 Product/CEO 明确新的 localization input gate；不得隐式发布 `/initialpose`。
- motion authorization 本轮未消费；任何新的 live action 仍须重新确认 current operator、路线、obstacle 与 readiness。
