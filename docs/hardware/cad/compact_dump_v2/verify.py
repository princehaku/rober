"""小侧斗离散几何、传感器占位和条件倾覆力矩筛查。"""
# 数值报告将几何、视线、材料包络和稳定性边界分开保存。
# 通过几何检查不代表可以打印、上车或装载目标质量。
# 厂家STL只用来建立包含车体与轮胎的保守障碍。
# 厂家外包络不作为轮胎支撑多边形使用。
# 侧向筛查边Y=-65是显式假设，仍需实车接地测量。
# 原车0.7kg为用户实测输入，代码不会据此猜重心位置。
# 未称重的新附件不计成已获得的抗倾覆力矩。
# 条件恢复矩的单位为kg·mm，数值不能当电机推力规格。
# 局部偏载点随斗旋转，其法向高度不同于竖直落料框高度。
# 每种偏载点在全角域取最坏值，并另存终点供核对。
# 垃圾真正滑动路径未知，固定点包络只用于风险筛查。
# 指定测试块是刚体，垃圾袋柔性、摩擦、卡塞没有被模拟。
# 材料沿斗底滑出后再自由下落，避免直接穿过导料唇。
# 最后接触地面属于路径终点，不生成接触动力学结论。
# 50mm与70mm通道需要分别报告，失败项不能被总通过掩盖。
# 导料唇与底板的共享面形成连接，闭门同样允许零厚度接触。
# 实际转动公差和紧固件不在这一级模型的验收范围。
# 设备盒和圆柱都是占位，真实型号替换后必须重新计算。
# 低塔允许卸料遮挡雷达，运输姿态仍须有正的扫描净空。
# 扫描遮挡结果只描述几何，驻车和导航互锁尚未写入软件。
# 相机检查使用显式假设视锥，不能当镜头厂家验收结果。
# 杆件采用完整胶囊半径，电机段单独用较大半径计算。
# 前后两个门杆都检查，不能只利用对称假设跳过一侧。
# 去程和回程独立计算，检查门分支和位置是否回到原点。
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
    p['base_cg_y_actual']=p['base_cg_y'] if re.search(r'^base_cg_known=true;',text,re.M) else None
    return p


def r2(v,a):
    # 侧向Y-Z平面旋转与SCAD绕X完全同向。
    c,s=math.cos(math.radians(a)),math.sin(math.radians(a))
    return np.array([[c,-s],[s,c]])@np.array(v)


def box(lo,hi,origin=(0,0,0),a=0):
    # 保存OBB真实旋转，倾斜的门与导料唇不退化为过大的世界AABB。
    c,s=math.cos(math.radians(a)),math.sin(math.radians(a))
    return np.array(lo),np.array(hi),np.array(origin),np.array([[1,0,0],[0,c,-s],[0,s,c]])


def separation(a,b):
    # 两盒都绕X，公共X与两组YZ法向构成完整分离轴集合。
    va,vb=corners(a),corners(b)
    return max(max((va@n).min()-(vb@n).max(),(vb@n).min()-(va@n).max()) for n in [a[3][:,0],a[3][:,1],a[3][:,2],b[3][:,1],b[3][:,2]])


