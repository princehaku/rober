# O3 Nav2 Localization Readiness Recovery - Side2Side Check

## Product acceptance metadata

- `sprint_type: epic`
- Product owner：`product-okr-owner`
- Implementation owners：`robot-software-engineer`、`robot-algorithm-engineer`
- Product decision：`accept_contract_and_owned_stop_reject_current_readiness_and_okr_credit`
- proof boundary：`strict_no_motion_persistent_lifecycle_fresh_pose_planner_only_path_readiness`
- `PLANNER_ONLY_NO_GO`
- `READINESS_GO=false`
- `OWNED_STOP_CLEAN=yes`
- `PRODUCT_CLOSEOUT_COMPLETE=yes`

## 用户价值与产品北极星

北极星是让真实路线 action 建立在同一 current window 的安全 lifecycle、可信定位/TF、planner-only path 与零控制证据上。本轮用户获得了真实生效的 strict-no-motion lifecycle 合同和 clean owned stop，消除了 `/api/nav2/start` 忽略 body、`auto` 可能新开串口的风险；但 helper 未在 80s budget 内形成 final readiness artifact，因此仍停在 mission attempt 之前。

代码合同、双方回归、导航文档和 current artifacts 是实际工程增量；`PLANNER_ONLY_NO_GO` 不是 mission、route、HIL 或 delivery 结果，也不产生 OKR credit。

## 计划与最终事实 side-by-side

| 验收项 | 计划口径 | 最终事实 | Product 裁决 |
| --- | --- | --- | --- |
| Start 合同 | body consumed；effective false/false | 两个窗口各 start=`1`，累计 `2`；均为 `started_strict_no_motion`、semantic success、false/false | 接受合同；第二窗口仍属竞态偏差 |
| 串口隔离 | base/LiDAR new-open=`0/0` | holder 未变化，new-open=`0/0`，command log delta=`0` | 接受 |
| 零控制边界 | initialpose/goal/cmd_vel/UART 全 0 | `initialpose/goal/cmd_vel/UART=0/0/0/0`；无物理运动 | 接受 |
| No-retry | 只允许一个 start/proof/latest/stop 窗口 | 首窗口 `1/1/1/1` 后发生第二窗口；全 sprint=`2/2/2/2` | 第二窗口为竞态偏差，不接受为正常 exactly-once，不给第二份 credit |
| Safe cleanup | 只停 owned lifecycle | stop semantic success；PID `684474` 与 PID file 均 removed | `OWNED_STOP_CLEAN=yes` |
| Current lifecycle | map/amcl/planner/controller active | partial 仅证明 map/amcl active；planner/controller 未证明 | 拒绝 readiness |
| Current localization | fresh pose、fresh unique dynamic TF、map-to-base | partial 证明 dynamic `map->odom` unique AMCL attribution 与 `map->base_link=true`；未证明 fresh `/amcl_pose`、formal TF freshness、persisted final gate | 拒绝 readiness |
| Planner-only path | attempted/succeeded，count > 0 | requested=true；attempted/succeeded/generated=false；count=0 | 拒绝 readiness |
| OKR/Mission | readiness 成立后再进入 attempt | route/HIL/delivery/safe/control/`okr_credit=false` | 不计分，不归档 |

## 工程交付验收

- Robot Software：`py_compile` exit 0；`114 tests OK (skipped=1 aiohttp)`；中文注释比例 `20.2%`。
- Algorithm：`py_compile` exit 0；`167 tests OK`；中文注释比例 `20.946%`。
- 双方 diff 与静态断言均绿，代码、测试和 navigation 文档合同接受。
- Product 本阶段不重跑工程 tests、SSH、ROS2、Nav2 或 control；只读交叉核对六文档、当前 8 个 JSON、测试留档与 final stop。

## Artifact 时序与证据边界

