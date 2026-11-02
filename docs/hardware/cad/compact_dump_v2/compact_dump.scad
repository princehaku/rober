// 小后卸斗整车运动概念；厂家原车参照来自本地WAVE ROVER STL/DXF。
// 用户称装电池/柱/电子后的车重约700g；其真实重心仍未知。
// 用户已改选0.5kg样机；当前只用于布局和运动观察，禁止直接投产。
// 共用原点固定在四柱孔组，斗的外形中心可独立调整。
// X轴沿车长，Y轴横向，当前设计将垃圾卸向负X车尾。
// 实车正向仍需装车确认，模型方向不写入ROS坐标配置。
// 主轴靠近后口可以降低斗体，避免中央轴下扫穿过底板。
// 后轴上抬三毫米为电机包络留隙，斗体保持低位。
// 原底板保留厂家孔位参照，不把新后轴座当成已验证的承力接口。
// 后轴座短悬臂仅表达连接路径，打印截面与固定孔待定。
// 斗体外尺寸不含门杆、销轴与伸出的导料唇。
// 导料唇放到斗底下方，并向内搭接以形成连续共享面。
// 伸唇会增大偏载力矩，不能仅为了大袋避轮持续加长。
// 当前五厘米块仅作为可重复的刚体几何试验物。
// 七厘米物体也单独核验，不能外推任意垃圾袋。
// 门铰与固定门杆位于斗宽两端外侧，让杆避开斗腔。
// 门的终点角由固定锚构造给出，途中角度由闭环求解。
// 圆交点支路在放平时选定，全程不切换支路。
// 后门侧套边包在斗外，内部止挡限定闭门位置，打印密封仍待验证。
// 所有销耳仍有接口示意重合，不能直接导出整机生产STL。
// 丝杆外筒与内杆重叠表示套筒内部运动，外部障碍另行检查。
// 深绿电机包络是占位，采购后必须替换真实外形再校核。
// 丝杆是否自锁、断电保持、双向承载与限位均未实测。
// 前传感器塔固定在底板，倾斗时设备不随斗转动。
// 雷达圆柱只表达空间，不声称对应某个厂家型号。
// 扫描高度默认兼顾运输，后卸阶段允许遮挡且要求驻车。
// 未来互锁逻辑需在机器人控制层实现，本稿没有控制真实底盘。
// 相机视锥角属于设计输入，实际镜头规格未知。
// 高度参数可调，但每次改动都应重跑当前模型的几何验证。
// 均匀垃圾重心不能覆盖垃圾向后口聚集的情况。
// 三条垃圾轨迹是固定局部点的姿态包络，并非柔性袋动力学。
// 原车七百克只给出质量，无法推导它的真实重心。
// 新增斗、塔和执行器尚未称重，不给它们填写猜测的稳定收益。
// 支撑多边形需要实际轮胎接地测量，厂家外包络不能替代。

/* [运动与展示] */
dump_angle=0; // [0:1:40]
max_angle=40;
animate=false;
cutaway=false;
show_cg=false;
show_drop_envelope=false;
show_chassis=true;

/* [斗与原四柱] */
bucket_length=180;
bucket_width=200;
bucket_height=70;
bucket_center_x=-35;
wall=3;
pillar_height=24; // 原柱体高度待实测，外牙约5毫米与柱高不同。
deck_thickness=12;
pivot_x=-105;
pivot_above_deck=27;
guide_length=30;
guide_overlap=6;

/* [后门闭环] */
gate_arm=25;
gate_fixed_z=20;
gate_target_angle=-40;
link_end_clearance=14;
gate_lap=6;
gate_side_gap=0.3;

/* [执行器设计占位] */
fixed_pin_u=65;
fixed_pin_above_deck=13;
moving_pin_u=145;
moving_pin_z=-9;
actuator_closed=75;
actuator_stroke=60;
actuator_body_length=42;

/* [固定传感器占位] */
mast_x=70;
lidar_center_x=95;
lidar_diameter=65;
lidar_height=40;
lidar_scan_z=180; // 运输无遮挡；驻车卸料时允许斗遮扫描，控制互锁尚未实现。
camera_x=100;
camera_z=120;
camera_width=64;
camera_depth=30;
camera_height=40;
camera_hfov=70; // 视锥仅为设计假设，镜头真实视场角待实测。
camera_vfov=50;

