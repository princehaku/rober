# O7 RTC Signaling Contract Micro Sprint

## sprint_type

micro

## 实际改动

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py` 新增 `GET /api/o7/rtc-signaling/contract` 和 `trashbot.o7.rtc_signaling_contract.v1` 静态合同 builder。
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py` 新增 HTTP endpoint 测试，覆盖公开只读访问、固定 fail-closed 字段、协议面清单、env token 不泄露和 forbidden actions。
- `cloud-relay/README.md`、`docs/product/pc_tools_workstation.md`、`docs/interfaces/o7_rtc_signaling_contract_api.md` 同步说明该入口只是 RTC/实时地图接入前置协议清单，不证明 WebRTC、视频、ROS2 `/tf` 或控制链路已通。

## 验证结果

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
  - 首轮失败：新增测试发现 HTTP 响应经过通用 `safe_value()` 后删除了 `reads_hardware`、`auth_token_handling` 和 `hardware_probe` 等字段。
  - 第一版修复偏差：曾把这些固定 false / 脱敏策略字段加入 phone-safe key exception，并把 token transport 文案改为不含真实 bearer 值的 `bearer_header_redacted`；验收发现该 exception 范围过宽。
  - 验收收紧：含 `token`/`auth` 的全局 exception 风险过宽，已移除 `auth_token_handling`、`token_transport`、`token_values_exposed` 例外；RTC contract 字段改为 `credential_handling`、`credential_transport_policy`、`credential_values_exposed`。
  - 复验修复：`reads_hardware` / `hardware_probe` 改为 `safe_value()` 中的 false-only key，只有值严格为 `False` 才透传，`True` 会被过滤；新增单测覆盖这一点。
  - 最终复跑结果：`Ran 114 tests in 36.827s`，`OK`。
- `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
  - 结果：退出码 0。
- `git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py cloud-relay/README.md docs/product/pc_tools_workstation.md docs/interfaces/o7_rtc_signaling_contract_api.md sprints/2026.05.27_41-42_o7-rtc-signaling-contract/tech-done.md`
  - 结果：退出码 0。

## 剩余风险

- 当前只新增静态 fail-closed 合同，未实现真实 signaling server、offer/answer、ICE、media transport、视频 track、pose event stream 或 ROS2 `/tf` bridge。
- 未进行 HIL、真实网络、真实摄像头、真实音频、真实机器人或公网云验证。