def geometry(p,a):
    # 所有位置由同一主轴变换求得，不能靠不同动画把杆端假连在一起。
    top=p['pillar_height']+p['deck_thickness']
    py,pz=p['pivot_y'],top+p['pivot_above_deck']
    xlo,xhi=p['bucket_center_x']-p['bucket_length']/2,p['bucket_center_x']+p['bucket_length']/2
    rear,front=-p['bucket_width']/2+p['wall']-py,p['bucket_width']/2-py
    world=lambda v:np.r_[v[0],np.array([py,pz])+r2(v[1:],a)]
    H0=np.array([rear,p['bucket_height']]);Q0=H0+[0,p['gate_arm']]
    Qt=r2(H0,p['max_angle'])+r2([0,p['gate_arm']],p['gate_target_angle'])
    dQ=Q0-Qt
    # 等长两姿态解出固定锚横坐标，随后每角度使用同一圆交点分支。
    G=np.array([(Q0@Q0-Qt@Qt-2*p['gate_fixed_z']*dQ[1])/(2*dQ[0]),p['gate_fixed_z']])
    link=np.linalg.norm(Q0-G);H=r2(H0,a);d=np.linalg.norm(G-H)
    assert abs(p['gate_arm']-link)<d<p['gate_arm']+link,'门四杆无实数闭环'
    e=(G-H)/d;q=(p['gate_arm']**2-link**2+d*d)/(2*d)
    # 初始闭门分支的符号全程固定，不能每帧随意选看起来更顺眼的交点。
    cross=lambda x,y:x[0]*y[1]-x[1]*y[0]
    branch=1 if cross(G-H0,Q0-H0)>=0 else -1
    Q=H+q*e+branch*math.sqrt(max(0,p['gate_arm']**2-q*q))*np.array([-e[1],e[0]])
    phi=math.degrees(math.atan2(-(Q-H)[0],(Q-H)[1]))
    A=np.array([p['bucket_center_x'],py+p['fixed_pin_u'],top+p['fixed_pin_above_deck']])
    B=world([p['bucket_center_x'],p['moving_pin_u'],p['moving_pin_z']])
    P=np.array([p['bucket_center_x'],py,pz]);origin=(0,py,pz)
    # 整体填实包络用于外部障碍，真实壁用于检验物料在斗腔内的通路。
    envelope=box([xlo,rear,0],[xhi,front,p['bucket_height']],origin,a)
    walls=[box([xlo,rear,0],[xhi,front,p['wall']],origin,a),
           box([xlo,front-p['wall'],p['wall']],[xhi,front,p['bucket_height']],origin,a),
           box([xlo,rear,p['wall']],[xlo+p['wall'],front,p['bucket_height']],origin,a),
           box([xhi-p['wall'],rear,p['wall']],[xhi,front,p['bucket_height']],origin,a)]
    gate=box([xlo,-p['wall'],-p['bucket_height']],[xhi,0,0],(0,py+H[0],pz+H[1]),phi)
    lip_tip=-p['bucket_width']/2-py-p['guide_length']
    # 6毫米内搭接在底板下方形成共享面，避免仅共一条边的虚假连接。
    guide=box([xlo,lip_tip,-p['wall']],[xhi,rear+p['guide_overlap'],0],origin,a)
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
    supports=[];links=[]
    for s in [-1,1]:
        x=p['bucket_center_x']+s*(p['bucket_length']/2+p['link_end_clearance']);foot=-108 if s<0 else 64
        # 三角座与门固定短臂分别保留真实圆端半径。
        supports += [([foot,y,top],[x,py,pz],5.5) for y in [-68,-45]]
        supports += [([x,py,pz],[x,py+G[0],pz+G[1]],4)]
        links += [([x,py+H[0],pz+H[1]],[x,py+Q[0],pz+Q[1]],3.5),
                  ([x,py+G[0],pz+G[1]],[x,py+Q[0],pz+Q[1]],3)]
    stops=[box([x-6,65,top],[x+6,77,pz]) for x in [-95,30]]
    return locals()


