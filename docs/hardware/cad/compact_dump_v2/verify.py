"""小后卸斗离散几何、传感器占位和条件倾覆力矩筛查。"""
# 数值报告将几何、视线、材料包络和稳定性边界分开保存。
# 通过几何检查不代表可以打印、上车或装载目标质量。
# 厂家STL只用来建立包含车体与轮胎的保守障碍。
# 厂家外包络不作为轮胎支撑多边形使用。
# 车尾筛查边X=-75是显式假设，仍需实车接地测量。
# 原车0.7kg为用户实测输入，代码不会据此猜重心位置。
# 未称重的新附件不计成已获得的抗倾覆力矩。
# 条件恢复矩的单位为kg·mm，数值不能当电机推力规格。
# 局部偏载点随斗旋转，其法向高度不同于竖直落料框高度。
# 每种偏载点在全角域取最坏值，并另存终点供核对。
# 垃圾真正滑动路径未知，固定点包络只用于风险筛查。
# 指定测试块是刚体，垃圾袋柔性、摩擦、卡塞没有被模拟。
# 材料沿真实折线轮廓越过后缘后才竖落，避免穿过固定斜壁。
# 最后接触地面属于路径终点，不生成接触动力学结论。
# 50mm与70mm通道需要分别报告，失败项不能被总通过掩盖。
# 固定斜壁与底板共享完整底面，连接区属于同一刚体。
# 实际转动公差和紧固件不在这一级模型的验收范围。
# 设备盒和圆柱都是占位，真实型号替换后必须重新计算。
# 低塔允许卸料遮挡雷达，运输姿态仍须有正的扫描净空。
# 扫描遮挡结果只描述几何，驻车和导航互锁尚未写入软件。
# 相机检查使用显式假设视锥，不能当镜头厂家验收结果。
# 杆件采用完整胶囊半径，电机段单独用较大半径计算。
# 两侧主轴支撑都检查，不用对称假设跳过实体圆端半径。
# 去程和回程独立计算，检查执行器端点和长度能否回到原点。
# 解析公式与源参数绑定，不能以旧JSON证明新参数正确。
# 非法配置必须明确失败，防止调参后仍显示错误通过状态。
from pathlib import Path
import hashlib
import importlib.util
import json
import math
import re
import numpy as np
import trimesh

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'compact_dump.scad'
REPO=ROOT.parents[3]
# 复用已审的盒顶点和线段到盒距离算法，不复用被否决的大斗参数。
spec=importlib.util.spec_from_file_location('cad_distance',ROOT.parent/'dump_kinematics_v1/verify.py')
distance=importlib.util.module_from_spec(spec)
spec.loader.exec_module(distance)
corners=distance.corners
segment_box_distance=distance.segment_box_distance


def parameters():
    # 当前SCAD是唯一设计参数入口；车CG未知状态另行保留为None。
    text=SOURCE.read_text(encoding='utf-8')
    p={m[1]:float(m[2]) for m in re.finditer(r'^([a-z_]+)=(-?[\d.]+);',text,re.M)}
    p['base_cg_x_actual']=p['base_cg_x'] if re.search(r'^base_cg_known=true;',text,re.M) else None
    return p


def r2(v,a):
    # 纵向X-Z平面旋转与SCAD绕Y负转完全同向。
    c,s=math.cos(math.radians(a)),math.sin(math.radians(a))
    return np.array([[c,-s],[s,c]])@np.array(v)


def box(lo,hi,origin=(0,0,0),a=0):
    # 保存OBB真实旋转，倾斜的底板和侧壁不退化为过大的世界AABB。
    c,s=math.cos(math.radians(a)),math.sin(math.radians(a))
    return np.array(lo),np.array(hi),np.array(origin),np.array([[c,0,-s],[0,1,0],[s,0,c]])


def separation(a,b):
    # 两盒都绕Y，公共Y与两组XZ法向构成完整分离轴集合。
    va,vb=corners(a),corners(b)
    return max(max((va@n).min()-(vb@n).max(),(vb@n).min()-(va@n).max()) for n in [a[3][:,0],a[3][:,1],a[3][:,2],b[3][:,0],b[3][:,2]])


