"""打印驱动的解析封装、牙形相位、齿轮啮合与条件力矩验证。"""
# 所有新增尺寸是设计输入；电机外形来源为用户提供商家图纸。
# 用户确认三伏六十转，工作扭矩没有可靠输入，不给承载通过结论。
# 独立止推与防转通过可检查几何表达，真实磨损需先打印试片。
# 丝杆转角的正负号必须与右旋螺线和滑块平移方向一致。
# 齿轮数值检查遍历一个齿周期，不能只看初始相位截图。
# 这里检查二维齿形，最终导出的三维实体另在导出程序核验。
# 轴肩固定轴向位置，滑块防转，测试不依赖齿面摩擦产生保持力。
# 每个包络对应一个实际零件区域，宽电机区不能被细丝杆半径代替。
# 两个固定座通过标准螺栓连接母体，销轴尺寸要包含耳宽与锁母。
# 下座沉头顶面齐平是封装条件，不能随意换凸头后沿用报告。
# 报告对车体采用厂家全包络，不能用它来证明细节螺孔已匹配。
# 工作行程保留前后余量，端部挡块不是任意行程的安全开关。
# 正确齿轮相位以真实轮廓相交检测，错误半齿位用负例验证。
# 右旋牙形经有限网格离散，三维布尔测试会额外检查微小穿透。
# 输出转速仅来自用户输入，不从功率表反推不可靠的持续扭矩。
# 导程与传动比改变时需重新生成全部零件和运动图，不能缩放STL。
# 温升、磨损、打印各向异性和柔性变形没有在几何模型中模拟。
# 真实试装通过之前，所有输出保持拟合样件和条件计算的证据级别。
from pathlib import Path
import hashlib
import json
import math
import re
import numpy as np

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'drive.scad'


def parameters():
    # 源文件是唯一参数入口，数值报告绑定源哈希。
    return {m[1]:float(m[2]) for m in re.finditer(r'^([a-z_]+)=(-?[\d.]+);',SOURCE.read_text(encoding='utf-8'),re.M)}


def envelopes(p,delta):
    # 输出沿轴向s、横向t、法向v的分件保守盒，供整车检查真实壳而非旧圆筒。
    center=p['gear_module']*(p['screw_teeth']+p['motor_teeth'])/2
    result=[('轨道前挡',[20.8,-13.4,-10.3],[p['guide_end']+3,13.4,10.3]),
            ('独立止推座',[5.5,-9,-9],[13,center+9,9]),
            ('后桥左',[6,-13.4,-9],[24,-8.4,9]),
            ('后桥右',[6,center+11.6,-8],[22+p['motor_length']+5,center+14.4,8]),
            ('电机夹持及电极预算',[22,center-8.5,-7.8],[22+p['motor_length']+5,center+14.4,7.8]),
            ('滑块螺母',[p['nut_start']+delta,-10,-8],[p['nut_start']+p['nut_length']+delta,10,8]),
            ('空心推杆',[p['nut_start']+p['nut_length']+delta,-8,-8],[p['closed_length']+delta,8,8]),
            ('上铰耳',[p['closed_length']+delta-6,-8,-6],[p['closed_length']+delta+6,8,6])]
    # 齿轮外径包含齿顶；两个转动部件各自保留完整扫掠圆的外盒。
    for name,t,z in [('螺杆齿轮',0,p['screw_teeth']),('输入齿轮',center,p['motor_teeth'])]:
        r=p['gear_module']*(z/2+1);result.append((name,[14,t-r,-r],[18,t+r,r]))
    for z in [28,p['nut_start']+5+p['working_stroke']]:result.append(('检修插销耳',[z-3,5.5,8.3],[z+3,13.4,11.3]))
    for z in [24,68]:result.append(('限位安装耳',[z-4,-18,-4],[z+4,-13,4]))
    for t,z in [(-14,28),(-14,70),(center+12.7,9),(center+12.7,45)]:
        result.append(('壳体紧固耳',[z-p['shell_boss_r'],t-p['shell_boss_r'],min(-10.3,10.3-p['housing_bolt_length'])],[z+p['shell_boss_r'],t+p['shell_boss_r'],10.3]))
    # 下铰的销孔邻域与固定架共轴，仅这一小段单独标为装配接触区。
    result.append(('下铰接口',[-5,-6,-5],[6,6,5]))
    return result


