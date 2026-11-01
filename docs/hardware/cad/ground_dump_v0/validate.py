"""检查候选打印件的封闭性和参数变化，生成双状态装配概览。"""
import json
import sys
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont

# 验证仅使用轻量网格与数值库，不引入ROS或物理仿真环境。
# 检查结果与 CAD 导出同目录保存，方便复查实际尺寸和版本。
out = Path(sys.argv[1]).resolve()
# 没有自动修网格流程，保持检查对象与用户拿到的 STL 完全一致。
# 记录依赖版本，后续换环境后可比较导出结果。
summary = {"trimesh": trimesh.__version__, "numpy": np.__version__, "parts": {}}
for name in ("camera_bracket", "mount_template", "mount_template_reference_check", "mount_template_changed_check"):
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
# 整板参考可含多个装配实体；它们只用于几何契约，不套用生产单体约束。
assembly90 = trimesh.load(out/"lidar_plate_reference_check.stl",force="mesh")
assembly100 = trimesh.load(out/"lidar_plate_wide_check.stl",force="mesh")
assert assembly90.is_watertight and assembly100.is_watertight
default_width = float(assembly90.extents[1])
# 直接比较导出网格包围框，避免只检查源文件里的参数文字。
changed_width = float(assembly100.extents[1])
assert abs(changed_width - default_width - 10) < 0.001
summary["parameter_check"] = {"mast_spacing": [90, 100], "plate_width_mm": [default_width, changed_width]}


# 从实际三角网格切片恢复圆孔，独立验证几何结果，不能仅比较参数文字。
def sliced_holes(mesh, height, return_polygons=False):
    # 先求三角面与水平面的交线，再重建边界环，结果来自实际STL。
    graph = {}
    for triangle in mesh.triangles:
        intersections = []
        # 只取穿越截面的边，水平边不会参与，避免重合线被重复计数。
        for first, second in ((0,1),(1,2),(2,0)):
            a, b = triangle[first], triangle[second]
            if (a[2]-height)*(b[2]-height) < 0:
                point = a+(b-a)*(height-a[2])/(b[2]-a[2])
                # 五位小数吸收二进制STL浮点误差，远小于打印精度。
                intersections.append(tuple(np.round(point[:2],5)))
        # 选在实体中部切片，避开顶底面，所有截面边应首尾闭合。
        if len(intersections) == 2 and intersections[0] != intersections[1]:
            a, b = intersections
            # 同时登记两个方向，后续可从任意顶点恢复完整闭环。
            graph.setdefault(a,set()).add(b)
            graph.setdefault(b,set()).add(a)
    assert graph and all(len(neighbors)==2 for neighbors in graph.values())
    # 每个截面顶点须有两条邻边，开裂或自交会在测孔前直接报错。
    unvisited, holes, polygons = set(graph), [], []
    while unvisited:
        start = next(iter(unvisited))
        # 外边界和孔边界一并遍历，只有小圆边界进入圆孔结果。
        loop, previous, current = [], None, start
        while current not in loop:
            loop.append(current)
            unvisited.discard(current)
            following = next(v for v in graph[current] if v != previous)
            previous, current = current, following
        points = np.array(loop)
        # 保存全部截面环，工具空间检查还需要外轮廓的占用信息。
        polygons.append(points)
        # 最小二乘圆拟合识别小圆孔，长直边组成的外轮廓不会通过误差门限。
        solution = np.linalg.lstsq(np.c_[2*points,np.ones(len(points))],(points**2).sum(axis=1),rcond=None)[0]
        center = solution[:2]
        # 圆拟合同时给出轴线中心，能够发现孔距对了但偏置错误的问题。
        radii = np.linalg.norm(points-center,axis=1)
        if len(points)>=24 and radii.std()<0.015 and 1.2<radii.mean()<3.4:
            # 排除外框大圆角，孔至少有24个截面点才视为可信圆环。
            segments = np.roll(points,-1,axis=0)-points
            # 多边形孔的内切通径略小于名义圆径，也记录下来供打印校准。
            distances = abs(segments[:,0]*(center[1]-points[:,1])-segments[:,1]*(center[0]-points[:,0]))/np.linalg.norm(segments,axis=1)
            holes.append({"center_mm": np.round(center,4).tolist(),
                          "circumdiameter_mm": round(float(2*radii.max()),4),
                          "minimum_clearance_mm": round(float(2*distances.min()),4)})
    # 以中心坐标排序，使不同导出三角面顺序不会影响逐孔比对。
    return polygons if return_polygons else sorted(holes,key=lambda item:item["center_mm"])


