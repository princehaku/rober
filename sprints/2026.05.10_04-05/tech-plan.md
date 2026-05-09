# Sprint 2026.05.10 04-05 Tech Plan

## Owner

User Touchpoint Full-Stack Engineer。

## 文件范围

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
- `OKR.md`
- 当前 sprint 文档

## 接口影响

`/api/diagnostics` 向后兼容新增 `vision_samples` 字段；保留 `vision_sample_manifest_ref`。

## 验收命令

- `python3 -m unittest discover -s src/ros2_trashbot_behavior/test -p "test_operator_gateway_diagnostics.py"`
- `python3 -m unittest discover -s src/ros2_trashbot_behavior/test -p "test_operator_gateway_http.py"`
- `PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh`
- `git diff --check`

## 风险边界

不声明真实摄像头样本、手机浏览器或硬件在环已验证。
