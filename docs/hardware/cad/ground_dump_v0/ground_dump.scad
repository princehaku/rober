// 地面后卸翻斗概念稿：所有尺寸为毫米，承载目标为垃圾 2 kg，尚待选型和实测。
// 资料来源：vendor 两份 WAVE ROVER DXF，完整原始坐标见 mount_reference.json。
// 安装原点为四孔组中心；上层58×86毫米经90度映射与下层86×58同轴。
// 主承力件拟用金属，橙色件仅供传感器适配试装，禁止据此承诺载重。

/* [显示与状态] */
// 装配或单件导出；单件自动落在打印平台上。
part = "assembly"; // [assembly,lidar_plate_assembly_reference,camera_bracket,base_adapter_assembly_reference,mount_template,mount_install,lidar_lower_print,lidar_upper_print,base_lower_print,base_upper_print,split_print_layout,split_assembly_detail]
// 向后翻转角；零度为运输状态，建议先在 0 至 55 度间检查干涉。
dump_angle = 0; // [0:1:65]
// 参考底盘保留DXF原图四孔，实物连接类型仍待核对，隐藏后可看主结构。
show_chassis = true;
// 隐藏斗体后可检查中央执行器与斗底横梁，适合看被斗壁遮挡的机构。
show_bucket = true;
// 传感器外形仅表示空间，不能代替实物包络。
show_sensor_envelopes = true;
// 丝杆与伸缩杆用于表达两个铰点的位置关系，尚无机构选型。
show_actuator = true;
// 地面和方向箭头便于识别向前行驶、向后卸料。
show_ground = true;
// 紧固件只展示设计包络，未建螺纹；下层图示2.05孔不能当作贯穿间隙。
show_fasteners = true;

/* [M2.5四孔安装接口] */
// 用户纠正为2.5毫米螺纹；原板图示孔径分别2.6和2.05，保持独立。
thread_diameter = 2.5; // [2:0.1:6]
// 新金属件及打印样板的设计通孔，打印后须校准，不能当作厂家孔径。
mount_clearance = 3.0; // [2.7:0.1:6.6]
// 安装原点是四孔组中心，两个孔距允许按实物调整。
mount_pitch_x = 58; // [50:1:80]
mount_pitch_y = 86; // [75:1:100]
// 对称孔阵无法确定行驶车头；本参数只切换整体展示方向，不改变机械相对位置。
display_direction = 1; // [-1,1]
// 板高、板厚及隔柱外径为设计占位，尚未采用厂家或标准件尺寸。
upper_plate_z = 112; // [108:1:116]
upper_plate_thickness = 2; // [1:0.5:3]
mount_post_diameter = 8; // [7:1:12]
mount_ear_thickness = 4; // [3:0.5:5]
// 头部与垫片尺寸均为工具空间占位，采购后须按实际标准件外形复核。
bolt_head_diameter = 5; // [4:0.5:8]
bolt_head_height = 2; // [1.5:0.5:4]
washer_diameter = 7; // [6:0.5:10]
washer_thickness = 0.8; // [0.5:0.1:1.5]
driver_clearance_diameter = 10; // [8:1:12]
mount_template_thickness = 2.5; // [2:0.5:4]

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
// 主梁放在上层板和安装耳上方，修改层高时保持实体接触。
metal_rail_z = upper_plate_z + upper_plate_thickness + mount_ear_thickness;

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
// 该打印件仅适配前传感器架；底盘四孔采用独立金属结构及对位样板。
// 缩短前传感器板，让四个底盘紧固点留在板后方；加长时会自动开工具避让窗。
base_length = 50; // [45:1:160]
base_width = 120; // [110:1:140]
base_thickness = 6; // [5:0.5:9]
sensor_foot_hole_diameter = 4.5; // [4:0.5:6]

