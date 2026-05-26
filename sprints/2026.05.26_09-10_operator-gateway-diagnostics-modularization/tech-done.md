# Operator Gateway Diagnostics Modularization Tech Done

sprint_type: micro

## 实际改动

- 新增 `operator_gateway_diagnostics_cloud_lifecycle.py`，承接 cloud command lifecycle audit/export、replay drill、replay acceptance packet 的安全清洗 helper 与 summary 构造。
- `operator_gateway_diagnostics.py` 改为从内部 lifecycle 子模块导入同名 public 函数，保留现有测试与外部调用的 `operator_gateway_diagnostics` 导入路径。
- 修复 `test_operator_gateway_diagnostics.py` 中已有的 `""robot-algorithm-engineer""` 字符串语法错误，使本轮验收单测可以执行；不改变断言语义。
- 更新 `docs/interfaces/operator_gateway_diagnostics.md`，明确本次拆分只改变内部结构，不改变 `/api/status`、`/api/diagnostics` payload 语义，也不把 not-proven/unavailable 提升为 proven。

## 验证结果

已执行：

```bash
cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
Ran 326 tests in 7.116s
OK

cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior
通过，无输出。

cd /mnt/e/rober && git diff --check
失败，阻断项来自范围外 `.idea/rober.iml` 的已有 trailing whitespace/CRLF 差异；按本轮约束未修改 `.idea/`。

cd /mnt/e/rober && git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_cloud_lifecycle.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.26_09-10_operator-gateway-diagnostics-modularization/tech-done.md
通过，无输出。本轮范围内改动未发现 whitespace error。
```

第一轮 unittest 失败定位：测试文件在第 39186 行附近存在已有语法错误 `""robot-algorithm-engineer""`，导致 unittest 在导入阶段中止；修复同类 5 处字符串后重跑通过。

## 剩余风险

- 本轮只做 software/unit 级结构拆分验证，未做真实手机浏览器、外部云、HIL、Nav2、WAVE ROVER 或串口验证。
- 仓库全量 `git diff --check` 仍被范围外 `.idea/rober.iml` 的 trailing whitespace 阻断；本轮按约束未清理该文件。
- 本轮未触碰与任务无关的 `pc-tools/`、`.idea/` 改动。
