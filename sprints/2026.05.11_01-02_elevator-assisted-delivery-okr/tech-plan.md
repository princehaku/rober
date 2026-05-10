# Sprint 2026.05.11 01-02 Elevator Assisted Delivery OKR - Tech Plan

## 状态

- 阶段：tech-plan completed。
- 时间：2026-05-11 01:02 Asia/Shanghai。
- 本轮 owner：`product-okr-owner`。
- 执行类型：产品/OKR/文档切片。

## 技术方案

本轮不进入代码实现，只建立后续工程的产品 contract。

1. 更新 `OKR.md`
   - 北极星加入电梯 assisted delivery 的 H2 方向。
   - 战略定位明确人工协助、低成本、不默认新硬件。
   - Objective 2、4、5 增加 H2 KR。
   - H2 路线新增电梯 assisted delivery 阶段。
   - 风险表和下一步建议加入电梯能力边界。
   - 进度快照说明本轮只完成产品方向，不抬实机完成度。

2. 新增 `docs/product/elevator_assisted_delivery.md`
   - 最小用户流程。
   - 指定语音提示。
   - 状态机边界。
   - 识别要求。
   - 人工协助边界。
   - 验收口径。
   - 责任 Engineer。

3. 新建 sprint 六件套
   - 记录目标、PRD、计划、实际改动、side-by-side 对照和最终复盘。

## 接口影响

- ROS2 topic/action/srv：无直接改动。
- 手机/API：无直接改动，仅定义未来 contract。
- 硬件：无直接改动，不新增 ESP32/WAVE ROVER/Orange Pi 引脚、电压、UART、波特率或机械安装假设。

## 风险边界

- 文档不能暗示当前 MVP 已能进出电梯。
- 文档不能把 ESP32 下位机写成楼层识别、语音求助或电梯决策承载方。
- 文档不能默认机械臂、深度相机、电梯控制器或楼宇改造。
- 本轮不能修改硬件 proof 参数门禁 sprint。

## 验收命令

```bash
git diff --check -- OKR.md docs/product sprints/2026.05.11_01-02_elevator-assisted-delivery-okr
python3 - <<'PY'
from pathlib import Path
required = [
    Path('OKR.md'),
    Path('docs/product/elevator_assisted_delivery.md'),
    Path('sprints/2026.05.11_01-02_elevator-assisted-delivery-okr/pre_start.md'),
    Path('sprints/2026.05.11_01-02_elevator-assisted-delivery-okr/prd.md'),
    Path('sprints/2026.05.11_01-02_elevator-assisted-delivery-okr/tech-plan.md'),
    Path('sprints/2026.05.11_01-02_elevator-assisted-delivery-okr/tech-done.md'),
    Path('sprints/2026.05.11_01-02_elevator-assisted-delivery-okr/side2side_check.md'),
    Path('sprints/2026.05.11_01-02_elevator-assisted-delivery-okr/final.md'),
]
missing = [str(p) for p in required if not p.exists()]
if missing:
    raise SystemExit(f'missing files: {missing}')
texts = {str(p): p.read_text(encoding='utf-8') for p in required}
checks = ['电梯', '开门', '目标楼层', '请帮我按一下电梯', 'Orange Pi', 'ROS2', '人工协助', '验收']
for token in checks:
    if not any(token in text for text in texts.values()):
        raise SystemExit(f'missing required token: {token}')
print('doc contract OK')
PY
```

## 后续实现建议

- `robot-software-engineer`：先做模拟事件驱动的电梯子状态 dry-run。
- `autonomy-engineer`：先定义门开/目标楼层/驶出证据 schema 和样本采集计划。
- `full-stack-software-engineer`：先把手机文案和 speaker prompt contract 接入 diagnostics/status。
- `hardware-engineer`：仅在进入实机安装、电气或串口事项时做 vendor 资料确认。
