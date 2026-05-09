# Sprint 2026.05.10 05-06 PRD

## 需求

学习阶段不能只停留在 SLAM 和 waypoint 学习入口。固定路线能力需要一个标准入口，在人工驾驶学习时同步记录 `route.csv` 和 `keyframes/*.jpg`，为后续 dry-run、visual gate 和自主送达提供数据来源。

## OKR 对齐

- Objective 3 KR1：`learn.launch.py` 学习流程纳入 route 数据采集。
- Objective 3 KR2：`route_data_recorder` 输入输出和启动参数进入工作流文档，并有静态契约测试保护。

## 验收

- `learn.launch.py` 新增 `route_recorder:=false` 默认开关，默认学习流程不强依赖相机。
- 启用 `route_recorder:=true` 时启动 `route_data_recorder`。
- launch 参数可配置输出目录、相机 topic、里程计 topic、最小记录距离和 route frame。
- `docs/navigation/fixed_route_workflow.md` 记录一键学习采集命令。
- 目标 launch contract 测试、py_compile、smoke 和 diff check 通过；Docker/Humble 如环境支持则验证，否则记录环境缺口。
