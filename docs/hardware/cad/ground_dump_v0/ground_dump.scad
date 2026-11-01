// 地面后卸翻斗概念稿：所有尺寸为毫米，承载目标为垃圾 2 kg，尚待选型和实测。
// 资料来源：docs/vendor/VENDOR_INDEX.md 与 WAVE ROVER_MODEL_STL.stl。
// 底盘模型仅使用该 STL 的包围尺寸参考；朝向、单位和安装孔位尚未实测。
// 主承力件拟用金属，橙色件仅供传感器适配试装，禁止据此承诺载重。

/* [显示与状态] */
// 装配或单件导出；单件自动落在打印平台上。
part = "assembly"; // [assembly,lidar_plate,camera_bracket,base_adapter]
// 向后翻转角；零度为运输状态，建议先在 0 至 55 度间检查干涉。
dump_angle = 0; // [0:1:65]
// 参考底盘不含真实孔位，隐藏后可看主结构。
show_chassis = true;
// 隐藏斗体后可检查中央执行器与斗底横梁，适合看被斗壁遮挡的机构。
show_bucket = true;
// 传感器外形仅表示空间，不能代替实物包络。
show_sensor_envelopes = true;
// 丝杆与伸缩杆用于表达两个铰点的位置关系，尚无机构选型。
show_actuator = true;
// 地面和方向箭头便于识别向前行驶、向后卸料。
show_ground = true;

/* [垃圾斗占位尺寸] */
// 加长垃圾斗会改变重心、执行器需求和前端间隙，必须重新评估。
bucket_length = 180; // [140:1:190]
bucket_width = 132; // [100:1:145]
bucket_height = 90; // [60:1:130]
bucket_wall = 3; // [2:0.5:5]
// 低挡边保留少量运输限位；封闭垃圾袋滑出需单独实测。
rear_lip_height = 12; // [6:1:25]
// 后铰轴固定在车架，垃圾斗局部 X 从铰轴朝前延伸。
// 后移给地面落料留出外伸距离，同时增加后翻重心风险，需实测复核。
hinge_x = -120; // [-130:1:-100]
hinge_z = 150; // [140:1:170]

/* [固定金属架占位尺寸] */
// 立柱位于前端，雷达和相机随车架固定，翻斗不会带动传感器。
mast_x = 110; // [105:1:125]
mast_spacing = 90; // [75:1:100]
mast_size = 12; // [10:1:18]
// 雷达安装面高度；其最低值仍需结合翻斗扫掠与扫描面复核。
lidar_height = 310; // [280:1:360]
camera_height = 222; // [205:1:245]
metal_rail_z = 118; // [115:1:125]

/* [雷达打印板占位尺寸] */
// 打印板宽度随立柱间距联动，确保固定孔外保留材料。
lidar_plate_depth = 70; // [60:1:90]
lidar_plate_margin = 20; // [18:1:30]
lidar_plate_thickness = 5; // [4:0.5:8]
// 雷达四孔使用长槽容纳小幅偏差，仍须先量实物。
lidar_hole_spacing_x = 35; // [20:1:45]
lidar_hole_spacing_y = 35; // [20:1:50]
lidar_hole_diameter = 3.4; // [3:0.2:5]
lidar_slot_travel = 6; // [0:1:10]

/* [相机打印座占位尺寸] */
// 相机仅用紧凑 L 形座，避免额外占用整层平台。
camera_width = 64; // [55:1:80]
camera_base_depth = 42; // [38:1:50]
camera_plate_height = 40; // [35:1:50]
camera_thickness = 5; // [4:0.5:7]
// 正值让相机朝前下倾，支架后侧仍与底板连接。
camera_pitch = 10; // [0:1:20]
camera_hole_spacing = 28; // [20:1:36]
camera_hole_diameter = 3.4; // [3:0.2:5]

