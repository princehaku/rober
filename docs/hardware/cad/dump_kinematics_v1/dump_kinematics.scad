// 翻斗运动概念稿：单位毫米；尺寸可调，尚无打印承载与整车稳定批准。
// 厂家参照为本地 WAVE ROVER DXF 与 WAVE ROVER_MODEL_STL.stl。
// 四柱轴线沿用 DXF 的58×86；新支架截面、支点与柱高均为设计参数。

/* [运动] */
// 动画仅扫这一段受检范围，执行器选型后再扩大可用倾角。
dump_angle=35; // [0:1:55]
max_angle=55;
animate=false;
show_chassis=true;
cutaway=true;
// 重心点只帮助发现后翻风险，未加入猜测的车体质量。
show_cg=true;

/* [斗和四柱] */
// 用户尺寸是外尺寸；壁厚与后门会占用部分内部空间。
bucket_length=400;
bucket_width=200;
bucket_height=200;
wall=3;
pillar_height=24; // 柱体未实测；外露5毫米螺杆不等于柱高。
deck_thickness=12;
body_offset_x=-22.641541;

/* [主轴和门连杆] */
// 主轴高于底座，给后门全高扫掠留出接近地面的空间。
pivot_x=-110;
pivot_above_deck=74;
gate_arm=35;
link_y_clearance=16;
side_support_offset=12;

/* [丝杆铰点与外包络] */
// 支点以主轴和板面为基准，换丝杆时可先调这组参数。
fixed_pin_dx=60;
fixed_pin_above_deck=35;
moving_pin_dx=260;
moving_pin_dz=-12;
actuator_closed=195;
// 允许行程与运动所需行程分别表达，后者由铰距变化计算。
actuator_stroke=100;
actuator_radius=10;

/* [Hidden] */
$fn=32;
vendor_top_z=52.7359;
vendor_ground_z=-88.52225;
// 顶板基准和地面基准均来自厂家模型，真实轮胎变形尚未计入。
deck_top=pillar_height+deck_thickness;
pivot_z=deck_top+pivot_above_deck;
// 后门厚度向后分配，底/侧壁止于门内面，放平仅接触且外长保持400。
rear=body_offset_x-bucket_length/2+wall-pivot_x;
front=body_offset_x+bucket_length/2-pivot_x;
link_y=bucket_width/2+link_y_clearance;
theta=animate ? max_angle*(1-abs(2*$t-1)) : dump_angle;
P=[pivot_x,0,pivot_z];
A=[pivot_x+fixed_pin_dx,0,deck_top+fixed_pin_above_deck];
// 用刚体变换得到各铰心，禁止按不同动画曲线拉开端点。
function rot(v,a)=[v.x*cos(a)-v.z*sin(a),v.y,v.x*sin(a)+v.z*cos(a)];
function world(v,a)=P+rot(v,a);
function rod_length(a)=norm(world([moving_pin_dx,0,moving_pin_dz],a)-A);
H=world([rear,0,bucket_height],theta);
B=world([moving_pin_dx,0,moving_pin_dz],theta);
// 顶铰后门由平行四杆维持全局竖直，不使用另一条门动画曲线。
G0=P+[0,0,gate_arm];
G1=H+[0,0,gate_arm];
cg=world([body_offset_x-pivot_x,0,bucket_height/2],theta);
L=norm(B-A);
// 这些护栏约束概念模型的几何域，不代表任何材料强度证明。
assert(theta>=0 && theta<=max_angle && max_angle<=60,"倾角超出概念验证范围");
assert(pillar_height>=15 && bucket_length>=300 && bucket_width>=180 && bucket_height>=100);
assert(gate_arm>=20 && link_y_clearance>=12 && actuator_radius>0);
assert(side_support_offset>=12,"侧座需要避开倾起斗壁");
assert(rear<0 && front>moving_pin_dx && moving_pin_dx>fixed_pin_dx);
// 参数改变后支座脚仍需落在旧底板上，禁止生成悬空支腿而无提示。
assert(pivot_x+2>=body_offset_x-100 && pivot_x+73<=body_offset_x+100,"主轴座脚越出底板");
assert(A.x-25>=body_offset_x-100 && A.x+25<=body_offset_x+100,"丝杆底脚越出底板");
assert(L>=actuator_closed && L<=actuator_closed+actuator_stroke,"丝杆铰距超出设定伸缩范围");
assert(H.z-bucket_height>vendor_ground_z+5,"后门底部接近地面，请调整主轴高度/倾角");
echo(angle_deg=theta,actuator_length_mm=L,gate_bottom_z=H.z-bucket_height,cargo_cg=cg);
// 默认镜头可看到两侧机构；切开近侧壁，清楚展示丝杆。
$vpt=[-95,0,165];
$vpr=[70,0,25];
$vpd=1850;