/* [负载证据边界] */
base_mass_kg=0.7; // 用户实测整车约700g，不含本稿新斗/塔/执行器。
base_cg_known=false;
base_cg_x=0; // 仅在另行实测并将known改true后使用，默认不参与判稳。
payload_kg=0.5;
bag_width=50;
bag_height=50;

/* [Hidden] */
$fn=24;
body_offset_x=-22.641541;
vendor_top_z=52.7359;
ground_z=-88.52225;
deck_top=pillar_height+deck_thickness;
pivot_z=deck_top+pivot_above_deck;
theta=animate ? max_angle*(1-abs(2*$t-1)) : dump_angle;
xlo=bucket_center_x-bucket_length/2;
xhi=bucket_center_x+bucket_length/2;
// u为纵向X坐标，后轴局部原点靠卸料口；外门厚度独立分配。
rear=xlo+wall-pivot_x;
front=xhi-pivot_x;
H0=[rear,bucket_height];
function r2(v,a)=[v.x*cos(a)-v.y*sin(a),v.x*sin(a)+v.y*cos(a)];
function dot(a,b)=a.x*b.x+a.y*b.y;
function cross2(a,b)=a.x*b.y-a.y*b.x;
function world(v,a)=[pivot_x+r2([v.x,v.z],a).x,v.y,pivot_z+r2([v.x,v.z],a).y];
// 固定锚由放平/终点两姿态等杆长约束求得，门角由圆交点计算。
Q0=H0+[0,gate_arm];
Ht=r2(H0,max_angle);
Qt=Ht+r2([0,gate_arm],gate_target_angle);
dQ=Q0-Qt;
G=[(dot(Q0,Q0)-dot(Qt,Qt)-2*gate_fixed_z*dQ.y)/(2*dQ.x),gate_fixed_z];
gate_link=norm(Q0-G);
branch=cross2(G-H0,Q0-H0)>=0 ? 1 : -1;
function gate_q(a)=let(h=r2(H0,a),d=norm(G-h),e=(G-h)/d,
    q=(gate_arm*gate_arm-gate_link*gate_link+d*d)/(2*d),v=sqrt(max(0,gate_arm*gate_arm-q*q)))
    h+q*e+branch*v*[-e.y,e.x];
H=r2(H0,theta);
Q=gate_q(theta);
gate_phi=atan2(-(Q-H).x,(Q-H).y);
A=[pivot_x+fixed_pin_u,0,deck_top+fixed_pin_above_deck];
B=world([moving_pin_u,0,moving_pin_z],theta);
L=norm(B-A);
// 这些是概念几何护栏，真实推拉力和断电保持仍须选型验证。
assert(theta>=0 && theta<=max_angle && max_angle<=45);
assert(gate_lap>=4 && gate_side_gap>=0.2,"门套边尺寸无效");
assert(guide_overlap>=4,"导料唇需要有效面搭接");
assert(lidar_scan_z>pivot_z+bucket_height+gate_arm+5,"运输时雷达平面过低");
assert(L>=actuator_closed && L<=actuator_closed+actuator_stroke,"执行器铰距超出占位范围");
assert(abs(dQ.x)>1 && norm(G-H)<gate_arm+gate_link && norm(G-H)>abs(gate_arm-gate_link),"门四杆无实数闭环");
echo(angle_deg=theta,actuator_length_mm=L,gate_angle_deg=gate_phi,base_mass_kg=base_mass_kg,base_cg_known=base_cg_known);
// 整车固定镜头包括较轻的前传感器塔，重斗保持低位。
$vpt=[-20,0,95];
$vpr=[67,0,40];
$vpd=1350;