def prism_separation(prism,obb):
    # 三角楔与盒都沿Y挤出，侧法向和两组XZ边法向构成完整分离轴。
    vertices,axes=prism;other=corners(obb)
    directions=axes+[obb[3][:,i] for i in range(3)]
    return max(max((vertices@n).min()-(other@n).max(),(other@n).min()-(vertices@n).max()) for n in directions)


def section_height(p,u):
    # 只取坡面真实高度；不会把坡面上方的开放空间误当实体。
    rear=p['bucket_center_x']-p['bucket_length']/2-p['pivot_x']
    return p['wall']+p['ramp_rise']*np.clip((rear+p['ramp_run']-u)/p['ramp_run'],0,1)


def geometry(p,a):
    # 所有位置由同一主轴变换求得，不能靠不同动画把杆端假连在一起。
    top=p['pillar_height']+p['deck_thickness']
    px,pz=p['pivot_x'],top+p['pivot_above_deck']
    xlo,xhi=p['bucket_center_x']-p['bucket_length']/2,p['bucket_center_x']+p['bucket_length']/2
    rear,front=xlo-px,xhi-px
    world=lambda v:np.array([px+r2([v[0],v[2]],a)[0],v[1],pz+r2([v[0],v[2]],a)[1]])
    A=np.array([px+p['fixed_pin_u'],0,top+p['fixed_pin_above_deck']])
    B=world([p['moving_pin_u'],0,p['moving_pin_z']])
    P=np.array([px,0,pz]);origin=(px,0,pz);w=p['bucket_width']/2;h=p['bucket_height'];t=p['wall']
    # 完整填实盒用于外部碰撞；真实四块壁用于有限物体内部通路。
    envelope=box([rear,-w,0],[front,w,h],origin,a)
    walls=[box([rear,-w,0],[front,w,t],origin,a),
           box([front-t,-w,t],[front,w,h],origin,a),
           box([rear,-w,t],[front,-w+t,h],origin,a),
           box([rear,w-t,t],[front,w,h],origin,a)]
    # 楔体直接使用与SCAD相同的三角截面顶点，完整底板连接在其下方。
    ramp_start=rear+p['ramp_run'];rise=p['ramp_rise'];rotation=envelope[3]
    ramp_vertices=np.array([world([u,y,z]) for y in [-w,w] for u,z in [(rear,t),(ramp_start,t),(rear,t+rise)]])
    slope_normal=np.array([rise/p['ramp_run'],0,1]);slope_normal/=np.linalg.norm(slope_normal)
    ramp=(ramp_vertices,[rotation@v for v in [np.array([0,1,0]),np.array([1,0,0]),np.array([0,0,1]),slope_normal]])
    deck=box([p['body_offset_x']-100,-80,p['pillar_height']],[p['body_offset_x']+100,80,top])
    platez=p['lidar_scan_z']-p['lidar_height']/2-5
    sensors=[box([p['mast_x']-7,-13,top],[p['mast_x']+7,13,platez]),
             box([p['lidar_center_x']-36,-36,platez],[p['lidar_center_x']+36,36,platez+5]),
             box([p['lidar_center_x']-p['lidar_diameter']/2,-p['lidar_diameter']/2,platez+5],
                 [p['lidar_center_x']+p['lidar_diameter']/2,p['lidar_diameter']/2,platez+5+p['lidar_height']]),
             box([p['camera_x']-p['camera_depth']/2,-p['camera_width']/2,p['camera_z']-p['camera_height']/2],
                 [p['camera_x']+p['camera_depth']/2,p['camera_width']/2,p['camera_z']+p['camera_height']/2])]
    sensors.append(box([p['camera_x']+p['camera_depth']/2,-9,p['camera_z']-9],
                       [p['camera_x']+p['camera_depth']/2+4,9,p['camera_z']+9]))
    sensor_arms=[([p['mast_x'],0,platez],[p['lidar_center_x'],0,platez],6),
                 ([p['mast_x'],0,p['camera_z']],[p['camera_x'],0,p['camera_z']],4.5)]
    # 下铰三角座也参与外部运动件检查，仅与执行器共轴邻域保留接口接触。
    supports=[([A[0]+dx,0,top],A,5) for dx in [-15,15]]
    for side in [-1,1]:
        y=side*(w+p['axle_end_clearance'])
        # 侧座脚位于旧板内，使用实际圆端半径检查运动件。
        supports += [([foot,side*65,top],[px,y,pz],5.5) for foot in [-95,-65]]
    stops=[box([30,y-6,top],[42,y+6,pz]) for y in [-65,65]]
    return locals()


