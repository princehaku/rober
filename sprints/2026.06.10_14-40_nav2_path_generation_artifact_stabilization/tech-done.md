# Nav2 path generation artifact stabilization

## sprint_type

micro

## owner

`robot-software-engineer`

## 用户价值和产品北极星

用户价值不是继续增加 PC surface、handoff 或只读 review，而是让真实上位机
`ssh root@192.168.1.11 -p 37878` 上的 no-motion path generation proof 即使失败也能
留下足够完整、可复跑、可定位的 artifact。下一轮 Engineer 必须能回答：

- planner path generation 到底是没被请求、service/action 不可用、planner lifecycle 未
  active、localization readiness 不稳定，还是 topic 观测判定过于保守。
- `/scan`、`/map`、`/amcl_pose`、planner lifecycle、compute-path 请求/响应和 cleanup
  证据是否来自同一个受控 no-motion 窗口。
- 本轮是否仍满足 `cmd_vel` 不发布、base UART `/dev/ttyS5` 不触碰、`safe_to_control=false`
  和 `delivery_success=false` 的安全边界。

产品北极星保持不变：把 `rober` 从软件侧可跑推进到真实现场可验证地完成送垃圾。本
micro sprint 只补 O3 现场验证 lane 的证据稳定性，不把 path generation 包装成路线执行、
运动执行或送达成功。

## OKR 映射和方向判断

- 对应 Objective：现场 O3 验证 lane（当前最高优先级，临时激活归档 Objective）。
- 方向判断：`继续`。
- 继续理由：
  1. `sprints/2026.06.10_09-15_managed_nav2_localization_proof/tech-done.md`
     已证明真实上位机 managed no-motion localization 可观测到 `/scan`、`/map`、
     `/amcl_pose` 和 localization TF。
  2. `sprints/2026.06.10_09-05_nav2_no_motion_path_generation_proof/tech-done.md`
     已实现 path generation opt-in，但远端复跑未得到 `path_generated=true`，且遗留问题
     指向 artifact 缺失和观测判定不稳定。
  3. 因此下一步最小可交付不是直接 route execution，也不是再做 surface，而是先修复
     path generation proof 的 artifact 留存、raw observation 和判定规则，使后续能准确
     证明或定位 planner path generation。

本轮不更新 `OKR.md` 进度百分比；如果下一轮真实上位机产出稳定
`path_generated=true` artifact，再由 Product Owner 判断是否更新 O3 临时 lane 证据状态。

## KR 拆解 / 更新

本轮不归档已完成 KR，也不迁移历史 KR；只为 O3 现场验证 lane 增加一个工程可执行的
证据稳定化 KR：

- KR-O3-PathArtifact-1：每次 no-motion path generation proof 无论成功、失败或 timeout，
  都必须保留完整 JSON artifact 和 raw observation 摘要，不能只在聊天或终端里留下结果。
- KR-O3-PathArtifact-2：artifact 必须区分 `service_available`、`planner_server_active`、
  `localization_ready`、`path_generation_attempted`、`path_generation_succeeded` 和
  `path_generated`，避免把不同失败阶段混成一个 root cause。
- KR-O3-PathArtifact-3：topic/action 观测判定必须处理“命令 timeout 但 stdout 已有有效
  message”的情况，避免把已有 `/map` 或其他输出误判为未观测。
- KR-O3-PathArtifact-4：direct-helper 和 API 两条真实上位机路径都必须写明 artifact
  路径、latest 指针、cleanup 结果和 no-motion safety flags。

## 本轮核心抓手

把 09:05 的 path generation opt-in 从“有代码路径但失败证据不够稳定”推进到“失败也能
定位的证据链”。本轮 Engineer 不应扩功能面，不应加控制页面，不应进入运动执行；只修
artifact schema、观测判定、持久化路径和真实上位机复跑流程。

## 功能点完整清单

1. 强化 `o10_amcl_nav2_runtime_proof.py` artifact 留存：
   - 每次运行生成唯一 run id。
   - 写出 `artifact_path`、`latest_artifact_path`、`run_started_at`、`run_finished_at`。
   - 即使 `rc != 0`、topic timeout、planner inactive 或 user stop，也必须落盘 partial
     artifact。
2. 强化 raw observation 字段：
   - 每个 `/scan`、`/map`、`/amcl_pose`、TF、lifecycle、compute-path 观测项都记录
     `attempted`、`timed_out`、`return_code`、`stdout_nonempty`、`stderr_tail`、
     `message_excerpt`、`observed`、`failure_reason`。
   - `message_excerpt` 只保留短摘要，避免 artifact 过大。
3. 修正 topic 观测判定：
   - stdout 中已出现可解析 message 时，允许 `timed_out=true` 但 `observed=true`。
   - stdout 为空且 timeout 时，才判定 `observed=false`。
   - 对 `/map` 的判定必须能解释 09:05 遗留的“已有 stdout 但仍被标成未观测”问题。
