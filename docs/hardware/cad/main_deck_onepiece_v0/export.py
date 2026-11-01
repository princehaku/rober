"""导出单件与两张真实网格预览，轻量核查四座及填回区域。"""
import argparse
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image, ImageChops, ImageDraw, ImageFont

# 所有输出路径从源文件解析，换cwd不会导入错误目录的模型。
ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'main_deck_onepiece.scad'


def cad(exe,target,source,extra):
    # 参数数组不经过第二层shell；中文诊断同时读取两个输出流。
    result=subprocess.run([exe,'-o',str(target),*extra,str(source)],capture_output=True,
                          text=True,encoding='utf-8',errors='replace')
    msg=result.stdout+result.stderr
    assert result.returncode==0 and 'ERROR:' not in msg,(target,result.returncode,msg)
    # 返回零但没有输出也视为失败，禁止旧空文件被当作成功。
    assert target.exists() and target.stat().st_size>0,target
    return result.returncode


def section(mesh,z):
    # 直接求实际三角网格截面，不用源参数回显替代孔位测量。
    graph={}
    # 空间邻格只合并截面数值误差，容差远低于打印分辨率。
    cells={}
    def weld(point):
        # 邻格搜索避免四舍五入边界把相距0.00001mm的同一切点拆开。
        # 不直接四舍五入，避免同一交点恰跨舍入网格边界。
        key=np.floor(point*10000).astype(int)
        for dx in [-1,0,1]:
            for dy in [-1,0,1]:
                for old in cells.get((key[0]+dx,key[1]+dy),[]):
                    if max(abs(point-np.array(old)))<.0001:return old
        # 首个坐标作为该交点的代表，不改变输入三角网格。
        value=tuple(point)
        cells.setdefault(tuple(key),[]).append(value)
        return value
    # 排除与切面平行边，当前高度也避开所有实体顶底平面。
    for tri in mesh.triangles:
        points=[]
        for a,b in [(0,1),(1,2),(2,0)]:
            p,q=tri[a],tri[b]
            if (p[2]-z)*(q[2]-z)<0:
                point=p+(q-p)*(z-p[2])/(q[2]-p[2])
                # 仅焊接截面临时点，不修补或移动生产STL顶点。
                points.append(weld(point[:2]))
        if len(points)==2 and points[0]!=points[1]:
            p,q=points
            graph.setdefault(p,set()).add(q)
            graph.setdefault(q,set()).add(p)
    # 每点恰有两邻边才可恢复闭环，避免在破面上继续拟合圆。
    assert graph and all(len(v)==2 for v in graph.values())
    # 每个闭环独立保留，孔和外围后续按奇偶规则区分。
    unseen=set(graph)
    rings=[]
    # 遍历到已见顶点结束，不按三角面排列猜轮廓连接顺序。
    while unseen:
        cur=next(iter(unseen))
        prev=None
        ring=[]
        while cur not in ring:
            ring.append(cur)
            unseen.discard(cur)
            nxt=next(v for v in graph[cur] if v!=prev)
            prev,cur=cur,nxt
        rings.append(np.array(ring))
    return rings


def solid(rings,p):
    # 奇偶规则同时处理外围与圆孔，测试实体点而非仅包围框。
    x,y=p
    inside=False
    for ring in rings:
        for a,b in zip(ring,np.roll(ring,-1,axis=0)):
            if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:
                inside=not inside
    return inside


def circles(rings,radius):
    # 外接径与最小通径都记录，STL圆离散化不等于打印孔径补偿。
    result=[]
    # 只接受小圆环，长矩形外框不能通过半径离散度门限。
    for p in rings:
        s=np.linalg.lstsq(np.c_[2*p,np.ones(len(p))],(p*p).sum(axis=1),rcond=None)[0]
        center=s[:2]
        radii=np.linalg.norm(p-center,axis=1)
        # 至少40点为本稿48边圆的可信证据，短直边不误当圆孔。
        if len(p)>=40 and radii.std()<.015 and abs(radii.mean()-radius)<.03:
            # 直径受STL多边形内切影响，记录最窄通道供孔径校准。
            e=np.roll(p,-1,axis=0)-p
            d=2*np.min(abs(e[:,0]*(center[1]-p[:,1])-e[:,1]*(center[0]-p[:,0]))/np.linalg.norm(e,axis=1))
            result.append({'center':center.round(5).tolist(),'outer_diameter':float(2*radii.max()),'minimum_diameter':float(d)})
    return sorted(result,key=lambda x:x['center'])


