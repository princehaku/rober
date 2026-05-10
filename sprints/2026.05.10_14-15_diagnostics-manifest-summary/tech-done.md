# Sprint 2026.05.10 14-15 Diagnostics Manifest Summary - Tech Done

## 状态

- 阶段：implementation completed by `full-stack-software-engineer`.
- 更新时间：2026-05-10 14:19:12 CST。

## 实际改动

- `operator_gateway_diagnostics.py`：`/api/diagnostics.vision_samples` 保留旧字段，并复用 `ros2_trashbot_vision.vision_sample_manifest.summarize_manifest()` 追加 manifest 完整性摘要。
- `test_operator_gateway_diagnostics.py`：新增完整 manifest、缺文件引用、未配置/缺失/corrupt manifest 的 diagnostics 字段覆盖。
- `docs/interfaces/ros_contracts.md`：补充 diagnostics `vision_samples` 新增字段契约。

## 用户旅程变化

远程支持或手机端读取 `/api/diagnostics` 时，不再只能看到 manifest 路径、最新样本和 review queue；现在可以直接判断视觉样本链是否 `ok`、`warning` 或 `error`，并看到缺失文件引用、error/warning 计数、文件计数和上下文字段覆盖。

## 接口影响

- 不改 ROS2 msg/srv/action。
- `/api/diagnostics.vision_samples` 旧字段保持兼容。
- 新增字段：`integrity_summary`、`integrity_errors`、`integrity_warnings`、`integrity_error_count`、`integrity_warning_count`、`missing_file_ref_count`、`missing_file_refs`、`context_field_coverage`、`file_counts`。
- 如果 manifest 未配置、vision checker 不可 import 或 checker 运行失败，diagnostics 返回结构化降级字段，不让整个 diagnostics payload 失败。

## 验证结果

- 通过：`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_behavior/test -p 'test_operator_gateway_diagnostics.py'`，8 tests OK。
- 通过：`python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`。
- 通过：`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_vision/test -p 'test_vision_sample_manifest.py'`，5 tests OK。
- 通过：`git diff --check`。
- 通过：`PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh`，interfaces 6、hardware 14、nav 27、bringup 9、behavior 111、vision 13 tests OK。

## 失败定位

- 第一轮 behavior 目标测试失败在测试入口无法 import `ros2_trashbot_behavior`，未进入业务断言；已在允许的 behavior 测试文件中按 vision 测试同款方式加入源码树 `sys.path`，并补充 vision 包源码路径以覆盖 checker import。

## 偏差与风险

- 本轮只证明 diagnostics/API 消费契约和 fixture 行为，不证明真实 camera/odom manifest 已在车上持续产生。
- 真实手机页面尚未消费这些字段；下一步需要 UI 把 integrity status 映射为普通用户可理解的诊断状态和恢复建议。
