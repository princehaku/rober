"""核对概念机构的刚体几何；不做材料强度或满载稳定性认证。"""
from pathlib import Path
import json
import math
import re
import hashlib
import numpy as np
import trimesh
import ezdxf

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
SOURCE = ROOT / 'dump_kinematics.scad'


def parameters():
    # 从用户可编辑的SCAD读取默认值，避免验证另一套悄悄漂移的参数。
    text = SOURCE.read_text(encoding='utf-8')
    return {m[1]: float(m[2]) for m in re.finditer(r'^([a-z_]+)=(-?[\d.]+);', text, re.M)}


def rotation(a):
    # X-Z平面正角将前端抬高，与SCAD绕Y负角一致。
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return np.array([[c, 0, -s], [0, 1, 0], [s, 0, c]])


def box(lo, hi, origin=None, angle=0):
    # 盒体保留局部坐标与旋转矩阵，用完整实体分离替代顶点穿入抽样。
    lo, hi = np.array(lo), np.array(hi)
    return (lo, hi, np.zeros(3) if origin is None else np.array(origin), rotation(angle))


def corners(b):
    # 统一盒的构造入口，避免图形展示的剖切条件污染验证实体。
    lo, hi, o, r = b
    # 八角点只用于凸盒的精确投影；并非将任意网格当作八点物体。
    pts = np.array([[x, y, z] for x in [lo[0], hi[0]] for y in [lo[1], hi[1]] for z in [lo[2], hi[2]]])
    return pts @ r.T + o


def box_separation(a, b):
    # 正值表示找到分离轴，零为共面接触，负值才有实体穿入。
    # 所有盒只绕Y转动；两组XZ边法向与公共Y足以完成分离轴判据。
    va, vb = corners(a), corners(b)
    axes = [a[3][:, 0], a[3][:, 2], b[3][:, 0], b[3][:, 2], np.array([0, 1, 0])]
    return max(max((va @ n).min() - (vb @ n).max(), (vb @ n).min() - (va @ n).max()) for n in axes)


def segment_box_distance(a, b, target):
    # 胶囊轴线变换到盒坐标；按穿过六面的参数分段，每段距离平方为二次式。
    lo, hi, o, r = target
    a, b = (np.array(a) - o) @ r, (np.array(b) - o) @ r
    d = b - a
    cuts = [0., 1.]
    for i in range(3):
        if abs(d[i]) > 1e-10:
            cuts += [float((v-a[i])/d[i]) for v in [lo[i], hi[i]] if 0 < (v-a[i])/d[i] < 1]
    cuts = sorted(cuts)
    candidates = list(cuts)
    for t0, t1 in zip(cuts, cuts[1:]):
        # 以区间中点确定各坐标超出哪一面，再求驻点；不依赖稀疏采样。
        mid = a + d*(t0+t1)/2
        outside = (mid < lo) | (mid > hi)
        bound = np.where(mid < lo, lo, hi)
        den = float(np.dot(d[outside], d[outside]))
        if den > 1e-16:
            t = -float(np.dot((a-bound)[outside], d[outside])) / den
            if t0 <= t <= t1:
                candidates.append(t)
    # 到闭盒的精确最小距离减胶囊半径，即为圆端梁的碰撞依据。
    return min(float(np.linalg.norm(np.maximum(lo-(a+d*t), 0)+np.minimum(hi-(a+d*t), 0))) for t in candidates)


def geometry(p, angle):
    # 只计算当前一帧，不缓存上一姿态，回程可独立重复核验。
    # 命名与SCAD一致，后门厚度从总长中单独分配，避免放平穿透。
    top = p['pillar_height']+p['deck_thickness']
    P = np.array([p['pivot_x'], 0, top+p['pivot_above_deck']])
    rear = p['body_offset_x']-p['bucket_length']/2+p['wall']-P[0]
    front = p['body_offset_x']+p['bucket_length']/2-P[0]
    w, h, t = p['bucket_width']/2, p['bucket_height'], p['wall']
    r = rotation(angle)
    # 所有活动铰中心共同使用同一旋转，避免视觉上接近但实际脱节。
    world = lambda v: P + r@np.array(v)
    H = world([rear, 0, h])
    A = np.array([P[0]+p['fixed_pin_dx'], 0, top+p['fixed_pin_above_deck']])
    B = world([p['moving_pin_dx'], 0, p['moving_pin_dz']])
    # 完整三壁在验证中保留，视图的剖切开关不会减轻碰撞检查。
    solids = [box([rear, -w, 0], [front, w, t], P, angle),
              box([front-t, -w, t], [front, w, h], P, angle),
              box([rear, -w, t], [front, -w+t, h], P, angle),
              box([rear, w-t, t], [front, w, h], P, angle)]
    gate = box([H[0]-t, -w, H[2]-h], [H[0], w, H[2]])
    # 底座取实心外盒比实际凹槽板更保守，不利用孔洞逃避相撞。
    deck = box([p['body_offset_x']-100, -80, p['pillar_height']], [p['body_offset_x']+100, 80, top])
    # 四支撑脚为实际圆端梁；主轴末端与活动耳的共同轴区另作接触豁免。
    supports = []
    for s in [-1, 1]:
        # 正负侧各自计算，禁止只凭左右对称而跳过一侧装配。
        for dx in [10, 65]:
            supports.append(([P[0]+dx, s*70, top], [P[0], s*(w+p['side_support_offset']), P[2]], 6.5))
    stops = [box([55, s*70-6, top], [67, s*70+6, P[2]]) for s in [-1, 1]]
    # 全包络包含全部内收圆端边梁，检验障碍时保守地把斗内空腔也填实。
    envelope = box([rear,-w,0],[front,w,h],P,angle)
    return locals()


