# Managed Nav2 localization proof

## sprint_type

micro

## owner

`robot-software-engineer`

## 用户价值和产品北极星

用户价值不是“多一个只读状态接口”，而是把现场 O3 验证 lane 再推进一个可执行台阶：
在不碰底盘运动、不占用 `/dev/ttyS5` 的前提下，拿到一份可以复用的 no-motion
localization 证据包，证明真实上位机上的 map、LiDAR、static TF、AMCL 和
localization TF 能否在同一受控窗口里成立。这样后续 O6/O7 才能消费真实定位材料，
而不是继续消费 `blocked_with_root_cause` 的只读 collector 结果。

产品北极星保持不变：把 `rober` 从“软件侧能跑”推进到“真实现场可验证地完成送垃圾”。
本轮只服务于这条主线，不新增 surface，不包装 not_proven 为完成。

## OKR 映射和方向判断

- 对应 Objective：现场 O3 验证 lane（当前最高优先级，临时激活归档 Objective）。
- 方向判断：`继续`。
- 继续理由：
  1. `sprints/2026.06.10_08-15_nav2_lifecycle_activation_probe/tech-done.md`
     已证明手动 no-motion runtime 内 `map_server`、`amcl` 可进入 `active [3]`，
     root cause 已从“包缺失”收敛到“formal collector 与手动 runtime 分离，
     且 AMCL 缺 initial pose / localization TF”。
  2. `sprints/2026.06.10_08-45_nav2_initialpose_no_motion_proof/tech-done.md`
     已证明 opt-in `/initialpose` 的安全边界成立，但在没有 active graph 的前提下，
     canonical collector 仍只能返回 `blocked_with_root_cause`。
  3. 因此下一轮不应继续做 read-only surface，也不应直接跳到 path execution；
     最小闭环应是“managed runtime + opt-in localization evidence + final cleanup”。

## KR 拆解 / 更新

本轮不归档已完成 KR，也不更新 `OKR.md` 百分比；只为 O3 验证 lane 定义新的最小交付 KR：

- KR-O3-Managed-1：helper/API 在显式 opt-in 下可短暂拉起 no-motion localization runtime。
- KR-O3-Managed-2：同一窗口内完成 `/scan`、`/map`、`/amcl_pose`、
  `map -> odom`、`map -> base_link` 证据采集。
- KR-O3-Managed-3：artifact 必须显式写出 runtime 是否由 helper 管理拉起、是否发布
  `/initialpose`、各 lifecycle 状态、TF 观测结果和 safety flags。
- KR-O3-Managed-4：proof 结束后必须完成清场，并给出 `/dev/ttyS5` 未占用、
  `/dev/ttyACM0` 无本轮残留、无 orphan `ros2 topic echo/pub` / `tf2_echo` 证据。

## 本轮核心抓手

把“手动 runtime 能 active”与“formal API 只读 collector 会 blocked”之间的断层补上，
做成一个显式 opt-in、默认关闭、受控清场的 managed no-motion localization proof。

## 功能点完整清单

1. `o10_amcl_nav2_runtime_proof.py` 增加 managed runtime opt-in，例如：
   `--managed-runtime-opt-in`、`--managed-timeout-s`、`--managed-map-yaml`，
   由 helper 在本轮 proof 窗口内短暂启动：
   - LiDAR `/dev/ttyACM0 @ 150000`
   - static TF `odom -> base_link`
   - static TF `base_link -> laser_frame`
   - `map_server`
   - `amcl`
   - `nav2_lifecycle_manager`
2. managed runtime 默认关闭；未显式 opt-in 时，保留既有 read-only collector 行为。
3. managed runtime 与 `initialpose_opt_in` 必须解耦：
   - 只开 managed runtime、不发 `/initialpose`：允许验证 active graph 是否成立。
   - managed runtime + `initialpose_opt_in=true`：允许进一步验证 `/amcl_pose` 和
     localization TF。
4. artifact 增加 managed runtime 字段：
   - `managed_runtime_requested`
   - `managed_runtime_started`
   - `managed_runtime_process_group`
   - `managed_runtime_cleanup_ok`
   - `managed_runtime_boundary`
5. artifact 必须保留并更新以下事实：
   - `map_server_active`
   - `amcl_active`
   - `scan_once_observed`
   - `map_once_observed`
   - `amcl_pose_observed`
   - `localization_tf_observed.map_to_odom`
   - `localization_tf_observed.map_to_base_link`
   - `initialpose_publish_attempted`
   - `initialpose_published`
