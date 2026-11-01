"""验证Tina2C生产分片与实际拼合几何，不生成或修补CAD模型。"""
import ast
import json
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont


# 截面奇偶判定避免引入射线加速/科学计算依赖，孔与实体外部均为空间开放。
def inside(point,polygons):
    # 分别处理每个闭环，实体轮廓与内部孔的奇偶交叉自然互相抵消。
    occupied = False
    for polygon in polygons:
        a,b = polygon,np.roll(polygon,-1,axis=0)
        hits = ((a[:,1]>point[1])!=(b[:,1]>point[1])) & (point[0]<(b[:,0]-a[:,0])*(point[1]-a[:,1])/(b[:,1]-a[:,1]+1e-20)+a[:,0])
        occupied ^= bool(np.count_nonzero(hits)%2)
    return occupied


# 独立恢复顶点连接组，生产件只能是一个实体，参考装配允许多个实体。
def components(mesh):
    # 合并三角面共享顶点，检测零件有没有意外断成两块打印孤岛。
    parents = list(range(len(mesh.vertices)))
    def root(i):
        # 压缩父链降低密集孔槽网格的重复查找成本。
        while parents[i]!=i:
            parents[i]=parents[parents[i]]
            i=parents[i]
        return i
    for face in mesh.faces:
        # 三角面三点必须归同组，禁止只按包围框接近就认为相连。
        for vertex in face[1:]:
            parents[root(int(vertex))]=root(int(face[0]))
    return len({root(i) for i in range(len(parents))})


# 把实际三角面裁到搭接内部，测接触面Z；肩侧间隙单独从截面测量。
def overlap_z(mesh,start,end):
    # 不要求顶点恰好落在检测带里，面内插值也会参与接触测量。
    points=[]
    for triangle in mesh.triangles:
        polygon=list(triangle)
        for limit,sign in ((start,1),(end,-1)):
            # 依次裁掉带外的两侧，保留真实三角面在搭接内部的部分。
            clipped=[]
            for a,b in zip(polygon,polygon[1:]+polygon[:1]):
                ia,ib=(a[1]-limit)*sign>=0,(b[1]-limit)*sign>=0
                if ia: clipped.append(a)
                if ia!=ib: clipped.append(a+(b-a)*(limit-a[1])/(b[1]-a[1]))
            polygon=clipped
            if not polygon: break
        points.extend(polygon)
    assert points,"搭接区没有实体表面"
    return np.min(points,axis=0)[2],np.max(points,axis=0)[2]


# 按孔环包围框找槽孔，切片结果来自STL，不拿参数文字冒充实测。
def require_feature(polygons,center,size):
    # 长槽用轴对齐的宽高识别，避免把邻近圆孔误当作设备槽。
    matches=[]
    for polygon in polygons:
        # 测量闭环极值和中心，能同时发现缩放、反向和偏置错误。
        bounds=np.array([polygon.min(axis=0),polygon.max(axis=0)])
        if np.allclose(bounds.mean(axis=0),center,atol=0.003) and np.allclose(bounds[1]-bounds[0],size,atol=0.003):
            matches.append(bounds.tolist())
    assert len(matches)==1,('孔槽不匹配',center,size)
    return matches[0]


