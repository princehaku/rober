// N20打印推举试装件；商品图来源见本地n20_reference，用户已确认3V/60RPM，持续工作扭矩未知。
// 本文件坐标：Z为执行器轴向s，X为横向，Y为壳体上下方向。
// 固定端销中心s=0，输出销中心随螺母平移；丝杆只旋转不轴向移动。
// 电机、金属销和紧固件不属于打印件，装配中用不同颜色显示。
// 外部传动比可改，改齿数后必须重新核对机身与导轨净空。
// 止推通过独立轴肩、垫圈、壳体回到下铰，不让电机轴承受推杆轴向力。
// 两半壳沿Y=0分开打印，便于装入轴肩并检查螺纹与齿轮。
// 螺纹用共轭螺旋多面体，母牙增加径向和轴向间隙，不用装饰螺旋代替。
// 滑块两侧受C形导轨约束，长推杆中空，容纳闭合时伸入的丝杆。
// 断电保持、PLA强度和摩擦均未验证；机械端挡不代替断电限位。
// 两处检修孔只供停机插销，驱动前必须拆下，不能带销转动。
// 导出为试配样件，先打印短牙和D孔试片，尺寸确认后再打印全套。

// 三伏六十转由用户确认；商家多档列表无法提供该台电机的连续工作扭矩。
// 单线导程每转两毫米，几何无载时间不包含负载掉速和启停过程。
// 模数一的二十齿齿顶径已接近竖向空间上限，改减速比须重查整车。
// 轴肩两侧各放一片止推垫圈，正反力都经过下壳和下转接座传递。
// 垫圈默认打印仅供拟合；磨损和发热可能要求独立耐磨垫片替换。
// 输入齿轮轴颈由分体壳径向承托，D轴径向小螺钉只负责夹紧传扭。
// 机身夹持套预留间隙，不使用图纸未提供的端面螺孔深度。
// 电机尾电极另留五毫米空间预算，真实焊线不能碰齿轮或滑块。
// 合壳左螺柱向外移，避免圆柱内缘伸进防转螺母的滑道。
// 上座底脚前偏以避轨前端，螺栓孔跟随该底脚一起移动。
// 两座底脚横向加宽，安装孔放到双耳腿外，使工具可以直线接近。
// 下座采用沉头齐平，凸起螺母会与邻近轴承壳底发生干涉。
// 外置开关只提供安装孔，开关尺寸和控制接线都不在本稿中猜测。
// 需要先断电并手动卸载后插检修销，不能以电机堵转代替到位停止。
// 原四柱与新框紧固仍未实配，本打印包不含整个斗或四柱平台的制造件。

part="assembly";
phase_error=0;
motor_voltage=3; // 用户确认当前电机3V，未据此配置驱动电气。
motor_rpm=60; // 用户确认60RPM，真实带载转速和持续扭矩未知。
extension=0;
exploded=false;
thread_d=10;
lead=2;
thread_depth=1;
thread_clearance=.25;
axial_clearance=.12;
thread_start=22;
thread_end=74;
nut_start=23;
nut_length=14;
closed_length=80.02499609497;
working_stroke=31.77679431348;
guide_end=71;
gear_module=1;
screw_teeth=20;
motor_teeth=20;
backlash=.2;
motor_width=12;
motor_height=10;
motor_length=24.1;
motor_shaft_d=3;
motor_shaft_flat=1; // 商品D截面总高2.50减半径1.50，得平面距中心1.00。
motor_shaft_length=10;
fit=.3;
pin_d=3.3;
nut_af=4.3; // M2螺母最大对边4.00，打印窝按对边再留0.30。
shell_boss_r=3.4;
housing_bolt_length=22; // 沉头长度含头，尾端1.4毫米外露也计入包络。
$fn=40;
// 横向中心距由两齿轮节圆求得，不能单独拖动电机破坏啮合。
gear_center=gear_module*(screw_teeth+motor_teeth)/2;
motor_face=22;
shaft_angle=-360*extension/lead;
motor_angle=-shaft_angle*screw_teeth/motor_teeth+180/motor_teeth;
assert(thread_d>8 && lead>=1.5 && thread_clearance>.1 && thread_clearance<.5);
assert(lead>1.6+2*axial_clearance,"母牙轴向间隙吃掉牙顶");
assert(extension>=0 && extension<=working_stroke);
assert(nut_start>=thread_start && nut_start+nut_length+working_stroke<=thread_end);
assert(closed_length-5>thread_end,"闭合上销与丝杆末端过近");
assert(gear_center-motor_width/2-fit>13.4,"并排电机侵入导轨");
assert(gear_module>=.9 && screw_teeth>=18 && motor_teeth>=18);