6. `upper_robot_api.py` 的 `/api/nav2/proof/refresh` body 增加显式 opt-in 透传：
   - `managed_runtime_opt_in`
   - `managed_timeout_s`
   - `managed_map_yaml`
   - 与既有 `initialpose_*` 参数并存
7. 单元测试覆盖三类路径：
   - 默认 read-only
   - managed runtime without initialpose
   - managed runtime with initialpose
8. 文档同步要求：
   - `docs/navigation/fixed_route_workflow.md`
   - `docs/hardware/board_sensor_stack_smoke.md`
   都必须补齐 09:15 边界与命令模板。

## 安全边界

本轮边界必须比 08:15 / 08:45 更清楚，且仍保持 no-motion：

- 允许：
  - 启动 LiDAR `/dev/ttyACM0`
  - 启动 smoke-only static TF
  - 启动 `map_server`、`amcl`、`nav2_lifecycle_manager`
  - 在显式 opt-in 下发布一次 `/initialpose`
  - 采集 `/map`、`/amcl_pose`、TF、lifecycle、topic once 证据
- 禁止：
  - 发送 Nav2 goal
  - 调用 compute path action/service
  - 发布 `/cmd_vel`
  - 调用 `/api/base/*`
  - 调用 `/api/nav2/start`、`/api/nav2/stop`
  - 启动 `autonomous.launch.py`
  - 打开 WAVE ROVER/base UART `/dev/ttyS5`
  - 把结果写成 `safe_to_control=true`、`delivery_success=true`、HIL 通过、
    fixed-route execution 成功或 path execution 成功

## 需要做什么

由 `robot-software-engineer` 单 owner 闭环完成：

1. 实现 managed runtime helper。
2. 把 HTTP body 显式透传到 helper。
3. 补单元测试和静态检查。
4. 在真实上位机 `root@192.168.1.11 -p 37878` 上做一次 direct-helper 验证，
   以及一次 API 验证。
5. 两次验证都要带 final cleanup 和 `/dev/ttyS5` 不占用检查。
6. 回填本 sprint `tech-done.md` 的实际改动、验证结果和剩余风险。

## 工程师可执行文件范围