/* [Tina2C分体接头设计占位] */
// 仅肩部XY留间隙；Z搭接面直接接触，避免紧固时把薄舌拉弯。
split_xy_clearance = 0.2; // [0.1:0.1:0.4]
split_hole_diameter = 3.4; // [3.2:0.1:3.8]
// M3头/母/垫片为采购前空间占位，源文件不声明标准件尺寸已确认。
split_head_diameter = 6;
split_head_height = 3;
split_washer_diameter = 7;
split_washer_thickness = 0.8;
split_nut_flat = 5.5;
split_nut_height = 2.4;
split_tool_diameter = 8;
// 相交诊断仅排除0.001毫米数值接触壳；实体拼合仍由真实STL测得Z贴合。
contact_tolerance = 0.001;

/* [Hidden] */
// 增加圆周细分以减少小孔多边形误差，实际打印还需孔径补偿。
$fn = 48;
// 命令行采用数字编号，避免 Windows PowerShell 对字符串引号的转义差异。
part_id = 0;
eps = 0.05;
lidar_plate_width = mast_spacing + lidar_plate_margin;
base_center_x = mast_x - base_length/2 + 12;
// 适配板放在前梁顶面，消除原先板与梁的实体重叠，立柱同步从板顶起。
base_install_z = metal_rail_z + 12;
mast_bottom = base_install_z + base_thickness;
lidar_lap_end = min(33,90-lidar_plate_width/2);
// 较宽板采用8毫米搭接，防止100柱距时设备槽旁只剩过薄全厚材料。
lidar_lap_start = lidar_lap_end-(lidar_plate_width>116?8:10);
lidar_joint_y = (lidar_lap_start+lidar_lap_end)/2;
lidar_joint_x = 28;
base_lap_start = -8;
base_lap_end = 8;
// 打印坐标先重居中，装配时严格逆变换，保留原设备孔与柱槽位置。
lidar_lower_shift = (lidar_plate_width/2-lidar_lap_end+split_xy_clearance/2)/2;
lidar_upper_shift = (lidar_plate_width/2+lidar_lap_start+split_xy_clearance/2)/2;
base_shift = (base_width/2-8+split_xy_clearance/2)/2;
// 下层顶板孔组比外轮廓中心朝图上偏22.641541，不能用板中心对齐。
body_offset_x = -22.641541;
// 主梁位于孔列外侧，给螺栓头、垫片和局部工具通道保留空间。
rail_y = max(58,mount_pitch_y/2+driver_clearance_diameter/2+8);
function mount_points(px=mount_pitch_x,py=mount_pitch_y) = [for(x=[-px/2,px/2]) for(y=[-py/2,py/2]) [x,y]];
// 平台限制只约束实际生产分片入口，参考装配和140毫米工具窗检查仍可运行。
base_print_requested = part_id==11 || part_id==12 || part_id==13 || (part_id==0 && (part=="base_lower_print" || part=="base_upper_print" || part=="split_print_layout"));
// 参数之间存在耦合；超出安全几何范围时明确失败，避免导出破碎件。
assert(bucket_wall < rear_lip_height && rear_lip_height < bucket_height);
assert(lidar_hole_spacing_x + lidar_slot_travel + lidar_hole_diameter < lidar_plate_depth-10);
assert(camera_hole_spacing + camera_hole_diameter < camera_width-12);
// 保证金属壁厚、孔间隙及两板之间正的隔柱高度。
assert(mount_clearance > thread_diameter && mount_post_diameter > mount_clearance+2);
assert(upper_plate_z>100 && hinge_z>metal_rail_z+24);
assert(max(washer_diameter,bolt_head_diameter)<=driver_clearance_diameter);
// 打印预算与孔/工具区共同约束，无法容纳的组合明确拒绝，不自动缩放。
assert(lidar_plate_depth>=68 && lidar_plate_depth<=90,"雷达分体板深需在68至90毫米，给接头边距留材料");
assert(!base_print_requested || (base_length<=90 && base_width<=140),"生产底座分片超出Tina2C预算；加长板可继续做参考检查");
assert(lidar_lap_start-split_xy_clearance/2-lidar_hole_spacing_y/2-lidar_hole_diameter/2>=1.2,"雷达设备槽至全厚肩的设计余量需至少1.2毫米");
assert(norm([lidar_joint_x,lidar_joint_y])>32.5+split_tool_diameter/2+0.5,"雷达工具包络侵入占位圆");