def scan(p,chassis,ground):
    # 验证当前范围去回，不外推连续运动、结构弹性或紧固件公差。
    n=int(p['max_angle']);assert n==p['max_angle'] and 0<n<=55
    assert p['guide_overlap']>=4 and p['payload_kg']<=.5
    assert p['mast_x']+7<=p['body_offset_x']+100 and p['mast_x']-7>p['bucket_center_x']+p['bucket_length']/2
    rows=[];mins={'body':1e9,'frame':1e9,'sensors':1e9,'actuator':1e9,'guide':1e9}
    for a in list(range(n+1))+list(range(n,-1,-1)):
        g=geometry(p,a);A,B,P=g['A'],g['B'],g['P'];L=np.linalg.norm(B-A)
        assert p['actuator_closed']<=L<=p['actuator_closed']+p['actuator_stroke']
        arm=np.linalg.norm(np.cross(B-P,A-P))/L
        assert arm>5,'执行器靠近死点'
        # 圆交点输出需同时满足两条杆长，并检查传动角远离共线。
        H,Q,G=g['H'],g['Q'],g['G']
        assert abs(np.linalg.norm(Q-H)-p['gate_arm'])<1e-8 and abs(np.linalg.norm(Q-G)-g['link'])<1e-8
        trans=abs(np.cross(np.r_[Q-H,0],np.r_[G-Q,0])[2])/(p['gate_arm']*g['link'])
        assert trans>.2
        moving=[g['envelope'],g['gate'],g['guide']]
        # 闭门和导料唇仅允许表面接触，穿透不会列作铰接豁免。
        assert separation(g['gate'],g['envelope'])>=-1e-8 and separation(g['gate'],g['guide'])>=-1e-8
        for m in moving:
            for name,t in [('body',chassis),('frame',g['deck'])]+[('sensors',t) for t in g['sensors']]:
                gap=separation(m,t);assert gap>.05,(name,a,gap)
                mins[name]=min(mins[name],gap)
            for stop in g['stops']:
                assert separation(m,stop)>=-1e-8,('止挡',a)
            for sa,sb,r in g['supports']:
                gap=segment_box_distance(sa,sb,m)-r;assert gap>.05,('支架',a,gap)
            for sa,sb,r in g['sensor_arms']:
                assert segment_box_distance(sa,sb,m)-r>.05,('传感器横撑',a)
            assert corners(m)[:,2].min()>ground+5,('地面',a)
        # 门连杆对所有外部设备和完整斗体检查，销轴端部共轴区另列未设计。
        for sa,sb,r in g['supports']:
            for sensor in g['sensors']:assert segment_box_distance(sa,sb,sensor)-r>.05,('固定架与设备',a)
        for sa,sb,r in g['links']:
            for target in [chassis,g['deck']]+g['sensors']+moving:
                assert segment_box_distance(sa,sb,target)-r>.05,('门杆',a)
        u=(B-A)/L
        # 绿色外筒、深绿电机以及内杆的外径不同，分别检查。
        for sa,sb,r in [(A+u*7,A+u*p['actuator_body_length'],7),(A+u*12,A+u*30,10),(A+u*(p['actuator_body_length']-7),B,3.5)]:
            for target in [chassis,g['deck']]+g['sensors']+moving+g['stops']:
                gap=segment_box_distance(sa,sb,target)-r;assert gap>.05,('执行器',a,gap)
                mins['actuator']=min(mins['actuator'],gap)
        mins['guide']=min(mins['guide'],separation(g['guide'],chassis))
        # 假设扫描平面单独检查，设备自身实体不当作自遮挡；真实出光位置未知。
        highest=max([corners(t)[:,2].max() for t in moving]+[max(sa[2],sb[2])+r for sa,sb,r in g['links']])
        if a==0:assert p['lidar_scan_z']>highest+5
        rows.append({'angle':a,'length':float(L),'arm':float(arm),'gate_angle':g['phi'],'transmission_sin':float(trans),
                     'scan_margin':float(p['lidar_scan_z']-highest)})
    assert rows[:n+1]==list(reversed(rows[n+1:]))
    assert abs(rows[0]['gate_angle'])<1e-8 and abs(rows[n]['gate_angle']-p['gate_target_angle'])<1e-8
    return {'samples':len(rows),'start':rows[0],'end':rows[n],'stroke':max(r['length'] for r in rows)-min(r['length'] for r in rows),
            'minimum_moment_arm':min(r['arm'] for r in rows),'minimum_scan_margin':min(r['scan_margin'] for r in rows),
            'scan_occluded_sample_angles':[r['angle'] for r in rows[:n+1] if r['scan_margin']<=0],'minimum_clearances':mins}


def load_report(p):
    # Y=-65仅作厂家候选接地带的筛查边，轮胎实测支撑多边形尚缺。
    edge=-65.;cases={};n=int(p['max_angle'])
    definitions={'uniform':(0,p['bucket_height']/2),'mouth_floor':(-p['bucket_width']/2,0),
                 'lip_floor':(-p['bucket_width']/2-p['guide_length'],0),
                 'lip_high35':(-p['bucket_width']/2-p['guide_length'],35),
                 'lip_high70':(-p['bucket_width']/2-p['guide_length'],70)}
    for name,(y,z) in definitions.items():
        # 后两项高度沿倾斜斗底法向定义，与竖直落料框的高度定义分开。
        values=[p['pivot_y']+r2([y-p['pivot_y'],z],a)[0] for a in range(n+1)]
        threshold=edge-p['payload_kg']*(min(values)-edge)/p['base_mass_kg']
        cases[name]={'end_cg_y':values[-1],'minimum_cg_y':min(values),'required_base_cg_y_gt':threshold,
                     'end_required_base_cg_y_gt':edge-p['payload_kg']*(values[-1]-edge)/p['base_mass_kg'],
                     'hypothetical_margin_if_base_cg_y_zero_kg_mm':p['base_mass_kg']*(-edge)+p['payload_kg']*(min(values)-edge)}
    # 车CG未实测，保持unknown；示例阈值绝不生成稳定PASS。
    return {'base_mass_user_measured_kg':p['base_mass_kg'],'payload_target_kg':p['payload_kg'],
            'base_cg_y_actual':p['base_cg_y_actual'],'new_attachment_mass_cg':'unknown','status':'not_certified',
            'screening_tip_edge_y':edge,'scenario_scope':'局部固定偏载点的全角包络，非垃圾袋动力学轨迹',
            'restoring_moment_formula':f'{p["base_mass_kg"]}*(base_cg_y+65)+{p["payload_kg"]}*(cargo_cg_y+65)+sum(attachment_mass*(attachment_cg_y+65))',
            'cases':cases}


