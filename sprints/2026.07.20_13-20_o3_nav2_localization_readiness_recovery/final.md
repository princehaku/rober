# O3 Nav2 Localization Readiness Recovery - Final

## Sprint metadata

- `sprint_type: epic`
- Product owner：`product-okr-owner`
- Engineer owners：`robot-software-engineer`、`robot-algorithm-engineer`
- Final status：`accepted_engineering_and_live_safety_contract_current_readiness_no_go_cleanup_complete`
- proof boundary：`strict_no_motion_persistent_lifecycle_fresh_pose_planner_only_path_readiness`
- `READINESS_GO=false`
- `PRODUCT_CLOSEOUT_COMPLETE=yes`

## Product final decision

Product 接受跨 owner 代码、测试、导航文档、8 个 JSON、真实上位机 strict-no-motion start 合同与 owned cleanup；拒绝 current localization/path readiness、motion/HIL/route/delivery/Mission/OKR credit。

用户获得的是一个真实生效且 fail-closed 的安全 lifecycle API，而不是 HTTP 200 假成功：start request body 已被消费，effective `base_enabled=false`、`lidar_enabled=false`，new-open=`0/0`，既存 base/LiDAR holders 未变。exactly-one current integration sequence 为 start/proof/latest/stop=`1/1/1/1`；goal/manual/base-stop/cmd_vel publish/initialpose publish/UART motion 均为 0，物理运动未发生。stop 仅清理 owned process group，Upper API 最终仍 healthy。

## 实际改动与验证证据

Robot Software 完成 strict start/stop semantic contract、fail-closed compatibility migration、API tests 与 field-route preflight 文档；Algorithm 完成 current persisted pose planner-only gate、helper tests 与 fixed-route 文档。

Engineer 验证留档：

- Robot：`py_compile` exit `0`；`114 tests OK`（另有 `5` targeted strict tests）；中文注释 `20.63%+`，集成 diff `25.24%`。
- Algorithm：`py_compile` exit `0`；`167 tests OK`；中文注释 `22.38%`。
- 8 个 JSON `json.tool` exit `0`；integration marker=`O3_STRICT_NO_MOTION_FINAL_NO_GO_CLEANUP_OK`。
- combined scoped `git diff --check` exit `0`。

Product 没有重跑工程 tests/build/SSH/ROS/Nav2/control，只做计划、`tech-done.md`、artifacts、双方 diff/测试结果、OKR/progress 的只读验收和 closeout 文档检查。

## Current NO-GO

Proof helper `elapsed_ms=81243`，超过 `process_timeout_s=80`，partial artifact 被保留。根因是：

- `amcl_pose_probe_interrupted_before_observation`
- `sigint_before_final_artifact`
- `helper_process_timeout_after_partial_artifact`

因此 current proof 未能证明 map/amcl/planner/controller active、persisted pose live consumed、fresh `/amcl_pose`、fresh dynamic uniquely-attributed `map->odom` 或 `map->base_link`。Path `requested=true`，但 attempted/succeeded/generated 均 false、count=`0`；`initialpose_publish_attempts=0` 正确保持。

## OKR、Mission、delta 与 KR

- O5：约 85%，provider/runtime blocker `2/2` 仍成立，最低 Objective 跳过理由仍成立。
- O6 / O7：各约 93%，flat。
- O1：约 94%，flat。
- 主百分比：不调整。
- `current_run_artifact_delta=true`
- `external_artifact_delta=false`：项目自有上位机 current evidence，不是 independent external/production/delivery evidence。
- `live_control_delta=false`
- `user_action_delta=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `nav2_goal_execution_proven=false`
- `hil_pass=false`
- `delivery_success=false`
- `safe_to_control=false`
- `okr_credit=false`
- KR：`不归档`；历史区无新增。

Mission Objective 0 不是 pending authorization：CEO 已给 fresh authorization，但本轮 strict-no-motion sequence 未消费。正确状态是 `blocked_before_attempt_on_current_localization_readiness`；没有进入 mission attempt，更不是 mission success。

## 失败修复与剩余风险

本轮已修复 start body 被忽略、`auto` 可能新开 serial、HTTP 200 被误判成功、initialpose opt-out path gate 不可达等合同错误；Upper API 首次受管 restart timeout 后通过 unit-scoped recovery 恢复 healthy，proof 失败后仍完成 owned cleanup。

未修复的是 O10 helper 80s budget/probe order/partial artifact 时序。不得在本 sprint 重试，也不得用 wrapper、旧 pose 或 operator 声明补齐 readiness。

## 下一轮唯一入口

先由 `robot-algorithm-engineer` 在本地修 helper 80s budget、AMCL/TF probe order 与 partial artifact，使 current pose/TF 能在 no-motion budget 内采到，并跑完整 helper 回归；本地 clean 后才允许一个新的 no-motion proof window。

若新窗口仍无 persisted pose，Product/CEO 必须明确新的 localization input gate，禁止隐式 `/initialpose`。运动授权仍未消费；新的 live action 还必须重新确认 current operator、路线、obstacle 与 readiness。