// 连通轻薄四孔样板仅用于先试孔距，绝不可承担垃圾或执行器载荷。
module mount_template() {
    difference() {
        union() {
            for(p=mount_points()) translate([p[0],p[1],0]) cylinder(d=12,h=mount_template_thickness);
            for(x=[-mount_pitch_x/2,mount_pitch_x/2]) translate([x-3,-mount_pitch_y/2,0]) cube([6,mount_pitch_y,mount_template_thickness]);
            for(y=[-mount_pitch_y/2,mount_pitch_y/2]) translate([-mount_pitch_x/2,y-3,0]) cube([mount_pitch_x,6,mount_template_thickness]);
        }
        for(p=mount_points()) translate([p[0],p[1],0]) slot_z(mount_clearance,0,mount_template_thickness);
    }
}

// 原板外形简化为包络及耳位，原始曲线请查看DXF重画图；原孔径不随新件改变。
module upper_plate_reference() {
    color([0.3,0.65,0.75,0.5]) difference() {
        union() {
            translate([-78.674829,-30.25,upper_plate_z]) cube([114.774829,60.5,upper_plate_thickness]);
            for(x=[-29,29]) for(y=[-43,43]) hull() {
                translate([x,y,upper_plate_z]) cylinder(d=7,h=upper_plate_thickness);
                translate([x,y>0?28:-28,upper_plate_z]) cylinder(d=7,h=upper_plate_thickness);
            }
        }
        // 这里固定保留DXF的2.6毫米原孔，不能被新件3毫米间隙覆盖。
        for(p=mount_points(58,86)) translate([p[0],p[1],upper_plate_z-eps]) cylinder(d=2.6,h=upper_plate_thickness+2*eps);
    }
}

// 紧固包络落在金属安装耳上；下层接口止于顶面，连接类型待实物核对。
module mount_fasteners() {
    for(p=mount_points()) {
        color([0.82,0.68,0.2]) translate([p[0],p[1],100]) cylinder(d=thread_diameter,h=metal_rail_z-100+washer_thickness);
        color([0.8,0.7,0.3]) translate([p[0],p[1],metal_rail_z]) difference() {
            cylinder(d=washer_diameter,h=washer_thickness);
            translate([0,0,-eps]) cylinder(d=mount_clearance,h=washer_thickness+2*eps);
        }
        color([0.72,0.58,0.15]) translate([p[0],p[1],metal_rail_z+washer_thickness]) cylinder(d=bolt_head_diameter,h=bolt_head_height);
    }
}

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

// 前适配板连在立柱脚下，并对底盘紧固点避让，主载荷由金属导轨承担。
module base_adapter() {
    difference() {
        translate([-base_length/2,-base_width/2,0]) cube([base_length,base_width,base_thickness]);
        // 用户加长板时，四轴工具窗口随安装孔距联动，确保螺栓头不会埋进塑料。
        for(p=mount_points()) let(x=p[0]-body_offset_x-base_center_x,y=p[1],r=driver_clearance_diameter/2) {
            translate([x,y,0]) slot_z(driver_clearance_diameter,0,base_thickness);
            // 靠边不足3毫米时直接开口到边缘，避免保留易折的薄小筋。
            if(x-r< -base_length/2+3 && x> -base_length/2)
                translate([-base_length/2-eps,y-r,-eps]) cube([x+base_length/2+eps,2*r,base_thickness+2*eps]);
            if(abs(y)+r>base_width/2-3 && abs(y)<base_width/2)
                translate([x-r,y>0?y: -base_width/2-eps,-eps]) cube([2*r,base_width/2-abs(y)+eps,base_thickness+2*eps]);
        }
        // 立柱脚孔与装配位置联动，避免柱子在预览里悬空。
        for (y=[-mast_spacing/2,mast_spacing/2])
            translate([base_length/2-12,y,0]) slot_z(sensor_foot_hole_diameter,0,base_thickness);
    }
}