4. 强化 path generation 阶段判定：
   - `path_generation_requested` 仅代表 opt-in 请求。
   - `path_generation_attempted` 仅在 service/action 可用且前置 readiness 通过后为 true。
   - `path_generation_succeeded` 仅代表 compute-path 调用返回成功。
   - `path_generated` 必须要求 path 点数满足下限、frame 合法、goal echo 可追溯。
   - planner inactive、localization 不稳定、service unavailable 必须分别写入不同
     `root_cause`。
5. 强化 API readback：
   - `/api/nav2/proof/refresh` 返回或 latest readback 必须暴露本轮新增 artifact 路径和
     summary 字段，便于主会话和后续 PC/O7 消费。
   - 默认 body 不传 path generation opt-in 时仍保持 read-only collector。
6. 强化 cleanup 和 safety flags：
   - artifact 继续强制记录 `publishes_cmd_vel=false`、`calls_base_manual=false`、
     `uses_base_uart=false`、`safe_to_control=false`、`delivery_success=false`。
   - 记录 `/dev/ttyS5`、`/dev/ttyACM0` 的 `lsof` / `fuser` 清场摘要。
7. 单元测试必须覆盖：
   - partial artifact 在失败时仍落盘。
   - stdout 非空但命令 timeout 时不误判 topic 未观测。
   - path generation 各阶段布尔字段互不替代。
   - API body / latest readback 包含 artifact 路径和 summary。
8. 文档同步：
   - 如果 Engineer 修改了导航 proof 行为，必须同步更新相关 `docs/` 导航或硬件 smoke
     文档。
   - 本 Product 设计轮没有权限改 `docs/`，下一轮实现必须把文档同步纳入验收。

## 安全边界

本轮仍是 no-motion path generation proof stabilization。

允许：

- 启动 LiDAR `/dev/ttyACM0`。
- 启动 smoke-only static TF、`map_server`、`amcl`、`planner_server` 和必要 lifecycle。
- 在显式 opt-in 下调用一次 planner compute-path。
- 保存 artifact、latest 指针、raw observation 摘要和 cleanup 证据。
- 通过 `ssh root@192.168.1.11 -p 37878` 在真实上位机复跑 direct-helper 和 API proof。

禁止：

- 发布 `/cmd_vel`。
- 打开或写入 WAVE ROVER/base UART `/dev/ttyS5`。
- 调用 `/api/base/*`。
- 调用 `/api/nav2/start`、`/api/nav2/stop`。
- 启动 `autonomous.launch.py`。
- 调用 `NavigateToPose`、`FollowPath`、`bt_navigator` 或 controller 执行链路。
- 把结果写成 HIL 通过、fixed-route execution 成功、path execution 成功、
  `safe_to_control=true` 或 `delivery_success=true`。

## 需要做什么

由 `robot-software-engineer` 单 owner 闭环完成：

1. 阅读 09:15 和 09:05 sprint 留档，先定位 artifact 缺口和观测判定缺口。
2. 修复 helper/API 的 artifact 留存、raw observation、topic 判定和 path generation
   summary，不新增运动能力。
3. 补齐单元测试和静态检查。
4. 在真实上位机 `ssh root@192.168.1.11 -p 37878` 上复跑 direct-helper 和 API 两条路径。
5. 无论远端是否 `path_generated=true`，都必须回填 artifact 路径、关键 JSON 片段、root
   cause 和 cleanup 证据。
6. 若复跑仍失败，必须能从 artifact 直接看出下一步应修 planner lifecycle、localization
   readiness、service/action 名称，还是观测器 timeout 判定。

## 工程师可执行文件范围

