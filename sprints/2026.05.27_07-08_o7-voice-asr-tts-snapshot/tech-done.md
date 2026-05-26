# O7 Voice ASR/TTS Snapshot Micro Sprint

## sprint_type

micro

## 实际改动

- 新增 `voice_asr_tts_snapshot` fail-closed contract，覆盖 ASR stream status、partial/final transcript 槽位、TTS draft/voice profile、speaker dispatch、command ACK/audit、media preflight dependency 和 next required evidence。
- PC O7 Console 新增只读 Voice ASR/TTS snapshot 面板，不提供输入框、发送按钮、设备探测或机器人直连。
- 同步更新 O7 operator console 接口文档、PC workstation 产品边界和 Vitest 覆盖。

## 验证结果

- 通过：`cd pc-tools/workstation && npm run build`
  - 关键结果：`✓ 29 modules transformed.`，`✓ built in 1.94s`
- 通过：`cd pc-tools/workstation && npm run test`
  - 关键结果：`Test Files  2 passed (2)`，`Tests  16 passed (16)`
- 通过：`cd pc-tools/workstation && npm run lint`
  - 关键结果：ESLint 退出码 0，无输出。
- 通过：`python3 -m py_compile cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py`
  - 关键结果：退出码 0，无输出。
- 通过：`git diff --check -- cloud-relay pc-tools docs/product/pc_tools_workstation.md docs/interfaces/o7_realtime_operator_console.md sprints/2026.05.27_07-08_o7-voice-asr-tts-snapshot`
  - 关键结果：退出码 0，无 whitespace error。

## 剩余风险

- 当前仍是 `source=software_proof` / `snapshot_status=blocked_not_proven`，不证明真实 ASR 输入流、真实 partial/final transcript、真实 TTS 播放、真实 speaker ACK、真实音频设备、真实 RTC 或云端 voice API。
- 本轮不更新 `OKR.md`，不抬 O7 百分比。