def scan(p,chassis,ground):
    # 验证当前范围去回，不外推连续运动、结构弹性或紧固件公差。
    n=int(p['max_angle']);assert n==p['max_angle'] and 0<n<=45
    assert p['payload_kg']<=.5
    assert p['wall']<p['ramp_run']<p['bucket_length']-p['wall'] and p['ramp_rise']>p['wall']
    assert p['wall']+p['ramp_rise']<p['bucket_height']
    assert math.degrees(math.atan2(p['ramp_rise'],p['ramp_run']))<p['max_angle'],'最大角度未让后坡向外下行'
    assert p['mast_x']+7<=p['body_offset_x']+100 and p['mast_x']-7>p['bucket_center_x']+p['bucket_length']/2
    rows=[];mins={'body':1e9,'deck':1e9,'support_rods':1e9,'sensors':1e9,'actuator':1e9,'ramp_body':1e9}
    for a in list(range(n+1))+list(range(n,-1,-1)):
        g=geometry(p,a);A,B,P=g['A'],g['B'],g['P'];L=np.linalg.norm(B-A)
        assert p['actuator_closed']<=L<=p['actuator_closed']+p['actuator_stroke']
        arm=np.linalg.norm(np.cross(B-P,A-P))/L
        assert arm>5,'执行器靠近死点'
        # 外部障碍采用包含整个斗体的保守OBB；斜楔额外记录真实截面分离。
        moving=[g['envelope']]
        gap=prism_separation(g['ramp'],chassis);assert gap>.05
        mins['ramp_body']=min(mins['ramp_body'],gap)
        for m in moving:
            for name,t in [('body',chassis),('deck',g['deck'])]+[('sensors',t) for t in g['sensors']]:
                gap=separation(m,t);assert gap>.05,(name,a,gap)
                mins[name]=min(mins[name],gap)
            for stop in g['stops']:
                assert separation(m,stop)>=-1e-8,('止挡',a)
            for sa,sb,r in g['supports']:
                gap=segment_box_distance(sa,sb,m)-r;assert gap>.05,('支架',a,gap)
                mins['support_rods']=min(mins['support_rods'],gap)
            for sa,sb,r in g['sensor_arms']:
                assert segment_box_distance(sa,sb,m)-r>.05,('传感器横撑',a)
            assert corners(m)[:,2].min()>ground+5,('地面',a)
        # 固定杆件与前设备独立检查；主轴/丝杆连接邻域仍仅表示共轴关系。
        for sa,sb,r in g['supports']:
            for sensor in g['sensors']:assert segment_box_distance(sa,sb,sensor)-r>.05,('固定架与设备',a)
        u=(B-A)/L
        # 绿色外筒、深绿电机以及内杆的外径不同，分别检查。
        for sa,sb,r in [(A+u*7,A+u*p['actuator_body_length'],7),(A+u*12,A+u*30,10),(A+u*(p['actuator_body_length']-7),B,3.5)]:
            for target in [chassis,g['deck']]+g['sensors']+moving+g['stops']:
                gap=segment_box_distance(sa,sb,target)-r;assert gap>.05,('执行器',a,gap)
                mins['actuator']=min(mins['actuator'],gap)
        # 假设扫描平面单独检查，设备自身实体不当作自遮挡；真实出光位置未知。
        highest=max(corners(t)[:,2].max() for t in moving)
        if a==0:assert p['lidar_scan_z']>highest+5
        rows.append({'angle':a,'length':float(L),'arm':float(arm),
                     'scan_margin':float(p['lidar_scan_z']-highest)})
    assert rows[:n+1]==list(reversed(rows[n+1:]))
    return {'samples':len(rows),'start':rows[0],'end':rows[n],'stroke':max(r['length'] for r in rows)-min(r['length'] for r in rows),
            'minimum_moment_arm':min(r['arm'] for r in rows),'minimum_scan_margin':min(r['scan_margin'] for r in rows),
            'scan_occluded_sample_angles':[r['angle'] for r in rows[:n+1] if r['scan_margin']<=0],'minimum_clearances':mins}