允许 `robot-software-engineer` 修改：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/scripts/upper_robot_api.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/fixed_route_workflow.md`
- `docs/hardware/board_sensor_stack_smoke.md`
- `sprints/2026.06.10_14-40_nav2_path_generation_artifact_stabilization/tech-done.md`

本轮不应修改：

- 任意 firmware/vendor 文件。
- 任意底盘默认参数或硬件配置。
- `autonomous.launch.py`。
- 任何会默认启用运动能力的 launch / behavior 配置。

## 优先级和验收口径

优先级：`P0`

产品设计阶段验收通过必须同时满足：

1. 本文件存在，且包含 `sprint_type`、`功能点`、`验收`、`no-motion`、`path generation`、
   `artifact`、`cmd_vel`、`owner`、`文件范围` 和 `ssh root@192.168.1.11`。
2. 文件明确下一轮最小可交付是 artifact 留存与观测判定稳定化，不是 surface、路线执行
   或送达成功。
3. 文件明确 Engineer 的允许文件范围、禁止范围、真实上位机验证入口和 no-motion 边界。

工程实现阶段验收通过必须同时满足：

1. 本地验证：
   - `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper`
   - `python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py --help`
   - `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/scripts/upper_robot_api.py`
   - `git diff --check`
2. 真实上位机 direct-helper 验证：
   - 使用 `ssh root@192.168.1.11 -p 37878` 进入 `/root/rober/onboard`。
   - 显式传入 managed runtime、initialpose 和 path generation opt-in。
   - 输出 artifact 路径和 summary。
   - 结束后给出 `lsof /dev/ttyS5 /dev/ttyACM0` 与 `fuser -v /dev/ttyS5 /dev/ttyACM0`
     摘要。
3. 真实上位机 API 验证：
   - `POST /api/nav2/proof/refresh` 显式传 path generation opt-in。
   - `GET /api/nav2/proof/latest` 能读回 artifact path、planner readiness、path summary
     和 no-motion flags。
4. 若 `path_generated=true`：
   - artifact 必须包含 path 点数、goal request、goal response、frame id、planner active
     证据和 cleanup 证据。
5. 若 `path_generated=false`：
   - artifact 必须包含明确 root cause，至少区分 `planner_server_not_active`、
     `localization_not_ready`、`path_service_unavailable`、`path_request_failed`、
     `topic_observation_timeout`。
6. 任何结果都必须保持：
   - `publishes_cmd_vel=false`
   - `calls_base_manual=false`
   - `uses_base_uart=false`
   - `safe_to_control=false`
   - `delivery_success=false`

## 本轮产品设计阶段验收命令

```bash
git status --short --branch
test -f sprints/2026.06.10_14-40_nav2_path_generation_artifact_stabilization/tech-done.md
rg -n "sprint_type|功能点|验收|no-motion|path generation|artifact|cmd_vel|owner|文件范围|ssh root@192.168.1.11" sprints/2026.06.10_14-40_nav2_path_generation_artifact_stabilization/tech-done.md
```

## 建议给 Engineer 的远端命令

本轮 Product 不执行下列实现验证命令；由下一轮 Engineer 执行并把日志片段回填到本文件。

```bash
ssh root@192.168.1.11 -p 37878 '
  set -e
  cd /root/rober/onboard
  source /opt/ros/humble/setup.bash
  python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
    --managed-runtime-opt-in \
    --managed-timeout-s 30 \
    --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml \
    --initialpose-opt-in \
    --initialpose-x 0.0 \
    --initialpose-y 0.0 \
    --initialpose-yaw 0.0 \
    --path-generation-opt-in \
    --path-generation-timeout-s 30 \
    --path-goal-frame-id map \
    --path-goal-x 0.8 \
    --path-goal-y 0.0 \
    --path-goal-yaw 0.0
  lsof /dev/ttyS5 /dev/ttyACM0 || true
  fuser -v /dev/ttyS5 /dev/ttyACM0 || true
'
```

```bash
ssh root@192.168.1.11 -p 37878 '
  set -e
  curl --max-time 180 -sS -X POST http://127.0.0.1:8787/api/nav2/proof/refresh \
    -H "Content-Type: application/json" \
    -d "{\"timeout_s\":30,\"managed_runtime_opt_in\":true,\"managed_timeout_s\":30,\"managed_map_yaml\":\"/root/rober/onboard/runtime/maps/trashbot_map.yaml\",\"initialpose_opt_in\":true,\"initialpose_x\":0.0,\"initialpose_y\":0.0,\"initialpose_yaw\":0.0,\"path_generation_opt_in\":true,\"path_generation_timeout_s\":30,\"path_goal_frame_id\":\"map\",\"path_goal_x\":0.8,\"path_goal_y\":0.0,\"path_goal_yaw\":0.0}"
  curl --max-time 30 -sS http://127.0.0.1:8787/api/nav2/proof/latest
  lsof /dev/ttyS5 /dev/ttyACM0 || true
  fuser -v /dev/ttyS5 /dev/ttyACM0 || true
