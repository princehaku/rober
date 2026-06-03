# 2026.06.03 15-16 O1 Feedback Artifact Readback

## sprint_type

micro

## 目标

继续推进当前最低 Objective 1：把 8787 `POST /api/base/feedback-samples`
采到的非运动 `T=130 -> T=1001` 多样本 evidence，从一次 HTTP 响应推进为可
持久保存、可只读回放的 latest artifact。目标不是 HIL pass，也不是
manual/motion；目标是让 PC/后续验收可以读取最近一次真实材料，而不必每次重新
打开串口。

## 团队执行说明

本轮按 AGENTS.md 先后派发两个 `robot-hardware-engineer` worker。两个 worker 均
在收口阶段长时间未返回；第一个 worker 留下了核心代码增量，第二个 worker未产出
可用留档。为避免自动化无限卡住，本轮由主节点兜底完成验收、文档、远端非运动验证
和 git 提交。该流程偏离已在本文件记录；后续应优先缩小子 agent 远端验证超时时间，
避免实现完成但收口卡死。

## 已读 vendor 来源

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`

## 已证实的硬件结论

- WAVE ROVER vendor 上位机参考使用 UART、UTF-8 JSON、每行一个 JSON 对象并以
  `\n` 结束。
- `json_cmd.h` 定义 `CMD_BASE_FEEDBACK=130` 和
  `FEEDBACK_BASE_INFO=1001`。
- `uart_ctrl.h` 的 `CMD_BASE_FEEDBACK` 分支调用 `baseInfoFeedback()`。
- `ugv_advance.h` 的 `baseInfoFeedback()` 输出 `T=1001`，包含
  `L/R/r/p/y/v` 等字段并 `Serial.println(...)`。
- `T=1`、`T=13`、`T=131` 分别属于运动或 feedback-flow 状态命令，本轮未发送。

## 实际改动

- `onboard/scripts/upper_robot_api.py`
  - 新增 `DEFAULT_FEEDBACK_SAMPLES_ARTIFACT_PATH`，默认
    `runtime/base_feedback_samples_latest.json`。
  - 新增 `--feedback-samples-artifact-path` 和
    `ROBER_BASE_FEEDBACK_SAMPLES_ARTIFACT_PATH` 配置入口。
  - `POST /api/base/feedback-samples` 现在把 latest payload 通过同目录临时文件
    + `os.replace()` 原子写入 artifact。
  - 新增只读 `GET /api/base/feedback-samples/latest`，只读取 artifact，不打开串口、
    不发送 `T=130` 或运动命令。
  - `/api/status` routes 暴露 `base_feedback_samples_latest`，并暴露 artifact
    path 配置摘要。
  - latest readback 顶层固定 `readback_sends_commands=false`、
    `safe_to_control=false`、`sends_commands=false`、
    `sends_motion_commands=false`、`robot_control_executed=false`、
    `delivery_success=false`、`hil_pass=false`。
- `onboard/scripts/test_upper_robot_api.py`
  - 覆盖 samples 写入 latest artifact。
  - 覆盖 latest readback 读取 artifact 后不打开 fake serial。
  - 覆盖 artifact missing / bad JSON fail-closed。
  - 覆盖 route registry 暴露 latest path。
- `docs/interfaces/o1_upper_robot_api_base_feedback.md`
  - 增加 latest endpoint、artifact path、response contract 和安全边界。
- `docs/interfaces/o7_upper_robot_api.md`
  - 更新 endpoint 表和 base 控制安全边界。
- `docs/hardware/o1_wave_rover_serial_feedback_probe.md`
  - 增加 latest artifact/readback 的硬件边界说明。
- `docs/process/okr_progress_log.md`
  - 追加本轮 O1 15-16 micro sprint 进度日志。
- `OKR.md`
  - 更新 O1 当前状态补充和 4.1 快照；百分比保持约 95.5%。
- `sprints/2026.06.03_15-16_o1-feedback-artifact-readback/tech-done.md`
  - 本轮 micro sprint 留档。

## 本地验证结果

```text
$ PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/scripts/test_upper_robot_api.py
.............
----------------------------------------------------------------------
Ran 13 tests in 1.057s

OK
```

```text
$ python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/test_upper_robot_api.py
exit 0
```

```text
$ git diff --check -- onboard/scripts/upper_robot_api.py onboard/scripts/test_upper_robot_api.py docs/interfaces/o1_upper_robot_api_base_feedback.md docs/interfaces/o7_upper_robot_api.md docs/hardware/o1_wave_rover_serial_feedback_probe.md
exit 0
```

## 远端部署与非运动验证

SSH 可达：

```text
$ timeout 8 ssh -o BatchMode=yes -o ConnectTimeout=5 -p 37878 root@192.168.1.11 'echo ssh_ready'
ssh_ready
```

部署：

```text
$ scp -P 37878 onboard/scripts/upper_robot_api.py root@192.168.1.11:/root/rober/onboard/scripts/upper_robot_api.py
exit 0
```

重启：

```text
$ ssh root@192.168.1.11 -p 37878 'systemctl restart trashbot-upper-robot-api.service && systemctl is-active trashbot-upper-robot-api.service'
active
```

只调用非运动 `POST /api/base/feedback-samples`：

```text
{
  "http_status": 200,
  "schema": "trashbot.upper_robot_api.v1.base_feedback_samples_result",
  "requested_sample_count": 3,
  "completed_sample_count": 3,
  "t1001_observed_count": 3,
  "observed_feedback_types": [130, 1001],
  "all_samples_observed_t1001": true,
  "sample_statuses": ["observed", "observed", "observed"],
  "artifact.write.ok": true,
  "artifact.write.bytes_written": 4989,
  "safe_to_control": false,
  "sends_motion_commands": false,
  "robot_control_executed": false,
  "hil_pass": false,
  "feedback_ack.robot_ack_connected": false
}
```

只读 `GET /api/base/feedback-samples/latest`：

```text
{
  "http_status": 200,
  "schema": "trashbot.upper_robot_api.v1.base_feedback_samples_latest_result",
  "artifact.status": "loaded",
  "latest_t1001_observed_count": 3,
  "latest_all_samples_observed_t1001": true,
  "readback_sends_commands": false,
  "safe_to_control": false,
  "sends_commands": false,
  "sends_motion_commands": false,
  "robot_control_executed": false,
  "hil_pass": false
}
```

## 安全声明

本轮远端业务验证没有调用 `/api/base/manual`，没有发送 `T=1`、`T=13`、
`T=131` 或 ROS `/cmd_vel`。POST samples 每个 sample 只发送 vendor
`{"T":130}`；GET latest 只读 artifact，不打开串口、不发送任何命令。

## 剩余风险

- latest artifact/readback 只证明真实反馈材料可保存和回放，不是 robot ACK
  connected，也不是 HIL pass。
- 仍未证明 `safe_to_control=true`、闭环安全控制、真实 `/odom`、
  `/imu/data`、`/battery`、真实 `/scan`、自动停车/急停现场演练或 delivery success。
- 后续如进入 `/api/base/manual` 或 ROS `/cmd_vel`，必须满足现场看护、物理净空、
  人工急停路径和 operator report。
- 本轮两个 worker 均卡在收口阶段；后续自动化应给远端验证设置更短硬超时，并要求
  worker 先落 sprint 文档再做可选远端长验证。