def section_check(p):
    # 内底上表面为同一基准；三角楔底面与完整底板连接，两端伸入侧壁。
    g=geometry(p,0);t=p['wall'];rear=g['rear'];run=p['ramp_run'];rise=p['ramp_rise']
    assert abs(section_height(p,rear+run)-t)<1e-9 and abs(section_height(p,rear)-t-rise)<1e-9
    assert g['walls'][0][0][0]==rear and g['walls'][0][1][0]==g['front']
    for side in g['walls'][1:]:assert abs(corners(side)[:,2].min()-corners(g['walls'][0])[:,2].max())<1e-8
    slope=p['max_angle']-math.degrees(math.atan2(rise,run));assert slope>0
    return {'fixed_rear_retention_height_above_floor_mm':rise,'rear_total_height_mm':t+rise,
            'ramp_run_mm':run,'ramp_floor_shared_face_mm2':run*p['bucket_width'],
            'outward_downslope_at_max_degrees':slope,'source':'SCAD同一三角截面/连续底与两侧壁',
            'boundary':f'运输浅挡边{rise:g}mm设计；真实行驶保持、液体密封、摩擦和倒净未测'}


def load_report(p):
    # X=-75来自厂家最低顶点的候选后接地区，实际接地边仍须测量。
    edge=-75.;cases={};n=int(p['max_angle']);mouth=p['bucket_center_x']-p['bucket_length']/2
    rim=p['wall']+p['ramp_rise']
    # 中部浅载点只是假设分布，后两项取真正出口表面以上的偏载。
    definitions={'centered_shallow_assumption':(p['bucket_center_x'],p['wall']+p['ramp_rise']/2),
                 'rim_surface':(mouth,rim),'rim_high35':(mouth,rim+35),'rim_high70':(mouth,rim+70)}
    for name,(x,z) in definitions.items():
        # 局部偏载点逐角包络包括运输姿态，不能仅用卸料终点判稳。
        values=[p['pivot_x']+r2([x-p['pivot_x'],z],a)[0] for a in range(n+1)]
        threshold=edge-p['payload_kg']*(min(values)-edge)/p['base_mass_kg']
        cases[name]={'end_cg_x':values[-1],'minimum_cg_x':min(values),'required_base_cg_x_gt':threshold,
                     'end_required_base_cg_x_gt':edge-p['payload_kg']*(values[-1]-edge)/p['base_mass_kg'],
                     'hypothetical_margin_if_base_cg_x_zero_kg_mm':p['base_mass_kg']*(-edge)+p['payload_kg']*(min(values)-edge)}
    # 当前质量已知而重心未知，所有数字只表达条件阈值，不生成稳定通过状态。
    return {'base_mass_user_measured_kg':p['base_mass_kg'],'payload_target_kg':p['payload_kg'],
            'base_cg_x_actual':p['base_cg_x_actual'],'new_attachment_mass_cg':'unknown','status':'not_certified',
            'screening_tip_edge_x':edge,'scenario_scope':'局部固定偏载点全角包络，非垃圾袋动力学轨迹',
            'restoring_moment_formula':f'{p["base_mass_kg"]}*(base_cg_x+75)+{p["payload_kg"]}*(cargo_cg_x+75)+sum(attachment_mass*(attachment_cg_x+75))',
            'cases':cases}