/* [底座打印适配板占位尺寸] */
// 这里只提供可测后修改的长槽，未采用任何厂家安装孔距。
base_length = 140; // [130:1:160]
base_width = 120; // [110:1:140]
base_thickness = 6; // [5:0.5:9]
base_hole_spacing_x = 90; // [70:1:100]
base_hole_spacing_y = 80; // [65:1:90]
base_hole_diameter = 4.5; // [4:0.5:6]
base_slot_travel = 12; // [0:1:16]

/* [Hidden] */
// 增加圆周细分以减少小孔多边形误差，实际打印还需孔径补偿。
$fn = 48;
// 命令行采用数字编号，避免 Windows PowerShell 对字符串引号的转义差异。
part_id = 0;
eps = 0.05;
lidar_plate_width = mast_spacing + lidar_plate_margin;
base_center_x = mast_x - base_length/2 + 12;
mast_bottom = metal_rail_z + 6;
// 参数之间存在耦合；超出安全几何范围时明确失败，避免导出破碎件。
assert(bucket_wall < rear_lip_height && rear_lip_height < bucket_height);
assert(lidar_hole_spacing_x + lidar_slot_travel + lidar_hole_diameter < lidar_plate_depth-10);
assert(camera_hole_spacing + camera_hole_diameter < camera_width-12);
assert(base_hole_spacing_x+base_slot_travel+base_hole_diameter < base_length-8);
assert(base_hole_spacing_y+base_hole_diameter < base_width-8);

// 长槽两端圆弧贯通，孔径和移动量分别控制，便于先小件试装。
module slot_z(d, travel, h) {
    hull() for (s=[-1,1]) translate([s*travel/2,0,-eps]) cylinder(d=d,h=h+2*eps);
}

// 雷达板用两侧立柱孔固定，中央四个槽用于设备安装。
module lidar_plate() {
    difference() {
        translate([-lidar_plate_depth/2,-lidar_plate_width/2,0])
            cube([lidar_plate_depth,lidar_plate_width,lidar_plate_thickness]);
        for (y=[-mast_spacing/2,mast_spacing/2])
            translate([0,y,0]) slot_z(4.5,8,lidar_plate_thickness);
        for (x=[-lidar_hole_spacing_x/2,lidar_hole_spacing_x/2])
            for (y=[-lidar_hole_spacing_y/2,lidar_hole_spacing_y/2])
                translate([x,y,0]) slot_z(lidar_hole_diameter,lidar_slot_travel,lidar_plate_thickness);
        // 后侧线缆口避开传感器安装区，布线仍需防磨护套。
        translate([-lidar_plate_depth/2+8,0,0]) slot_z(8,0,lidar_plate_thickness);
    }
}

// 相机斜板绕根部倾斜，保留与底板的实体重叠以形成单个连通件。
module camera_face() {
    translate([camera_base_depth/2-camera_thickness,0,camera_thickness-1])
        rotate([0,camera_pitch,0]) children();
}

module camera_bracket() {
    difference() {
        union() {
            translate([-camera_base_depth/2,-camera_width/2,0])
                cube([camera_base_depth,camera_width,camera_thickness]);
            camera_face() translate([0,-camera_width/2,0])
                cube([camera_thickness,camera_width,camera_plate_height]);
            // 两侧三角筋限制板根挠曲，避开相机孔和底座螺钉工具通道。
            for (y=[-camera_width/2+4,camera_width/2])
                translate([0,y,0]) rotate([90,0,0]) linear_extrude(height=4)
                    polygon([[-12,0],[camera_base_depth/2,0],
                        [camera_base_depth/2-camera_thickness+sin(camera_pitch)*camera_plate_height*0.7+1,
                        camera_thickness-1+cos(camera_pitch)*camera_plate_height*0.7]]);
        }
        // 两个底孔连接前端金属横梁，孔位置处于斜板后方。
        for (y=[-camera_hole_spacing/2,camera_hole_spacing/2])
            translate([-8,y,0]) slot_z(4.5,6,camera_thickness);
        // 前板孔沿板法向贯穿，可用两螺钉固定相机外壳。
        for (y=[-camera_hole_spacing/2,camera_hole_spacing/2])
            camera_face() translate([-eps,y,camera_plate_height*0.62])
                rotate([0,90,0]) cylinder(d=camera_hole_diameter,h=camera_thickness+2*eps);
    }
}