允许 `robot-software-engineer` 修改：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/scripts/upper_robot_api.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/fixed_route_workflow.md`
- `docs/hardware/board_sensor_stack_smoke.md`
- `sprints/2026.06.10_09-15_managed_nav2_localization_proof/tech-done.md`

本轮不应修改：

- 任意底盘/firmware/vendor 文件
- `autonomous.launch.py`
- 任何会默认启用运动能力的 launch / behavior 配置

## 优先级和验收口径

优先级：`P0`

验收通过必须同时满足：

1. 默认 body 不传 `managed_runtime_opt_in` 时，`/api/nav2/proof/refresh` 仍保持
   read-only collector，不能新增 runtime、副作用或串口占用。
2. direct-helper managed runtime 验证中，artifact 明确记录：
   - `managed_runtime_started=true`
   - `scan_once_observed=true`
   - `map_server_active=true`
   - `amcl_active=true`
3. 若显式传 `initialpose_opt_in=true`，则至少满足以下二选一：
   - `/amcl_pose` 与 localization TF 成功观测；或
   - artifact 明确给出失败根因，但 managed runtime 和 cleanup 本身通过
4. final cleanup 证据明确显示：
   - 无 `ros2 topic echo/pub`、`tf2_echo` 残留
   - `lsof /dev/ttyS5 /dev/ttyACM0` 无本轮非法占用
   - `fuser -v /dev/ttyS5 /dev/ttyACM0` 无本轮非法占用
5. 所有 artifact 继续保持：
   - `publishes_cmd_vel=false`
   - `calls_base_manual=false`
   - `uses_base_uart=false`
   - `safe_to_control=false`
   - `delivery_success=false`

## 建议给 Engineer 的验收命令

本轮 Product 不执行下列命令；由 Engineer 执行并回填结果：

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
    --initialpose-yaw 0.0
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
    -d "{\"timeout_s\":20,\"managed_runtime_opt_in\":true,\"managed_timeout_s\":20,\"managed_map_yaml\":\"/root/rober/onboard/runtime/maps/trashbot_map.yaml\",\"initialpose_opt_in\":true,\"initialpose_x\":0.0,\"initialpose_y\":0.0,\"initialpose_yaw\":0.0}"
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
- 咨询：本轮默认不并行派单；若实现中需要确认 AMCL / TF 判定逻辑，可只读咨询
  `robot-algorithm-engineer`，但不扩成双 owner sprint。

## 风险、阻塞和需要补齐的证据链

- 最大风险不是代码，而是真实上位机上 managed runtime 是否会与现有 graph /
  常驻服务互相污染。
- `/dev/ttyACM0` LiDAR 可用性此前已通过 no-motion smoke 证明，但仍可能出现历史
  进程残留；所以 cleanup 证据是必选项，不是附加项。
- `/dev/ttyS5` 当前不能碰；若实现阶段为了重启 API 服务而间接触碰 base UART，
  该 sprint 直接判定未过边界。
- 即使本轮拿到 `/amcl_pose` 和 TF，也仍不是路径规划、固定路线或送达成功证据；
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

## 需要创建或更新的 sprint 文档

- 本轮是 `micro sprint`，只强制维护：
  - `sprints/2026.06.10_09-15_managed_nav2_localization_proof/tech-done.md`
- Engineer 完成实现后，必须在同一文件补齐：
  - 实际改动
  - 验证结果
  - 失败定位（如有）
  - 剩余风险

## 实际改动

- 实现 `onboard/scripts/o10_amcl_nav2_runtime_proof.py` 的 managed runtime opt-in：
  - 新增 `--managed-runtime-opt-in`
  - 新增 `--managed-timeout-s`
  - 新增 `--managed-map-yaml`
  - managed runtime 只启动 LiDAR `/dev/ttyACM0 @ 150000`、两个 static TF、
    `map_server`、`amcl`、`lifecycle_manager`
  - managed runtime 与 `initialpose_opt_in` 解耦
  - artifact 新增：
    - `managed_runtime_requested`
    - `managed_runtime_started`
    - `managed_runtime_process_group`
    - `managed_runtime_cleanup_ok`
    - `managed_runtime_boundary`
  - 增加进程组清理、lifecycle recheck、TF 成功优先判定，避免 CLI 抖动误报 blocker
- 更新 `onboard/scripts/upper_robot_api.py`
  - `/api/nav2/proof/refresh` 显式透传
    `managed_runtime_opt_in`、`managed_timeout_s`、`managed_map_yaml`
  - 默认 body 缺省仍保持 read-only collector
- 更新 `onboard/tests/test_nav2_runtime_proof_helper.py`
  - 覆盖默认 read-only
  - 覆盖 managed without initialpose
  - 覆盖 managed with initialpose
  - 覆盖 no-motion / no-UART / no-goal / cleanup guard
- 更新文档：
  - `docs/navigation/fixed_route_workflow.md`
  - `docs/hardware/board_sensor_stack_smoke.md`
- 回填远端证据到：
  - `sprints/2026.06.10_09-15_managed_nav2_localization_proof/artifacts/remote_capture/`

## 验证结果

本轮已运行并通过本地验收命令：

- `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper`
  - 结果：`Ran 13 tests ... OK`
- `python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py --help`
  - 结果：CLI 输出包含 `--managed-runtime-opt-in`、`--managed-timeout-s`、
    `--managed-map-yaml`、`--initialpose-*`
- `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/scripts/upper_robot_api.py`
  - 结果：通过
- `git diff --check`
  - 结果：通过

远端 direct-helper 验证（真实上位机 `root@192.168.1.11:37878`）：

- 命令：`python3 scripts/o10_amcl_nav2_runtime_proof.py --managed-runtime-opt-in --managed-timeout-s 20 --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml --initialpose-opt-in --initialpose-x 0.0 --initialpose-y 0.0 --initialpose-yaw 0.0`
- 结果：
  - `status=nav2_no_motion_localization_runtime_observed`
  - `managed_runtime_started=true`
  - `managed_runtime_cleanup_ok=true`
  - `scan_once_observed=true`
  - `map_once_observed=true`
  - `map_server_active=true`
  - `amcl_active=true`
  - `amcl_pose_observed=true`
  - `localization_tf_observed.map_to_odom=true`
  - `localization_tf_observed.map_to_base_link=true`
  - `safe_to_control=false`
- 设备清场：
  - `lsof /dev/ttyS5 /dev/ttyACM0` 无输出
  - `fuser -v /dev/ttyS5 /dev/ttyACM0` 无输出

远端 API 验证：

- 为加载新 `upper_robot_api.py`，执行过一次
  `systemctl restart trashbot-upper-robot-api.service`
- 重启前后 service 都是 `active (running)`，证据见：
  - `trashbot_upper_status_before.txt`
  - `trashbot_upper_status_after.txt`
- 默认 body：
  - `POST /api/nav2/proof/refresh {"timeout_s":20}`
  - 结果保持 read-only：
    - `managed_runtime_requested=false`
    - `managed_runtime_started=false`
    - `scan_once_observed=false`
    - `map_once_observed=false`
    - `safe_to_control=false`
- managed body：
  - `POST /api/nav2/proof/refresh {"timeout_s":20,"managed_runtime_opt_in":true,"managed_timeout_s":20,"managed_map_yaml":"/root/rober/onboard/runtime/maps/trashbot_map.yaml","initialpose_opt_in":true,"initialpose_x":0.0,"initialpose_y":0.0,"initialpose_yaw":0.0}`
  - 结果：
    - top-level `status=refreshed`
    - proof `status=nav2_no_motion_localization_runtime_observed`
    - `managed_runtime_started=true`
    - `managed_runtime_cleanup_ok=true`
    - `scan_once_observed=true`
    - `map_once_observed=true`
    - `map_server_active=true`
    - `amcl_active=true`
    - `amcl_pose_observed=true`
    - `localization_tf_observed.map_to_odom=true`
    - `localization_tf_observed.map_to_base_link=true`
    - `safe_to_control=false`
- `GET /api/nav2/proof/latest`
  - 顶层仍按 software guard 返回 `status=not_proven`
  - 但 `latest_proof_status=nav2_no_motion_localization_runtime_observed`
  - 且 `latest_map_server_active/latest_amcl_active/latest_amcl_pose_observed` 已正确刷新
- `GET /api/nav2/status`
  - 顶层 `status=not_proven`
  - 通过嵌套 `proof_latest` 暴露最新摘要，不直接翻转为 runtime proven
- API 验证后设备清场：
  - `nav2_device_lsof.txt` 为空
  - `nav2_device_fuser.txt` 为空

## 失败定位

实现过程中遇到并已修复/规避的失败点：

- 第一次 direct-helper 失败：远端板子仍是旧 helper 脚本，不识别新 CLI。
  - 处理：先 `scp` 同步 `o10_amcl_nav2_runtime_proof.py` 和 `upper_robot_api.py`
- 第二次 direct-helper 失败：AMCL configure 报
  `Input t_sec is too large or too small for tf2::Duration`
  - 根因：参数文件过度精简，缺少官方常用 AMCL 参数
  - 处理：按 Navigation2 Humble 官方 `nav2_params.yaml` 的 AMCL 段补齐
    `transform_tolerance`、`save_pose_rate`、`beam_skip_*`、`pf_*`、`z_*`
- 第三次 direct-helper 失败：TF 已输出成功 transform，但判定函数被早期
  `Waiting for transform` 日志误导
  - 处理：`tf_echo_transform_observed()` 改为“先看是否已输出完整 transform，再看失败提示”
- 第四次 direct-helper 失败：`ros2 lifecycle get` 在板端偶发超时
  - 处理：lifecycle CLI timeout 从 `6s` 放宽到 `10s`，并加入 recheck 合并逻辑

当前未再发现功能 blocker。managed direct-helper 与 managed API 都已通过。

## 剩余风险

- `GET /api/nav2/proof/latest` 和 `GET /api/nav2/status` 顶层仍按 software guard
  返回 `not_proven`；读取方必须消费 `latest_proof_status` 与 `proof_latest.latest_*`
  字段，不能只盯顶层 `status`。
- managed runtime 清场成功，但 `lidar_driver` 在 SIGINT 收尾时仍会打印
  `rcl_shutdown already called` traceback。该日志不影响 `managed_runtime_cleanup_ok=true`
  和设备清场结果，但若后续要追求更干净的 runtime 日志，需要单独修
  `ros2_trashbot_hardware/lidar_driver.py` 的 shutdown 逻辑。
- 本轮仍只证明 no-motion localization proof，不证明 planner/controller、
  compute path、path execution、fixed-route execution、HIL 或 delivery success。

记录时间：2026-06-10 08:38:00 CST。
