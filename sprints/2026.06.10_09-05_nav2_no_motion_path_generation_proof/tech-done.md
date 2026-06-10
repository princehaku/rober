# Nav2 no-motion path generation proof

## sprint_type

micro

## owner

`robot-software-engineer`

## 用户价值和产品北极星

用户价值不是再做一层只读状态面，而是在真实上位机 `root@192.168.1.11 -p 37878`
上，把“定位已观测”继续推进到“规划器能在 no-motion 窗口里产出可复用的 path”。
这一步的意义是：后续 O3 现场验证、route replay、固定路线准备和 O6/O7 的数据
材料，都可以引用同一条真实 planner 证据链，而不是继续停留在 localization only
 或 handoff/review surface。

产品北极星不变：把 `rober` 做成一台面向普通手机用户的低成本 ROS2 自主垃圾投递
机器人。本轮只推进 O3 现场验证 lane 的下一格，不把 path generation 写成运动执行，
也不把 planner ready 包装成 delivery success。

## OKR 映射和方向判断

- 对应 Objective：现场 O3 验证 lane（当前最高优先级，临时激活归档 Objective）。
- 方向判断：`继续`。
- 继续理由：
  1. 上一轮 managed no-motion localization proof 已证明真实上位机上 `map_server`、
     `amcl`、`localization TF` 可以在受控窗口里成立，`safe_to_control=false` 且
     清场成功。
  2. 但目前仍缺一个更靠近 planner 的证据台阶：在不发车、不发 `/cmd_vel`、
     不碰 `/dev/ttyS5` 的前提下，证明 Nav2 planner 可以对一个显式目标产出 path。
  3. 这一步比直接进入 route execution 更小，也更符合“先证据、后执行”的 O3 现场
     验证节奏。

## KR 拆解 / 更新

本轮不归档已完成 KR，也不调整 `OKR.md` 百分比；只为 O3 验证 lane 增加一个新的
最小交付 KR：

- KR-O3-PathGen-1：helper/API 在显式 opt-in 下可短暂拉起 no-motion planner runtime。
- KR-O3-PathGen-2：在 localization 已观测的前提下，可通过单次 planner compute-path
  调用得到一份 path artifact。
- KR-O3-PathGen-3：artifact 必须显式写出 planner lifecycle、compute-path 请求与响应、
  path 点数、path 目标、边界说明和 safety flags。
- KR-O3-PathGen-4：proof 结束后必须完成清场，并给出 `/dev/ttyS5` 未占用、无 orphan
  `ros2 topic echo/pub` / `tf2_echo` 证据。

## 本轮核心抓手

复用现有 `o10_amcl_nav2_runtime_proof.py` 的 managed runtime / initialpose / cleanup
骨架，只新增一个受控的 planner compute-path opt-in 分支，避免再造一套 helper 和
artifact schema。

## 功能点完整清单

1. `o10_amcl_nav2_runtime_proof.py` 增加 planner/path generation opt-in：
   - `--path-generation-opt-in`
   - `--path-generation-timeout-s`
   - `--path-goal-frame-id`
   - `--path-goal-x`
   - `--path-goal-y`
   - `--path-goal-yaw`
2. path generation opt-in 默认关闭；只有显式开启时，helper 才允许在满足
   localization proof 的前提下调用一次 Nav2 planner compute-path 服务。
3. 这轮的 path generation 只允许调用 planner 的计算接口，不允许切换到任何会驱动
   机器人运动的入口。
   - 允许：`ComputePathToPose` 风格的 planner 计算调用。
   - 禁止：`NavigateToPose` / `FollowPath` / `bt_navigator` / `controller_server`
     执行链路。
4. helper 仍以现有 managed runtime 为底座，但 planner readiness 证明窗口里应保持
   controller 侧不作为主路径，不把 controller 活跃当成验收前提。
5. artifact 新增 / 强化字段：
   - `path_generation_opt_in`
   - `path_generation_requested`
   - `path_generation_attempted`
   - `path_generation_service_name`
   - `path_generation_service_available`
   - `path_generation_succeeded`
   - `path_generated`
   - `path_point_count`
   - `path_goal_request`
   - `path_goal_response`
   - `path_generation_boundary`
   - `planner_server_active`
   - `controller_server_active`
   - `controller_server_requested`
   - `planner_readiness_summary`
6. HTTP body 需要显式透传同一组字段，默认 body 不传时仍保持 read-only collector。
7. 单元测试覆盖三类路径：
   - 默认 read-only
   - managed runtime + initialpose，无 path generation
   - managed runtime + initialpose + path generation opt-in