def verify_split(out,slice_mesh):
    # 入口由原验证链调用，输出目录可为用户自选或临时回归目录。
    out=Path(out)
    # 参数清单提供当前尺寸和坐标映射，所有结果仍对真实网格独立核对。
    params={}
    for line in (out/'split_parameters.echo').read_text(encoding='utf-8').splitlines():
        if line.startswith('ECHO: '):
            record=ast.literal_eval(line[6:])
            params[record[0]]=record[1:]
    report={'parameters':params,'production':{},'interfaces':{}}
    assembled={}
    # 明确四个生产名，禁止自动把装配参考或诊断网格收为可打印件。
    names=('lidar_lower','lidar_upper','base_lower','base_upper')
    for name in names:
        mesh=trimesh.load(out/'tina2c'/f'{name}.stl',force='mesh')
        record={'extents_mm':np.round(mesh.extents,4).tolist(),'volume_mm3':round(float(mesh.volume),3),
                'faces':len(mesh.faces),'watertight':bool(mesh.is_watertight),'consistent':bool(mesh.is_winding_consistent),
                'components':components(mesh),'min_z_mm':float(mesh.bounds[0,2])}
        # 90毫米预算只用于新生产半片，原98毫米四孔样板维持已有证据边界。
        assert record['watertight'] and record['consistent'] and record['components']==1 and mesh.volume>0
        assert np.all(mesh.extents[:2]<=90.001) and mesh.extents[2]<=100.001
        assert abs(mesh.bounds[0,2])<0.001
        # 平底面积与零高度一起检查，避免一个尖点落零却让主体悬空。
        bottom=np.abs(mesh.triangles[:,:,2]).max(axis=1)<1e-5
        record['bed_area_mm2']=round(float(mesh.area_faces[bottom].sum()),3)
        assert record['bed_area_mm2']>100,'没有可信的平底落床面'
        report['production'][name]=record
        # 改变的是测量副本，原STL不会被验证脚本重新保存或修网格。
        # 高舌片执行打印翻面的严格逆变换，重新回到原板坐标。
        restored=mesh.copy()
        if name.startswith('lidar'):
            # 每块板厚与居中量读当前清单，95/100柱距都使用同一检查链。
            thickness=params['lidar_size'][2]
            shift=params['print_shifts'][1 if name.endswith('upper') else 0]
        else:
            thickness=params['base_size'][2]
            shift=params['print_shifts'][2]
        if name.endswith('upper'):
            # 原顶面落床的高舌片，逆变换后再次位于板原始Z范围。
            restored.vertices[:,1]=shift-restored.vertices[:,1]
            restored.vertices[:,2]=thickness-restored.vertices[:,2]
            # 两轴翻转保持正行列式，不改变封闭网格的外向法线。
        else:
            restored.vertices[:,1]-=shift
        assembled[name]=restored
        print('PASS split production',name,record)

    # 分片实际接触面贴合，肩部XY余量从上下两种截面独立计算。
    for family in ('lidar','base'):
        # 家族间共用验收算法，但尺寸和孔位各自独立核对。
        lower,upper=assembled[family+'_lower'],assembled[family+'_upper']
        t=params[family+'_size'][2]
        start,end=params['lidar_lap'][:2] if family=='lidar' else (-8,8)
        zlower=overlap_z(lower,start+0.2,end-0.2)
        zupper=overlap_z(upper,start+0.2,end-0.2)
        # Z必须贴合，不能用预留空气层来规避相交检测。
        assert abs(zlower[1]-t/2)<0.001 and abs(zupper[0]-t/2)<0.001
        assert abs(zupper[0]-zlower[1])<0.001,'Z搭接面存在空气层或穿透'
        low_top=slice_mesh(lower,t*0.75,True)
        up_top=slice_mesh(upper,t*0.75,True)
        low_bottom=slice_mesh(lower,t*0.25,True)
        up_bottom=slice_mesh(upper,t*0.25,True)
        gap_start=min(p[:,1].min() for p in up_top)-max(p[:,1].max() for p in low_top)
        gap_end=min(p[:,1].min() for p in up_bottom)-max(p[:,1].max() for p in low_bottom)
        # 高低两种截面分别测两肩，防止只检查其中一边余量。
        assert np.allclose([gap_start,gap_end],params['clearances'][0],atol=0.002)
        # 四个实际圆孔中心来自切片拟合，验证穿栓同轴及通孔尺寸。
        targets=[[-params['lidar_lap'][2],params['lidar_lap'][3]],[params['lidar_lap'][2],params['lidar_lap'][3]]] if family=='lidar' else [[-15,0],[-1,0]]
        holes=[]
        # 分别测低舌和高舌的圆孔，螺栓能通过两半才算同轴。
        for half,z in ((lower,t*0.25),(upper,t*0.75)):
            candidates=slice_mesh(half,z)
            selected=[]
            for target in targets:
                # 穿孔既要对中心，也要对真实直径，不能只见孔就通过。
                matches=[h for h in candidates if np.allclose(h['center_mm'],target,atol=0.002)]
                assert len(matches)==1,(family,target,'拼接口未同轴')
                assert abs(matches[0]['circumdiameter_mm']-params['clearances'][1])<0.015
                selected.append(matches[0])
            holes.append(selected)
        report['interfaces'][family]={'z_contact_mm':t/2,'xy_shoulder_gaps_mm':[round(gap_start,4),round(gap_end,4)],'holes':holes}

    # 雷达四个设备槽和两立柱槽仍位于原坐标，线缆孔没有被拼接挡住。
    dx,dy,travel,hole,spacing,foot_x,foot_d=params['local_features']
    # 设备槽与柱孔始终回到装配坐标，不拿打印居中后的坐标冒充孔距。
    t=params['lidar_size'][2]
    low=slice_mesh(assembled['lidar_lower'],t*0.25,True)
    high=slice_mesh(assembled['lidar_upper'],t*0.75,True)
    device_bounds=[]
    for x in (-dx/2,dx/2):
        # 四设备槽全在低半片完整厚度区，逐一保留原始中心和长轴长度。
        for y in (-dy/2,dy/2): device_bounds.append(require_feature(low,[x,y],[travel+hole,hole]))
    # 实际全厚肩位置减去设备槽顶缘，独立验证100柱距的薄肩修复。
    full_section=slice_mesh(assembled['lidar_lower'],t*0.75,True)
    material_margin=max(p[:,1].max() for p in full_section)-max(bounds[1][1] for bounds in device_bounds)
    assert material_margin>=1.199,'设备槽到实际全厚肩的材料余量不足1.2毫米'
    report['lidar_device_to_shoulder_margin_mm']=round(float(material_margin),4)
    require_feature(low,[0,-spacing/2],[12.5,4.5])
    require_feature(high,[0,spacing/2],[12.5,4.5])
    require_feature(low,[-params['lidar_size'][0]/2+8,0],[8,8])
    # 线缆通道与拼接头互相独立，不能为加连接件把线缆出口封死。
    # 底座两柱脚孔也从拼合后的上下实体分别读取，避免翻面反向。
    bt=params['base_size'][2]
    require_feature(slice_mesh(assembled['base_lower'],bt*0.25,True),[foot_x,-spacing/2],[foot_d,foot_d])
    require_feature(slice_mesh(assembled['base_upper'],bt*0.75,True),[foot_x,spacing/2],[foot_d,foot_d])

    # 精确CSG相交见证块体积为1，扣除后必须无正体积碰撞，允许接触面共享。
    for name in ('lidar_overlap_check','base_overlap_check','base_metal_collision_check'):
        # 诊断只去掉明确的微米级接触壳，不跳过生产实体或正体积穿透。
        witness=trimesh.load(out/f'{name}.stl',force='mesh')
        assert witness.is_watertight and abs(witness.volume-1)<0.0001,(name,witness.volume)
        report[name]={'positive_intersection_mm3':round(float(witness.volume-1),6)}
    report['intersection_contact_tolerance_mm']=params['contact_tolerance'][0]
    assert abs(params['install'][0]-params['install'][2])<0.001
    assert abs(params['install'][1]-params['install'][0]-bt)<0.001
    # 这个高度关系对应已修复的130板底/136柱脚，设备上表面高度保持不变。

    # 雷达占位及M3头/垫片/工具的圆包络由实际孔中心核对，保留至少0.5净距。
    lidar_centers=report['interfaces']['lidar']['holes'][0]
    minimum=min(np.linalg.norm(h['center_mm'])-32.5-params['clearances'][2]/2 for h in lidar_centers)
    # 工具圆包络比头部和垫片更大，因此通过它也覆盖这两种占位外形。
    assert minimum>0.5
    report['lidar_tool_clearance_to_65_mm']=round(float(minimum),4)
    # 下方工具圆盘在实际金属框架截面中必须开放，检查螺母所在的高度。
    frame=trimesh.load(out/'mount_frame_reference_check.stl',force='mesh')
    metal=slice_mesh(frame,params['install'][0]-100-2,True)
    # 框架检查网格统一下移100，测量高度也相应换算，避免误查到空层。
    for center in report['interfaces']['base']['holes'][0]:
        world=np.array(center['center_mm'])+params['base_world_xy']
        for radius in (0,2,params['clearances'][2]/2):
            # 同时采圆心和多圈，捕捉螺母中部被梁占住的情况。
            for angle in np.linspace(0,2*np.pi,33):
                assert not inside(world+radius*np.array([np.cos(angle),np.sin(angle)]),metal),'底座螺母工具被金属梁封堵'
    # 旧加长板/改距工具窗仍检查真实网格，生产90毫米规则不套到参考件。
    long=trimesh.load(out/'sensor_adapter_long_check.stl',force='mesh')
    long_polygons=slice_mesh(long,bt*0.37,True)
    # 加长参考件可超平台，但底盘工具窗口仍需要保持原有可达性。
    for x in (-34,34):
        for y in (-48,48):
            for angle in np.linspace(0,2*np.pi,49):
                assert not inside(np.array([x,y])+4.95*np.array([np.cos(angle),np.sin(angle)]),long_polygons)
    print('PASS split interfaces: original slots/columns, coincident M3 axes, Z contact, XY clearance, no positive overlap')
    print('PASS split access: lidar envelope, base nut tools, 130/136 metal contact, 140 mm reference tools')

    # 单独清单防止用户把整板参考或检查网格送进切片器，翻面已在STL完成。
    # 打印朝向与取件后的装配翻面分开说明，避免新手把高舌再次立起切片。
    lines=['# Tina2C生产分片清单','','四个STL逐个导入、分别打印，每片1件；示意图的四张灰色平面是四次独立摆盘，不要把四件放进同一张100×100盘。保持mm、100%和STL原方向，高舌片已翻面落床，切片时不要再翻。取件装配时将upper翻回，让其台阶朝下，与lower朝上的台阶相搭，孔对齐且板面平齐后紧固。','', '| 文件 | 数量 | 实测尺寸mm |','|---|---:|---|']
    lines += [f"| {name}.stl | 1 | {' × '.join(str(v) for v in report['production'][name]['extents_mm'])} |" for name in names]
    # 清单只列本轮新增接头件数，底盘既有M2.5不会被误换成M3。
    lines += ['', '接头M3螺栓4、螺母4、垫片8，头上母下各一垫片（设计选择，规格/长度采购后复核）；底盘M2.5沿用。本目录没有检查件，金属主架及2kg承载未验证。','']
    (out/'tina2c'/'PRINT_LIST.md').write_text('\n'.join(lines),encoding='utf-8')
    (out/'split_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

    # 仅拼接实际CAD渲染图，分别看打印面、上螺头和下螺母；不生成替代几何。
    # 图片只做标签排版，所有可见零件均取实际OpenSCAD渲染。
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',23)
    overview=Image.new('RGB',(1800,650),'#f4f5f7')
    draw=ImageDraw.Draw(overview)
    for index,(file,title) in enumerate((('split_print_raw.png','打印：四片各1，保持原方向'),('split_assembly_raw.png','装配上侧：雷达旁M3螺头'),('split_underside_raw.png','装配下侧：外露螺母与金属梁'))):
        image=Image.open(out/file).convert('RGB')
        # 去除纯背景后放大机械主体，缩小图像也能辨认搭接方向。
        pixels=np.array(image).astype(int)
        content=np.argwhere(np.max(abs(pixels-pixels[0,0]),axis=2)>20)
        top,left=np.maximum(content.min(axis=0)-12,0)
        bottom,right=np.minimum(content.max(axis=0)+13,[image.height,image.width])
        image=image.crop((left,top,right,bottom))
        scale=min(580/image.width,440/image.height)
        image=image.resize((round(image.width*scale),round(image.height*scale)))
        overview.paste(image,(index*600+(600-image.width)//2,60+(440-image.height)//2))
    # 所有图片贴完后重建画笔，避免后续paste影响已画文字的缓冲。
    draw=ImageDraw.Draw(overview)
    for index,title in enumerate(('四件分别摆盘（各1）','装配上侧：M3螺头','装配下侧：螺母与梁')):
        draw.text((12+index*600,12),title,font=font,fill='#203343')
    small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',19)
    lidar_low=report['production']['lidar_lower']['extents_mm']
    lidar_up=report['production']['lidar_upper']['extents_mm']
    base=report['production']['base_lower']['extents_mm']
    # 图中尺寸读本轮网格，改柱距后不会继续标注旧尺寸。
    dimensions=lambda values:'×'.join(f'{value:g}' for value in values)
    draw.text((12,520),f"雷达低舌{dimensions(lidar_low)} / 高舌{dimensions(lidar_up)} mm",font=small,fill='#203343')
    draw.text((12,552),f"底座低/高舌均{dimensions(base)} mm，各1",font=small,fill='#203343')
    draw.text((612,520),'M3头上、母下；设备孔/柱孔保留原坐标',font=small,fill='#203343')
    draw.text((1212,520),'底座放在梁顶；下螺母工具避开横梁',font=small,fill='#203343')
    draw.text((15,602),'四灰盘代表分别打印，每片1件；M3为设计占位，未切片/实打或强度验证。',font=font,fill='#98342c')
    overview.save(out/'split_overview.png')
    return report