// 两片半搭接共用分区逻辑；Z接触面为厚度一半，肩侧只留XY间隙。
module lap_mask(upper,start,end,total_y,depth,t) {
    // 两肩各退半个间隙，避免打印收缩后肩部顶死；受压面仍不留Z空气层。
    g=split_xy_clearance/2;
    if(!upper) union() {
        translate([-depth/2,-total_y/2,0]) cube([depth,start-g+total_y/2,t]);
        translate([-depth/2,start-g,0]) cube([depth,end-start,t/2]);
    }
    else union() {
        translate([-depth/2,end+g,0]) cube([depth,total_y/2-end-g,t]);
        translate([-depth/2,start+g,t/2]) cube([depth,end-start,t/2]);
    }
}

// 分件直接裁切既有设备孔槽形状，防止复制孔位造成安装契约漂移。
module lidar_half(upper=false) {
    // 两半共享同一设备孔模块，只增加接头穿孔，不挪动传感器安装中心。
    difference() {
        intersection() {
            lidar_plate();
            lap_mask(upper,lidar_lap_start,lidar_lap_end,lidar_plate_width,lidar_plate_depth,lidar_plate_thickness);
        }
        for(x=[-lidar_joint_x,lidar_joint_x])
            translate([x,lidar_joint_y,0]) slot_z(split_hole_diameter,0,lidar_plate_thickness);
    }
}

// 底座接头放在梁后侧；柱孔与底盘工具窗继续从既有模块继承。
module base_half(upper=false) {
    // 此处切的是实际前适配板，已有四个底盘螺头工具窗会继续联动。
    difference() {
        intersection() {
            base_adapter();
            lap_mask(upper,base_lap_start,base_lap_end,base_width,base_length,base_thickness);
        }
        for(x=[-15,-1]) translate([x,0,0]) slot_z(split_hole_diameter,0,base_thickness);
    }
}

// 高舌片的原顶面翻到打印平台，避免薄舌底部成为悬空层。
module lidar_print(upper=false) {
    // 居中平移是可逆的，供打印的文件不会改变装配空间孔距。
    if(upper) translate([0,lidar_upper_shift,lidar_plate_thickness]) rotate([180,0,0]) lidar_half(true);
    else translate([0,lidar_lower_shift,0]) lidar_half(false);
}

module base_print(upper=false) {
    // 两半用相同Y居中量，高舌片同时翻转Y/Z，防止仅降Z导致悬空。
    if(upper) translate([0,base_shift,base_thickness]) rotate([180,0,0]) base_half(true);
    else translate([0,base_shift,0]) base_half(false);
}

// 螺母外露可用工具夹持；不设置难打印的盲袋，零件翻面后仍保持平底。
module split_fasteners(points,t) {
    for(p=points) {
        color([0.76,0.6,0.2]) translate([p[0],p[1],-split_nut_height-split_washer_thickness-1])
            cylinder(d=3,h=t+split_nut_height+2*split_washer_thickness+1);
        color([0.84,0.7,0.32]) for(z=[-split_washer_thickness,t])
            translate([p[0],p[1],z]) difference() {
                cylinder(d=split_washer_diameter,h=split_washer_thickness);
                translate([0,0,-eps]) cylinder(d=split_hole_diameter,h=split_washer_thickness+2*eps);
            }
        color([0.72,0.55,0.15]) translate([p[0],p[1],t+split_washer_thickness]) cylinder(d=split_head_diameter,h=split_head_height);
        // 六角外接径由对边值换算，仅为空间假设，采购后核对实际螺母。
        color([0.65,0.55,0.3]) translate([p[0],p[1],-split_washer_thickness-split_nut_height])
            difference() {
                cylinder(d=split_nut_flat/cos(30),h=split_nut_height,$fn=6);
                translate([0,0,-eps]) cylinder(d=3,h=split_nut_height+2*eps);
            }
    }
}

