# Sprint 2026.05.10 17-18 Visual Gate Proof - Tech Done

## 状态

- 阶段：implementation completed。
- 时间：2026-05-10 17:48 Asia/Shanghai。
- 主责：Autonomy Algorithm Engineer。
- 本轮抓手：Objective 3/4 的 fixed-route visual gate 离线 proof artifact。无 ROS2 daemon、无 Nav2、无硬件时也能读取 route、keyframe、live-frame 输入并输出结构化证据。

## 实际改动文件

- `src/ros2_trashbot_nav/ros2_trashbot_nav/visual_gate_proof.py`
- `src/ros2_trashbot_nav/setup.py`
- `src/ros2_trashbot_nav/test/test_visual_gate_proof.py`
- `sprints/2026.05.10_17-18_visual-gate-proof/tech-done.md`

## 实现内容

- 新增 ROS-free `build_visual_gate_proof(route_file, keyframe_dir, live_frame_dir, threshold=25, output_file=None, matcher=None)`。
- 支持 YAML/CSV route 输入，复用 `route_utils` 的 `ROUTE_CONTRACT_VERSION`、CSV 读取和 YAML waypoint 校验。
- 默认按 `<dir>/<index:03d>.jpg` 读取每个 checkpoint 的 keyframe 和 live-frame，并先做文件存在检查。
- 生成 proof JSON，顶层包含 `route`、`checkpoints`、`summary`、`debug_status`、`inputs`。
- 新增 `visual_gate_proof` console script，参数为 `--route-file`、`--keyframe-dir`、`--live-frame-dir`、`--threshold`、`--output`。
- 单测通过 `matcher(keyframe_path, live_frame_path, threshold)` injection 锁定 match count 和失败路径，避免测试依赖真实图像特征稳定性；默认 matcher 在 OpenCV 不可用或读图/descriptor 失败时返回结构化 `no_descriptors`/相关状态。

## Proof artifact 示例字段

```json
{
  "route": {
    "path": ".../fixed_route.yaml",
    "contract_version": "fixed_route.v1",
    "total_checkpoints": 2
  },
  "checkpoints": [
    {
      "index": 0,
      "keyframe": ".../keyframes/000.jpg",
      "live_frame": ".../live/000.jpg",
      "match_count": 32,
      "threshold": 25,
      "status": "passed",
      "detail": "visual gate passed checkpoint 0"
    }
  ],
  "summary": {
    "status": "passed",
    "passed": 2,
    "failed": 0,
    "failure_reasons": {}
  },
  "debug_status": {
    "mode": "offline_proof",
    "visual_gate_status": "passed",
    "visual_gate_detail": "visual gate passed checkpoint 1",
    "visual_gate_checkpoint": 1,
    "failure_reason": "",
    "keyframe_preflight": {
      "route_visual_ready": true
    }
  }
}
```

## 接口影响

- 新增 console script：`visual_gate_proof = ros2_trashbot_nav.visual_gate_proof:main`。
- 不改 ROS2 msg/srv/action。
- 不改 `fixed_route_autonomy.py`、`route_debug_web.py` 或 `/api/status` shape。
- 不改 launch、Nav2、硬件、UART、WAVE ROVER、ESP32、Orange Pi 配置。

## 验证结果

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_nav/test -p 'test_visual_gate_proof.py'`
  - 结果：`Ran 8 tests in 0.549s - OK`
- `python3 -m py_compile src/ros2_trashbot_nav/ros2_trashbot_nav/visual_gate_proof.py`
  - 结果：exit 0
- `git diff --check -- src/ros2_trashbot_nav/ros2_trashbot_nav/visual_gate_proof.py src/ros2_trashbot_nav/setup.py src/ros2_trashbot_nav/test/test_visual_gate_proof.py sprints/2026.05.10_17-18_visual-gate-proof/tech-done.md`
  - 结果：exit 0
- 按本轮收口要求，没有运行 full smoke 或完整 nav test discover。

## 失败定位

- 本轮未出现验证失败。
- CLI 对缺失 route 的路径会生成结构化 `invalid_route` proof JSON，测试已锁定该行为。
- OpenCV 不可用时模块仍可导入；真实图像匹配会降级为结构化 `no_descriptors` proof 状态，不会把异常抛到 CLI 外层。

## 剩余风险

- 本轮 proof 只证明离线证据结构、route 解析和匹配状态输出，不证明真实相机光照鲁棒性。
- 真实 route、真实 keyframe/live-frame、真实 camera frame、真实 fixed-route/Nav2 行驶仍未上车验证。
- route debug web 和任务记录尚未消费该 proof artifact；后续接入前需要锁定字段迁移策略。