// 底座板连在立柱脚下；长槽仅用于适配，主载荷由金属导轨承担。
module base_adapter() {
    difference() {
        translate([-base_length/2,-base_width/2,0]) cube([base_length,base_width,base_thickness]);
        for (x=[-base_hole_spacing_x/2,base_hole_spacing_x/2])
            for (y=[-base_hole_spacing_y/2,base_hole_spacing_y/2])
                translate([x,y,0]) slot_z(base_hole_diameter,base_slot_travel,base_thickness);
        // 立柱脚孔与装配位置联动，避免柱子在预览里悬空。
        for (y=[-mast_spacing/2,mast_spacing/2])
            translate([base_length/2-12,y,0]) slot_z(4.5,0,base_thickness);
    }
}

// 任意两点间画圆杆，丝杆两端始终随下铰点和斗底上铰点对齐。
module rod(a,b,d) {
    v=b-a;
    translate(a) rotate([0,acos(v[2]/norm(v)),atan2(v[1],v[0])]) cylinder(d=d,h=norm(v));
}

// 局部坐标以斗底后缘为零点；后低挡边和斜口留下真实卸料出口。
module bucket() {
    color([0.12,0.62,0.78,0.68]) union() {
        translate([0,-bucket_width/2,0]) cube([bucket_length,bucket_width,bucket_wall]);
        translate([bucket_length-bucket_wall,-bucket_width/2,0]) cube([bucket_wall,bucket_width,bucket_height]);
        translate([0,-bucket_width/2,0]) cube([bucket_wall,bucket_width,rear_lip_height]);
        // 两侧斜口从前高侧壁降至后低挡边，顶面与后口保持敞开。
        for (y=[-bucket_width/2,bucket_width/2-bucket_wall])
            translate([0,y+bucket_wall,0]) rotate([90,0,0]) linear_extrude(height=bucket_wall)
                polygon([[0,0],[bucket_length,0],[bucket_length,bucket_height],[0,rear_lip_height]]);
    }
}

// 原 STL 包围尺寸约 172.399 × 194.030 × 99.939；此处仅画简化外形。
// 将长轴作为车长是设计坐标假设，不代表已核实原 STL 的车辆朝向。
module chassis_reference() {
    color([0.2,0.24,0.28]) translate([-85,-65,25]) cube([170,130,75]);
    color([0.10,0.11,0.12]) for (x=[-62,62]) for (y=[-77,77])
        translate([x,y,38]) rotate([90,0,0]) cylinder(d=72,h=18,center=true);
}

module fixed_metal_frame() {
    color([0.58,0.63,0.68]) {
        // 四个占位金属脚把纵梁接到简化底盘顶面，真实安装点仍须量车。
        for(x=[-60,60]) for(y=[-50,50])
            translate([x-6,y-6,100]) cube([12,12,metal_rail_z-100]);
        // 两条纵梁连后铰支座和前传感器架，主骨架拟用金属。
        for (y=[-50,50]) translate([hinge_x-6,y-6,metal_rail_z]) cube([mast_x-hinge_x+12,12,12]);
        translate([hinge_x-6,-80,metal_rail_z+12]) cube([12,160,12]);
        // 中央执行器的下铰点落在金属横梁上，横梁两端与纵梁连接。
        translate([hinge_x+32,-56,metal_rail_z+12]) cube([12,112,12]);
        // 铰轴两侧耳板与横梁实体相接，转轴横穿斗底后缘。
        for (y=[-78,72]) translate([hinge_x-6,y,metal_rail_z+20]) cube([12,6,hinge_z-metal_rail_z-10]);
        rod([hinge_x,-82,hinge_z],[hinge_x,82,hinge_z],8);
        // 立柱与底座适配板、顶雷达板直接接触，横梁承托相机底座。
        for (y=[-mast_spacing/2,mast_spacing/2])
            translate([mast_x-mast_size/2,y-mast_size/2,mast_bottom]) cube([mast_size,mast_size,lidar_height-mast_bottom]);
        translate([mast_x-camera_base_depth/2,-mast_spacing/2-mast_size/2,camera_height-8])
            cube([camera_base_depth,mast_spacing+mast_size,8]);
    }
}