module lidar_assembly(fasteners=false) {
    // 装配入口恢复原始坐标，生产导出入口独立执行翻面变换。
    color("DarkOrange") lidar_half(false);
    color([1,0.7,0.25]) lidar_half(true);
    if(fasteners) split_fasteners([[-lidar_joint_x,lidar_joint_y],[lidar_joint_x,lidar_joint_y]],lidar_plate_thickness);
}

module base_assembly(fasteners=false) {
    // 参考STL可包含贴合的多件，用户只从专门生产目录取打印半片。
    color("DarkOrange") base_half(false);
    color([1,0.7,0.25]) base_half(true);
    if(fasteners) split_fasteners([[-15,0],[-1,0]],base_thickness);
}

// 四个打印件分别置于100毫米方格中心，形状已按各自真实落床方向变换。
module split_print_layout() {
    for(x=[-60,60]) for(y=[-60,60])
        color([0.88,0.9,0.92]) translate([x-50,y-50,-1]) cube([100,100,0.8]);
    color("DarkOrange") translate([-60,60,0]) lidar_print(false);
    color([1,0.7,0.25]) translate([60,60,0]) lidar_print(true);
    color("DarkOrange") translate([-60,-60,0]) base_print(false);
    color([1,0.7,0.25]) translate([60,-60,0]) base_print(true);
}

