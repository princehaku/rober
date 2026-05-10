# Sprint 2026.05.10 12-13 Pre Start

## 目标

本轮由 Robot Platform Engineer 推进 Objective 2：隔离 legacy `trash_collection_server.py` 的 sleep-demo 债务，避免旧入口继续伪造一次“导航 -> 收集 -> 投递成功”的完成证据。

## 上轮遗留

- Objective 2 已有 `task_orchestrator` fixed-route 证据写入 task record。
- 旧 `legacy_trash_collection_server` 仍会 sleep 后 `succeed()`，不能作为送垃圾闭环完成证据。
- Docker/Humble、真实 Nav2/fixed-route 行驶、WAVE ROVER HIL 仍缺实测。

## Owner

- 主责：Robot Platform Engineer。
- 任务不涉及硬件、串口、厂商协议或 vendor 文件。

## 验收口径

- legacy console script 保持可安装、可导入。
- legacy action server 被调用时不能返回 fake success；必须给出明确 quarantine 错误，指向 `task_orchestrator`。
- 静态测试证明 sleep-demo pipeline 被移除，`setup.py` 和接口文档仍声明 `task_orchestrator` 是默认入口、legacy 只保留兼容。
- 更新 `OKR.md` 和本 sprint `tech-done.md` / `final.md`。

## 风险

- 本轮只清理旧入口债务，不替代真实 ROS2/Humble action runtime、Nav2 行驶或硬件在环验证。
