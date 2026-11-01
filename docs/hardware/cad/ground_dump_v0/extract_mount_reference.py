"""从本地厂家 DXF 读取四孔，保留原始坐标、单位及坐标映射证据。"""
import json
from pathlib import Path

import ezdxf
from ezdxf import path
from PIL import Image, ImageDraw, ImageFont

# 数据源固定指向本地厂家文件，脚本只读，不写回任何DXF。
# 以孔组中心为安装原点，避免两块外轮廓中心不同而误对齐。
root = Path(__file__).resolve().parents[4]
out = Path(__file__).resolve().parent
specs = [
    ("upper", "WAVE ROVER-EP DXF.dxf", ["302", "303", "311", "32E"], (40, 180, 170, 270)),
    ("lower", "WAVE ROVER DXF.dxf", ["2DFB", "2DFC", "2DFD", "2E2F"], (210, 375, 352, 536)),
]
report = {"source": "本地 vendor DXF，截图仅用于识别对应轮廓", "ezdxf": ezdxf.__version__, "plates": {}}
# 句柄来自逐一对照截图后的实体选择，可追溯到原文件中的具体圆。
drawings = {}
for key, name, handles, region in specs:
    source = root / "docs/vendor/waveshare_wave_rover" / name
    # 直接解析模型空间，避免把打印图框比例当作机械尺寸缩放。
    doc = ezdxf.readfile(source)
    # 仅图框和标题栏为块插入，零件本体直接存在于模型空间。
    inserts = [{"name": e.dxf.name, "scale": [e.dxf.xscale, e.dxf.yscale, e.dxf.zscale],
                "rotation_deg": e.dxf.rotation} for e in doc.modelspace().query("INSERT")]
    holes = []
    for handle in handles:
        entity = doc.entitydb[handle]
        # 同时保存实体原始OCS和统一WCS，便于复核负法向导致的翻号。
        # CIRCLE 使用负 Z 法向，OCS 横坐标经变换后翻号，必须转为 WCS。
        wcs = entity.ocs().to_wcs(entity.dxf.center)
        holes.append({"handle": handle, "ocs_center": list(entity.dxf.center),
                      "extrusion": list(entity.dxf.extrusion), "wcs_center": list(wcs),
                      "diameter_mm": round(entity.dxf.radius * 2, 6)})
    center = [sum(h["wcs_center"][i] for h in holes) / 4 for i in (0, 1)]
    # 中心距由圆心坐标相减得到，与截图大小或显示缩放无关。
    pitch = [max(h["wcs_center"][i] for h in holes) - min(h["wcs_center"][i] for h in holes) for i in (0, 1)]
    # 区域筛选排除其他正交视图和标题栏；不从截图像素换算毫米。
    lines = []
    for entity in doc.modelspace():
        # 同一图纸含多个正交视图，只保留已定位的顶视区域。
        if entity.dxf.layer != "Visible":
            continue
        try:
            # 曲线细分仅服务预览，四孔中心和直径始终读取解析实体值。
            points = list(path.make_path(entity).flattening(0.02))
        except (TypeError, ValueError):
            continue
        if points and all(region[0] < p.x < region[1] and region[2] < p.y < region[3] for p in points):
            lines.append([(p.x, p.y) for p in points])
    # 原板中心仅用于说明孔组偏置，不拿来充当安装原点。
    bounds = [min(p[0] for line in lines for p in line), min(p[1] for line in lines for p in line),
              max(p[0] for line in lines for p in line), max(p[1] for line in lines for p in line)]
    # 下层基准采用已独立核对的顶板外边实体，排除整图其他小特征的0.05偏移。
    reference_bounds = bounds if key == "upper" else [210.775454,352.499357,374.515448,535.606831]
    plate_center = [(reference_bounds[0]+reference_bounds[2])/2, (reference_bounds[1]+reference_bounds[3])/2]
    record = {"file": str(source.relative_to(root)).replace("\\", "/"), "insunits": doc.header.get("$INSUNITS"),
              "unit": "mm", "measurement": doc.header.get("$MEASUREMENT"), "inserts": inserts,
              "holes": holes, "hole_center_wcs": center, "pitch_wcs_mm": pitch,
              "drawing_region_bounds_wcs_mm": bounds, "reference_outline_bounds_wcs_mm": reference_bounds,
              "outline_center_wcs": plate_center,
              "reference_outline_entities": "2EA6/2EA7/2EA8/2EAB/2EAC" if key=="lower" else "上层顶视区域曲线包围框",
              "hole_group_offset_from_outline_center_mm": [center[i]-plate_center[i] for i in (0, 1)]}
    assert record["insunits"] == 4 and len(holes) == 4
    # 单位若被更新为其他值，必须中断并重新确认，不能继续默认为毫米。
    report["plates"][key] = record
    drawings[key] = (lines, center)
    # 打印核心尺寸摘要，便于sprint留档而无需拷贝整份厂家文件。
    print(key, "INSUNITS=4 mm", "center WCS", center, "pitch", pitch, "diameters", [h["diameter_mm"] for h in holes])

