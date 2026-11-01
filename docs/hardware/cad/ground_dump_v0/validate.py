"""检查候选打印件的封闭性和参数变化，生成双状态装配概览。"""
import json
import sys
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont

# 检查结果与 CAD 导出同目录保存，方便复查实际尺寸和版本。
out = Path(sys.argv[1]).resolve()
# 没有自动修网格流程，保持检查对象与用户拿到的 STL 完全一致。
# 记录依赖版本，后续换环境后可比较导出结果。
summary = {"trimesh": trimesh.__version__, "numpy": np.__version__, "parts": {}}
for name in ("lidar_plate", "camera_bracket", "base_adapter", "lidar_plate_reference_check", "lidar_plate_wide_check"):
    mesh = trimesh.load(out / f"{name}.stl", force="mesh")
    # 每个命名文件独立验证，某个文件失败时直接指出对应零件。
    # 以顶点邻接判断连通性，不依赖庞大的科学计算库。
    # trimesh 已合并 STL 中重复坐标，父索引可直接描述实体连接。
    parent = list(range(len(mesh.vertices)))

    # 压缩路径避免循环查找相同顶点链。
    def root(vertex):
        while parent[vertex] != vertex:
            parent[vertex] = parent[parent[vertex]]
            vertex = parent[vertex]
        return vertex

    # 三角面共享任一顶点即归同组；封闭性还须单独检查共享边。
    for face in mesh.faces:
        for vertex in face[1:]:
            parent[root(int(vertex))] = root(int(face[0]))
    # 所有顶点必须归于同一实体，禁止导出多个分离打印块。
    components = len({root(i) for i in range(len(parent))})
    # 最低点落在 Z=0，适合直接载入切片器；悬垂另见说明。
    record = {
        "faces": len(mesh.faces), "watertight": bool(mesh.is_watertight),
        "winding_consistent": bool(mesh.is_winding_consistent),
        "components": components, "volume_mm3": round(float(mesh.volume), 3),
        "extents_mm": np.round(mesh.extents, 3).tolist(),
        "min_z_mm": round(float(mesh.bounds[0, 2]), 4),
    }
    # 同时检查体积和法线，避免只有外壳外观却无法切片的输出。
    assert record["faces"] > 0 and record["watertight"], (name, record)
    assert record["winding_consistent"] and components == 1, (name, record)
    assert record["volume_mm3"] > 0 and abs(record["min_z_mm"]) < 0.001, (name, record)
    summary["parts"][name] = record
    print(f"PASS {name}: {json.dumps(record)}")

# 固定 90/100 对照不依赖用户源文件默认柱距，修改默认值仍可完整导出。
default_width = summary["parts"]["lidar_plate_reference_check"]["extents_mm"][1]
# 直接比较导出网格包围框，避免只检查源文件里的参数文字。
changed_width = summary["parts"]["lidar_plate_wide_check"]["extents_mm"][1]
assert abs(changed_width - default_width - 10) < 0.001
summary["parameter_check"] = {"mast_spacing": [90, 100], "plate_width_mm": [default_width, changed_width]}

# 标注与图例只排版既有 CAD 渲染，没有改写任何机械几何。
# Windows 使用本机中文字体；其他系统仍可生成图像但需替换字体路径。
font_path = Path("C:/Windows/Fonts/msyh.ttc")
font = ImageFont.truetype(str(font_path), 27) if font_path.exists() else ImageFont.load_default()
small = ImageFont.truetype(str(font_path), 22) if font_path.exists() else font
canvas = Image.new("RGB", (1800, 900), "#f4f5f7")
draw = ImageDraw.Draw(canvas)
# 图上明确写证据边界，避免单独分享预览时误解为已定型机构。
draw.text((30, 16), "地面后卸翻斗 · 可编辑机械草案 v0", font=font, fill="#1c2935")
# 两幅原图保留完整画幅，仅缩小排在同一张概览。
for index, (filename, title) in enumerate((("transport.png", "运输 · 0°"), ("dump_55.png", "后卸 · 55°"))):
    image = Image.open(out / filename).convert("RGB")
    image.thumbnail((880, 660))
    canvas.paste(image, (10 + index * 900, 90))
    draw.text((35 + index * 900, 63), title, font=font, fill="#1c2935")
draw.text((30, 766), "灰：金属主骨架    橙：打印适配件    蓝：敞口垃圾斗    紫：执行器占位    红：雷达占位", font=small, fill="#233443")
draw.text((30, 811), "绿色箭头 FRONT +X = 车头；REAR / DUMP = 后卸方向。所有未实测尺寸均为设计占位。", font=small, fill="#233443")
draw.text((30, 852), "2 kg 为垃圾目标；尚未验证总载荷、推力、行程、重心、滑出效果及防倾覆。", font=small, fill="#9a352c")
# 保存的报告只代表几何验证，不推断材料强度或装配兼容性。
canvas.save(out / "overview.png")
summary["preview"] = "CAD 渲染，仅完成视觉布局检查；没有机械仿真或实物试装。"
(out / "geometry_report.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"PASS parameter change: plate width {default_width} -> {changed_width} mm")
print(f"Overview: {out / 'overview.png'}")
