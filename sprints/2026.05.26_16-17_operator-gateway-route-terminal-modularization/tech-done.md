# Operator Gateway Route Terminal Modularization Tech Done

sprint_type: micro

## 实际改动

- 新增 `operator_gateway_diagnostics_route_terminal.py`，承接 route task terminal
  completion rehearsal / review decision 的 schema/gate 常量、默认 blocked 摘要、
  `not_proven`、source contract、同 `evidence_ref` 校验和 summarize 逻辑。
- `operator_gateway_diagnostics.py` 继续作为 public compatibility facade，从新模块
  re-export 相关常量和函数，现有测试导入路径不变。
- 新模块通过延迟访问 facade helper 复用既有脱敏、safe ref、safe debug dict/list
  和 unsafe guard，避免复制 route field-run / completion signal 的大块逻辑。
- 更新 `docs/interfaces/operator_gateway_diagnostics.md`，记录 route terminal
  diagnostics 模块边界和 metadata-only 软件证明约束。

## 验证结果

```bash
cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
..........................................................................................................................................................................................................................................................................................................................................
----------------------------------------------------------------------
Ran 326 tests in 7.047s

OK

cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior
通过，无输出。

cd /mnt/e/rober && git diff --check
失败，失败点是范围外 `.idea/rober.iml` 既有 CRLF/trailing whitespace：

.idea/rober.iml:1: trailing whitespace.
.idea/rober.iml:2: trailing whitespace.
.idea/rober.iml:3: trailing whitespace.
... 同文件 1-14 行均为 trailing whitespace。

cd /mnt/e/rober && git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_route_terminal.py docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.26_16-17_operator-gateway-route-terminal-modularization/tech-done.md
通过，无输出。
```

## 剩余风险

- 本轮是结构性拆分，未接入真实硬件、真实串口/UART、WAVE ROVER、Nav2 或 HIL；
  route terminal summary 仍只能表示 metadata-only software proof。
- 未改测试用例，验证覆盖依赖现有 `test_operator_gateway_diagnostics.py` 对 public
  facade 导入和行为的回归检查。