def material_check(p,chassis,ground):
    g=geometry(p,p['max_angle']);tip=g['world']([p['bucket_center_x'],g['lip_tip'],0]);columns={}
    # 先做点出口下的有限宽竖直通道筛查：50与70必须分别报告。
    for width in [50,70]:
        corridor=box([tip[0]-width/2,tip[1]-width/2,ground],[tip[0]+width/2,tip[1]+width/2,tip[2]+p['bag_height']])
        gap=separation(corridor,chassis)
        columns[str(width)]={'wheel_envelope_gap_mm':float(gap),'clear':bool(gap>0)}
    assert columns['50']['clear']
    if p['guide_length']==40 and p['bucket_width']==200 and p['max_angle']==50:
        assert not columns['70']['clear']
    # 50毫米刚体块沿倾斜斗底滑出：先接触3mm底板，再下降到导料唇表面。
    width=50.;height=50.;states=[];min_gap=1e9
    release_u=g['lip_tip']-width/2-1
    for u in np.linspace(30,release_u,60):
        base=p['wall'] if u+width/2>=g['rear'] else 0
        states.append(box([p['bucket_center_x']-25,u-25,base],[p['bucket_center_x']+25,u+25,base+height],(0,g['py'],g['pz']),p['max_angle']))
    # 物体完全离开唇后才进行竖直下落，不能让悬在斜唇上的盒直接穿透下落。
    released=states[-1];fall=corners(released)[:,2].min()-ground
    assert fall>0
    for dz in np.linspace(0,fall,40):
        lo,hi,o,r=released;states.append((lo,hi,o-np.array([0,0,dz]),r))
    for block in states:
        # 斗底和导料唇允许接触；地面终点接触也属于预期状态。
        for target in [chassis,g['gate']]+g['sensors']+g['walls']+[g['guide']]:
            gap=separation(block,target);assert gap>=-1e-7,('50mm材料路径',gap)
        min_gap=min(min_gap,separation(block,chassis))
    return {'vertical_corridors':columns,'test_block_mm':[50,50,50],'rigid_path_samples':len(states),
            'path_chassis_minimum_gap':min_gap,'release_u':release_u,'boundary':'仅指定刚体块采样通路；滑动驱动力、柔性垃圾袋、脱离姿态和堵塞需实测'}


def main():
    p=parameters();raw_path=REPO/'docs/vendor/waveshare_wave_rover/WAVE ROVER_MODEL_STL.stl'
    raw=trimesh.load_mesh(raw_path,process=False).vertices
    v=np.c_[raw[:,1]+p['body_offset_x'],-raw[:,0],raw[:,2]-p['vendor_top_z']]
    lo,hi=v.min(axis=0),v.max(axis=0);chassis=box(lo,hi)
    # 本次直接读取厂家全部顶点外盒；结果比精确车体碰撞更保守。
    default=scan(p,chassis,lo[2]);materials=material_check(p,chassis,lo[2])
    varied=scan(dict(p,pillar_height=26,lidar_scan_z=260),chassis,lo[2])
    rejected=[]
    for name,changes in [('行程不足',{'actuator_stroke':1}),('低雷达',{'lidar_scan_z':130}),('无唇搭接',{'guide_overlap':0})]:
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
            'geometry':default,'variation':varied,'rejected_invalid':rejected,'materials':materials,'loads':load_report(p),
            'camera':{'assumed_hfov':p['camera_hfov'],'assumed_vfov':p['camera_vfov'],'front_platform_vertical_gap':plate_bottom-cone_top},
            'not_proven':['全部销耳/轴承/紧固件公差和真实转动间隙','真实设备尺寸/出光高度/FOV','实际车CG与新增附件质量','0.5kg静态或动态承载','柔性袋滑动摩擦/脱离/夹袋','连续碰撞与变形']}
    out=ROOT/'exports';out.mkdir(exist_ok=True)
    (out/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'geometry':default,'materials':materials,'loads':report['loads'],'rejected':rejected},ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
