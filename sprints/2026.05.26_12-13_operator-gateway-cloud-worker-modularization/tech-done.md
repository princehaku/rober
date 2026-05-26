# Operator Gateway Cloud Worker Modularization Tech Done

sprint_type: micro

## 实际改动

完成。本轮继续推进“重构代码、架构清晰、易读、模块化、易用”，聚焦 `operator_gateway_diagnostics.py` 中 cloud worker migration rehearsal / cutover drain 相关 metadata-only diagnostics summary 拆分。保留 public import 兼容层，只改变内部结构，不改变 `/api/status`、`/api/diagnostics` payload 语义。

- 新增 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_cloud_worker.py`，承载 cloud worker migration rehearsal / cutover drain 的 schema、evidence boundary、required `not_proven`、status helper、fail-closed default summary、`summarize_cloud_worker_migration_rehearsal(path)` 和 `summarize_cloud_worker_cutover_drain(path)`。
- 更新 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`，从新 worker 模块 re-export 相关常量、helper 和 summarizer，保持既有 `from operator_gateway_diagnostics import ...` 测试和外部调用不变。
- 更新 `docs/interfaces/operator_gateway_diagnostics.md`，补充 cloud worker metadata-only summaries 的内部模块边界、schema/evidence boundary、允许字段、fail-closed 条件和明确未证明事项。
- 未修改 `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`；现有兼容测试继续覆盖原 public import 路径。
- 未触碰 unrelated `.idea/`、`pc-tools/`、`docs/vendor/`、硬件/导航/视觉包，也未回滚前三轮新增的 diagnostics cloud 模块。

## 验证结果

通过。验收命令由 `full-stack-software-engineer` 执行：

```bash
cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior
cd /mnt/e/rober && git diff --check
```

结果：

```text
python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
Ran 326 tests in 7.362s
OK

python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior
exit code 0

git diff --check
exit code 2
.idea/rober.iml:1-14: trailing whitespace
```

全量 `git diff --check` 失败来自本轮范围外 `.idea/rober.iml` 已存在尾随空白，按任务要求未修改该文件。已追加运行本轮文件限定检查：

```bash
cd /mnt/e/rober && git diff --check -- \
  onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py \
  onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_cloud_worker.py \
  onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py \
  docs/interfaces/operator_gateway_diagnostics.md \
  sprints/2026.05.26_12-13_operator-gateway-cloud-worker-modularization/tech-done.md
```

限定检查结果：exit code 0。

新 worker 模块当前为未跟踪文件，普通 `git diff --check -- <path>` 不会纳入未跟踪内容；已追加 no-index whitespace 自检：

```bash
cd /mnt/e/rober && git diff --check --no-index /dev/null \
  onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_cloud_worker.py
```

结果：无 whitespace 报错；命令 exit code 1 是 no-index 对“文件存在差异”的预期返回。

## 剩余风险

无新增功能风险。本轮是内部模块化拆分，现有 public import、summary schema、fail-closed 状态、`not_proven` 列表和 action flags 语义由 326 个 unittest 覆盖并保持通过。

剩余外部风险：

- 全量 `git diff --check` 仍受范围外 `.idea/rober.iml` 尾随空白影响；本轮未处理，避免覆盖 unrelated IDE 改动。
- 该摘要仍是 metadata-only software proof，不证明 real cloud worker migration/cutover、production DB/queue、ACK completion、cursor persistence、HIL、真实机器人控制或 delivery success。