# 当前用户参数的样板测量另存，固定回归则比较58×86和68×96两组。
summary["mounting"] = {"reference_upper_hole_mm": 2.6, "reference_lower_dxf_circle_mm": 2.05,
                       "thread_user_confirmed_mm": 2.5, "new_parts_design_clearance_mm": 3.0, "cases": {}}
for kind, pitch in (("reference",(58,86)),("changed",(68,96))):
    template = trimesh.load(out/f"mount_template_{kind}_check.stl",force="mesh")
    frame = trimesh.load(out/f"mount_frame_{kind}_check.stl",force="mesh")
    sensor_adapter = trimesh.load(out/f"sensor_adapter_{kind}_check.stl",force="mesh")
    # 金属检查网格有多个装配实体，只要求每个边界封闭，不当作单个打印件。
    assert frame.is_watertight and frame.is_winding_consistent and frame.volume>0
    template_holes = sliced_holes(template,float(template.bounds[1,2])/2)
    # 实际框架已整体下移100，Z=5截面穿过四个金属隔柱。
    frame_holes = sliced_holes(frame,5)
    expected = sorted([[x,y] for x in (-pitch[0]/2,pitch[0]/2) for y in (-pitch[1]/2,pitch[1]/2)])
    # 样板与框架独立出网格，再比较两者轴线，防止只测同一复制几何。
    assert len(template_holes)==4 and len(frame_holes)==4
    for measured, supports, target in zip(template_holes,frame_holes,expected):
        assert np.allclose(measured["center_mm"],target,atol=0.001)
        assert np.allclose(supports["center_mm"],target,atol=0.001)
        assert 2.99<measured["minimum_clearance_mm"]<=3.001
        assert 2.99<supports["minimum_clearance_mm"]<=3.001
    # 平面奇偶规则直接测实际塑料实体占用，不依赖外部射线加速库。
    # 既检查实际塑料适配板，也检查螺头高度处的金属主梁，不只看预览外观。
    clearance_sections = [("传感器适配板",sliced_holes(sensor_adapter,float(sensor_adapter.bounds[1,2])*0.37,True)),
                          ("金属主梁螺头高度",sliced_holes(frame,20,True))]
    for section_name, polygons in clearance_sections:
        for center in expected:
            # 中心和两圈径向采样共同检查圆盘，避免仅测圆周漏掉中间实心障碍。
            for radius, angle in ((r,a) for r in (0,2.5,4.95) for a in np.linspace(0,2*np.pi,49)):
                sample = np.array(center)+radius*np.array([np.cos(angle),np.sin(angle)])
                occupied = False
                for polygon in polygons:
                    # 多个轮廓按奇偶规则组合，板内孔和板外都算开放空间。
                    a, b = polygon, np.roll(polygon,-1,axis=0)
                    crossing = ((a[:,1]>sample[1])!=(b[:,1]>sample[1])) & (sample[0] < (b[:,0]-a[:,0])*(sample[1]-a[:,1])/(b[:,1]-a[:,1]+1e-20)+a[:,0])
                    occupied ^= bool(np.count_nonzero(crossing)%2)
                assert not occupied, (kind,center,section_name,"封堵工具通道")
    # 报告区分厂家原孔、用户螺纹和新增件间隙，避免不同证据混用。
    summary["mounting"]["cases"][kind] = {"pitch_mm": pitch, "template_holes": template_holes, "actual_frame_post_holes": frame_holes}
    print(f"PASS four-hole {kind}: pitch={pitch}, template/post axes aligned, nominal 3.0, polygon minimum clearance >2.99 mm")
    print(f"PASS tool access {kind}: four 9.9 mm circular envelopes clear of actual sensor adapter")

# 新样板本身也从网格测量，便于用户修改默认孔距后复查实际输出。
actual_template = trimesh.load(out/"mount_template.stl",force="mesh")
# 默认样板采用用户当前源参数，独立于固定对照组保存测量结果。
summary["mounting"]["actual_template_holes"] = sliced_holes(actual_template,float(actual_template.bounds[1,2])/2)
assert len(summary["mounting"]["actual_template_holes"]) == 4