## 安全边界

本轮仍然必须保持 no-motion。

允许：

- 启动 LiDAR `/dev/ttyACM0`
- 启动 smoke-only static TF
- 启动 `map_server`、`amcl`、`planner_server`、`nav2_lifecycle_manager`
- 在显式 opt-in 下调用一次 planner compute-path 服务
- 采集 path artifact、lifecycle、topic once 证据
- 结束后做完整清场和串口占用检查

禁止：

- 发送 Nav2 goal
- 调用 `NavigateToPose`
- 调用 `FollowPath`
- 启动 `bt_navigator`
- 发布 `/cmd_vel`
- 调用 `/api/base/*`
- 调用 `/api/nav2/start`、`/api/nav2/stop`
- 启动 `autonomous.launch.py`
- 打开 WAVE ROVER/base UART `/dev/ttyS5`
- 把结果写成 `safe_to_control=true`、`delivery_success=true`、HIL 通过、
  fixed-route execution 成功或 path execution 成功

为什么这仍然是 no-motion：

1. planner compute-path 只返回离线路径数据，不直接驱动底盘。
2. 本轮禁止 controller/BT/goal 链路，因此不会进入实际执行层。
3. 任何 `/cmd_vel` 或底盘 UART 写入都被视为越界。

## 需要做什么

由 `robot-software-engineer` 单 owner 闭环完成：

1. 扩展 `o10_amcl_nav2_runtime_proof.py`，加入 path generation opt-in 分支。
2. 把 HTTP body 显式透传到 helper。
3. 补单元测试和静态检查。
4. 在真实上位机 `root@192.168.1.11 -p 37878` 上做一次 direct-helper 验证，以及一次
   API 验证。
5. 两次验证都要带 final cleanup 和 `/dev/ttyS5` 不占用检查。
6. 回填本 sprint `tech-done.md` 的实际改动、验证结果和剩余风险。

## 工程师可执行文件范围

允许 `robot-software-engineer` 修改：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/scripts/upper_robot_api.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/fixed_route_workflow.md`
- `docs/hardware/board_sensor_stack_smoke.md`
- `sprints/2026.06.10_09-05_nav2_no_motion_path_generation_proof/tech-done.md`

本轮不应修改：

- 任意底盘/firmware/vendor 文件
- `autonomous.launch.py`
- 任何会默认启用运动能力的 launch / behavior 配置

## 优先级和验收口径

优先级：`P0`

产品设计阶段验收通过必须同时满足：

1. `git status --short --branch` 只反映本轮允许范围内的变更。
2. 新建的 sprint 文件存在，且包含 `sprint_type`、`owner`、`功能点`、
   `验收`、`no-motion`、`compute`、`cmd_vel`、`owner`、`文件范围` 等关键字。
3. 设计稿明确说明：允许显式 opt-in 调用 planner compute-path，但仍然禁止任何会进入
   底盘运动层的入口。
4. 设计稿明确区分：
   - localization proof
   - planner readiness / path generation proof
   - path execution / delivery success

工程实现阶段的验收口径预留如下：

1. 默认 body 不传 `path_generation_opt_in` 时，`/api/nav2/proof/refresh` 仍保持
   read-only collector，不新增 path generation 副作用。
2. direct-helper path generation 验证中，artifact 明确记录：
   - `planner_server_active=true`
   - `path_generation_requested=true`
   - `path_generation_succeeded=true`
   - `path_generated=true`
3. final cleanup 证据明确显示：
   - 无 `ros2 topic echo/pub`、`tf2_echo` 残留
   - `lsof /dev/ttyS5 /dev/ttyACM0` 无本轮非法占用
   - `fuser -v /dev/ttyS5 /dev/ttyACM0` 无本轮非法占用
4. 所有 artifact 继续保持：
   - `publishes_cmd_vel=false`
   - `calls_base_manual=false`
   - `uses_base_uart=false`
   - `safe_to_control=false`
   - `delivery_success=false`

## 本轮产品设计阶段验收命令

```bash
git status --short --branch
test -f sprints/2026.06.10_09-05_nav2_no_motion_path_generation_proof/tech-done.md
rg -n "sprint_type|功能点|验收|no-motion|cmd_vel|compute|owner|文件范围" sprints/2026.06.10_09-05_nav2_no_motion_path_generation_proof/tech-done.md
```

## 建议给 Engineer 的验收命令

本轮产品设计阶段不执行下列命令；由 Engineer 在实现阶段执行并回填结果：

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py --help
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/scripts/upper_robot_api.py
git diff --check
```