// 装配细节使用真实分片，雷达占位可透明看见，底座梁显示实际局部包络。
module split_assembly_detail() {
    translate([-60,0,8]) {
        lidar_assembly(true);
        color([0.8,0.1,0.15,0.35]) translate([0,0,lidar_plate_thickness]) cylinder(d=65,h=15);
    }
    translate([60,0,8]) {
        base_assembly(true);
        color([0.6,0.65,0.7]) translate([7,-base_width/2,-12]) cube([12,base_width,12]);
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
    color([0.2,0.24,0.28]) translate([body_offset_x-85,-65,25]) cube([170,130,73]);
    // 顶板包络来自DXF顶视边界，仍为简化矩形；原孔保留图示2.05毫米。
    color([0.36,0.4,0.44]) difference() {
        translate([body_offset_x-91.553737,-81.869997,98]) cube([183.107474,163.739994,2]);
        for(p=mount_points(58,86)) translate([p[0],p[1],98-eps]) cylinder(d=2.05,h=2+2*eps);
    }
    color([0.10,0.11,0.12]) for (x=[-62,62]) for (y=[-77,77])
        translate([body_offset_x+x,y,38]) rotate([90,0,0]) cylinder(d=72,h=18,center=true);
}

module fixed_metal_frame() {
    color([0.58,0.63,0.68]) difference() {
      union() {
        // 在车体局部坐标中减去偏置，装配变换后四根隔柱准确落在共用四孔上。
        for(p=mount_points()) translate([p[0]-body_offset_x,p[1],100]) cylinder(d=mount_post_diameter,h=upper_plate_z-100);
        // 两根带孔金属横梁跨过上下板耳位，向外连接主纵梁，载荷经金属传递。
        for(x=[-mount_pitch_x/2,mount_pitch_x/2])
            translate([x-body_offset_x-8,-rail_y-6,upper_plate_z+upper_plate_thickness]) cube([16,2*rail_y+12,mount_ear_thickness]);
        // 两条纵梁连后铰支座和前传感器架，主骨架拟用金属。
        for (y=[-rail_y,rail_y]) translate([hinge_x-6,y-6,metal_rail_z]) cube([mast_x-hinge_x+12,12,12]);
        translate([hinge_x-6,-80,metal_rail_z+12]) cube([12,160,12]);
        // 中央执行器的下铰点落在金属横梁上，横梁两端与纵梁连接。
        translate([hinge_x+32,-rail_y-6,metal_rail_z+12]) cube([12,2*rail_y+12,12]);
        // 铰轴两侧耳板与横梁实体相接，转轴横穿斗底后缘。
        for (y=[-78,72]) translate([hinge_x-6,y,metal_rail_z+20]) cube([12,6,hinge_z-metal_rail_z-10]);
        rod([hinge_x,-82,hinge_z],[hinge_x,82,hinge_z],8);
        // 前横梁把立柱脚连到外移后的纵梁，前适配板依然得到金属承托。
        translate([mast_x-6,-rail_y-6,metal_rail_z]) cube([12,2*rail_y+12,12]);
        // 立柱与底座适配板、顶雷达板直接接触，横梁承托相机底座。
        for (y=[-mast_spacing/2,mast_spacing/2])
            translate([mast_x-mast_size/2,y-mast_size/2,mast_bottom]) cube([mast_size,mast_size,lidar_height-mast_bottom]);
        translate([mast_x-camera_base_depth/2,-mast_spacing/2-mast_size/2,camera_height-8])
            cube([camera_base_depth,mast_spacing+mast_size,8]);
      }
      // 从隔柱到上安装耳使用同轴贯穿间隙；上层原板另以原孔径显示。
      for(p=mount_points()) translate([p[0]-body_offset_x,p[1],100-eps])
          cylinder(d=mount_clearance,h=metal_rail_z-100+2*eps);
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

// 安装视图移去上层业务部件，能直接检查四柱、耳位、头部和原板。
module mount_install() {
    if (show_chassis) chassis_reference();
    upper_plate_reference();
    // 仅裁切显示安装区域，所有孔与隔柱仍来自实际主框架模块，避免复制假几何。
    intersection() {
        translate([body_offset_x,0,0]) fixed_metal_frame();
        translate([-60,-75,99]) cube([120,150,36]);
    }
    if(show_fasteners) mount_fasteners();
}

module assembly_layout() {
    if (show_chassis) chassis_reference();
    upper_plate_reference();
    if(show_fasteners) mount_fasteners();
    // 整个既有斗体和前架保留相对车体的位置，再换算到安装原点。
    translate([body_offset_x,0,0]) {
    fixed_metal_frame();
    // 后铰轴固定；负 Y 转角使前端抬高，垃圾向后方低端滑动。
    translate([hinge_x,0,hinge_z]) rotate([0,-dump_angle,0]) {
        if (show_bucket) bucket();
        // 斗底横向支点把中央执行器受力分给斗体，尺寸仍待结构设计。
        color([0.58,0.63,0.68]) rod([bucket_length*0.78,-bucket_width/2,0],[bucket_length*0.78,bucket_width/2,0],8);
    }
    translate([base_center_x,0,base_install_z]) base_assembly(show_fasteners);
    translate([mast_x,0,lidar_height]) lidar_assembly(show_fasteners);
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
    }
    if (show_ground) {
        color([0.89,0.9,0.91]) translate([-240,-150,-4]) cube([490,300,3]);
        color([0.15,0.4,0.25]) translate([165,-20,0]) linear_extrude(1)
            polygon([[0,-5],[35,-5],[35,-14],[58,0],[35,14],[35,5],[0,5]]);
        color([0.15,0.4,0.25]) translate([165,20,0]) linear_extrude(1) text("FRONT +X",size=10);
        color([0.25,0.3,0.4]) translate([-220,70,0]) linear_extrude(1) text("REAR / DUMP",size=10);
    }
}

// 四孔中心固定在原点；方向切换同时旋转整机和参考板，避免只翻单个孔组。
module assembly() { rotate([0,0,display_direction==1?0:180]) assembly_layout(); }

// 候选 STL 共用同一份参数，导出脚本无需复制几何定义。
// 数字入口优先于 GUI 保存值，修改 part 后也能正确批量导出全部文件。
if (part_id == 1) lidar_assembly();
else if (part_id == 2) camera_bracket();
else if (part_id == 3) base_assembly();
else if (part_id == 4) assembly();
else if (part_id == 5) mount_template();
else if (part_id == 6) rotate([0,0,display_direction==1?0:180]) mount_install();
// 实际金属框架网格仅供切片核对隔柱孔轴线，含多个装配实体，禁止当作打印件。
else if (part_id == 7) translate([body_offset_x,0,-100]) fixed_metal_frame();
// 将实际前适配板换算到安装坐标，只用于验证四处头部/工具空间保持开放。
else if (part_id == 8) translate([body_offset_x+base_center_x,0,0]) base_assembly();
else if (part_id == 9) lidar_print(false);
else if (part_id == 10) lidar_print(true);
else if (part_id == 11) base_print(false);
else if (part_id == 12) base_print(true);
else if (part_id == 13) split_print_layout();
else if (part_id == 14) split_assembly_detail();
// 数值清单用于把当前参数映射到独立网格检查，单件尺寸仍从STL实测。
else if (part_id == 15) {
    echo(["lidar_size",lidar_plate_depth,lidar_plate_width,lidar_plate_thickness]);
    echo(["lidar_lap",lidar_lap_start,lidar_lap_end,lidar_joint_x,lidar_joint_y]);
    echo(["print_shifts",lidar_lower_shift,lidar_upper_shift,base_shift]);
    echo(["base_size",base_length,base_width,base_thickness]);
    echo(["clearances",split_xy_clearance,split_hole_diameter,split_tool_diameter]);
    echo(["install",base_install_z,mast_bottom,metal_rail_z+12,lidar_height,camera_height]);
    echo(["local_features",lidar_hole_spacing_x,lidar_hole_spacing_y,lidar_slot_travel,lidar_hole_diameter,mast_spacing,base_length/2-12,sensor_foot_hole_diameter]);
    echo(["base_world_xy",body_offset_x+base_center_x,0]);
    echo(["contact_tolerance",contact_tolerance]);
}
// 一立方毫米见证块让“无实体相交”也能正常导出STL，验证再扣除此体积。
else if (part_id == 16) union() {
    translate([400,400,0]) cube(1);
    intersection() {
        fixed_metal_frame();
        // 仅剔除上下共享接触面的数值壳，既有真实接触高度另行核验。
        translate([base_center_x,0,base_install_z+contact_tolerance])
            scale([1,1,(base_thickness-2*contact_tolerance)/base_thickness]) base_assembly();
    }
}
else if (part_id == 17) union() {
    translate([400,400,0]) cube(1);
    intersection() { lidar_half(false); translate([0,0,contact_tolerance]) lidar_half(true); }
}
else if (part_id == 18) union() {
    translate([400,400,0]) cube(1);
    intersection() { base_half(false); translate([0,0,contact_tolerance]) base_half(true); }
}
else if (part == "lidar_plate_assembly_reference") lidar_assembly();
else if (part == "camera_bracket") camera_bracket();
else if (part == "base_adapter_assembly_reference") base_assembly();
else if (part == "lidar_lower_print") lidar_print(false);
else if (part == "lidar_upper_print") lidar_print(true);
else if (part == "base_lower_print") base_print(false);
else if (part == "base_upper_print") base_print(true);
else if (part == "split_print_layout") split_print_layout();
else if (part == "split_assembly_detail") split_assembly_detail();
else if (part == "mount_template") mount_template();
else if (part == "mount_install") rotate([0,0,display_direction==1?0:180]) mount_install();
else if (part == "assembly") assembly();
else assert(false,"未知零件名称");