# 分体模块复用实际网格切片入口，额外检查逆变换、贴合面和螺母工具空间。
from verify_split import verify_split
summary["split"] = verify_split(out,sliced_holes)

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
# 安装详情来自CAD渲染，右侧标注用实际样板网格测得的四孔轴线生成。
install = Image.new("RGB",(1800,1100),"#f4f5f7")
mark = ImageDraw.Draw(install)
mark.text((25,15),"M2.5 四孔金属安装 · 原点=孔组中心",font=font,fill="#1c2935")
# 孔距标签读实际网格；图像像素仅用于摆放文字，不参与毫米测量。
centers = np.array([hole["center_mm"] for hole in summary["mounting"]["actual_template_holes"]])
pitch_x, pitch_y = np.ptp(centers,axis=0)
for index, name in enumerate(("mount_install_raw.png","mount_top_raw.png")):
    preview = Image.open(out/name).convert("RGB")
    # 去掉CAD渲染的空白边界后放大安装部位，保留所有实体不改变几何。
    pixels = np.asarray(preview)
    content = np.argwhere(np.max(abs(pixels.astype(int)-pixels[0,0].astype(int)),axis=2)>20)
    top, left = np.maximum(content.min(axis=0)-25,0)
    bottom, right = np.minimum(content.max(axis=0)+26,[preview.height,preview.width])
    preview = preview.crop((left,top,right,bottom))
    scale = min(840/preview.width,650/preview.height)
    preview = preview.resize((round(preview.width*scale),round(preview.height*scale)))
    position = (30+900*index+(840-preview.width)//2,110+(650-preview.height)//2)
    install.paste(preview,position)
    mark.text((25+900*index,65),"侧视：四隔柱与金属安装耳" if index==0 else "俯视：同轴孔与螺栓头",font=small,fill="#1c2935")
    if index == 1:
        # 从金色螺头的像素区域找标签锚点，几何正确性已由前面的STL切片验证。
        rgb = np.asarray(preview).astype(int)
        gold = (rgb[:,:,0]>110)&(rgb[:,:,1]>80)&(rgb[:,:,2]<100)&(rgb[:,:,0]>rgb[:,:,1]*1.05)
        remaining = set(map(tuple,np.argwhere(gold)))
        heads = []
        while remaining:
            start = remaining.pop()
            cluster, queue = [start], [start]
            while queue:
                y,x = queue.pop()
                for neighbor in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)):
                    if neighbor in remaining:
                        remaining.remove(neighbor)
                        cluster.append(neighbor)
                        queue.append(neighbor)
            if len(cluster)>5:
                heads.append(np.array(cluster).mean(axis=0)[::-1]+position)
        # 隐藏紧固件时仍能导出，只有恰好四个可见螺头才把尺寸线贴到渲染图上。
        if len(heads)==4:
            points = np.array(heads)
            origin = points.mean(axis=0)
            x0,y0 = points.min(axis=0)
            x1,y1 = points.max(axis=0)
            mark.line((origin[0]-12,origin[1],origin[0]+12,origin[1]),fill="#1e9665",width=3)
            mark.line((origin[0],origin[1]-12,origin[0],origin[1]+12),fill="#1e9665",width=3)
            mark.text(tuple(origin+[15,8]),"O (0,0)",font=small,fill="#1e8058")
            mark.line((x0,y0-35,x1,y0-35),fill="#b43d32",width=2)
            mark.text(((x0+x1)/2-38,y0-70),f"{pitch_x:g} mm",font=small,fill="#b43d32")
            mark.line((x1+35,y0,x1+35,y1),fill="#b43d32",width=2)
            mark.text((x1+43,(y0+y1)/2),f"{pitch_y:g} mm",font=small,fill="#b43d32")
            for point in points:
                number = 1+2*(point[0]>origin[0])+(point[1]>origin[1])
                mark.text(tuple(point+[12,4]),f"H{number}",font=small,fill="#b43d32")
# 维度文字与孔中心表均取实际网格，不能因用户改默认值而继续标旧孔距。
centers = np.array([hole["center_mm"] for hole in summary["mounting"]["actual_template_holes"]])
pitch_x, pitch_y = np.ptp(centers,axis=0)
mark.text((25,815),f"实测网格孔距 X={pitch_x:g} mm，Y={pitch_y:g} mm；默认四孔 X=±29，Y=±43。",font=small,fill="#1c2935")
mark.text((25,862),"金色：M2.5轴/头部与垫片占位；灰：金属隔柱与横梁；青：上层参考板。",font=small,fill="#1c2935")
mark.text((25,910),"原孔径：上层2.60 / 下层图示2.05；新件通孔3.0是设计间隙。下层连接类型待实物确认。",font=small,fill="#9a352c")
mark.text((25,958),"固定原点保持两板孔组对齐；原板外形中心各自偏置，车头方向仍为假设。",font=small,fill="#1c2935")
mark.text((25,1005),"仅几何与安装空间草案；先紧固安装耳再装斗，打印样板仅供对位，无载重验证。",font=small,fill="#9a352c")
install.save(out/"mount_installation.png")
summary["preview"] = "CAD 渲染，仅完成视觉布局检查；没有机械仿真或实物试装。"
(out / "geometry_report.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"PASS parameter change: plate width {default_width} -> {changed_width} mm")
print(f"Overview: {out / 'overview.png'}")