远端 direct-helper 验证建议命令：

```bash
ssh root@192.168.1.11 -p 37878 '
  set -e
  cd /root/rober/onboard
  source /opt/ros/humble/setup.bash
  python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
    --managed-runtime-opt-in \
    --managed-timeout-s 20 \
    --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml \
    --initialpose-opt-in \
    --initialpose-x 0.0 \
    --initialpose-y 0.0 \
    --initialpose-yaw 0.0 \
    --path-generation-opt-in \
    --path-generation-timeout-s 20 \
    --path-goal-frame-id map \
    --path-goal-x 0.8 \
    --path-goal-y 0.0 \
    --path-goal-yaw 0.0
  lsof /dev/ttyS5 /dev/ttyACM0 || true
  fuser -v /dev/ttyS5 /dev/ttyACM0 || true
'
```

远端 API 验证建议命令：

```bash
ssh root@192.168.1.11 -p 37878 '
  set -e
  curl --max-time 150 -sS -X POST http://127.0.0.1:8787/api/nav2/proof/refresh \
    -H "Content-Type: application/json" \
    -d "{\"timeout_s\":20,\"managed_runtime_opt_in\":true,\"managed_timeout_s\":20,\"managed_map_yaml\":\"/root/rober/onboard/runtime/maps/trashbot_map.yaml\",\"initialpose_opt_in\":true,\"initialpose_x\":0.0,\"initialpose_y\":0.0,\"initialpose_yaw\":0.0,\"path_generation_opt_in\":true,\"path_generation_timeout_s\":20,\"path_goal_frame_id\":\"map\",\"path_goal_x\":0.8,\"path_goal_y\":0.0,\"path_goal_yaw\":0.0}"
  curl --max-time 30 -sS http://127.0.0.1:8787/api/nav2/proof/latest
  curl --max-time 30 -sS http://127.0.0.1:8787/api/nav2/status
  lsof /dev/ttyS5 /dev/ttyACM0 || true
  fuser -v /dev/ttyS5 /dev/ttyACM0 || true
'
```

如 API 验证需要重启服务，必须在验证记录中写清：

- 重启前后 `trashbot-upper-robot-api.service` 状态
- 是否影响常驻 `/dev/ttyS5` 占用
- 为什么仍满足 no-motion 边界

## 对应责任 Engineer

- 主责：`robot-software-engineer`
- 咨询：本轮默认不并行派单；若实现中需要确认 AMCL / planner / TF 判定逻辑，可只读咨询
  `robot-algorithm-engineer`，但不扩成双 owner sprint。

## 风险、阻塞和需要补齐的证据链

- 最大风险不是 path 算法本身，而是真实上位机上的 planner runtime 是否会和现有 graph
  / 常驻服务互相污染。
- `ComputePathToPose` 的结果必须被保守解释为 path 数据，不可被误读为 motion ready。
- `/dev/ttyS5` 当前不能碰；若实现阶段为了重启 API 服务而间接触碰 base UART，该 sprint
  直接判定未过边界。
- 即使本轮拿到 `path_generated=true`，也仍不是 route execution、fixed-route execution、
  controller output、physical motion、safe_to_control 或 delivery_success 证据；
  后续还需要 route replay / map consumption / task result 证据链。

## 已完成 KR 的历史记录位置、证据来源和剩余风险

本轮不迁移 KR 到历史区，但必须引用以下既有证据作为前序完成事实：

- 手动 lifecycle active 证据：
  `sprints/2026.06.10_08-15_nav2_lifecycle_activation_probe/tech-done.md`
  - 证据来源：手动 runtime 内 `/map_server active [3]`、`/amcl active [3]`
  - 剩余风险：formal collector 与手动 runtime 分离，且无 `/initialpose`
- initialpose opt-in 边界证据：
  `sprints/2026.06.10_08-45_nav2_initialpose_no_motion_proof/tech-done.md`
  - 证据来源：`initialpose_opt_in` API/helper 透传和 cleanup guard 已成立
  - 剩余风险：没有 active graph 时 `/initialpose` 发布超时，`/amcl_pose` 仍未成立
- managed localization proof 证据：
  `sprints/2026.06.10_09-15_managed_nav2_localization_proof/tech-done.md`
  - 证据来源：真实上位机 managed no-motion localization 证实 `scan_once_observed=true`、
    `map_server_active=true`、`amcl_active=true`、`amcl_pose_observed=true`
  - 剩余风险：尚未证明 planner compute-path 或 path generation

