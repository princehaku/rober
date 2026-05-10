# Sprint 2026.05.10 17-18 Visual Gate Proof - Tech Plan

## 状态

- 阶段：tech-plan completed，可进入 implementation。
- 时间：2026-05-10 17:00 Asia/Shanghai。
- 主责：Autonomy Algorithm Engineer。
- 执行方式：1 owner 单线闭环，必须由 `autonomy-engineer` 子 agent 实现、验证并更新 `tech-done.md`。Coordinator/Product Owner 不直接写产品代码或测试代码。

## 文件范围

Autonomy Engineer 可改：

- `src/ros2_trashbot_nav/ros2_trashbot_nav/visual_gate_proof.py`
- `src/ros2_trashbot_nav/setup.py`
- `src/ros2_trashbot_nav/test/test_visual_gate_proof.py`
- `sprints/2026.05.10_17-18_visual-gate-proof/tech-done.md`

允许只读：

- `AGENTS.md`
- `OKR.md`
- `sprints/2026.05.10_17-18_visual-gate-proof/pre_start.md`
- `sprints/2026.05.10_17-18_visual-gate-proof/prd.md`
- `src/ros2_trashbot_nav/ros2_trashbot_nav/fixed_route_autonomy.py`
- `src/ros2_trashbot_nav/ros2_trashbot_nav/route_debug_web.py`
- `src/ros2_trashbot_nav/ros2_trashbot_nav/route_utils.py`
- `src/ros2_trashbot_nav/test/test_fixed_route_dry_run_offline.py`
- `src/ros2_trashbot_nav/test/test_fixed_route_status_static.py`
- `src/ros2_trashbot_nav/test/test_route_csv_to_yaml.py`

禁止改动：

- `OKR.md`
- `AGENTS.md`
- `.codex/agents/`
- `docs/vendor/`
- `src/ros2_trashbot_hardware/`
- `src/ros2_trashbot_behavior/`
- `src/ros2_trashbot_interfaces/`
- `src/ros2_trashbot_bringup/`
- `src/ros2_trashbot_nav/ros2_trashbot_nav/fixed_route_autonomy.py`，除非实现时发现必须抽取无副作用纯函数；若改动，必须先保持接口不变并在 `tech-done.md` 解释原因。
- `src/ros2_trashbot_nav/ros2_trashbot_nav/route_debug_web.py`
- ROS2 msg/srv/action
- launch 硬件参数、UART、WAVE ROVER、ESP32、Orange Pi 相关配置

## 接口影响

- 新增 CLI 建议入口：`visual_gate_proof = ros2_trashbot_nav.visual_gate_proof:main`。
- 不改现有 console scripts 的行为。
- 不改 `/api/status` 路径。
- 不改 fixed-route runtime status JSON producer 的字段 shape。
- 新增 proof JSON artifact contract，建议字段：

```json
{
  "route": {
    "path": "...",
    "contract_version": "fixed_route.v1",
    "total_checkpoints": 2
  },
  "checkpoints": [
    {
      "index": 0,
      "keyframe": "...",
      "live_frame": "...",
      "match_count": 32,
      "threshold": 25,
      "status": "passed",
      "detail": "visual gate passed checkpoint 0"
    }
  ],
  "summary": {
    "status": "passed",
    "passed": 1,
    "failed": 0
  },
  "debug_status": {
    "visual_gate_status": "passed",
    "visual_gate_detail": "visual gate passed checkpoint 0",
    "visual_gate_checkpoint": 0,
    "keyframe_preflight": {}
  }
}
```

- Artifact 字段命名应尽量贴近 `fixed_route_autonomy.py` 的 debug status 语义，便于后续 route debug web 或 task record 消费。

## 实施任务

### Task 1：新增 visual gate proof 模块

文件：

- `src/ros2_trashbot_nav/ros2_trashbot_nav/visual_gate_proof.py`

要求：

1. 提供纯函数入口，例如 `build_visual_gate_proof(route_file, keyframe_dir, live_frame_dir, threshold, output_file=None)`。
2. 支持 YAML/CSV route 读取，优先复用 `route_utils` 现有 contract 校验。
3. 每个 checkpoint 默认读取：
   - keyframe：`<keyframe_dir>/<index:03d>.jpg`
   - live frame：`<live_frame_dir>/<index:03d>.jpg`
