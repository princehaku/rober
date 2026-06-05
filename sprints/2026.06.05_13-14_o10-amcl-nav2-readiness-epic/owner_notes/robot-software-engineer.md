# Robot Software Engineer Owner Note

## 本轮范围

- sprint: `2026.06.05_13-14_o10-amcl-nav2-readiness-epic`
- owner: `robot-software-engineer`
- Objective: O10 AMCL/Nav2 readiness 的 Robot Software 输入护栏
- 时间: 2026-06-05 13:23:59 CST

## 实际改动

- 在 `onboard/scripts/upper_robot_api.py` 的 `/api/nav2/status` 增加
  `amcl_nav2_readiness`。
- 该字段从 canonical latest JSON
  `/root/rober/onboard/runtime/map_lifecycle_latest.json` 和 map artifacts
  `/root/rober/onboard/runtime/maps` 只读折算 AMCL/Nav2 readiness 输入。
- readiness 只判断 latest、map metadata、YAML、PGM、canonical map dir 是否齐备；
  不启动 ROS2、不发布 `/cmd_vel`、不调用 `/api/base/manual`、不打开底盘 UART。
- 输入齐备时状态为 `map_inputs_ready_for_no_motion_nav2_collector`；输入缺失或契约漂移时状态为
  `blocked_with_root_cause`。
- 同步更新 `docs/navigation/nav2_map_quality_metrics.md`，记录 O10 readiness 输入护栏。

## 验证结果

- 精确测试：
  `python3 -m unittest onboard.scripts.test_upper_robot_api.UpperRobotApiSafetyTest.test_nav2_status_derives_readiness_inputs_from_canonical_map_proof onboard.scripts.test_upper_robot_api.UpperRobotApiSafetyTest.test_nav2_status_blocks_readiness_when_canonical_map_proof_missing`
  结果：2 tests OK。
- `python3 -m compileall -q onboard/scripts onboard/src`
  结果：exit 0，无输出。
- `python3 -m unittest discover -s onboard/scripts -p 'test_*.py'`
  结果：Ran 86 tests in 4.930s，OK，skipped=3。
- `python3 -m unittest discover -s onboard/src -p 'test_*.py'`
  结果：exit 5，Ran 0 tests；根因是当前 `onboard/src` 布局的测试在各 ROS2 package 的
  `test/` 子目录，顶层 discovery 没进入包级目录，不是本轮 readiness 代码失败。
- 替代包级验证：
  - `python3 -m unittest discover -s onboard/src/ros2_trashbot_nav/test -p 'test_*.py'`
    结果：Ran 54 tests in 5.412s，OK。
  - `python3 -m unittest discover -s onboard/src/ros2_trashbot_bringup/test -p 'test_*.py'`
    结果：Ran 12 tests in 0.101s，OK。
  - `python3 -m unittest discover -s onboard/src/ros2_trashbot_hardware/test -p 'test_*.py'`
    结果：Ran 68 tests in 4.064s，OK。
  - `python3 -m unittest discover -s onboard/src/ros2_trashbot_interfaces/test -p 'test_*.py'`
    结果：Ran 6 tests in 0.107s，OK。
  - `python3 -m unittest discover -s onboard/src/ros2_trashbot_vision/test -p 'test_*.py'`
    结果：Ran 20 tests in 1.221s，OK。
  - `python3 -m unittest discover -s onboard/src/ros2_trashbot_behavior/test -p 'test_*.py'`
    结果：Ran 843 tests in 574.642s，OK；期间有一个既有 `ResourceWarning: unclosed socket`，
    未导致测试失败。
- `git diff --check -- onboard/scripts/upper_robot_api.py onboard/scripts/test_upper_robot_api.py docs/navigation/nav2_map_quality_metrics.md sprints/2026.06.05_13-14_o10-amcl-nav2-readiness-epic/owner_notes/robot-software-engineer.md`
  结果：exit 0，无输出。

## Evidence Type

- evidence_type: `software_guard`
- 上游材料来源字段：`source_evidence_type` 可反映 canonical map proof 的
  `robot_runtime_material`。
- 未外推项：AMCL 定位、Nav2 消费 `/scan` + map、路径生成、fixed-route 执行、HIL、
  `safe_to_control=true` 和 delivery success。

## 剩余风险

- 该护栏只能证明 readiness 输入是否齐备，不证明 map quality pass。
- 真实 AMCL/Nav2 lifecycle 仍需 Robot Algorithm/Robot Software 后续 no-motion collector 产出 runtime artifact。
- 远端 8787 readback 尚未在本 note 写入最终结果；若网络或服务不可达，应记录为远端验证缺口，而不是本地软件失败。