function polar(r,a)=[r*cos(a),r*sin(a)];
function invdeg(r,b)=sqrt(max(0,r*r/(b*b)-1))*180/PI-acos(min(1,b/r));
module gear(z,h=4){
    // 标准20度渐开线；两侧各减半齿隙，齿根圆连接所有齿。
    rp=gear_module*z/2;rb=rp*cos(20);ra=rp+gear_module;rf=rp-1.25*gear_module;
    half=90/z-backlash/rp*180/PI/2;
    radii=[for(i=[0:10]) rb+(ra-rb)*i/10];
    flank=[for(r=radii) polar(r,half+invdeg(rp,rb)-invdeg(r,rb))];
    linear_extrude(height=h) union(){
        circle(r=rf);
        for(i=[0:z-1]) rotate(i*360/z) polygon(concat([polar(rf,half+invdeg(rp,rb))],flank,
            [for(j=[len(flank)-1:-1:0]) [flank[j].x,-flank[j].y]],[polar(rf,-half-invdeg(rp,rb))]));
    }
}
module helical_thread(length,clearance=0,axial=0){
    // 梯形轴向截面沿右旋螺线扫掠，起末多出一圈后裁齐。
    rr=thread_d/2-thread_depth+clearance;rt=thread_d/2+clearance;
    turns=ceil(length/lead)+2;steps=turns*32;
    profile=[[rr,-.8-axial],[rt,-.275-axial],[rt,.275+axial],[rr,.8+axial]];
    pts=[for(i=[0:steps]) for(v=profile) let(a=i*360/32) [v.x*cos(a),v.x*sin(a),-lead+i*lead/32+v.y]];
    faces=concat([[3,2,1,0]],[for(i=[0:steps-1]) for(j=[0:3]) each [[4*i+j,4*i+(j+1)%4,4*(i+1)+(j+1)%4],[4*i+j,4*(i+1)+(j+1)%4,4*(i+1)+j]]],[[4*steps,4*steps+1,4*steps+2,4*steps+3]]);
    intersection(){
        // 母牙根部再放0.05，覆盖根圆柱与螺旋分面的微小离散裂隙。
        union(){cylinder(r=rr+(clearance>0?.05:0),h=length);polyhedron(points=pts,faces=faces,convexity=30);}
        translate([-rt-1,-rt-1,0]) cube([2*rt+2,2*rt+2,length]);
    }
}
module screw(){
    // 轴肩一体打印；两面垫圈夹在壳内台阶间，留微小轴向游隙。
    cylinder(d=6,h=22);
    translate([0,0,8]) cylinder(d=12,h=3);
    translate([0,0,14]) gear(screw_teeth);
    translate([0,0,thread_start]) helical_thread(thread_end-thread_start);
}
module d_bore(h,extra=0){
    // D平面和圆弧共用商品图尺寸，试片用于补偿实际打印收缩。
    intersection(){cylinder(d=motor_shaft_d+2*extra,h=h);translate([-5,-5,0]) cube([5+motor_shaft_flat+extra,10,h]);}
}
module input_gear(){
    difference(){
        union(){translate([0,0,8]) cylinder(d=6,h=10);translate([0,0,14]) gear(motor_teeth);translate([0,0,18]) cylinder(d=8,h=3.7);}
        // 独立长轴颈在壳中径向承托，D孔联接只传扭；径向M2螺钉压紧平面。
        translate([0,0,11.8]) d_bore(11,.15);
        translate([0,0,20]) rotate([0,90,0]) cylinder(d=1.8,h=6);
    }
}
module slider(){
    difference(){
        union(){
            translate([-10,-8,nut_start]) cube([20,16,nut_length]);
            translate([-8,-8,nut_start+nut_length-.3]) cube([16,16,closed_length-nut_start-nut_length+.3]);
            translate([-8,0,closed_length]) rotate([0,90,0]) cylinder(r=6,h=16);
        }
        // 女牙与轴牙同一绝对相位；装配轴转负角时滑块向正s移动。
        intersection(){translate([0,0,thread_start]) helical_thread(60,thread_clearance,axial_clearance);translate([-8,-8,nut_start-.1]) cube([16,16,nut_length+.2]);}
        translate([0,0,nut_start+nut_length-.01]) cylinder(d=thread_d+1.4,h=closed_length-5-nut_start-nut_length+.01);
        translate([-12,0,closed_length]) rotate([0,90,0]) cylinder(d=pin_d,h=24);
        // 检修销偏离中央螺杆，避免横销直接穿过螺纹轴。
        translate([7.2,-12,nut_start+5]) rotate([-90,0,0]) cylinder(d=2.2,h=24);
    }
}
module housing_solid(){
    // 两侧C轨固定防转；输出杆比螺母窄，前端挡块只拦螺母。
    for(s=[-1,1]){
        translate([s<0?-13.4:10.4,-10.3,21]) cube([3,20.6,guide_end-21]);
        for(y=[-10.3,8.3]) translate([s<0?-13.4:8.8,y,21]) cube([4.6,2,guide_end-21]);
    }
    translate([-13.4,-10.3,20.8]) cube([26.8,20.6,.8]);
    translate([-13.4,-10.3,guide_end]) cube([26.8,20.6,3]);
    // 后止推座与外侧旁通梁连接导轨，避开齿轮转动圆。
    translate([-9,-9,5.5]) cube([gear_center+18,18,7.5]);
    translate([-13.4,-9,6]) cube([1.8,18,18]);
    translate([-13.4,-9,6]) cube([5,18,7]);
    translate([gear_center+11.6,-8,6]) cube([2.8,16,motor_face+motor_length+5-6]);
    // 后铰耳通过实体桥连止推座，横销位于丝杆尾端之后。
    translate([-6,0,0]) rotate([0,90,0]) cylinder(r=5,h=12);
    translate([-6,-5,0]) cube([12,10,6]);
    // 夹持电机机身，不使用未知深度的M1.6端面螺孔。
    translate([gear_center-8.5,-7.8,motor_face]) cube([17,15.6,motor_length+2]);
    translate([gear_center+8,-7.8,motor_face]) cube([6.4,15.6,motor_length+5]);
    for(z=[28,nut_start+5+working_stroke]) translate([5.5,8.3,z-3]) cube([7.9,3,6]);
    // 限位安装耳只留长槽，开关型号待选；其位置在滑块端面邻近。
    for(z=[24,68]) translate([-18,-4,z-4]) cube([5,8,8]);
    for(v=[[-14,28],[-14,70],[gear_center+12.7,9],[gear_center+12.7,45]])
        translate([v.x,-10.3,v.y]) rotate([-90,0,0]) cylinder(r=shell_boss_r,h=20.6);
}
module housing(){
    difference(){
        housing_solid();
        // 丝杆尾端从s6起；下销中心s0与轴尾之间保留材料与间隙。
        translate([0,0,5]) cylinder(d=6.5,h=9);
        translate([0,0,7.2]) cylinder(d=12.6,h=4.6);
        translate([gear_center,0,5]) cylinder(d=6.5,h=9);
        translate([-9.2,-8.2,20]) cube([18.4,16.4,2]);
        translate([-8.4,-8.2,guide_end-.1]) cube([16.8,16.4,4]);
        translate([gear_center-motor_width/2-fit,-motor_height/2-fit,motor_face-.1]) cube([motor_width+2*fit,motor_height+2*fit,motor_length+2.2]);
        translate([gear_center,0,12.9]) cylinder(d=8.8,h=10);
        translate([-15,0,0]) rotate([0,90,0]) cylinder(d=pin_d,h=30);
        for(z=[28,nut_start+5+working_stroke]) translate([7.2,-12,z]) rotate([-90,0,0]) cylinder(d=2.2,h=26);
        for(v=[[-14,28],[-14,70],[gear_center+12.7,9],[gear_center+12.7,45]]){
            translate([v.x,-12,v.y]) rotate([-90,0,0]) cylinder(d=2.3,h=26);
            // 沉头和六角螺母陷入壳耳，紧固件不突破已验证的外包络。
            translate([v.x,9.1,v.y]) rotate([-90,0,0]) cylinder(d1=2.3,d2=4.5,h=1.3);
            translate([v.x,-10.31,v.y]) rotate([-90,0,0]) cylinder(d=nut_af/cos(30),h=1.8,$fn=6);
        }
        for(z=[24,68]) translate([-15.5,-8,z]) rotate([-90,0,0]) cylinder(d=2.2,h=16);
    }
}
module shell(side){
    // 分型面Y=0，装配螺钉夹紧上下半壳，丝杆轴肩可从侧面装入。
    intersection(){housing();translate([-30,side<0?-30:0,-8]) cube([80,30,100]);}
}
module washer(){difference(){cylinder(d=12,h=.5);translate([0,0,-.1]) cylinder(d=6.4,h=.7);}}
module motor(angle=motor_angle){
    // 商品图：机身12×10×24.1，轴外露10；尾部电极另预留5毫米。
    color("#9a9fa5") translate([gear_center-motor_width/2,-motor_height/2,motor_face]) cube([motor_width,motor_height,motor_length]);
    color("#d4ba68") translate([gear_center,0,motor_face-motor_shaft_length]) rotate([0,0,angle]) d_bore(motor_shaft_length);
}
module drive_assembly(delta=extension,explode=exploded){
    // 装配使用真实输出行程，不通过拉伸零件制造假动作。
    assert(delta>=-.000001 && delta<=working_stroke+.000001);
    color("#4b95ad") translate([0,explode?-22:0,0]) shell(-1);
    color([.3,.62,.72,.65]) translate([0,explode?22:0,0]) shell(1);
    color("#e3b952") rotate([0,0,-360*delta/lead]) difference(){screw();translate([0,0,-1]) cylinder(d=6,h=7);}
    color("#dc7c36") translate([0,0,delta+(explode?22:0)]) slider();
    color("#8ac780") translate([gear_center,0,0]) rotate([0,0,360*delta/lead*screw_teeth/motor_teeth+180/motor_teeth]) input_gear();
    color("#b6b9be") for(z=[7.4,11.1]) translate([0,0,z]) washer();
    motor(360*delta/lead*screw_teeth/motor_teeth+180/motor_teeth);
    // M2×22沉头螺钉含尾端外露，标准件只在装配出现，不导出为打印件。
    color("#b8bdc3") for(v=[[-14,28],[-14,70],[gear_center+12.7,9],[gear_center+12.7,45]]){
        translate([v.x,10.3,v.y]) rotate([90,0,0]) cylinder(d=2,h=housing_bolt_length);
        translate([v.x,10.3,v.y]) rotate([90,0,0]) cylinder(d1=4.2,d2=2,h=1.1);
        translate([v.x,-10.3,v.y]) rotate([-90,0,0]) cylinder(d=4/cos(30),h=1.6,$fn=6);
    }
}
module thread_coupon(){
    // 试片用同一螺旋和相位，仅缩短长度，禁止调整缩放来配牙。
    difference(){translate([-8,-8,0]) cube([16,16,10]);helical_thread(10,thread_clearance,axial_clearance);}
}
module shaft_coupon(){difference(){cylinder(d=10,h=6);translate([0,0,-.1]) d_bore(6.2,.15);}}
module clevis_mount(gap=13,axis_height=13,stem_x=-8,base_x=0){
    // 两只打印转接座独立固定在框/斗母体，M3轴通过真实槽宽连接驱动。
    difference(){
        union(){
            translate([base_x-14,-22,0]) cube([28,44,3]);
            for(y=[-gap/2-4,gap/2]) hull(){
                translate([stem_x-4,y,3]) cube([8,4,1]);
                translate([0,y,axis_height]) rotate([-90,0,0]) cylinder(d=10,h=4);
            }
        }
        translate([0,-20,axis_height]) rotate([-90,0,0]) cylinder(d=pin_d,h=40);
        for(x=[-10,10]) for(y=[-18,18]){
            translate([base_x+x,y,-.1]) cylinder(d=3.4,h=3.2);
            // 下座前方紧邻轴承壳，M3沉头必须与底脚顶面齐平，不能凸出螺母。
            if(gap==13) translate([base_x+x,y,1.3]) cylinder(d1=3.6,d2=6.4,h=1.8);
        }
    }
}
module print_part(name){
    // 壳体平面朝下，轴/滑块竖直打印；每个导出件独立放到Z=0。
    if(name=="lower_shell") rotate([-90,0,0]) shell(-1);
    if(name=="upper_shell") rotate([90,0,0]) shell(1);
    if(name=="screw") translate([0,0,-6]) difference(){screw();translate([0,0,-1]) cylinder(d=6,h=7);}
    if(name=="slider") translate([0,0,-nut_start]) slider();
    if(name=="input_gear") translate([0,0,-8]) input_gear();
    if(name=="washer") washer();
    if(name=="thread_coupon") thread_coupon();
    if(name=="male_coupon") helical_thread(12);
    if(name=="shaft_coupon") shaft_coupon();
    if(name=="lower_mount") clevis_mount(13,13);
    if(name=="upper_mount") clevis_mount(17,12,8,14);
}
// 独立入口可切换装配、爆炸及打印件；整车通过use调用模块。
if(part=="assembly") drive_assembly();
else if(part=="internal_intersection") intersection(){
    housing();
    union(){
        rotate([0,0,shaft_angle]) difference(){screw();translate([0,0,-1]) cylinder(d=6,h=7);}
        translate([0,0,extension]) slider();
        translate([gear_center,0,0]) rotate([0,0,motor_angle]) input_gear();
        motor();
    }
}
else if(part=="thread_intersection") intersection(){rotate([0,0,shaft_angle+phase_error]) screw();translate([0,0,extension]) slider();}
else print_part(part);
$vpt=[7,0,40];
$vpr=[65,0,35];
$vpd=260;
