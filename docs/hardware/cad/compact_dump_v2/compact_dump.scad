// 无活动门小后卸斗；厂家原车参照来自本地WAVE ROVER STL/DXF。
// 用户实测装电池/柱/电子的车重约700g，实际重心尚未测得。
// 0.5kg是样机目标，本稿只验证空间与运动，不能直接投产。
// X沿车长、Y横向，相机朝+X，垃圾向-X车尾卸出。
// 实车正向仍需装车确认，本稿不修改ROS坐标或控制参数。
// 后横轴和单丝杆保留，前端抬起时固定后斜壁一同转动。
// 后斜壁由内底连续上升，运输时提供浅挡料高度。
// 低后缘限制填充高度，不能按70毫米满壁高度装散料。
// 卸料时坡向下降不保证滑动，实际摩擦与袋体变形需要实测。
// 后壁为实心楔形，与底板及两侧壁连续连接，省去门和连杆。
// 原低位导料唇已删除，物料从真实斜壁上缘离开。
// 不用加长外伸或提高角度掩盖有限物体落料空间问题。
// 原底座只表达四柱定位，新轴座承力接口仍未完成制造设计。
// 斗体尺寸不包括横向短轴销和外悬轴座。
// 所有销耳共轴连接仍为概念接口，轴承和转动间隙尚未设计。
// 丝杆内外筒重叠表达伸缩运动，深绿色电机仅为外形占位。
// 自锁、断电保持、双向承载与限位必须在选型后验证。
// 前塔固定到静止底板，雷达和相机不随斗旋转。
// 设备外形与相机视场角为设计输入，真实型号和安装尺寸未知。
// 运输扫描需留空；停车卸料时遮挡区须由后续控制互锁处理。
// 该模型不发送控制指令，不证明真实车辆驻车能力。
// 均匀和后口偏载点只描述条件重心，不能代表柔性垃圾动态。
// 原车重量不能推出重心，新增机构重量也不填写猜测值。
// 支撑多边形仍需测真实轮胎接地区，厂家外包络只用于碰撞。
// 指定刚体路径取脚印最高支承点，空间可行不等于必然自行滑出。
// 参数修改后须重跑验证，不能沿用之前导出的图片或JSON结论。

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
ramp_run=45;
ramp_rise=25;
axle_end_clearance=14;

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
// u沿X，内底到后缘的固定坡高以底板上表面为基准。
rear=xlo-pivot_x;
front=xhi-pivot_x;
ramp_start=rear+ramp_run;
ramp_angle=atan(ramp_rise/ramp_run);
function r2(v,a)=[v.x*cos(a)-v.y*sin(a),v.x*sin(a)+v.y*cos(a)];
function world(v,a)=[pivot_x+r2([v.x,v.z],a).x,v.y,pivot_z+r2([v.x,v.z],a).y];
A=[pivot_x+fixed_pin_u,0,deck_top+fixed_pin_above_deck];
B=world([moving_pin_u,0,moving_pin_z],theta);
L=norm(B-A);
// 这些是概念几何护栏，真实推拉力和断电保持仍须选型验证。
assert(theta>=0 && theta<=max_angle && max_angle<=45);
assert(ramp_run>wall && ramp_run<bucket_length-wall && ramp_rise>wall,"后斜壁截面无效");
assert(wall+ramp_rise<bucket_height && ramp_angle<max_angle,"卸料后斜壁必须向外下坡");
assert(lidar_scan_z>pivot_z+bucket_height+5,"运输时雷达平面过低");
assert(L>=actuator_closed && L<=actuator_closed+actuator_stroke,"执行器铰距超出占位范围");
echo(angle_deg=theta,actuator_length_mm=L,outward_slope_deg=theta-ramp_angle,base_mass_kg=base_mass_kg,base_cg_known=base_cg_known);
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
    for(s=[-1,1]) let(y=s*(bucket_width/2+axle_end_clearance)){
        color("#3b8bb2"){
            // 左右后轴座从板内起脚；外悬耳只表达连接路径，截面需实物验证。
            bar([-95,s*65,deck_top],[pivot_x,y,pivot_z],11);
            bar([-65,s*65,deck_top],[pivot_x,y,pivot_z],11);
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
        // 默认三面高壁加低斜后壁，后口与底连续，顶部保持敞开。
        color([.94,.48,.15,1]){
            translate([rear,-bucket_width/2,0]) cube([front-rear,bucket_width,wall]);
            translate([front-wall,-bucket_width/2,wall]) cube([wall,bucket_width,bucket_height-wall]);
            translate([rear,bucket_width/2-wall,wall]) cube([front-rear,wall,bucket_height-wall]);
            if(!cutaway) translate([rear,-bucket_width/2,wall]) cube([front-rear,wall,bucket_height-wall]);
        }
        // 填实楔形只占坡面以下，验证时同样保留上方开放的实际空间。
        color("#edb757") translate([0,bucket_width/2,0]) rotate([90,0,0])
            linear_extrude(height=bucket_width) polygon([[rear,wall],[ramp_start,wall],[rear,wall+ramp_rise]]);
        color("#da8a26"){
            // 保留三面上框，后缘不再横跨高杆，以免形成虚假的卸料障碍。
            for(y=[-bucket_width/2+2,bucket_width/2-2]) bar([rear+2,y,bucket_height-2],[front-2,y,bucket_height-2],4);
            bar([front-2,-bucket_width/2+2,bucket_height-2],[front-2,bucket_width/2-2,bucket_height-2],4);
            // 主轴耳保留真实连接路径；概念共轴邻域仍未完成转动公差设计。
            for(s=[-1,1]) bar([0,s*bucket_width/2,3],[0,s*(bucket_width/2+axle_end_clearance),0],10);
            bar([moving_pin_u,0,0],[moving_pin_u,0,moving_pin_z],10);
        }
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
    // 三点为中部浅载假设、后缘表面、后缘高半斗偏载，车CG仍未知。
    for(v=[[bucket_center_x,wall+ramp_rise/2],[xlo,wall+ramp_rise],[xlo,wall+ramp_rise+bucket_height/2]]) let(p=world([v.x-pivot_x,0,v.y],theta)){
        color(v.x==bucket_center_x?"#e7404c":(v.y==wall+ramp_rise?"#9b54b4":"#ad1858")) translate(p) sphere(d=9);
        color([.8,.1,.2,.3]) bar(p,[p.x,p.y,ground_z],1);
        // 全角轨迹为固定局部点姿态包络，真实垃圾滑动不受这条线约束。
        color([.7,.15,.3,.5]) for(a=[0:5:max_angle-5])
            bar(world([v.x-pivot_x,0,v.y],a),world([v.x-pivot_x,0,v.y],min(a+5,max_angle)),1);
    }
}
module drop_envelope(){
    // 真实出口为后斜壁上缘；仅辅助图显式显示有限宽落料通道。
    p=world([rear,0,wall+ramp_rise],max_angle);
    color([.2,.75,.6,.16]) translate([p.x-bag_width/2,p.y-bag_width/2,ground_z])
        cube([bag_width,bag_width,p.z+bag_height-ground_z]);
}
if(show_chassis) chassis();
fixed_frame();bucket();actuator();sensors();
if(show_cg) load_markers();
if(show_drop_envelope) drop_envelope();