def compose_preview(out,length,width,t):
    # 标注只裁背景/加文字，不补画CAD没有的支撑或紧固件。
    # 显示为安装姿态，避免读者将打印翻面误认成顶底设计错误。
    canvas=Image.new('RGB',(1440,740),'white')
    draw=ImageDraw.Draw(canvas)
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',22)
    draw.text((22,12),f'一体底座代打稿 · {length:g}×{width:g}×{t:g} mm · 1件 / 比例100% / PLA试装',(25,40,50),font=font)
    for i,(name,label) in enumerate([('top','安装顶面：四个下沉螺母窝'),('bottom','背面：整体厚肋，无分缝 / 燕尾槽 / 止退孔')]):
        im=Image.open(out/f'{name}.png').convert('RGB')
        mask=ImageChops.difference(im,Image.new('RGB',im.size,im.getpixel((0,0)))).convert('L').point(lambda v:255 if v>18 else 0)
        box=mask.getbbox()
        if box:im=im.crop((max(box[0]-15,0),max(box[1]-15,0),min(box[2]+15,im.width),min(box[3]+15,im.height)))
        im.thumbnail((700,490))
        canvas.paste(im,(i*720+(720-im.width)//2,80+(490-im.height)//2))
        draw.text((i*720+18,54),label,(25,40,50),font=font)
    draw.text((22,590),'四轴58×86 · Ø3通孔 · Ø22外圈 / Ø10顶窝 / 2mm夹底 · 原柱外牙约5mm需先试座',(25,40,50),font=font)
    draw.text((22,635),'200×160超Tina2C100³；STL已顶面朝床，四窝内局部支撑需清理；无切片 / 实打 / 承载验证',(25,40,50),font=font)
    draw.text((22,680),'2kg为垃圾目标；垃圾＋斗架/执行器等总附加载荷未验证，不代表已经可以上车负载',(25,40,50),font=font)
    canvas.save(out/'overview.png')


def run():
    parser=argparse.ArgumentParser()
    parser.add_argument('--openscad',required=True)
    parser.add_argument('--output',type=Path,default=ROOT/'exports')
    args=parser.parse_args()
    # 输出目录可显式指定，默认只写本一体版目录。
    out=args.output.resolve()
    out.mkdir(parents=True,exist_ok=True)
    # 当前源参数用于期望值，实际孔轴仍从输出网格测得。
    text=SOURCE.read_text(encoding='utf-8')
    # 用户可在Customizer改默认值，检测值从当前源读取，不硬锁成200。
    def p(name):return float(re.search(rf'^{name}\s*=\s*([-\d.]+)',text,re.M)[1])
    length,width,t,clamp=p('deck_length'),p('deck_width'),p('panel_thickness'),p('clamp_thickness')
    offset=p('body_offset_x')
    # 以孔组原点列出四轴，外形偏置不能吞掉这一独立基准。
    axes=sorted([[x,y] for x in [-p('mount_pitch_x')/2,p('mount_pitch_x')/2] for y in [-p('mount_pitch_y')/2,p('mount_pitch_y')/2]])
    # 只生成这一件实际打印姿态STL，不生成桥键或整机参考网格。
    path=out/'main_deck_onepiece.stl'
    cad(args.openscad,path,SOURCE,['--export-format','binstl','-D','part_id=1'])
    # 只焊接重复顶点，不自动补洞或做形状修复。
    mesh=trimesh.load_mesh(path,process=True)
    # 面邻接并查集不依赖scipy，要求共享边的单个封闭实体。
    parent=np.arange(len(mesh.faces))
    def root(i):
        while parent[i]!=i:
            parent[i]=parent[parent[i]]
            i=parent[i]
        return i
    for a,b in mesh.face_adjacency:parent[root(a)]=root(b)
    # 单体、封闭、正体积和绕序分别检查，任何一项失败即停。
    count=len({root(i) for i in range(len(parent))})
    assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume>0 and count==1
    # 厚肋圆端越界会在这里直接失败，不能靠预览隐藏。
    assert np.allclose(mesh.extents,[length,width,t],atol=.001) and abs(mesh.bounds[0,2])<.001
    assert abs(mesh.bounds[:,0].mean()-offset)<.001
    print('PASS mesh:',mesh.extents.round(5).tolist(),'watertight/consistent/positive/single/Z0',flush=True)
    # 绕X旋转两次还原安装姿态，行列式为正，不反转面绕序。
    # JSON孔坐标统一用安装姿态，STL本身已按打印姿态摆放。
    world=mesh.copy()
    world.vertices[:,1]*=-1
    world.vertices[:,2]=t-world.vertices[:,2]
    assert world.volume>0 and world.is_winding_consistent
    # 低切片测直通孔，高切片测同轴工具窝。
    low=section(world,clamp/2)
    high=section(world,clamp+.17)
    bores=circles(low,p('mount_hole')/2)
    wells=circles(high,p('nut_well_diameter')/2)
    assert len(bores)==len(wells)==4
    # 四座逐一配对，可发现孔距正确而整体平移错误的问题。
    for a,b,xy in zip(bores,wells,axes):
        assert np.allclose(a['center'],xy,atol=.001) and np.allclose(b['center'],xy,atol=.001)
        assert abs(a['outer_diameter']-p('mount_hole'))<.002 and abs(b['outer_diameter']-p('nut_well_diameter'))<.002
        # 三个高度检验外圈实体连续到顶，不能只留下顶面薄皮。
        for z in [clamp-.03,clamp+.03,t-.17]:
            rings=section(world,z)
            # 平座台阶上下状态相反，夹底不能只凭一段圆柱外观确认。
            assert solid(rings,np.array(xy)+[3,0])==(z<clamp)
            for angle in np.linspace(0,2*np.pi,20):
                assert solid(rings,np.array(xy)+10.5*np.array([np.cos(angle),np.sin(angle)]))
    print('PASS actual sections: four axes 58x86, D3/D10, 2mm clamp, D22 outer rim',flush=True)
    # 在旧七槽两侧男性截面位置测实体，证明没有沿用含槽carved_deck。
    # 七个旧槽各测两个被挖空的榫型位置，填回才应为实体。
    slot_points=[]
    for x in [-122.641541,-70,0]:
        slot_points += [[x+15.17,u] for u in [-9,9]]
    for x in [-70,0]:
        slot_points += [[x+u,y] for u in [-9,9] for y in [-64.83,64.83]]
    for xy in slot_points:assert solid(section(world,3.13),xy),('残留旧槽',xy)
    # 五止退孔原位置应在高低两层均为实体，连沉头锥也完全填回。
    # 这些仅是旧孔位置的诊断坐标，一体源不再生成相应孔。
    stops=[[-116.641541,22],[-48,-74],[-48,74],[22,-74],[22,74]]
    for z in [.73,t-.73]:
        rings=section(world,z)
        for xy in stops:
            for a in np.linspace(0,2*np.pi,16):assert solid(rings,np.array(xy)+1.5*np.array([np.cos(a),np.sin(a)]))
    # 原分缝两侧与中心都应连续，顶部整皮只允许四个安装窝开口。
    skin=section(world,t-.3)
    for x in [-70,0]:
        for y in np.linspace(-77,77,31):
            for dx in [-.2,0,.2]:assert solid(skin,[x+dx,y])
    for x in np.linspace(offset-length/2+3,offset+length/2-3,41):assert solid(skin,[x,0])
    # 顶皮只允许四个圆窝，额外闭环说明仍有遗留开口。
    assert len(skin)==5,'顶面除了外边界应只有四个安装窝'
    print('PASS filled: old 7 slots, 5 stop holes, all former seams; only 4 mounting interfaces',flush=True)
    # 报告绑定实际源/打印STL，源坐标与打印翻面明确区分。
    # 源和STL哈希随JSON保存，便于代打前确认文件版本一致。
    report={'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'stl_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'size_mm':mesh.extents.tolist(),'volume_mm3':float(mesh.volume),'watertight':bool(mesh.is_watertight),
            'winding_consistent':bool(mesh.is_winding_consistent),'components':count,'z_min':float(mesh.bounds[0,2]),
            'body_offset_x':offset,'bores':bores,'wells':wells,'clamp_thickness':clamp,
            'old_slot_sample_count':len(slot_points),'old_stop_holes_filled':5,'former_seams_filled':True,
            'print_pose':'安装顶面朝床；还原安装姿态为绕X180后上移板厚，四窝底需局部支撑',
            'boundary':'PLA代打试装稿；外牙约5mm/螺母啮合/柱高/总载荷均待实配，非承载批准'}
    (out/'dimensions.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    # 从实际STL渲染两面，显式相机确保完整轮廓，不依赖自动取景。
    with tempfile.TemporaryDirectory(prefix='rober-onepiece-') as tmp:
        wrapper=Path(tmp)/'view.scad'
        wrapper.write_text(f'color("#70a4bd") translate([0,0,{t}]) rotate([180,0,0]) import("{path.as_posix()}");',encoding='utf-8')
        # 使用相同视距与中心，两个视图都应留足背景而不裁边。
        for name,angle in [('top',60),('bottom',130)]:
            cad(args.openscad,out/f'{name}.png',wrapper,['--imgsize=1200,900','--projection=o','--colorscheme=Tomorrow',f'--camera={offset},0,6,{angle},0,25,560'])
    compose_preview(out,length,width,t)
    print('PASS two CAD views rc0/no ERROR; onepiece export complete',flush=True)


if __name__=='__main__':run()
