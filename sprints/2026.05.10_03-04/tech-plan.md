# Sprint 2026.05.10_03-04 Tech Plan

## 技术方案

1. 继续使用 `operator_gateway_http.py` 内置单页 HTML，避免引入前端构建链。
2. 页面新增手机优先布局：
   - 顶部状态、目标输入和主操作按钮。
   - 任务流程 stepper，对齐 waiting/loaded/delivering/arrived/returning/completed/failed 状态。
   - 诊断面板展示 software/map/route/version、failure、log refs、task record、vision manifest。
3. JS 仍只消费已有 API：
   - `GET /api/status`
   - `GET /api/diagnostics`
   - `POST /api/collect`
   - `POST /api/dropoff/confirm`
   - `POST /api/cancel`
4. 扩展 HTTP/static 测试，防止页面回退成只会打印 JSON 的 demo。

## 验证计划

| 命令 | 目的 |
| --- | --- |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src/ros2_trashbot_behavior python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_static.py` | 验证手机页面和 operator gateway 静态 contract |
| `PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh` | 全局软件护栏 |
| `git diff --check` | 提交前 whitespace 检查 |

## 风险边界

- 页面可在手机浏览器打开，但本轮不做真实设备浏览器截图。
- 诊断面板展示的是已有 diagnostics contract，不保证引用文件一定存在。