def material_check(p,chassis,ground):
    g=geometry(p,p['max_angle']);tip=g['world']([g['rear'],0,p['wall']+p['ramp_rise']]);columns={};paths={}
    # 出口附近竖落框与沿真实固定后坡移动的块属于不同假设，分别保留结论。
    for width in [50,70]:
        corridor=box([tip[0]-width/2,tip[1]-width/2,ground],[tip[0]+width/2,tip[1]+width/2,tip[2]+p['bag_height']])
        gap=separation(corridor,chassis)
        columns[str(width)]={'wheel_envelope_gap_mm':float(gap),'clear':bool(gap>0)}
        # 有限块保持与斗底同姿态，底面跟随脚印下最高截面，完全离口才竖落。
        states=[];release_u=g['rear']-width/2-1
        for u in np.linspace(60,release_u,60):
            base=section_height(p,u-width/2)
            states.append(box([u-width/2,-width/2,base],[u+width/2,width/2,base+width],g['origin'],p['max_angle']))
        released=states[-1];fall=corners(released)[:,2].min()-ground
        assert fall>0
        for dz in np.linspace(0,fall,40):
            lo,hi,o,r=released;states.append((lo,hi,o-np.array([0,0,dz]),r))
        min_gap=1e9;hits=[]
        targets=[('车轮/底盘',chassis)]+[('设备',t) for t in g['sensors']]+[('斗壁',t) for t in g['walls']]
        for i,block in enumerate(states):
            # 允许理想接触，出现穿透就记录具体物块、帧和障碍，不把所有物体总括为通过。
            for name,target in targets:
                d=separation(block,target)
                if d < -1e-7:hits.append({'sample':i,'obstacle':name,'penetration_mm':float(-d)})
            # 对三角楔做精确分离轴，不能将楔上方空腔填成盒后误判堵塞。
            d=prism_separation(g['ramp'],block)
            if d < -1e-7:hits.append({'sample':i,'obstacle':'固定后斜壁','penetration_mm':float(-d)})
            min_gap=min(min_gap,separation(block,chassis))
        paths[str(width)]={'test_cube_mm':width,'samples':len(states),'clear':not hits,'minimum_chassis_gap_mm':min_gap,'first_collisions':hits[:4]}
    assert paths['50']['clear'],paths['50']
    return {'vertical_corridors':columns,'rigid_paths':paths,'tip_world':tip.tolist(),
            'path_assumption':'物块与斗底同姿态，底面取脚印覆盖截面的最高值，完全离开后缘才竖落',
            'boundary':'几何可行路径；未模拟真实驱动力、转动、摩擦、柔性袋或行驶保持'}


def main():
    p=parameters();raw_path=REPO/'docs/vendor/waveshare_wave_rover/WAVE ROVER_MODEL_STL.stl'
    raw=trimesh.load_mesh(raw_path,process=False).vertices
    v=np.c_[raw[:,1]+p['body_offset_x'],-raw[:,0],raw[:,2]-p['vendor_top_z']]
    lo,hi=v.min(axis=0),v.max(axis=0);chassis=box(lo,hi)
    # 本次直接读取厂家全部顶点外盒；结果比精确车体碰撞更保守。
    default=scan(p,chassis,lo[2]);materials=material_check(p,chassis,lo[2])
    varied=scan(dict(p,pillar_height=26,lidar_scan_z=260,ramp_run=50,ramp_rise=20),chassis,lo[2])
    rejected=[]
    for name,changes in [('行程不足',{'actuator_stroke':1}),('低雷达',{'lidar_scan_z':130}),('无坡程',{'ramp_run':0}),('后坡不下行',{'ramp_rise':45})]:
        try:scan(dict(p,**changes),chassis,lo[2])
        except AssertionError:rejected.append(name)
        else:raise AssertionError('未拒绝'+name)
    # 相机正前锥在最近的雷达平台前缘仍远低于平台，其他结构全部位于镜头后。
    lens_x=p['camera_x']+p['camera_depth']/2+4
    plate_front=p['lidar_center_x']+36;plate_bottom=p['lidar_scan_z']-p['lidar_height']/2-5
    cone_top=p['camera_z']+max(0,plate_front-lens_x)*math.tan(math.radians(p['camera_vfov']/2))
    assert plate_bottom-cone_top>5 and p['bucket_center_x']+p['bucket_length']/2<lens_x
    # 报告分别给出几何成功、预期落料失败及稳定性unknown，避免一个总PASS吞掉边界。
    report={'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'parameters':p,'vendor_bounds':[lo.tolist(),hi.tolist()],
            'geometry':default,'fixed_section':section_check(p),'variation':varied,'rejected_invalid':rejected,'materials':materials,'loads':load_report(p),
            'camera':{'assumed_hfov':p['camera_hfov'],'assumed_vfov':p['camera_vfov'],'front_platform_vertical_gap':plate_bottom-cone_top},
            'not_proven':['全部销耳/轴承/紧固件公差和真实转动间隙','真实设备尺寸/出光高度/FOV','实际车CG与新增附件质量','0.5kg静态或动态承载','柔性袋滑动摩擦/脱离/夹袋','连续碰撞与变形']}
    out=ROOT/'exports';out.mkdir(exist_ok=True)
    (out/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'geometry':default,'fixed_section':report['fixed_section'],'materials':materials,'loads':report['loads'],'rejected':rejected},ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