def gear_outline(p,z):
    # 生成与SCAD同样的渐开线齿侧，闭合轮廓包含相邻齿之间的根圆。
    rp=p['gear_module']*z/2;rb=rp*math.cos(math.radians(20));ra=rp+p['gear_module'];rf=rp-1.25*p['gear_module']
    inv=lambda r:math.sqrt(max(0,r*r/(rb*rb)-1))-math.acos(min(1,rb/r))
    half=math.pi/(2*z)-p['backlash']/(2*rp);radii=np.linspace(rb,ra,11)
    flank=[(r,half+inv(rp)-inv(r)) for r in radii];root=half+inv(rp)
    pts=[]
    for i in range(int(z)):
        theta=i*2*math.pi/z
        for r,a in [(rf,-root)]+[(r,-a) for r,a in flank]+list(reversed(flank))+[(rf,root)]:pts.append([r*math.cos(theta+a),r*math.sin(theta+a)])
        # 根圆短弧补点避免用过长直线切掉根部。
        for a in np.linspace(theta+root,theta+2*math.pi/z-root,5)[1:-1]:pts.append([rf*math.cos(a),rf*math.sin(a)])
    return np.array(pts)


def edges_cross(a,b):
    # 严格相交表示实体齿廓穿透；理想切触留给打印间隙吸收。
    aa=np.roll(a,-1,axis=0);bb=np.roll(b,-1,axis=0)
    cross=lambda u,v:u[...,0]*v[...,1]-u[...,1]*v[...,0]
    u=aa-a;v=bb-b;w=b[None,:,:]-a[:,None,:]
    d=cross(u[:,None,:],v[None,:,:]);valid=abs(d)>1e-10
    with np.errstate(divide='ignore',invalid='ignore'):
        t=cross(w,v[None,:,:])/d;s=cross(w,u[:,None,:])/d
    return bool(np.any(valid&(t>1e-7)&(t<1-1e-7)&(s>1e-7)&(s<1-1e-7)))


