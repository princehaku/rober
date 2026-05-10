# Sprint 2026.05.10 13-14 OKR Function - Tech Done

## 状态

- 阶段：tech-done 已完成。
- 主责：Autonomy Algorithm Engineer。
- 功能切片：Objective 4 route/camera sample manifest 离线检查与汇总。
- 更新时间：2026-05-10 13:27:18 CST。

## 自主能力目标和本轮抓手

- 目标：真实采集后的 route/camera sample manifest 可以在无 ROS2 daemon、无硬件、无真实相机的环境里被离线检查，输出稳定结构化 summary。
- 抓手：在 vision 包内新增纯 Python helper/CLI，先把 manifest 引用完整性、字段覆盖、上下文覆盖、负样本/异常样本计数跑通，后续 diagnostics 和人工复盘可直接消费。

## 实际改动

- `src/ros2_trashbot_vision/ros2_trashbot_vision/vision_sample_manifest.py`
  - 新增 `summarize_manifest(manifest_path)` 纯 Python helper。
  - 支持 `python3 -m ros2_trashbot_vision.vision_sample_manifest <manifest>` 输出 JSON summary。
  - 支持 `vision_sample://`、相对路径、绝对路径、manifest `sample_output_dir` 和 manifest 所在目录解析。
  - 输出稳定字段：`manifest_path`、`schema`、`sample_output_dir`、`sample_count`、`file_counts`、`context_counts`、`event_counts`、`sample_type_counts`、`negative_sample_count`、`anomaly_sample_count`、`route_keyframe_sample_count`、`detection_sample_count`、`missing_file_refs`、`field_coverage`、`context_field_coverage`、`errors`、`warnings`。
  - CLI 在 `errors` 非空时返回非零。
- `src/ros2_trashbot_vision/test/test_vision_sample_manifest.py`
  - 覆盖 valid manifest 汇总、缺引用文件、空 manifest/schema 问题、缺关键字段、坏 manifest shape、route_data_recorder 风格 manifest 兼容。
- `docs/vision/perception_upgrade_evaluation.md`
  - 补充离线 manifest checker 在真实采集后、diagnostics/人工复盘前的使用方式和 JSON summary 字段。

## 接口影响

- 不改 ROS2 msg/srv/action contract。
- 不改 `route_data_recorder` producer contract。
- 不改手机/API 生产代码，包括 `operator_gateway_http.py` 和 `operator_gateway_diagnostics.py`。
- 新增模块级 CLI；未改 packaging console script。

## 验证结果

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_vision/test -p 'test_*.py'`
  - 结果：通过。
  - 输出摘要：`Ran 13 tests in 0.564s`，`OK`。
- `python3 -m py_compile $(find src/ros2_trashbot_vision -name '*.py' -print)`
  - 结果：通过，无错误输出。
- `git diff --check`
  - 结果：通过，无 whitespace/error 输出。
- `PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh`
  - 结果：通过。
  - 输出摘要：`Ran 6 tests`、`Ran 14 tests`、`Ran 27 tests`、`Ran 9 tests`、`Ran 110 tests`、`Ran 13 tests`，全部 `OK`。

## 偏差

- 无生产 API 接入；本轮按 tech-plan 只在 vision/autonomy 侧提供可复用离线能力。

## 剩余风险

- 当前没有真实上车采集 manifest，只能验证离线 contract 和 fixtures。
- 后续 full-stack diagnostics 接入时，需要对齐旧 `summarize_vision_manifest()` 是否复用本 helper 或映射字段。
- 本轮未改 ROS2 launch、硬件参数、手机/API 生产代码；真实采集后的 manifest 仍需下一轮导入此 checker 做实数据复盘。