module bar(a,b,d){
    // 圆端杆用真实半径显示，不能只按中心线判断空间。
    hull(){translate(a) sphere(d=d);translate(b) sphere(d=d);}
}
module pin(p,length=18,d=6){
    // 全部后倾铰轴沿Y；短销为接口示意，未设计轴承公差。
    translate(p) rotate([90,0,0]) cylinder(d=d,h=length,center=true);
}
module moving(){
    // 绕Y负转使+X车头升高；垃圾向-X车尾卸出。
    translate([pivot_x,0,pivot_z]) rotate([0,-theta,0]) children();
}
module chassis(){
    // 已以四孔匹配厂家1:1模型，不从照片估计底盘大小。
    color("#63727f") multmatrix([[0,1,0,body_offset_x],[-1,0,0,0],[0,0,1,-vendor_top_z],[0,0,0,1]])
        import("../../../vendor/waveshare_wave_rover/WAVE ROVER_MODEL_STL.stl");
}
module fixed_frame(){
    // 原底板只是四柱定位参照，新架真实固定接口尚未定型。
    color("#4c96bd") translate([0,0,deck_top]) rotate([180,0,0])
        import("../main_deck_onepiece_v0/exports/main_deck_onepiece.stl");
    for(x=[-29,29]) for(y=[-43,43]) color("#c5a042") translate([x,y,0]) cylinder(d=7,h=pillar_height);
    for(s=[-1,1]) let(y=s*(bucket_width/2+link_end_clearance)){
        color("#3b8bb2"){
            // 左右后轴座从板内起脚；外悬耳只表达连接路径，截面需实物验证。
            bar([-95,s*65,deck_top],[pivot_x,y,pivot_z],11);
            bar([-65,s*65,deck_top],[pivot_x,y,pivot_z],11);
            bar([pivot_x,y,pivot_z],[pivot_x+G.x,y,pivot_z+G.y],8);
        }
        color("#d74d45") pin([pivot_x,y,pivot_z],16,7);
    }
    color("#3b8bb2"){
        // 前方双止挡承托放平斗底，前端抬起后自然脱开。
        for(y=[-65,65]) translate([30,y-6,deck_top]) cube([12,12,pivot_z-deck_top]);
        bar([A.x-15,A.y,deck_top],A,10);bar([A.x+15,A.y,deck_top],A,10);
    }
}
module bucket(){
    moving(){
        // 默认完整三固定壁；仅显式调试开关可移除近侧长壁。
        color([.94,.48,.15,1]){
            translate([rear,-bucket_width/2,0]) cube([front-rear,bucket_width,wall]);
            translate([front-wall,-bucket_width/2,wall]) cube([wall,bucket_width,bucket_height-wall]);
            translate([rear,bucket_width/2-wall,wall]) cube([front-rear,wall,bucket_height-wall]);
            if(!cutaway) translate([rear,-bucket_width/2,wall]) cube([front-rear,wall,bucket_height-wall]);
            // 止挡与侧壁相连，后面共面接触门内面；实际预压和密封条尚未设计。
            for(y=[-bucket_width/2,bucket_width/2-4]) translate([rear,y,10]) cube([8,4,12]);
        }
        color("#da8a26"){
            // 圆端上框内收半径，保持名义斗体包络并避免闭门穿插。
            for(y=[-bucket_width/2+2,bucket_width/2-2]) bar([rear+2,y,bucket_height-2],[front-2,y,bucket_height-2],4);
            for(x=[rear+2,front-2]) bar([x,-bucket_width/2+2,bucket_height-2],[x,bucket_width/2-2,bucket_height-2],4);
            for(s=[-1,1]) bar([0,s*bucket_width/2,3],[0,s*(bucket_width/2+link_end_clearance),0],10);
            bar([moving_pin_u,0,0],[moving_pin_u,0,moving_pin_z],10);
        }
        // 后导料唇内搭六毫米，底板下面有连续承托共享面。
        color("#edb757") translate([xlo-pivot_x-guide_length,-bucket_width/2,-wall])
            cube([guide_length+wall+guide_overlap,bucket_width,wall]);
    }
}
module gate(){
    // 门角来自同一四杆闭环，后门和斗体作为两个真实相对运动刚体。
    color([.96,.7,.22,1]) translate([pivot_x+H.x,0,pivot_z+H.y]) rotate([0,-gate_phi,0]){
        translate([-wall,-bucket_width/2-gate_side_gap-wall,-bucket_height])
            cube([wall,bucket_width+2*(gate_side_gap+wall),bucket_height]);
        // 两侧套边向前包住斗壁，留出设计侧隙；密封与压紧依赖后续实配。
        for(s=[-1,1]) translate([-wall,s<0?-bucket_width/2-gate_side_gap-wall:bucket_width/2+gate_side_gap,-bucket_height])
            cube([wall+gate_lap,wall,bucket_height]);
    }
    for(s=[-1,1]) let(y=s*(bucket_width/2+link_end_clearance)){
        color("#ad5bb9"){
            bar([pivot_x+H.x,y,pivot_z+H.y],[pivot_x+Q.x,y,pivot_z+Q.y],7);
            bar([pivot_x+G.x,y,pivot_z+G.y],[pivot_x+Q.x,y,pivot_z+Q.y],6);
            bar([pivot_x+H.x,s*bucket_width/2,pivot_z+H.y],[pivot_x+H.x,y,pivot_z+H.y],7);
        }
        for(v=[H,Q,G]) color("#eed05a") pin([pivot_x+v.x,y,pivot_z+v.y],10,4);
    }
}
module actuator(){
    // 采用较短伸缩包络，不能沿用大斗125mm外筒塞入80mm闭距。
    u=(B-A)/L;
    color("#4ca78d") bar(A+u*7,A+u*actuator_body_length,14);
    color("#c4d0d5") bar(A+u*(actuator_body_length-7),B,7);
    color("#27665b") bar(A+u*12,A+u*30,20);
    for(p=[A,B]) color("#eed05a") pin(p,20,6);
}
module sensors(){
    // 设备尺寸与孔位未知：圆柱/盒体仅作可调外形占位。
    plate_z=lidar_scan_z-lidar_height/2-5;
    color("#4089ad"){
        translate([mast_x-7,-13,deck_top]) cube([14,26,plate_z-deck_top]);
        bar([mast_x,0,plate_z],[lidar_center_x,0,plate_z],12);
        translate([lidar_center_x-36,-36,plate_z]) cube([72,72,5]);
        bar([mast_x,0,camera_z],[camera_x,0,camera_z],9);
    }
    color("#c85455") translate([lidar_center_x,0,plate_z+5]) cylinder(d=lidar_diameter,h=lidar_height);
    // 雷达环表示运输扫描平面；卸料会出现遮挡，实车需驻车并做互锁。
    color([.95,.3,.3,.35]) translate([lidar_center_x,0,lidar_scan_z])
        difference(){cylinder(r=44,h=.6);translate([0,0,-1]) cylinder(r=42,h=3);}
    color("#3d4856") translate([camera_x-camera_depth/2,-camera_width/2,camera_z-camera_height/2])
        cube([camera_depth,camera_width,camera_height]);
    color("#80cde3") translate([camera_x+camera_depth/2,0,camera_z]) rotate([0,90,0]) cylinder(d=18,h=4);
}
module load_markers(){
    // 三点为均匀、后口底部、后唇高半斗的垃圾CG，整车重心仍未知。
    for(v=[[bucket_center_x,bucket_height/2],[xlo,0],[xlo-guide_length,bucket_height/2]]) let(p=world([v.x-pivot_x,0,v.y],theta)){
        color(v.x==bucket_center_x?"#e7404c":(v.y==0?"#9b54b4":"#ad1858")) translate(p) sphere(d=9);
        color([.8,.1,.2,.3]) bar(p,[p.x,p.y,ground_z],1);
        // 固定局部点的全角轨迹只描述条件偏载，不模拟柔性垃圾袋。
        color([.7,.15,.3,.5]) for(a=[0:5:max_angle-5])
            bar(world([v.x-pivot_x,0,v.y],a),world([v.x-pivot_x,0,v.y],min(a+5,max_angle)),1);
    }
}
module drop_envelope(){
    // 辅助图检查车尾通道，计入试验块高度，默认整车图隐藏该框。
    p=world([xlo-pivot_x-guide_length,0,0],max_angle);
    color([.2,.75,.6,.16]) translate([p.x-bag_width/2,p.y-bag_width/2,ground_z])
        cube([bag_width,bag_width,p.z+bag_height-ground_z]);
}
if(show_chassis) chassis();
fixed_frame();bucket();gate();actuator();sensors();
if(show_cg) load_markers();
if(show_drop_envelope) drop_envelope();