def scan(p, chassis, ground):
    # 未知真实支腿和质量不会被填入通过条件，稳定性单独保留未验证。
    # 去程和回程都按1度枚举；当前刚体机构无迟滞，回程应严格重合。
    rows, minimum = [], {'chassis': 1e9, 'deck': 1e9, 'support': 1e9, 'actuator_floor': 1e9, 'gate_ground': 1e9}
    n = int(p['max_angle'])
    assert n == p['max_angle'] and 0 < n <= 60
    # 支脚圆端和丝杆三角座必须落在旧板面内，避免调参数生成悬空落点。
    xlo, xhi = p['body_offset_x']-100, p['body_offset_x']+100
    assert p['pivot_x']+2 >= xlo and p['pivot_x']+73 <= xhi
    assert p['pivot_x']+p['fixed_pin_dx']-25 >= xlo and p['pivot_x']+p['fixed_pin_dx']+25 <= xhi
    for a in list(range(n+1))+list(range(n, -1, -1)):
        # 每帧同时计算活动实体和固定支座，支点改动也会影响障碍关系。
        g = geometry(p, a)
        P, H, A, B = (g[k] for k in ['P', 'H', 'A', 'B'])
        # 平行四杆闭合：两竖臂等长同向、两长边等长平行。
        G0, G1 = P+[0, 0, p['gate_arm']], H+[0, 0, p['gate_arm']]
        assert np.linalg.norm((G1-G0)-(H-P)) < 1e-10
        assert abs(np.linalg.norm(G1-H)-p['gate_arm']) < 1e-10
        phi = math.degrees(math.acos(abs((H-P)[2])/np.linalg.norm(H-P)))
        assert phi > 10, ('门四杆接近共线', a, phi)
        length = np.linalg.norm(B-A)
        # 有效行程由两铰心决定，不能把可见内杆长度当成采购行程。
        assert p['actuator_closed'] <= length <= p['actuator_closed']+p['actuator_stroke']
        arm = np.linalg.norm(np.cross(B-P, A-P))/length
        # 力臂门限只排除接近死点，不能据此断言任意电机推力足够。
        assert arm > 10, ('丝杆接近死点', a, arm)
        # 门与所有斗壁仅允许边界接触；闭合时没有3毫米体积重叠。
        for solid in g['solids']:
            # 对应后门的每片真实平壁分别比较，允许零厚度接触面。
            assert box_separation(g['gate'], solid) >= -1e-8, ('门与斗穿透', a)
        # 厂家全部网格顶点外包络属于保守障碍；通过说明真正整车也在分离区内。
        for solid in [g['envelope'],g['gate']]:
            for name, target in [('chassis', chassis), ('deck', g['deck'])]:
                gap = box_separation(solid, target)
                assert gap > .1, (name, a, gap)
                minimum[name] = min(minimum[name], gap)
            for sa, sb, radius in g['supports']:
                gap = segment_box_distance(sa, sb, solid)-radius
                assert gap > .1, ('固定支架', a, gap)
                minimum['support'] = min(minimum['support'], gap)
            for stop in g['stops']:
                # 放平硬止挡是设计接触；倾起后同样不能穿入斗体。
                assert box_separation(solid, stop) >= -1e-8, ('硬止挡穿透', a)
        # 执行器外筒/深绿色电机段/内杆分别检查实际半径，不能只用细杆外径。
        u = (B-A)/length
        # 机身和内杆的同轴重叠属于伸缩套筒内部，外部障碍仍逐段计算。
        capsules = [(A+10*u, A+125*u, p['actuator_radius']), (A+22*u, A+48*u, 13.5), (A+112*u, B, 4.5)]
        for sa, sb, radius in capsules:
            for target in [chassis, g['deck']]+g['stops']+[g['envelope'],g['gate']]:
                gap = segment_box_distance(sa, sb, target)-radius
                assert gap > .1, ('丝杆外包络', a, gap)
            minimum['actuator_floor'] = min(minimum['actuator_floor'], segment_box_distance(sa, sb, g['solids'][0])-radius)
        # 后门全高最低点及所有斗壁最低点均需高于地面；门底是本方案的紧约束。
        gate_clearance = H[2]-p['bucket_height']-ground
        assert gate_clearance > 5, ('后门扫地', a, gate_clearance)
        minimum['gate_ground'] = min(minimum['gate_ground'], gate_clearance)
        for solid in g['solids']:
            assert corners(solid)[:, 2].min() > ground+5
        # 外侧长杆/短臂圆端全部在斗宽之外，固定上短臂亦不跨入斗体。
        link_y = p['bucket_width']/2+p['link_y_clearance']
        for s in [-1, 1]:
            for sa, sb, radius in [(P+[0,s*link_y,0],G0+[0,s*link_y,0],4.5),
                                   (H+[0,s*link_y,0],G1+[0,s*link_y,0],4.5),
                                   (G0+[0,s*link_y,0],G1+[0,s*link_y,0],3.5)]:
                for target in [chassis,g['deck']]+g['solids']+[g['gate']]:
                    assert segment_box_distance(sa,sb,target)-radius > .1, ('门连杆',a)
        cg = g['world']([p['body_offset_x']-p['pivot_x'], 0, p['bucket_height']/2])
        # 这个点仅代表均匀垃圾，车架、斗壁和执行器重量都尚未测得。
        rows.append({'angle':a,'length_mm':float(length),'moment_arm_mm':float(arm),'fourbar_angle_deg':phi,
                     'gate_ground_mm':float(gate_clearance),'cargo_cg_x_mm':float(cg[0]),
                     'gate_horizontal_gap_mm':p['bucket_height']*math.sin(math.radians(a))})
    # 原路返回证据是实际重复计算出的状态，排除错误门分支或角度回零漂移。
    assert rows[:n+1] == list(reversed(rows[n+1:]))
    assert rows[0]['gate_horizontal_gap_mm'] == 0 and rows[n]['gate_horizontal_gap_mm'] > 100
    return {'samples':len(rows),'minimum_clearances_mm':minimum,'start':rows[0],'end':rows[n],
            'required_stroke_mm':max(x['length_mm'] for x in rows)-min(x['length_mm'] for x in rows),
            'minimum_moment_arm_mm':min(x['moment_arm_mm'] for x in rows),
            'minimum_fourbar_angle_deg':min(x['fourbar_angle_deg'] for x in rows)}


