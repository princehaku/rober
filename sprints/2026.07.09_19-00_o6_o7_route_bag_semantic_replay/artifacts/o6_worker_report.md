# O6 Worker Report

## 实际改动文件

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`

## 验证命令输出

```bash
$ python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py && python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
................................................................................................................................................................
----------------------------------------------------------------------
Ran 160 tests in 56.976s

OK
```

## 失败定位

- 首轮失败 1：`route_bag_semantic_replay` 在 field-evidence 路径缺少 fixture 注入，导致 section 回退为 `route_bag_semantic_replay_not_available`。已把 semantic replay fixture 同步接入 field-evidence 与 artifact-bundle 测试请求。
- 首轮失败 2：topic sanitizer 把合法白名单 topic `/camera/image_raw` 中的 `raw` 误判为危险词，导致 semantic replay 被降级为 `route_bag_semantic_replay_unsafe`。已把 topic 名校验调整为允许 topic label 中的 `raw`，但继续禁止 raw 内容、base64、路径、token 和 credential URL。
- 首轮失败 3：HTTP 响应层 `safe_value()` 会去掉包含 `topic` 的 key，导致 `semantic_topic_types` 在实际 API 回包中丢失。已把 `semantic_topic_types` 加入 `PHONE_SAFE_KEY_EXCEPTIONS`，保持只读白名单字段可见。

## 剩余风险

- 当前只证明 `software_proof_route_bag_semantic_replay_only` 的 local/mock O6 archive/readback 合同，不证明真实 production cloud、真实 DB3 全量语义解码覆盖率、真实 live Nav2 route execution、真实 robot motion、真实 delivery record、真实 operator confirmation 或真实 delivery success。
- 语义摘要目前只按白名单接收 LaserScan / Image / TF 的有限统计字段；后续如果 Algorithm 合同扩展到更多 ROS message type，O6 仍需要新增显式白名单而不能透传原始内容。