- remote API/helper SHA 均与本地一致。
- 首窗口 helper `elapsed_ms=81243`；roots 为 `amcl_pose_probe_interrupted_before_observation`、`sigint_before_final_artifact`、`helper_process_timeout_after_partial_artifact`，首窗口 start/proof/latest/owned-stop=`1/1/1/1`。
- 第二窗口 helper `elapsed_ms=80444`，`process_timeout_s=80`，partial artifact preserved；last successful phase=`tf_probe`，timeout command=`ros2 pkg list`。
- 精确 runtime roots 包含 `helper_process_timeout_after_partial_artifact` 与 `sigint_before_final_artifact`。
- `readiness_assertion.json` 是 pre-stop snapshot，保留 PID `684474` running、stop pending 是正确的时点事实；最终 cleanup 只以 `lifecycle_safety_manifest.json.final_stop` 与 `api_nav2_stop_response.json` 为准，两者证明 lifecycle stopped、PID removed、cleanup clean。
- commit `3fe3c053c` 发生在最终 Algorithm proof / owned stop 之前；Product 不沿用该 commit 中的初版派生结论，当前四个修正 artifact 是最终事实来源。

## post_publish_race_window

第二窗口是发布后的非预期后台/编排竞态，违反 no-retry 边界；artifact 无 agent/session/operator identity 字段，因此调用者身份不能判定。第二窗口 PID/PG=`684474`，proof PG=`685333`；窗口内 `1/1/1/1`，与首窗口合计 `2/2/2/2`，但不计第二份 OKR 进展。

它新增的 current partial facts 是 `map_server_active=true`、`amcl_active=true`、dynamic `map->odom` observed/timestamp parsed/`attributed_unique_amcl`、`map->base_link=true`。formal freshness gate、current AMCL pose、persisted pose audit、planner/controller 和 path 仍未证明，path attempted/generated=false，故 `READINESS_GO=false`。

16:54 第二 owned stop clean；16:55 audit 新增 stop=`0`，最终 lifecycle stopped、Upper API healthy、tty holders/command log unchanged、owned lifecycle/proof residual=0、`physical_motion=false`。最终状态只取 `lifecycle_safety_manifest.post_publish_race_cleanup`，不能用 pre-stop `readiness_assertion` 覆盖。

## OKR 映射与方向判断

- O5：约 `85%`，provider/runtime blocker `2/2`，继续暂停重复消费。
- O6/O7：各约 `93%`，flat；O1：约 `94%`，flat。
- O3：本轮只增加 current no-motion artifact，不新增 Mission credit，主百分比不调整。
- `current_run_artifact_delta=true`；`external_artifact_delta=false`、`live_control_delta=false`、`user_action_delta=false`。
- `robot_control_executed=false`、`route_execution_success=false`、`hil_pass=false`、`delivery_success=false`、`safe_to_control=false`、`okr_credit=false`。
- KR：`不归档`；历史区无新增完成记录。

Mission Objective 0 状态仍为 `blocked_before_attempt_on_current_localization_readiness`。旧 motion authorization 的 current context 已经过两个窗口；strict-no-motion 窗口仍不构成 user action 或 live control，后续动作不得直接复用该授权。

## 剩余风险与下一轮唯一入口

- 当前直接 blocker 是 O10 helper 在 TF probe 后又进入 `ros2 pkg list`，最终超出 API 80s budget；不是缺少另一个 wrapper/readback。
- 暂停重复 strict-start wrapper/live refresh；禁止第三个 proof/window。
- `next_offline_runtime_budget_fix`：由 Robot Software + Algorithm 先在本地/离线剖析 helper/API budget、probe order 和 final artifact 时序，补齐能在 80s 内自然完成的测试；只有这些新测试 clean 后，才允许新的 no-motion current proof。
- 若新窗口仍缺 persisted pose，应由 Product/CEO 明确 localization input gate；不得隐式发布 `/initialpose`。
- 任何新动作必须重新确认 current readiness、operator、route 与 obstacle gate。
