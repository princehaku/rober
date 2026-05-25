# pc-tools/evidence

`pc-tools/evidence/` 现在保留非 Python 证据资产，主要入口是：

```text
pc-tools/evidence/fixtures/
```

旧 Python evidence gate 和 Python 测试文件已移除。Evidence Tools 页面不再扫描 `.py`，而是由 Node API 递归索引 `fixtures/**/*.json`，按 fixture 一级目录生成资产分组。

## JSON Fixture 语义

JSON fixture 是脱敏软件证明材料或测试样例。fixture 可读只表示工作站能索引并解析本地 JSON，不表示真实现场材料齐全，也不表示 HIL、手机、云端、ROS2、Nav2、WAVE ROVER 或交付成功通过。

所有工作站响应仍固定：

- `source=software_proof`
- `proof_status=not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`

## 验证

Evidence fixture 索引由工作站测试覆盖：

```bash
cd pc-tools/workstation && npm run test
```

旧 Python gate 命令不再作为 `pc-tools` 验收入口。