module bar(a,b,d){
    // 圆端梁在连接处保持几何重合；此处尚未设计打印榫口/螺栓公差。
    hull(){translate(a) sphere(d=d);translate(b) sphere(d=d);}
}
module axle(p,length=22,d=7){
    // 铰轴统一沿Y，模型中的短销仅表示紧固件接口。
    translate(p) rotate([90,0,0]) cylinder(d=d,h=length,center=true);
}
module moving(){
    // OpenSCAD 绕Y负角度，对应X轴向上翻起的右手刚体变换。
    translate(P) rotate([0,-theta,0]) children();
}
module chassis(){
    // 原始STL四孔与DXF一致后采用刚体变换，完全不缩放。
    color("#64727d") multmatrix([[0,1,0,body_offset_x],[-1,0,0,0],
        [0,0,1,-vendor_top_z],[0,0,0,1]])
        import("../../../vendor/waveshare_wave_rover/WAVE ROVER_MODEL_STL.stl");
}
module frame(){
    // 这里显示连续的受力路径；销轴附近仍是接口示意，未做孔隙配合。
    // 底座仅作原四柱定位参照；本稿未修改现有可代打STL。
    color("#4693be") translate([0,0,deck_top]) rotate([180,0,0])
        import("../main_deck_onepiece_v0/exports/main_deck_onepiece.stl");
    for(x=[-29,29]) for(y=[-43,43]) color("#c4a04d")
        translate([x,y,0]) cylinder(d=7,h=pillar_height);
    // 两个三角侧座从底座边缘长到主轴外侧，固定路径清晰可见。
    for(s=[-1,1]) color("#3686ad"){
        bar([pivot_x+10,s*70,deck_top],[pivot_x,s*(bucket_width/2+side_support_offset),pivot_z],13);
        bar([pivot_x+65,s*70,deck_top],[pivot_x,s*(bucket_width/2+side_support_offset),pivot_z],13);
        bar([pivot_x+10,s*70,deck_top],[pivot_x+65,s*70,deck_top],16);
        // 门四杆固定短臂上置，长杆因此保持在侧壁以外。
        bar([pivot_x,s*link_y,pivot_z],[pivot_x,s*link_y,pivot_z+gate_arm],9);
        bar([pivot_x,s*(bucket_width/2+side_support_offset),pivot_z],[pivot_x,s*link_y,pivot_z],12);
        // 前部硬止挡只在放平接触，承担运输姿态定位。
        translate([55,s*70-6,deck_top]) cube([12,12,pivot_z-deck_top]);
    }
    color("#3686ad"){
        // 丝杆下座固定到板面；具体螺栓和局部补强待制造设计。
        bar([A.x-18,0,deck_top],[A.x,0,A.z],14);
        bar([A.x+18,0,deck_top],[A.x,0,A.z],14);
    }
    for(s=[-1,1]) color("#d95043") axle([pivot_x,s*(bucket_width/2+6),pivot_z],30,8);
}
module bucket(){
    moving(){
        // 橙色部分为斗与随斗托架，近侧壁可剖去以看清机构。
        color([.94,.48,.13,.55]){
            translate([rear,-bucket_width/2,0]) cube([front-rear,bucket_width,wall]);
            translate([front-wall,-bucket_width/2,wall]) cube([wall,bucket_width,bucket_height-wall]);
            translate([rear,bucket_width/2-wall,wall]) cube([front-rear,wall,bucket_height-wall]);
            if(!cutaway) translate([rear,-bucket_width/2,wall]) cube([front-rear,wall,bucket_height-wall]);
        }
        color("#d98322"){
            // 四条外边梁显示完整包络；剖切不改变验证用三壁包络。
            for(s=[-1,1]){
                // 圆端梁的中心内收半径，整个斗体保持名义外包络且不穿后门。
                bar([rear+3.5,s*(bucket_width/2-3.5),3.5],[front-3.5,s*(bucket_width/2-3.5),3.5],7);
                bar([rear+2.5,s*(bucket_width/2-2.5),bucket_height-2.5],[front-2.5,s*(bucket_width/2-2.5),bucket_height-2.5],5);
                bar([front-2.5,s*(bucket_width/2-2.5),4],[front-2.5,s*(bucket_width/2-2.5),bucket_height-2.5],5);
                bar([rear+2.5,s*(bucket_width/2-2.5),4],[rear+2.5,s*(bucket_width/2-2.5),bucket_height-2.5],5);
                // 斗侧主轴小耳将活动斗连接到外侧短轴。
                bar([0,s*bucket_width/2,4],[0,s*(bucket_width/2+8),0],12);
            }
            // 活动上耳位于斗底下方；丝杆上铰与此处严格共轴。
            bar([moving_pin_dx,0,0],[moving_pin_dx,0,moving_pin_dz],12);
        }
    }
}
module gate(){
    // 门板位于后口外侧，放平时与底边、侧边共面接触。
    // 该门保持世界坐标竖直，开合角恰为斗倾角；连杆闭环固定此姿态。
    color([.95,.69,.22,.85]) translate([H.x-wall,-bucket_width/2,H.z-bucket_height])
        cube([wall,bucket_width,bucket_height]);
    for(s=[-1,1]){
        color("#bd5bc4"){
            bar([H.x,s*link_y,H.z],[G1.x,s*link_y,G1.z],9);
            bar([G0.x,s*link_y,G0.z],[G1.x,s*link_y,G1.z],7);
            // 门侧耳跨过外壁，将长杆受力传到顶铰门板。
            bar([H.x,s*bucket_width/2,H.z],[H.x,s*link_y,H.z],9);
        }
        for(p=[P,H,G0,G1]) color("#f1d15c") axle([p.x,s*link_y,p.z],10,5);
    }
}
module actuator(){
    // 深绿色段是电机外包络占位，真实外形需随最终型号替换。
    // 两段同轴伸缩包络；外筒长度固定、内杆重叠变化，端点始终在两铰。
    u=(B-A)/L;
    color("#51ad8b") bar(A+u*10,A+u*125,2*actuator_radius);
    color("#becad0") bar(A+u*112,B,9);
    color("#275f58") bar(A+u*22,A+u*48,27);
    for(p=[A,B]) color("#f3d35c") axle(p,28,7);
}
module cargo_marker(){
    // 红点仅表示均匀2kg垃圾的假设重心，不代表整车重心。
    color("#e83b48") translate(cg) sphere(d=13);
    color([.9,.15,.2,.45]) bar(cg,[cg.x,cg.y,vendor_ground_z],1.5);
}
if(show_chassis) chassis();
frame();bucket();gate();actuator();
if(show_cg) cargo_marker();
// 地面只用细边框提示，不遮住轮胎和后门最低点。
color([.5,.6,.6,.4]) for(y=[-145,145]) bar([-440,y,vendor_ground_z],[220,y,vendor_ground_z],1);
