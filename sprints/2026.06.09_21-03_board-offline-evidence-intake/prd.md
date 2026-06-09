# Board Offline Evidence Intake PRD

## 产品目标

把现场材料交付方式从“必须由当前开发机 SSH 到 `192.168.1.11:37878` 采集”调整为“支持现场人工导出 evidence packet 后离线导入”。这样即使现场网络、VPN、端口映射或 SSH 条件暂时不可达，O6 archive 与 O7 consumer 仍可继续消费真实或半真实材料，不再被单一网络 blocker 锁死。

## 功能点定义

### FP1：离线 evidence packet intake

新增或补齐一个工程入口，接受本地目录作为输入。该目录可以来自现场人工导出、USB 拷贝、压缩包解压或后续 SSH 成功后的 run 目录。最小支持以下任一类材料：

- `map.yaml` / 地图相关文件
- `route.csv` / fixed-route YAML
- keyframes / image evidence
- `route_bag/` 或 rosbag 目录线索
- `replay.jsonl`
- 已生成的 `trashbot.field_evidence_manifest.v1`

入口必须输出统一状态：是否具备 manifest gate、哪些 artifact present/missing、是否可作为 delivery proof、是否允许 control claim。

### FP2：复用现有 manifest gate 与 fail-closed 语义

离线 intake 不重新定义一套“成功”口径，必须复用现有 `trashbot.field_evidence_manifest.v1` 和 O6/O7 consumer detail 的字段语义：

- `gate_pass`
- `artifact_status`
- `not_proven`
- `delivery_success`
- `safe_to_control`
- `primary_actions_enabled`

缺少真实 delivery 或真实 control 证据时，必须保持 `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`。

### FP3：后续 live SSH 成功时可直接接同一路径

真实 SSH 恢复后，live capture 输出的 run 目录也应进入同一个 offline intake 路径，避免 live 与 offline 两套验收分叉。

## 用户价值

普通用户最终只关心小车是否能沿真实路线完成送垃圾任务。离线 intake 的价值是缩短从现场材料到产品功能验证的距离：现场人员只需导出材料，研发侧即可完成 archive、路线回放、标注队列和失败诊断联调。

## 非目标

- 不解决当前开发机到 `192.168.1.11:37878` 的网络不可达问题。
- 不改硬件参数、串口协议、WAVE ROVER 指令或底盘控制策略。
- 不要求本轮拿到真实物理上位机登录权限。
- 不把离线 manifest gate 通过等同于真实 delivery success。

## 验收口径

### P0 验收

- 给定一个本地 fixture evidence packet，工程入口能生成或读取 `trashbot.field_evidence_manifest.v1`。
- 缺少关键真实产物时，输出必须是 fail-closed：`delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`。
- O6/O7 consumer 侧能继续识别 manifest gate 与 artifact status，不把 not_proven 展示成成功交付。
- `tech-done.md` 记录实际输入目录、输出 manifest 摘要、测试命令和剩余风险。

### P1 验收

- 支持现场人工导出包的目录结构说明，后续可写入 `docs/`。
- 如果真实 SSH 在实现期间恢复，可以把真实 run 目录作为附加样本，但不能让 SSH 失败阻断 P0。

## 优先级

1. P0：本地 fixture/offline packet → manifest gate → O6/O7 consumer detail。
2. P0：fail-closed 安全语义不回退。
3. P1：真实 SSH 恢复后的 live run 目录复用同一路径。

## 成功边界

本功能点成功只代表“现场材料有了非 SSH 的导入通道”，不代表真实送达、真实路线采集或真实控制完成。OKR 进度如需调整，必须等工程 sprint 的测试证据与消费者链路通过后再判断。