4. 输出 proof dict，并可写入 JSON 文件。
5. 失败路径必须结构化：
   - route 缺失或非法 -> `invalid_route`
   - keyframe 缺失 -> `missing_keyframe`
   - live frame 缺失 -> `missing_live_frame`
   - 图像不可读或无 descriptor -> `no_descriptors` 或更精确状态
   - 匹配不足 -> `insufficient_matches`
6. 不启动 ROS2 node，不创建 `BasicNavigator`，不订阅 camera topic。

### Task 2：新增 CLI

文件：

- `src/ros2_trashbot_nav/ros2_trashbot_nav/visual_gate_proof.py`
- `src/ros2_trashbot_nav/setup.py`

要求：

1. CLI 参数建议：
   - `--route-file`
   - `--keyframe-dir`
   - `--live-frame-dir`
   - `--threshold`
   - `--output`
2. 正常生成 proof 时退出码为 0。
3. route 或输入非法时输出结构化错误 JSON；若选择非 0 退出码，测试要锁定行为。
4. 不新增外部服务、前端构建或 ROS2 runtime 依赖。

### Task 3：新增 focused 单测

文件：

- `src/ros2_trashbot_nav/test/test_visual_gate_proof.py`

要求：

1. 使用标准库 `unittest`。
2. 用临时目录创建 route、keyframe/live-frame fixture。
3. 如果依赖 OpenCV，测试中要能用 monkeypatch/stub 覆盖 descriptor 和 match count，避免测试依赖真实图像特征稳定性。
4. 至少覆盖：
   - passed proof artifact。
   - insufficient matches。
   - missing keyframe。
   - missing live frame。
   - invalid route 或 missing route。
   - CLI 写出 JSON 文件。
5. 断言 proof JSON 包含 `route`、`checkpoints`、`summary`、`debug_status`。

### Task 4：写 tech-done

文件：

- `sprints/2026.05.10_17-18_visual-gate-proof/tech-done.md`

记录：

- 实际改动文件。
- Objective 3/4 本轮推进点。
- proof artifact 示例字段。
- 接口影响。
- 验证命令和结果。
- 失败定位。
- 剩余风险，尤其是真实相机/真实路线/实车验证仍未完成。

## 验收命令

Autonomy Engineer 必须至少运行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_nav/test -p 'test_visual_gate_proof.py'
python3 -m py_compile src/ros2_trashbot_nav/ros2_trashbot_nav/visual_gate_proof.py
git diff --check -- src/ros2_trashbot_nav/ros2_trashbot_nav/visual_gate_proof.py src/ros2_trashbot_nav/setup.py src/ros2_trashbot_nav/test/test_visual_gate_proof.py sprints/2026.05.10_17-18_visual-gate-proof/tech-done.md
```

如果改动影响 nav 包通用测试，还应运行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_nav/test
```

如果本地耗时可接受，继续运行完整护栏：

```bash
PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh
```

本 planning 子 agent 只运行只读检查：

```bash
grep -n "文件范围\|验收命令\|接口影响\|风险" sprints/2026.05.10_17-18_visual-gate-proof/tech-plan.md
```

## 风险边界

- 本轮 proof artifact 不证明真实 camera frame、真实 keyframe 光照鲁棒性或 Nav2 行驶成功。
- 本轮不接硬件，不读取 vendor 文档，不改变任何 WAVE ROVER、UART、ESP32、Orange Pi 假设。
- 如果 OpenCV 在当前环境不可用，Autonomy Engineer 应优先保持模块可导入，并用 dependency injection/stub 让单测稳定；真实 ORB 匹配可作为可选路径。
- CLI 输出 contract 一旦被 route debug web 或 task record 消费，后续字段变更需要迁移策略；本轮先保持 artifact 明确、简单、可替换。

## 子 Agent 启动建议

下阶段 implementation 应派发 1 个 `autonomy-engineer` worker，prompt 必须包含：

- 角色 System Prompt：从 `.codex/agents/autonomy-engineer.toml` 的 `prompt` 字段完整复制。
- 本轮任务：实现 visual gate proof helper/CLI，生成/验证 fixed-route visual gate 离线证据。
- 文件范围：使用本 tech-plan 的“文件范围”。
- 验收命令：使用本 tech-plan 的“验收命令”。
- 输出要求：实际改动文件、验证命令输出、失败定位、剩余风险。