# 安装坐标中前后方向为设计映射，可通过源文件参数旋转180度。
report["mapping"] = {"upper": "X=u-130.837759, Y=v-220.264173", "lower": "X=V-466.694635, Y=-(U-292.645451)",
                     "orientation": "两图相差90度；四孔对称无法确定行驶车头，CAD仅提供整体180度展示切换", "thread_user_confirmed_mm": 2.5,
                     "lower_connection": "原图孔径2.05，未见攻牙标注；用户确认M2.5安装，连接类型待实物核对"}
(out / "mount_reference.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
# 证据JSON只保存坐标和映射，不复制厂家大型模型或用户原图。

# 图上采用同一安装原点和毫米比例，展示偏置和90度映射后的同轴关系。
font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 23)
# 使用本机中文字体给参考图加说明，机械曲线仍全部来自解析后的实体。
small = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 19)
image = Image.new("RGB", (1600, 1040), "#f6f7f9")
draw = ImageDraw.Draw(image)
draw.text((25, 16), "四孔接口 · DXF 原始几何与共用安装原点", font=font, fill="#152a3b")
for index, key in enumerate(("upper", "lower")):
    lines, center = drawings[key]
    origin = (470+index*790, 470)
    # 几何变换仅旋转和平移；两个面板共用每毫米3.6像素的绘图比例。
    def map_point(point):
        u, v = point[0]-center[0], point[1]-center[1]
        x, y = (u, v) if key == "upper" else (v, -u)
        return origin[0]+x*3.6, origin[1]-y*3.6

    for line in lines:
        # 两板映射到同一方向，读者可直接比对四个红圈位置。
        draw.line([map_point(point) for point in line], fill="#525c66", width=1)
    for hole in report["plates"][key]["holes"]:
        x, y = map_point(hole["wcs_center"][:2])
        # 两图用同一安装坐标编号，H1至H4能直接一一对应。
        number = 1 + 2*(x>origin[0]) + (y>origin[1])
        draw.ellipse((x-10,y-10,x+10,y+10), outline="#d83f32", width=3)
        draw.text((x+13,y-12), f"H{number}", font=small, fill="#b33327")
    draw.line((origin[0]-12,origin[1],origin[0]+12,origin[1]), fill="#208a56", width=2)
    # 绿色十字标安装原点；外轮廓中心与其偏移不会被偷偷消除。
    draw.line((origin[0],origin[1]-12,origin[0],origin[1]+12), fill="#208a56", width=2)
    draw.text((25+index*790, 75), "上层四耳板 · 原孔 Ø2.60" if key=="upper" else "一层顶板 · 原图孔 Ø2.05", font=font, fill="#152a3b")
    draw.text((25+index*790, 115), "安装原点=四孔组中心；X横向58，Y纵向86 mm", font=small, fill="#152a3b")
draw.text((25, 815), "上下层经90°旋转和平移后：X=±29，Y=±43 mm，四条安装轴线重合。", font=font, fill="#152a3b")
draw.text((25, 862), "用户已确认 M2.5。原板参考孔径分别2.60 / 2.05；下层通孔或螺纹类型待实物核对。", font=small, fill="#9b3c2f")
draw.text((25, 903), "新样板/金属件通孔默认Ø3.0为本稿设计间隙；孔径与螺纹分别参数化。", font=small, fill="#152a3b")
draw.text((25, 944), "本图由DXF实体生成；车头朝向尚待确认，不能仅凭四孔对称阵列判断。", font=small, fill="#152a3b")
image.save(out / "mount_dxf_reference.png")
