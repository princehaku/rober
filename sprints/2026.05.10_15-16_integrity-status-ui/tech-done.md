# Sprint 2026.05.10 15-16 Integrity Status UI - Tech Done

## 状态

- 阶段：implementation completed by `full-stack-software-engineer`.
- 更新时间：2026-05-10 15:34:45 CST。

## 实际改动

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`：在本地 operator 页面 Support Diagnostics panel 内新增 Vision evidence chain 卡片，显示视觉证据链状态灯、状态摘要、最多 3 条缺失/错误/警告原因、context coverage、file counts 和恢复建议。
- `src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`：补齐 `/api/diagnostics.vision_samples` integrity fixture，断言 HTTP JSON 继续透传新增诊断字段，并增加页面静态护栏，确认新 DOM id、渲染函数和字段名存在。
- `sprints/2026.05.10_15-16_integrity-status-ui/tech-done.md`：记录本轮实现、验证结果、失败定位和剩余风险。

## 用户旅程变化和触点收益

普通用户或现场支持打开手机本地 operator 页面后，不再只能看 raw diagnostics JSON。点击 Diagnostics 后，页面会把 `/api/diagnostics.vision_samples.integrity_summary.status` 映射成 `Healthy`、`Needs review`、`Broken`、`Not configured`、`Checker unavailable`、`Checker failed` 或 `Unknown`，并给出人话摘要和下一步恢复建议。

当 manifest 有缺失文件引用、checker error、warning 或 read error 时，页面优先展示缺失文件原因，例如 `Missing raw_image: /tmp/vision/missing/raw.jpg`。长路径会在列表内自动换行，避免手机页面被撑破。

## 接口影响

- 不改 ROS2 msg/srv/action。
- 不改 `/api/diagnostics` payload shape。
- 页面只消费现有 `vision_samples` 字段：`integrity_summary`、`integrity_errors`、`integrity_warnings`、`missing_file_refs`、`read_error`、`context_field_coverage` 和 `file_counts`。
- 保持原有 `diagVisionSamples`、`diagLatestVisionSample`、`diagReviewQueue`、`diagNextReviewSample`、raw status JSON 和 API failure path。

## 前后端/ROS2 联调结果

- 本轮属于本地 HTTP operator 页面消费后端 diagnostics payload，不触碰 diagnostics builder、vision checker、ROS2 contract 或硬件配置。
- `FakeGateway.diagnostics_payload` 已模拟上一轮 diagnostics builder 输出的 integrity 字段，HTTP endpoint 断言确认字段透传，页面静态断言确认 operator 页面具备对应渲染入口。
- 未做真实手机浏览器截图或真实 camera/odom manifest 上车联调。

## 验证结果

- 第一轮失败：`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_behavior/test -p 'test_operator_gateway_http.py'` 在导入阶段失败，错误为 `ModuleNotFoundError: No module named 'ros2_trashbot_behavior'`，未进入业务断言。
- 已修复：在允许修改的 HTTP 测试文件中按 diagnostics 测试同款方式加入源码树 `sys.path`。
- 通过：`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_behavior/test -p 'test_operator_gateway_http.py'`，16 tests OK。
- 通过：`python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`。
- 通过：`git diff --check`。
- 通过：`PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh`，interfaces 6、hardware 14、nav 27、bringup 9、behavior 111、vision 13 tests OK。

## 失败定位

- 已处理的失败仅为本地测试入口 import path 缺口，和页面功能无关。
- 未触碰 diagnostics builder 或 vision checker contract，因此未额外运行 `test_operator_gateway_diagnostics.py` 和 `test_vision_sample_manifest.py` 的单独命令；完整 smoke 已覆盖 behavior 和 vision 包测试。

## 剩余风险

- 本轮只证明 operator 页面能消费 diagnostics 字段，不证明真实 camera/odom manifest 会持续产生。
- 本轮未做真实手机浏览器视觉验收；后续 `side2side_check.md` 应补一次手机宽度截图或人工浏览器检查。
- 视觉证据链状态仍依赖上一轮 diagnostics builder 和 vision checker 的字段质量；如果未来字段语义变化，需要同步更新页面文案映射。