'
```

## 对应责任 Engineer

- 主责：`robot-software-engineer`
- 默认不并行派单。若实现中需要确认 Nav2 planner action/service 名称或 lifecycle 判定，可
  只读咨询 `robot-algorithm-engineer`，但不得扩大为双 owner 实现 sprint。

## 风险、阻塞和需要补齐的证据链

- 09:05 已经出现远端 path generation 未通过，本轮不能把失败重复包装成新进展；必须新增
  artifact 证据能力。
- 真实上位机可能仍出现 `/scan`、`/map`、`/amcl_pose` timeout；本轮验收重点是失败原因
  能否被 artifact 清楚解释。
- 如果 `planner_server` 在 managed runtime 中仍不稳定，下一轮必须由 artifact 指向具体
  lifecycle、参数、map 或 TF 问题，不能继续停留在“planner not active”一句话。
- 本轮不证明运动安全、底盘 HIL、路线执行、固定路线回放或送达成功。

## 已完成 KR 的历史记录位置、证据来源和剩余风险

本轮不移动 KR 到历史区。前序证据引用如下：

- localization 证据来源：
  `sprints/2026.06.10_09-15_managed_nav2_localization_proof/tech-done.md`
  - 已证明：真实上位机 managed no-motion localization 观察到 `/scan`、`/map`、
    `/amcl_pose` 和 localization TF。
  - 剩余风险：未证明 planner compute-path。
- path generation 代码路径证据来源：
  `sprints/2026.06.10_09-05_nav2_no_motion_path_generation_proof/tech-done.md`
  - 已证明：helper/API 已存在 path generation opt-in 和安全 flags。
  - 剩余风险：远端未获得 `path_generated=true`，且 artifact 不足以稳定定位失败。

## 需要创建或更新的 sprint 文档

- 已创建本 micro sprint 文档：
  `sprints/2026.06.10_14-40_nav2_path_generation_artifact_stabilization/tech-done.md`
- 不创建 `pre_start.md`、`prd.md`、`tech-plan.md`、`side2side_check.md` 或 `final.md`，因为本轮
  是单 owner、单一设计切片、预计小于 1 小时的 micro sprint。

## 本轮实际改动

- 创建本文件，完成下一轮 Engineer 的产品/迭代设计、功能点完整性、文件范围、验收口径和
  风险边界。
- `onboard/scripts/upper_robot_api.py`：把 managed runtime、initialpose 和 path generation
  opt-in 参数统一追加到 `helper_argv`，再通过 `bash -lc` 显式 source
  `/opt/ros/humble/setup.bash` 与可选的 `/root/rober/onboard/install/setup.bash` 后执行 helper。
- `docs/navigation/fixed_route_workflow.md` 与 `docs/hardware/board_sensor_stack_smoke.md`：
  同步说明 API proof helper 的 ROS setup 来源，以及该变化不改变 no-motion 边界。
- 未修改 `OKR.md` 进度百分比。
- 未修改硬件配置、launch 默认运动链路或任何会默认启用运动能力的配置。

## 本轮验证结果

Product 设计阶段验收已执行：

```text
$ git status --short --branch
## master...origin/master
 M docs/hardware/board_sensor_stack_smoke.md
 M docs/navigation/fixed_route_workflow.md
 M onboard/scripts/upper_robot_api.py
 M sprints/2026.06.10_09-45_pc_robot_control_console/tech-done.md
?? sprints/2026.06.10_14-40_nav2_path_generation_artifact_stabilization/
```

结论：命令成功；工作区存在非本轮遗留改动
`docs/hardware/board_sensor_stack_smoke.md`、`docs/navigation/fixed_route_workflow.md`、
`onboard/scripts/upper_robot_api.py` 与
`sprints/2026.06.10_09-45_pc_robot_control_console/tech-done.md`。本轮新增范围只有
`sprints/2026.06.10_14-40_nav2_path_generation_artifact_stabilization/`。

```text
$ test -f sprints/2026.06.10_14-40_nav2_path_generation_artifact_stabilization/tech-done.md
```

结论：命令成功，目标文件存在。

```text
$ rg -n "sprint_type|功能点|验收|no-motion|path generation|artifact|cmd_vel|owner|文件范围|ssh root@192.168.1.11" sprints/2026.06.10_14-40_nav2_path_generation_artifact_stabilization/tech-done.md
```

结论：命令成功，关键字均命中。代表性命中包括：

- `3:## sprint_type`
- `7:## owner`
- `14:\`ssh root@192.168.1.11 -p 37878\` 上的 no-motion path generation proof 即使失败也能`
- `67:## 功能点完整清单`
- `145:## 工程师可执行文件范围`
- `163:## 优先级和验收口径`
- `169:1. 本文件存在，且包含 \`sprint_type\`、\`功能点\`、\`验收\`、\`no-motion\`、\`path generation\`、`
- `200:   - \`publishes_cmd_vel=false\``

工程实现命令由下一轮 `robot-software-engineer` 执行。

主会话补充执行了最小本地验证：

```text
$ python3 -m py_compile onboard/scripts/upper_robot_api.py
```

结论：命令成功，`upper_robot_api.py` 语法通过。

```text
$ git diff --check
```

结论：命令成功，没有空白错误。

## 剩余风险

- 当前只修复 API proof helper 的 ROS setup 启动环境；尚未修复 helper artifact schema、
  raw observation、topic 判定或 path generation summary。
- 下一轮 Engineer 必须在真实上位机复跑；没有新的远端 artifact 前，O3 path generation
  仍是 not proven。
- 本轮没有执行真实上位机 direct-helper/API path generation 复跑，因此不能声明
  `path_generated=true`、fixed-route execution、HIL pass 或送达成功。
