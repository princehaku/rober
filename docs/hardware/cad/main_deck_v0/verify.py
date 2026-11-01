"""实际打印网格与可装配榫卯的轻量验证；几何证据不代表强度。"""
import json
import re
from pathlib import Path

import numpy as np
import trimesh

# 所有验收只读本轮输出，不加载旧整机结果或借用旧PASS。
ROOT = Path(__file__).resolve().parent


def loops(mesh, height, axis=2):
    # 三角面与平面逐边相交，不需要额外切片器或图算法依赖。
    # 指定不同切片轴可复用同一边界恢复逻辑。
    other = [i for i in range(3) if i != axis]
    # 使用五位小数焊接数值噪声，远小于0.2mm最小试配间隙。
    graph = {}
    # 避开与切面重合的面，只收集真正穿越平面的边。
    for tri in mesh.triangles:
        pts = []
        for a, b in [(0,1),(1,2),(2,0)]:
            u, v = tri[a], tri[b]
            if (u[axis]-height)*(v[axis]-height) < 0:
                p = u+(v-u)*(height-u[axis])/(v[axis]-u[axis])
                pts.append(tuple(np.round(p[other],5)))
        if len(pts)==2 and pts[0]!=pts[1]:
            a,b=pts
            graph.setdefault(a,set()).add(b)
            graph.setdefault(b,set()).add(a)
    # 每个点必须恰有两邻边，否则不能继续用不完整环拟合孔。
    assert graph and all(len(n)==2 for n in graph.values()), '切片边界未闭合'
    unseen, result = set(graph), []
    # 外轮廓和孔轮廓都保留，后续按奇偶判断实体占用。
    while unseen:
        start=next(iter(unseen))
        ring=[]
        prev,cur=None,start
        while cur not in ring:
            ring.append(cur)
            unseen.discard(cur)
            nxt=next(n for n in graph[cur] if n!=prev)
            prev,cur=cur,nxt
        result.append(np.array(ring))
    return result


def occupied(polygons, point):
    # 多个边界环按奇偶规则组合，孔内与外部都为空。
    x,y=point
    inside=False
    # 射线跨越奇数次表示实体内，凹窝和开槽同样适用。
    for ring in polygons:
        for p,q in zip(ring,np.roll(ring,-1,axis=0)):
            if (p[1]>y)!=(q[1]>y) and x<(q[0]-p[0])*(y-p[1])/(q[1]-p[1])+p[0]:
                inside=not inside
    return inside


def line_edges(mesh, z, y):
    # 水平截面再与一条直线相交，独立测量真实燕尾边界。
    # 只量交线坐标，不拿源参数文字作为接口检验。
    edges=[]
    for ring in loops(mesh,z):
        for a,b in zip(ring,np.roll(ring,-1,axis=0)):
            if (a[1]-y)*(b[1]-y)<0:
                edges.append(float(a[0]+(b[0]-a[0])*(y-a[1])/(b[1]-a[1])))
    return sorted(edges)


