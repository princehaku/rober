# Board Live Route Preflight and Capture PRD

## 产品目标

用 1 小时内真实上位机入口重新打开现场 lane：优先把 `ssh root@192.168.1.11 -p 37878` 可达性转化为可复盘证据产出，不再停留在 review/handoff/状态面板型交付。  
本 sprint 允许出现受阻，但不允许在无替代产物时直接以 blocked 收口；必须落地可复用预检入口。

## 功能点定义

### FP1：真实上位机 route capture 前置与闭环

本 sprint 的唯一功能点 `board_live_route_preflight_and_capture`：  
工程师完成以下任一成功结果即判定该功能点成功：

1. 登录真实上位机成功，并记录 `hostname`、`date`、`command -v ros2` 与 setup 文件查找结果。
2. 在上位机采集到 `route.yaml` / `map.yaml` / `route.csv` / keyframe（含证据目录名）中的至少一个并可定位到时间戳目录。
3. 生成固定路线 replay 输入与 dry-run 可运行记录（`route_csv_to_yaml` / `fixed_route_autonomy --ros-args`）。

### FP2：SSH 不可达时的复用 runbook 交付

若 SSH 不可达、ROS2 不可用或上位机启动异常，必须在本轮交付：

1. 一份本地可复用的预检/采集 runbook（包含一键命令序列）。
2. 预检结果模板（包含 SSH 失败原因、网关/端口可达性、topic 缺失列表、建议修复动作）。
3. 下一次执行的文档同步说明（runbook 与证据字段对齐）。

## 用户价值

成功拿到真实 `map.yaml` 与 `route.csv` 后，后续 `O2` 真实送达、`O7` 路线回放与报警调试都能消费同一材料；这比继续补充界面或状态文案更直接对齐“能运行的小车”价值。

## 非目标

- 不新增或变更 WAVE ROVER UART 指令、串口参数、底盘速度映射、机器人硬件驱动策略。
- 不提交手机/Web/PC UI 交付；不做云外网部署动作。
- 不把 replay 成功替代现场路线完成；不将本轮结果误记为 delivery success。

## 验收口径

### P0 验收

- 指定 SSH 命令成功尝试执行：
  - `ssh root@192.168.1.11 -p 37878`
- 记录 topic 探测和频率命令输出，至少覆盖 `/scan`、`/camera/image_raw`、`/odom`、`/tf`、`/map`。
- 至少留下一类成功证据：  
  - `map.yaml` 或 `map.*` 相关文件  
  - `route.csv` 或 fixed-route YAML  
  - keyframe / evidence 文件（含相机与里程计目录线索）  
  - `rosbag`、`replay JSONL` 中任一项
- `tech-done` 需明确成功/失败边界，不可省略失败根因。

### P1 验收（加码）

- 能提供 dry-run/replay 成功日志（或失败原因可复现实验步骤）。
- 无法建图/移动时，至少产出 topic 观测证据与本地 runbook，证明下一步执行路径明确，不是空任务关闭。

## 里程碑与优先级

1. P0 第一优先级：真实 SSH + route/map 证据链。  
2. P0 失败路径：同轮交付可复用 runbook 与失败归档。  
3. P1 在 P0 通过后进行 route replay 与 rosbag 补齐。

优先级规则：只要上位机可达且无硬件安全阻断，优先产出真实 `map.yaml` 与 `route.csv`；若受阻则执行可复用 runbook 交付，不允许“只做 blocker 记录”。
