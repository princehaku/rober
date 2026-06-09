# Board Live SLAM Route Sprint PRD

## 产品目标

在真实上位机上产出一份可复盘的建图与路线材料包，让项目从软件 mock/面板 proof 进入真实路线证据阶段。

## 功能点定义

本轮只定义一个功能点：`board_live_slam_route_evidence_pack`。

该功能点完成后，Engineer 必须能给出以下至少一类成功证据：

- `map.yaml` 和对应 map image。
- `route.csv` 或路线 recorder manifest。
- keyframe/evidence 文件，至少能说明相机 topic 与采集目录。
- fixed-route YAML 或 replay JSONL。
- dry-run/replay 日志，证明 route 文件能被本项目工具消费。

如果无法完成成功证据，必须给出同级别的失败证据：

- SSH/认证失败。
- ROS2/Humble/工作区 source 失败。
- 传感器 topic 缺失或无数据。
- SLAM 保存地图服务不可用。
- 路线 recorder 输出缺失。
- 硬件移动或场地安全不允许执行。

## 非目标

- 不新增手机、PC、云端 UI 功能。
- 不改 WAVE ROVER 固件、串口协议、底盘速度映射或硬件接线。
- 不把 dry-run 或 topic 存在性声明为真实送达完成。
- 不提交任何凭证、SSH key、真实 token 或敏感网络信息。

## 验收口径

P0 验收：

- 使用 CEO 提供的真实 SSH 入口尝试上位机执行。
- 给出 topic 探测结果：`/scan`、`/camera/image_raw`、`/odom`、`/tf`、`/map` 中哪些存在，哪些缺失。
- 产出 `map.yaml` + `route.csv` + fixed-route dry-run/replay 三段证据；若任一段失败，必须保留命令、错误和下一步定位建议。
- 更新本 sprint `tech-done.md`，列出产物路径、验证命令输出和风险边界。

P1 验收：

- 若有相机数据，采集至少 1 张 keyframe 或 evidence ref。
- 若有 rosbag 工具和磁盘空间，录制短 rosbag 或给出明确不可录原因。
- 若有可安全移动条件，记录人工驾驶路线；若没有，明确现场安全 blocker。

## 优先级

P0 高于所有 O6/O7 只读 surface。只有当 SSH 上位机不可达或 ROS2/传感器完全不可用时，才回退到本地离线验证或请求 CEO 补材料。

## 用户可见价值

用户最终不关心 SSH、topic 或 Docker；用户关心小车是否能沿真实路线送垃圾。本轮材料将成为后续「手机一键发车」「PC 路线回放」「真实送达验收」的共同事实源。

