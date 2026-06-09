# Board Field Evidence Preflight Sprint Pre-start

## sprint_type: epic

## 背景

Automation：`1小时OKR`，本轮用户要求继续完成代码和功能，并明确要求设计完成后才能开始写功能点、功能点完整后才能写代码、结束后提交并推送。

上一轮 `sprints/2026.06.09_13-00_board-live-slam-route/` 已尝试真实上位机入口：

```bash
ssh root@192.168.1.11 -p 37878
```

结果停在网络层：SSH、ping、nc 均返回 `No route to host` 或 100% 丢包，ARP 对 `192.168.1.11` 为 incomplete。按照同一 blocker 最多消费 2 轮的红线，本轮不继续把时间花在重复 SSH 失败上，而是补一个能直接解锁下一次现场执行的标准预检工具。

## 本轮功能点

功能点名称：`board_field_evidence_preflight_cli`。

目标是提供一个一键现场证据预检 CLI，在本地或上位机运行，输出标准 JSON evidence packet。下一次网络恢复后，现场同学不需要重新翻聊天或 sprint 文档，可以直接用该 CLI 分层确认 SSH、本机 ROS2、setup.bash、项目包、topic、topic smoke、learn.launch 命令模板和证据输出路径。

## OKR 映射

主目标：临时激活归档 O3「可验证导航与固定路线」现场验证 lane。

支撑目标：

- O7：PC 端历史路线回放后续需要真实 `map.yaml`、`route.csv`、keyframe、replay JSONL。
- O6：云端 archive 后续需要标准化 evidence packet 作为真实机器人数据入口。

## Owner

设计 owner：`product-okr-owner`。

实现 owner：`robot-algorithm-engineer`，因为本轮核心围绕 SLAM、topic smoke、固定路线和现场证据链。若实现中涉及 ROS2 package entry point 或 bringup 集成，再由 `robot-software-engineer` 只读补接口事实。

## 范围边界

本轮允许实现软件工具和离线测试，不要求真实 SSH 网络必须恢复。

本轮不证明：

- 真实上位机已连通。
- 真实 ROS2 topic 存在。
- 已产出 map、route、keyframe、rosbag 或 replay JSONL。
- Nav2/fixed-route 已上车通过。
- WAVE ROVER/UART/HIL 已通过。

## 启动条件

进入实现前必须先完成：

1. `prd.md` 定义功能完整性和失败分层。
2. `tech-plan.md` 定义文件范围、接口影响、验收命令和 OKR 最低优先级核对。
3. 运行时必须有可用子 agent；如果子 agent 工具不可用，主节点不得越权写产品代码。