## 本轮实际改动

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - 增加显式 `--path-generation-opt-in` 分支；默认不调用 planner。
  - managed runtime 在 path opt-in 时只追加 `planner_server`，不启动
    `controller_server`、`bt_navigator`、`NavigateToPose` 或 `FollowPath`。
  - 在 localization ready 且 `planner_server` active 后，才尝试一次
    `ComputePathToPose` action，并把请求、响应、path 点数、planner readiness
    和失败原因写入 artifact。
  - artifact 继续强制 `publishes_cmd_vel=false`、`calls_base_manual=false`、
    `uses_base_uart=false`、`safe_to_control=false`、`delivery_success=false`。
- `onboard/scripts/upper_robot_api.py`
  - `POST /api/nav2/proof/refresh` 增加 `path_generation_opt_in`、
    `path_generation_timeout_s`、`path_goal_frame_id`、`path_goal_x`、
    `path_goal_y`、`path_goal_yaw` 显式透传。
  - `/api/nav2/proof/latest` / `/api/nav2/status` 摘要增加 path generation
    readback 字段，便于 PC 页面后续读取 planner proof 状态。
- `onboard/tests/test_nav2_runtime_proof_helper.py`
  - 增加默认 read-only、path opt-in 只拉 planner、不拉 controller/BT、
    API 透传和安全字段的回归覆盖。
- `docs/navigation/fixed_route_workflow.md`
  - 增加 09:05 path generation opt-in 的 no-motion 边界说明。
- `docs/hardware/board_sensor_stack_smoke.md`
  - 增加现场硬件 smoke 里的 planner proof 边界，明确不是 HIL、运动或送达成功。

本轮未修改 firmware/vendor 文件、`autonomous.launch.py`、底盘配置或任何默认启用运动的
launch 参数。

## 本轮验证结果

由 `robot-software-engineer` 子 agent 执行并返回：

```text
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
Ran 15 tests ... OK

python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py --help
通过，help 输出包含 --path-generation-* 参数。

python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/scripts/upper_robot_api.py
通过。

git diff --check
通过。
```

远端真实上位机 `root@192.168.1.11 -p 37878` 尝试结果：

- 已把 helper/API 同步到 `/root/rober/onboard/scripts/`。
- direct-helper 第一次执行返回 `rc=2`，root cause 为
  `planner_server_not_active`。当时 `map_server_active=true`、
  `amcl_active=true`，`/scan`、`/map`、`/amcl_pose` 曾被观测，但 planner
  lifecycle 未进入 active。
- 修复 helper 时序后第二次执行仍返回 `rc=2`，root cause 退化到 localization
  readiness 不稳定；`/map` 有 stdout 但 topic echo timeout，`/scan` 和
  `/amcl_pose` 未稳定采到。
- 第三次带 `--timeout-s 20` 重试时被主节点要求停止继续等待，改为收口和清场。

清场结果由子 agent 返回：

- 已清理远端残留 Nav2/LiDAR/static TF/helper 进程组。
- `trashbot-upper-robot-api.service` 已恢复为 `active`。
- 最终 `lsof /dev/ttyS5 /dev/ttyACM0` 与
  `fuser -v /dev/ttyS5 /dev/ttyACM0` 无占用输出。

本轮没有保留完整远端日志 artifact，因此上述远端结果只能作为子 agent 执行回报和
sprint 留档事实；不能升级为正式 `path_generated=true` 证据。

## 剩余风险

- 真实上位机 path generation proof 未通过；`path_generated=true`、
  `path_generation_succeeded=true` 仍未证明。
- 当前 blocker 是 managed no-motion runtime 下 localization/planner readiness
  不稳定：`/compute_path_to_pose` action server 曾出现，但 planner lifecycle 未稳定
  active，后续重试又出现 `/scan`、`/amcl_pose` 采样 timeout。
- helper 对 `ros2 topic echo --once` 的 timeout+stdout 情况仍偏保守；`/map`
  已有 stdout 时仍可能被标成未观测，下一轮应修正观测判定并保留完整 artifact。
- 本轮只推进 PC/API 后续控制页面可消费的 planner proof 字段，不证明 PC 页面已经能
  完整控制雷达、建图、定位移动、手动移动或实时图传。
- no-motion 安全边界仍成立：`publishes_cmd_vel=false`、
  `calls_base_manual=false`、`uses_base_uart=false`、`safe_to_control=false`、
  `delivery_success=false`。运动、HIL、fixed-route execution 和送达成功仍未证明。