module actuator_placeholder() {
    // 单根中央丝杆/电动推杆只表达候选布局，伸缩外形不代表实际运动副。
    let(a=[hinge_x+38,0,metal_rail_z+20],
        b=[hinge_x+bucket_length*0.78*cos(dump_angle),0,hinge_z+bucket_length*0.78*sin(dump_angle)],
        mid=a+(b-a)*0.55) {
        color([0.55,0.25,0.65,0.85]) rod(a,mid,13);
        color([0.82,0.78,0.86]) rod(mid,b,6);
        // 铰接球体仅标注装配点，耳板强度、螺栓与行程尚未设计。
        color([0.55,0.25,0.65]) for(p=[a,b]) translate(p) sphere(d=13);
    }
}

module assembly() {
    if (show_chassis) chassis_reference();
    fixed_metal_frame();
    // 后铰轴固定；负 Y 转角使前端抬高，垃圾向后方低端滑动。
    translate([hinge_x,0,hinge_z]) rotate([0,-dump_angle,0]) {
        if (show_bucket) bucket();
        // 斗底横向支点把中央执行器受力分给斗体，尺寸仍待结构设计。
        color([0.58,0.63,0.68]) rod([bucket_length*0.78,-bucket_width/2,0],[bucket_length*0.78,bucket_width/2,0],8);
    }
    color("DarkOrange") translate([base_center_x,0,mast_bottom-base_thickness]) base_adapter();
    color("DarkOrange") translate([mast_x,0,lidar_height]) lidar_plate();
    color("DarkOrange") translate([mast_x,0,camera_height]) camera_bracket();
    if (show_actuator) actuator_placeholder();
    if (show_sensor_envelopes) {
        // 雷达形状和相机形状均为独立占位，不借用未实测设备尺寸。
        color([0.85,0.12,0.16]) translate([mast_x,0,lidar_height+lidar_plate_thickness]) cylinder(d=65,h=36);
        color([0.12,0.16,0.2]) translate([mast_x,0,camera_height]) camera_face()
            translate([camera_thickness,-21,8]) cube([18,42,24]);
        color([0.18,0.5,0.85]) translate([mast_x,0,camera_height]) camera_face()
            translate([camera_thickness+18,0,20]) rotate([0,90,0]) cylinder(d=16,h=3);
    }
    if (show_ground) {
        color([0.89,0.9,0.91]) translate([-240,-150,-4]) cube([490,300,3]);
        color([0.15,0.4,0.25]) translate([165,-20,0]) linear_extrude(1)
            polygon([[0,-5],[35,-5],[35,-14],[58,0],[35,14],[35,5],[0,5]]);
        color([0.15,0.4,0.25]) translate([165,20,0]) linear_extrude(1) text("FRONT +X",size=10);
        color([0.25,0.3,0.4]) translate([-220,70,0]) linear_extrude(1) text("REAR / DUMP",size=10);
    }
}

// 三种 STL 共用同一份参数，导出脚本无需复制几何定义。
// 数字入口优先于 GUI 保存值，修改 part 后也能正确批量导出全部文件。
if (part_id == 1) lidar_plate();
else if (part_id == 2) camera_bracket();
else if (part_id == 3) base_adapter();
else if (part_id == 4) assembly();
else if (part == "lidar_plate") lidar_plate();
else if (part == "camera_bracket") camera_bracket();
else if (part == "base_adapter") base_adapter();
else if (part == "assembly") assembly();
else assert(false,"未知零件名称");