def verify_all(exe,out,temp,cad,regression):
    # 当前源与网格成对使用，回归另放临时目录。
    source=ROOT/'main_deck.scad'
    text=source.read_text(encoding='utf-8')
    # 当前生产参数来自源默认值；固定对照另显式传参，不覆盖用户输出。
    def param(name):
        return float(re.search(rf'^{name}\s*=\s*([-\d.]+)',text,re.M)[1])
    # 把打印坐标还原为共同四孔原点，避免居中变换掩盖偏置。
    t,c,g=param('panel_thickness'),param('fit_clearance'),param('seam_gap')
    bore=param('mount_hole')
    length,width,offset=param('deck_length'),param('deck_width'),param('body_offset_x')
    xs=[offset-length/2,-70,0,offset+length/2]
    panels=[]
    # 六片各有独立的裁切包围，不能以一整板替代分片检查。
    for i in range(6):
        m=trimesh.load_mesh(out/'print'/f'P{i+1}_panel.stl')
        col,row=i%3,i//3
        lo,hi=xs[col]+(g/2 if col else 0),xs[col+1]-(g/2 if col<2 else 0)
        yl,yh=(-width/2,g/-2) if row==0 else (g/2,width/2)
        # 逆向翻床变换，后续全部测量实际拼合后的STL坐标。
        m.vertices[:,0]+=(lo+hi)/2
        m.vertices[:,1]=-m.vertices[:,1]+(yl+yh)/2
        m.vertices[:,2]=t-m.vertices[:,2]
        # 绕X的180度旋转行列式为正，不能额外倒转三角面。
        assert m.is_winding_consistent and m.volume>0, '绕X旋转180度保持正向绕序'
        panels.append(m)
    # 多体拼装参考允许多实体，打印单体要求已在入口逐件执行。
    all_panels=trimesh.util.concatenate(panels)
    # 顶皮中部圆环恢复四孔中心和真实最小通径。
    # 小直孔在夹底内部切片，不能在工具窝高度误拟合大圆。
    holes=[]
    # 导入的是实际打印STL恢复的坐标，实体见证不另造简化接头。
    for i,m in enumerate(panels):
        for ring in loops(m,.73):
            # 最小二乘找圆心，再用半径离散度排除外框等非圆边界。
            solution=np.linalg.lstsq(np.c_[2*ring,np.ones(len(ring))],(ring**2).sum(axis=1),rcond=None)[0]
            center=solution[:2]
            radius=np.linalg.norm(ring-center,axis=1)
            if len(ring)>=40 and radius.std()<.01 and abs(radius.mean()-bore/2)<.02:
                # STL圆是多边形，同时记录外接径与真正最小通径。
                edges=np.roll(ring,-1,axis=0)-ring
                clearance=2*np.min(abs(edges[:,0]*(center[1]-ring[:,1])-edges[:,1]*(center[0]-ring[:,0]))/np.linalg.norm(edges,axis=1))
                holes.append({'panel':i+1,'center':center.round(5).tolist(),'diameter':float(2*radius.max()),'inscribed':float(clearance)})
    holes.sort(key=lambda h:h['center'])
    # 四轴安装事实独立固定；板中心参数不能改变四孔基准。
    expected=sorted([[x,y] for x in [-29,29] for y in [-43,43]])
    assert len(holes)==4,holes
    # 每轴逐一配对，可检测轴距正确但整体平移错误的情况。
    for h,p in zip(holes,expected):
        assert np.allclose(h['center'],p,atol=.001) and abs(h['diameter']-bore)<.002 and h['inscribed']>bore-.01,h
        # 三个高度测孔座圆环实体，保证不是仅顶皮薄孔。
        # 外周座取多个高度，确认不是只有薄皮圈出相似外观。
        m=panels[h['panel']-1]
        for z in [.17,5.17,t-.17]:
            rings=loops(m,z)
            for a in np.linspace(0,2*np.pi,25):
                assert occupied(rings,np.array(p)+10.5*np.array([np.cos(a),np.sin(a)])),(p,z,a)
    assert np.allclose(all_panels.bounds[:,:2],[[xs[0],-width/2],[xs[3],width/2]],atol=.001)
    # 窝底夹厚与工具径也测实际网格，外周全厚不等于全厚夹持。
    # 夹持厚度独立于全板厚度，适配用户约5mm外露短牙。
    clamp,well=param('clamp_thickness'),param('nut_well_diameter')
    # 窝底上下两切片确认台阶与薄底平座真实存在。
    for h in holes:
        m=panels[h['panel']-1]
        for z,empty_r in [(clamp-.1,1.4),(clamp+.1,well/2-.1)]:
            rings=loops(m,z)
            for a in np.linspace(0,2*np.pi,20):
                assert not occupied(rings,np.array(h['center'])+empty_r*np.array([np.cos(a),np.sin(a)]))
        assert occupied(loops(m,clamp-.1),np.array(h['center'])+[well/2-.1,0])
    print('PASS actual STL four axes 58x86; D3 bore; D22 full-height rim; 2mm clamp/D10 recess; offset',flush=True)
    # 桥键逆变换与面板不同，有耳件居中偏移也必须恢复。
    keys=[]
    for j in range(7):
        name=f'H{j+1}_bridge' if j<3 else f'V{j-2}_bridge'
        m=trimesh.load_mesh(out/'print'/f'{name}.stl')
        ear=(j==0 or j>=3)
        # 两端公差沿插入轴扣除，连接长度并非整列宽度。
        L=xs[j+1]-xs[j]-10 if j<3 else width/2-24
        m.vertices[:,0]+=5 if ear else 0
        m.vertices[:,1]+=L/2
        m.vertices[:,2]-=3
        # 所有槽键局部截面保持同一接口，可独立测斜壁与开口。
        edges=line_edges(m,3.13,15.17)
        half=3+4*3.13/6
        assert np.allclose(edges,[-9-half,-9+half,9-half,9+half],atol=.001),(j,edges)
        # XY交换或单轴反射才需要倒面，纯旋转无需倒面。
        if j<3:
            m.vertices[:,:2]=m.vertices[:,[1,0]]
            m.vertices[:,0]+=xs[j]
            m.faces=m.faces[:,::-1]
        else:
            seam=-70 if j<5 else 0
            sign=-1 if j%2==1 else 1
            m.vertices[:,0]+=seam
            m.vertices[:,1]=sign*(width/2-m.vertices[:,1])
            if sign==1:
                m.faces=m.faces[:,::-1]
        keys.append(m)
    # 用实际两邻片的反变换截面量女性槽，不接受参数echo冒充几何。
    # 每个接头都检查，不能只凭一套共用模块推断全部布局正确。
    for j in range(7):
        canonical=all_panels.copy()
        if j<3:
            canonical.vertices[:,0]-=xs[j]
            canonical.vertices[:,:2]=canonical.vertices[:,[1,0]]
        else:
            sign=-1 if j%2==1 else 1
            canonical.vertices[:,0]-=-70 if j<5 else 0
            canonical.vertices[:,1]=width/2-sign*canonical.vertices[:,1]
        # 在非三角顶点高度测横截面，避免共面浮点退化。
        edges=line_edges(canonical,3.13,15.17)
        half=3+4*3.13/6+c
        for target in [-9-half,-9+half,9-half,9+half]:
            assert min(abs(np.array(edges)-target))<.001,(j,target,edges)
    print(f'PASS actual STL dovetail: male 6->14x6, side clearance {c}, roof clearance {c}',flush=True)
    # 诊断从实际STL导入，避免源模块见证与用户产物发生漂移。
    for i,m in enumerate(panels):
        m.export(temp/f'p{i}.stl')
    for j,m in enumerate(keys):
        m.export(temp/f'k{j}.stl')
    def imp(name):
        return f'import("{(temp/name).as_posix()}");'
    def group(items):
        return 'union(){'+''.join(items)+'}'
    ps=group([imp(f'p{i}.stl') for i in range(6)])
    # 正碰撞和无碰撞使用同一导入流程，防止诊断入口始终空输出。
    def witness(name,body,positive=False):
        # 1mm³远处标记保证无碰撞时也生成非空STL；不修改生产几何。
        wrapper=temp/f'{name}.scad'
        wrapper.write_text('union(){translate([-500,-500,-500]) cube(1);'+body+'}',encoding='utf-8')
        target=temp/f'{name}.stl'
        cad(exe,target,source=wrapper)
        # 远处标记体积严格1，扣除后只剩待测交集的体积。
        value=float(trimesh.load_mesh(target).volume)-1
        assert value>.01 if positive else abs(value)<.003,(name,value)
        return round(value,6)
    # 整键包含耳，逐对检查交会，不只测槽体包围。
    # 完整键体含耳，接头交会不能仅比较燕尾槽的边界。
    pairs=[]
    for a in range(7):
        pairs.append('intersection(){'+ps+imp(f'k{a}.stl')+'}')
        for b in range(a+1,7):
            pairs.append('intersection(){'+imp(f'k{a}.stl')+imp(f'k{b}.stl')+'}')
    collision=witness('final_no_overlap',group(pairs))
    # 42个位置为离散插入采样，不能声称连续全程运动仿真。
    path=[]
    # 各列尚分离时先插H键，仅对应两面板构成障碍；之后V键从外缘插。
    for j in range(7):
        # 横键在独立列插；竖键同时面对面板和其余所有已装桥键。
        obstacles=group([imp(f'p{i}.stl') for i in ([j,j+3] if j<3 else range(6))]+
                        ([] if j<3 else [imp(f'k{k}.stl') for k in range(7) if k!=j]))
        L=xs[j+1]-xs[j]-10 if j<3 else width/2-24
        direction=np.array([-1,0,0]) if j<3 else np.array([0,-1 if j%2==1 else 1,0])
        for fraction in [1.1,.8,.5,.2,.03,0]:
            shift=(direction*L*fraction).tolist()
            path.append('intersection(){'+obstacles+f'translate({shift})'+imp(f'k{j}.stl')+'}')
    insertion=witness('insert_paths',group(path))
    # 插入状态的正约束：Z和跨缝位移会碰唇口，轴向退出由螺栓或实体端墙拦住。
    # 故意施加超出设计间隙的位移，必须出现实体阻挡才算有约束。
    locks={}
    for name,vec in [('z',[0,0,1]),('cross',[1,0,0])]:
        locks[name]=witness('lock_'+name,'intersection(){'+ps+f'translate({vec})'+imp('k3.stl')+'}',True)
    # 内部横键无需追加螺丝，但必须由邻列实体端墙正向封口。
    for j in [1,2]:
        locks[f'H{j+1}_wall']=witness(f'wall_{j}','intersection(){'+ps+'translate([-2,0,0])'+imp(f'k{j}.stl')+'}',True)
    # M3止退杆穿过真实耳孔，沿退出方向偏移后才会发生实体相撞。
    # 五孔不在板外空锁；逐点检查板法兰、键耳和下方维护通道。
    bolt_points=[[xs[0]+6,22],[-48,-width/2+6],[-48,width/2-6],[22,-width/2+6],[22,width/2-6]]
    for j,p in zip([0,3,4,5,6],bolt_points):
        dx=[-2,0,0] if j==0 else [0,-2 if j%2==1 else 2,0]
        shaft=f'translate([{p[0]},{p[1]},-3.2]) cylinder(d=3,h=3.4,$fn=48);'
        locks[f'key{j}_bolt']=witness(f'bolt_lock_{j}','intersection(){'+shaft+f'translate({dx})'+imp(f'k{j}.stl')+'}',True)
        # 上部孔来自实际面板；耳孔来自实际桥键，中心和实体包围同轴检查。
        # 空心中心与外围实体同时检查，避免只证明孔附近没有材料。
        for m,z,r in [(all_panels,t-2,1.6),(keys[j],-1.4,1.6)]:
            rings=loops(m,z)
            assert not occupied(rings,p)
            for a in np.linspace(0,2*np.pi,20):
                assert occupied(rings,np.array(p)+(r+.2)*np.array([np.cos(a),np.sin(a)])),(j,z,a)
        # 下部Ø8工具直达外露螺母，其他板键不得侵入，耳本身是夹紧接触面。
        tool=f'translate([{p[0]},{p[1]},-12]) cylinder(d=8,h=8.99,$fn=48);'
        witness(f'tool_{j}','intersection(){'+group([ps]+[imp(f'k{k}.stl') for k in range(7) if k!=j])+tool+'}')
    print('PASS actual STL final overlap/42 insertion stages; Z/cross locks; 2 wall stops; 5 bolt stops/tools',flush=True)
    # 试片与正式件截面都从实际STL量取，同模块并非唯一证据。
    # 三档试片各量截面，确保实际间隙不同且沿用正式件榫型。
    for cc in [.2,.3,.4]:
        left=trimesh.load_mesh(out/'coupons'/f'fit_{cc:.1f}_left.stl')
        left.vertices[:,0]-=14.15
        left.vertices[:,1]=18-left.vertices[:,1]
        left.vertices[:,2]=t-left.vertices[:,2]
        edge=line_edges(left,3.13,15.17)
        half=3+4*3.13/6+cc
        for target in [-9-half,-9+half]:
            assert min(abs(np.array(edge)-target))<.001
    # 翻床后任何非床面朝下表面都应为至少45度斜面，拒绝封闭水平悬顶。
    # 用法线找真实下悬面，明确排除只有已说明的安装窝环形桥。
    for folder in ['print','coupons']:
        for path in (out/folder).glob('*.stl'):
            m=trimesh.load_mesh(path)
            down=(m.face_normals[:,2]<-.001)&(m.triangles_center[:,2]>.005)
            # 仅安装窝底允许明确标出的水平环形桥，必须切片局部支撑并清理。
            bad=down&(m.face_normals[:,2]<-np.sqrt(.5)-.005)
            # 允许的例外只在夹底高度，其他隐藏平顶都必须失败。
            if bad.any():
                assert path.name.startswith('P') or path.stem=='mount_seat_first',path
                assert np.all(abs(m.triangles_center[bad,2]-(t-clamp))<.002),(path,m.triangles_center[bad])
    print('PASS coupon identity; dovetail slopes <=45deg; ONLY recessed seat rings need local support',flush=True)
    # 参数回归不写进用户生产目录，避免误选检查件打印。
    regress=[]
    if regression:
        # 固定回归只在临时目录，不改变生产输出或用户默认参数。
        from build import mesh_info
        # 同时验证公差和厚度的真实几何，不仅看参数回显。
        for label,defs in [('c02',['fit_clearance=0.2']),('c04',['fit_clearance=0.4']),('thick14',['panel_thickness=14','top_skin=5'])]:
            for pid in [2,12]:
                target=temp/f'{label}_{pid}.stl'
                cad(exe,target,[f'part_id={pid}']+defs)
                changed,info=mesh_info(target)
                if pid==2:
                    tt=14 if label=='thick14' else t
                    cc={'c02':.2,'c04':.4}.get(label,c)
                    changed.vertices[:,0]+=-35
                    changed.vertices[:,1]=-changed.vertices[:,1]-(width/2+g/2)/2
                    changed.vertices[:,2]=tt-changed.vertices[:,2]
                    measured=line_edges(changed,3.13,-width/2+15.17)
                    half=3+4*3.13/6+cc
                    for expected_edge in [-61-half,-61+half]:
                        assert min(abs(np.array(measured)-expected_edge))<.001,(label,measured)
                    assert not occupied(loops(changed,6+cc-.03),[-61,-width/2+15.17])
                    assert occupied(loops(changed,6+cc+.03),[-61,-width/2+15.17])
                    assert abs(info['size_mm'][2]-tt)<.001
                regress.append({'case':label,'part_id':pid,'size':info['size_mm']})
        # 超平台、薄槽顶、过大公差均必须报明确信息，不能空模型视为通过。
        import subprocess
        # 不可行参数应输出具体断言，绝不放大平台或丢掉检查。
        for label,d in [('oversize','deck_length=260'),('thin','panel_thickness=7'),('loose','fit_clearance=0.8')]:
            proc=subprocess.run([exe,'-o',str(temp/f'bad_{label}.stl'),'-D','part_id=2','-D',d,str(source)],capture_output=True,text=True,encoding='utf-8',errors='replace')
            diagnostic=proc.stdout+proc.stderr
            assert 'Assertion' in diagnostic and 'ERROR:' in diagnostic,(label,proc.returncode,diagnostic)
            regress.append({'case':label,'rejected':True,'returncode':proc.returncode})
        print('PASS parameter c0.2/c0.4/thickness14; oversize/thin/loose rejected',flush=True)
    return {'four_holes':holes,'body_offset_x':offset,'seam_gap':g,'side_and_roof_clearance':c,
            'final_overlap_volume':collision,'insertion_overlap_volume':insertion,'positive_lock_volumes':locks,
            'load_path':'X负端列P1/P4→X=-70双燕尾→中列P2/P5→X=-29孔座；中列/X正端列各两柱；未验证承载',
            'mounting':{'clamp_thickness':clamp,'well_diameter':well,'user_approx_stud':5,'washer_design':.5,'nut_design':2,
                        'nominal_remaining_thread':5-clamp-.5-2,'local_support_required':True},
            'regressions':regress,'boundary':'几何/文件验证，未切片/实打/逐级加载'}
