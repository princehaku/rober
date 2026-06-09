# sprint_type: micro

## 实际改动

- 在 `onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py` 修正电梯 assist 契约静态测试，分离并明确两条 launch 的默认值边界：
  - 新增 `test_bringup_default_elevator_assist_off_and_pass_to_task_orchestrator`：要求 `bringup.launch.py` 默认 `elevator_assist_enabled=false`，并确认其 4 个 elevator assist 参数透传到 `task_orchestrator`。
  - 新增 `test_autonomous_default_elevator_assist_on_and_pass_to_task_orchestrator`：要求 `autonomous.launch.py` 默认 `elevator_assist_enabled=true`（保留 `dry_run` 主链路契约），并确认同样参数透传到 `task_orchestrator`。
- 为这两条断言补充中文注释，明确为什么两类 launch 的默认值设计不同：`bringup` 侧偏向基础可控收敛链路，`autonomous` 侧偏向主线软件 proof dry-run 验收链路。
- 未修改 `autonomous.launch.py` 或 `bringup.launch.py` 的默认值本身，仅修正测试与现有契约一致，避免“测试硬编码”反推 launch 行为。

## 验证结果

- `python3 -m unittest onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py`
  - 通过
  - 关键日志片段：
    - `Ran 11 tests in 0.010s`
    - `OK`
- `bash onboard/scripts/run_smoke_tests.sh`
  - 通过单测链路中的前两段，最终因已知环境缺失问题未完全通过：`FAILED (failures=4, errors=1)`（总计 `Ran 863 tests in 197.267s`）。
  - 关键日志片段：
    - `ERROR: test_evidence_crosscheck_writes_rehearsal_artifact_with_blocked_hil_not_proven (test_task_record.TaskRecordTest.test_evidence_crosscheck_writes_rehearsal_artifact_with_blocked_hil_not_proven)`
    - `FileNotFoundError: [Errno 2] No such file or directory: '/var/folders/.../rehearsal_artifact.json'`
    - `AssertionError: '/.../pc-tools/evidence/evidence_crosscheck.py': [Errno 2] No such file or directory`
    - `Ran 863 tests in 197.267s`
    - `FAILED (failures=4, errors=1)`
  - 后续同轮 `evidence-crosscheck-entrypoint-restore` micro sprint 已恢复缺失入口，最新全量 smoke 结果为 `Ran 863 tests ... OK`。
- `git diff --check -- onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py sprints/2026.06.09_15-16_launch-contract-elevator-assist-default-drift/tech-done.md docs/product/elevator_assisted_delivery.md`
  - 通过，无空白/格式问题
- `git status --short`
  - 工作区出现既有未提交改动（非本次范围内）与本次新增 sprint 文档：
    - `M onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py`
    - `?? sprints/2026.06.09_15-16_launch-contract-elevator-assist-default-drift/`

## 剩余风险

- 本 micro sprint 仅处理了契约测试漂移（launch 默认值差异）；后续同轮已继续处理 evidence crosscheck 入口缺失并让全量 smoke 恢复通过。若下一轮 smoke 有新失败，需按其失败链路继续分解修复。
- 未修改文档侧约束文本，因为本次未发现 `docs/product/elevator_assisted_delivery.md` 存在可直接落地的默认值冲突条目，仍建议在后续行为说明更新时再次确认“主链路 dry-run 与主启动参数默认值”表述一致。
