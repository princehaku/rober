# Upper Free Roam Mapping Active Ready Gate

## sprint_type

micro

## 实际改动

- 修改 `onboard/scripts/upper_robot_api.py`：`POST /api/free-roam/autonomy/start` 仍允许在现场安全确认后打开自由移动状态机，但只有 `sensor_readiness.mapping_readiness.ready=true` 时才把 `mapping_active=true` 写入 `free_roam_autonomy_node`。
- 回包新增 `mapping_active_applied`，并保留 `mapping_active_requested`，用于区分“用户请求建图”和“后端实际进入可建图会话”。
- 修改 `onboard/tests/test_upper_robot_api.py`：覆盖雷达/相机建图质量不 ready 时仍可自由移动但不应用建图、建图质量 ready 时才应用 `mapping_active=true`、未勾建图确认时保持 false。
- 更新 `docs/product/pc_free_roam_mapping_design.md`：记录上位机 API 对直接调用也执行 camera/radar 建图质量二次门禁。

## 验证结果

- `cd onboard && python3 -m pytest tests/test_upper_robot_api.py -k free_roam`：未执行成功，本机 `/Library/Developer/CommandLineTools/usr/bin/python3` 缺少 `pytest` 模块。
- `cd onboard && python3 -m unittest tests.test_upper_robot_api`：通过，`Ran 54 tests in 0.135s`，`OK`。
- `git diff --check`：通过，无 whitespace 错误。

## 剩余风险

- 本轮是上位机 API 单元验证，不等于真实 HIL；摄像头真实出画面、雷达 fresh proof、底盘低速运动和真实建图保存仍需要现场验证。
