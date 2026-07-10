# O6 Repair Worker Report

## 实际改动文件

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`

## 验证结果

### 1. 语法检查

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
```

- 结果：通过（exit 0，无输出）

### 2. 单元测试

```bash
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
```

- 首次复跑中出现 1 次既有 HTTP 连接重置波动：`test_o6_cloud_archive_tasks_endpoint_rejects_unsafe_or_oversized_payloads` 报 `URLError: [Errno 54] Connection reset by peer`
- 复跑后通过：

```text
Ran 181 tests in 77.619s

OK
```

### 3. 字段锚点检查

```bash
rg -n "localization_path_material_bridge_present|same_run_localization_tf_map_to_odom|same_run_tf_map_to_odom_observed|localization_path_material_readback_ready_not_route_execution_proof" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md
```

- 结果：通过
- 关键命中：
  - `remote_cloud_relay.py` 已同时出现 `same_run_localization_tf_map_to_odom` 与 `same_run_tf_map_to_odom_observed`
  - `remote_cloud_relay.py` 已输出 `localization_path_material_bridge_present`
  - `test_remote_cloud_relay.py` 已覆盖 Algorithm-shaped payload
  - `docs/interfaces/o6_cloud_archive_api.md` 已记录新旧字段兼容与 O7 aliases

### 4. diff 格式检查

```bash
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md sprints/2026.07.10_21-27_o6_o7_localization_path_material_readback
```

- 结果：通过（exit 0，无输出）

## 失败定位

- 主因：O6 summary 之前只接受旧字段 `same_run_tf_map_to_odom_observed` / `same_run_tf_map_to_base_link_observed`，没有吸收 Algorithm 当前产出的 `same_run_localization_tf_*`
- 次因：O6 回读缺少 O7 需要的 `localization_path_material_bridge_present`、`same_run_localization_material_present` 和 `same_run_localization_tf_*` aliases，导致真实 Algorithm packet 被 O6/O7 降级
- 测试返工中有 2 个对齐点：
  - “无 comparator” 的 O6 规范化输出是 `cross_run_clean_baseline_path_summary={"present": false}`，不是空对象
  - 全量 relay 单测有 1 次既有大包拒绝测试出现连接重置，复跑后通过，未见与本次字段修改相关的稳定失败

## 剩余风险

- O6 现在对新旧 TF 字段双写兼容，但仍要求这些字段最终是布尔值；如果上游再改成字符串或嵌套结构，仍会 fail-closed
- `same_run_localization_material_present` 当前对缺失时回退到 `localization_path_material_bridge_present`，这满足当前 Algorithm/O7 合同，但若后续两者语义拆开，需要再收紧
- 这次未改 O7 文件；若 O7 后续额外依赖更多 Algorithm 原始字段，仍需要在下一轮由对应 owner 扩充 consumer 合同