def main():
    # 报告绑定本次源哈希，避免之后调参仍误用旧验证结果。
    p = parameters()
    # 直接读取厂家原始STL，不把旧JSON中的尺寸当成本次复核结果。
    path = REPO/'docs/vendor/waveshare_wave_rover/WAVE ROVER_MODEL_STL.stl'
    raw = trimesh.load_mesh(path, process=False)
    v = raw.vertices
    mapped = np.c_[v[:,1]+p['body_offset_x'], -v[:,0], v[:,2]-p['vendor_top_z']]
    low, high = mapped.min(axis=0), mapped.max(axis=0)
    # 最低顶点平面仅作CAD地面参照，不等于实测轮胎接触多边形。
    chassis = box(low, high)
    # 本地上层DXF四耳孔用OCS转WCS，直接校对轴距和孔径。
    dxf = ezdxf.readfile(REPO/'docs/vendor/waveshare_wave_rover/WAVE ROVER-EP DXF.dxf')
    entities = [dxf.entitydb[h] for h in ['302','303','311','32E']]
    pts = np.array([list(e.ocs().to_wcs(e.dxf.center))[:2] for e in entities])
    assert np.allclose(pts.max(axis=0)-pts.min(axis=0), [58,86])
    assert all(abs(e.dxf.radius*2-2.6)<1e-6 for e in entities)
    result = scan(p, chassis, low[2])
    # 参数回归保持硬件参照不变，只改变模型允许调整的设计尺寸。
    # 改柱高/斗高/主轴偏高后重跑全程，证明参数不是仅影响画面外观。
    varied = dict(p, pillar_height=30, bucket_height=220, pivot_above_deck=85)
    variation = scan(varied, chassis, low[2])
    # 故意缩短允许行程与降低主轴都必须失败，避免危险组合静默通过。
    rejected = []
    for name, changes in [('行程不足',{'actuator_stroke':5}), ('主轴过低',{'pivot_above_deck':30}), ('底脚越界',{'pivot_x':-180})]:
        try:
            scan(dict(p, **changes), chassis, low[2])
        except AssertionError:
            rejected.append(name)
        else:
            raise AssertionError('非法参数未被拒绝:'+name)
    report = {'evidence':'sampled_concept_geometry_only','parameters':p,'vendor_bounds_mm':[low.tolist(),high.tolist()],
              'vendor_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
              'default':result,'parameter_variation':variation,'rejected_invalid':rejected,
              'collision_scope':'包含完整三壁和内收圆端边梁的斗体OBB、门OBB；厂家全部STL顶点AABB；底座AABB；侧座/丝杆/电机/门连杆胶囊；前止挡闭盒。每1度去回采样。',
              'not_proven':['非连续碰撞证明','主铰/门铰/销耳连接重合区未设计公差与实体转动间隙','边梁已纳入外包络碰撞，连接处及强度未验收',
                            '实际电机与紧固件包络待选型','真实柱高','2kg满载稳定性及支撑方案','打印强度、导程制动、摩擦、袋体通过性']}
    out = ROOT/'exports'
    # 输出仅在本模型目录内，不写入厂家资料或既有生产底板文件。
    out.mkdir(exist_ok=True)
    (out/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'PASS':result,'parameter_variation_samples':variation['samples'],'rejected':rejected},ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