def validate(p):
    # 啮合长度、导向长度和末端余量独立检查，不以能移动替代能承力。
    assert p['thread_d']>8 and p['lead']>=1.5 and .1<p['thread_clearance']<.5
    assert p['lead']>1.6+2*p['axial_clearance']
    assert p['nut_start']>=p['thread_start']
    assert p['nut_start']+p['nut_length']+p['working_stroke']<=p['thread_end']
    assert p['closed_length']-5>p['thread_end']
    assert p['nut_length']>=12 and p['gear_module']>=.9
    center=p['gear_module']*(p['screw_teeth']+p['motor_teeth'])/2
    assert center-p['motor_width']/2-p['fit']>13.4
    assert p['motor_voltage']==3 and p['motor_rpm']>0
    assert p['nut_af']>=4.2 and p['shell_boss_r']-p['nut_af']/math.cos(math.pi/6)/2>.6
    ratio=p['screw_teeth']/p['motor_teeth'];samples=[]
    for d in np.linspace(0,p['working_stroke'],41):
        angle=-360*d/p['lead']
        # 右旋表面z=导程乘方位角，负旋转带来正向轴移，母牙相位保持不变。
        residual=d+p['lead']*angle/360;assert abs(residual)<1e-9
        engagement=min(p['thread_end'],p['nut_start']+d+p['nut_length'])-max(p['thread_start'],p['nut_start']+d)
        guide=min(p['guide_end'],p['nut_start']+d+p['nut_length'])-max(21,p['nut_start']+d)
        assert engagement>=p['nut_length']-1e-8 and guide>=p['nut_length']-1e-8
        samples.append((float(d),float(engagement),float(guide)))
    # 齿轮按外啮合反向转动，半齿相位将一侧齿中心对准另一侧齿槽。
    a,b=gear_outline(p,p['screw_teeth']),gear_outline(p,p['motor_teeth'])
    rotate=lambda pts,deg:pts@np.array([[math.cos(math.radians(deg)),math.sin(math.radians(deg))],[-math.sin(math.radians(deg)),math.cos(math.radians(deg))]])
    for angle in np.linspace(0,360/p['screw_teeth'],41):
        assert not edges_cross(rotate(a,angle),rotate(b,-angle*ratio+180/p['motor_teeth'])+[center,0]),('齿轮穿透',angle)
    assert edges_cross(a,b+[center,0]),'零相位负例没有触发齿轮穿透'
    # 条件输入扭矩仅覆盖五十牛推力；未计斗、传动自重和启动摩擦。
    # 五十牛仅作灵敏度算例；以下另读取实际新铰点估算两种垃圾位置的推力。
    compact=ROOT.parent/'compact_dump_v2/compact_dump.scad'
    cp={m[1]:float(m[2]) for m in re.finditer(r'^([a-z_]+)=(-?[\d.]+);',compact.read_text(encoding='utf-8'),re.M)}
    az=cp['fixed_pin_above_deck']-cp['pivot_above_deck'];ax=cp['fixed_pin_u'];bx=cp['moving_pin_u'];bz=cp['moving_pin_z']
    distance=math.hypot(bx-ax,bz-az);arm=abs(bx*az-bz*ax)/distance
    assert abs(distance-p['closed_length'])<1e-7
    # 这里只计垃圾重力，斗、螺杆和打印框自重都会增加真实需求。
    forces={name:cp['payload_kg']*9.80665*(x-cp['pivot_x'])/arm for name,x in [('center',cp['bucket_center_x']),('front_edge',cp['bucket_center_x']+cp['bucket_length']/2)]}
    torque=[50*p['lead']/1000/(2*math.pi*eta*ratio) for eta in [.15,.35]]
    return {'stroke_mm':p['working_stroke'],'minimum_thread_engagement_mm':min(v[1] for v in samples),'minimum_guide_overlap_mm':min(v[2] for v in samples),
            'thread_phase_samples':len(samples),'gear_phase_samples':41,'gear_ratio':ratio,'gear_center_distance_mm':center,
            'forward_thread_reserve_mm':p['thread_end']-p['nut_start']-p['working_stroke']-p['nut_length'],
            'screw_to_output_pin_reserve_mm':p['closed_length']-5-p['thread_end'],
            'theoretical_unloaded_seconds':p['working_stroke']/p['lead']*ratio/p['motor_rpm']*60,
            'conditional_motor_torque_50N_Nm':torque,'efficiency_assumption':[.15,.35],'cargo_only_push_force_N':forces,'cargo_only_motor_torque_Nm':{k:[force*p['lead']/1000/(2*math.pi*eta*ratio) for eta in [.35,.15]] for k,force in forces.items()},'gear_loss_assumption':'未计外齿轮损失，所列扭矩为此模型下限','actual_motor_working_torque':'unknown','load_status':'not_certified'}


def main():
    p=parameters();result=validate(p);rejected=[]
    # 真实破坏啮合和封装的参数作为负例，不能只测试无关显示开关。
    for name,changes in [('牙长不足',{'thread_end':60}),('母牙吃光',{'axial_clearance':.3}),('电机碰导轨',{'motor_width':18}),('上销碰轴',{'closed_length':77})]:
        try:validate(dict(p,**changes))
        except AssertionError:rejected.append(name)
        else:raise AssertionError(name)
    # 少量变参覆盖间隙调校，打印材料变化仍需实物验证。
    variant=validate(dict(p,thread_clearance=.3,backlash=.25))
    report={'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'compact_source_sha256':hashlib.sha256((ROOT.parent/'compact_dump_v2/compact_dump.scad').read_bytes()).hexdigest(),'parameters':p,'geometry':result,'variation':variant,'rejected_invalid':rejected,
            'not_proven':['PLA强度/磨损/实际牙配合','电机持续扭矩和带载速度','断电保持和控制限位','新紧固件与原四柱叠层实配']}
    (ROOT/'exports').mkdir(exist_ok=True)
    (ROOT/'exports/verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2));print('PASS default / variation / 4 invalid configurations')


if __name__=='__main__':main()
