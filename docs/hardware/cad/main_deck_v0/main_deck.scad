// 榫卯主底板试装稿：原始四轴来自本地WAVE ROVER两张DXF。
// 上层原孔2.6、下层图示圆2.05；用户确认M2.5外牙约5mm，实际螺母仍待核。
// 本稿取消金属条；双燕尾传力，五枚M3只作可拆止退，未验证强度。

/* [外形与安装基准] */
// 外形居中于车体参考，安装四轴仍以孔组为原点。
// 两者不能同时强制居中，否则会改变已确认的装车接口。
deck_length = 200;
deck_width = 160;
body_offset_x = -22.641541;
panel_thickness = 12;
top_skin = 4;
seam_gap = 0.6;
mount_hole = 3.0;
clamp_thickness = 2; // 用户近似量得外露牙5mm，薄底夹厚是设计值，需座试片确认。
nut_well_diameter = 10; // 工具窝设计包络，真实螺母/垫片/套筒尺寸待核。
stud_projection = 5; // 用户近似实测，不代表每根柱都已测量。
pillar_height = 24; // 柱长仅示意，必须实测下方工具净空。

/* [榫卯与打印] */
// 间隙为理想CAD单边值，实际PLA收缩与象脚须用小试片确认。
// 不用摩擦自锁证明承重，轴向退出另由螺丝或实体端墙约束。
fit_clearance = 0.3; // 单边水平及顶部间隙，先打印三档试片。
flange_width = 26;
rib_width = 5;
minimum_service_gap = 12; // 设计准入，现有柱顶到车顶净空待测。

/* [显示] */
// 数值入口服务可重复导出，显示选项只影响参考装配。
// 生产面板和桥键均预先摆平；不用斜放绕开平台限制。
part_id = 0; // 0装配，1..6面板，11..17桥键，21..23试片。
part_index = 0;
view_mode = 0; // 0上车，1底面，2爆炸，3步骤，4接头试片。
assembly_stage = 3; // 1三列独立，2三列合并，3安装竖键。
show_hardware = true;
show_reference = true;
diagnostic = 0; // 仅导出脚本调用的实体见证，不混入生产打印目录。
diagnostic_index = 0;

$fn=48;
xs=[body_offset_x-deck_length/2,-70,0,body_offset_x+deck_length/2];
// 非等宽三列使安装座避开分缝；每列仍低于90mm预算。
// 纵横键分区到|Y|24，完整桥而非仅槽体须保留交会空间。
ys=[-deck_width/2,0,deck_width/2];
mounts=[[-29,-43],[-29,43],[29,-43],[29,43]];
// 横键留10mm实体端墙；后两键的退出口在合列后由邻列端墙遮挡。
function joint(j)= j<3 ? [0,xs[j],0,xs[j+1]-xs[j]-10,j==0] :
    [1,j<5?-70:0,(j%2==1)?-1:1,deck_width/2-24,true];
function panel_bounds(i)=[xs[i%3]+(i%3>0?seam_gap/2:0),
    xs[i%3+1]-(i%3<2?seam_gap/2:0),ys[floor(i/3)]+(i>=3?seam_gap/2:0),
    ys[floor(i/3)+1]-(i<3?seam_gap/2:0)];
function stop_xy(j)=j<3?[xs[j]+6,22]:[joint(j)[1]+22,joint(j)[2]*(deck_width/2-6)];
// 螺丝位于实体法兰与键耳重叠处；顶面沉头不承担接缝主载荷。
// 耳的下方开放，拆卸工具不能被相邻桥键封死。

// 约束只对真实打印预算生效，装配与试片采用相同接口断言。
assert(panel_thickness>=10 && panel_thickness<=18,"板厚需10..18，确保槽顶至少3.6mm实体");
// 不允许缩薄顶皮掩盖开槽后的脆弱截面，范围外须重新设计。
assert(top_skin>=3 && top_skin<=panel_thickness-6.4,"顶皮/槽顶组合不可行");
assert(fit_clearance>=0.15 && fit_clearance<=0.4,"试配间隙需0.15..0.4");
assert(seam_gap>=0.4 && seam_gap<=0.8,"板缝需0.4..0.8");
assert(flange_width>=26 && flange_width<=28,"接头与止退耳需26..28法兰");
assert(minimum_service_gap>=12,"下面螺母和维护工具需至少12mm设计净空");
assert(clamp_thickness>=2 && clamp_thickness<=4,"夹厚需2..4，另核外露牙啮合");
assert(nut_well_diameter>=9 && nut_well_diameter<=12,"窝径需9..12，保留孔座外围与唇口");
assert(deck_width>=150 && deck_width<=176,"竖键交会避让及平台预算限制板宽150..176");
assert(xs[0]<-100 && xs[3]>60,"外形会截断四孔座或止退点");
for(i=[0:5]) assert(panel_bounds(i)[1]-panel_bounds(i)[0]<=90 &&
    panel_bounds(i)[3]-panel_bounds(i)[2]<=90,"单面板超过90mm打印预算");

// 局部坐标u跨缝、s沿插入轴，所有正式件与试片共用这两个模块。
module axial_profile(points,length){
    // 让二维截面处于XZ、挤出沿Y，便于所有接头复用同一尺寸。
    multmatrix([[1,0,0,0],[0,0,1,0],[0,1,0,0],[0,0,0,1]])
        linear_extrude(height=length) polygon(points);
}
module socket(length,c=fit_clearance){
    // 两个独立槽各自有完整两侧唇口，桥键才可同时约束两块板。
    // 屋顶留单独竖向间隙；不把最终接触误当正体积穿透。
    for(u=[-9,9]) translate([u,0,0]) axial_profile([
        [-3-c,-0.02],[3+c,-0.02],[3+c,0],[7+c,6],
        [7+c,6+c],[-7-c,6+c],[-7-c,6],[-3-c,0]],length);
}
// 桥底平整；33.7度斜面逐层外扩，桥键不需要封闭槽顶支撑。
module bridge(length,ear=false,c=fit_clearance){
    // 底桥把两个男榫连成单件，避免分开的键无法传递面内分离力。
    // 两端减去公差，保留闭端墙前的真实装配余量。
    difference(){
        union(){
            translate([-16,c,-3]) cube([32,length-2*c,3]);
            for(u=[-9,9]) translate([u,c,0])
                axial_profile([[-3,0],[3,0],[7,6],[-7,6]],length-2*c);
            if(ear) translate([15,2,-3]) cube([11,8,3]);
        }
        if(ear) translate([22,6,-4]) cylinder(d=3.4,h=6);
    }
}
// 转换仅改变装配坐标，不改变任何榫卯截面。
module at_joint(j){
    // 横键从列负X端进入；竖键分别从正负Y外边进入。
    q=joint(j);
    if(q[0]==0) translate([q[1],0,0])
        multmatrix([[0,1,0,0],[1,0,0,0],[0,0,1,0],[0,0,0,1]]) children();
    else translate([q[1],q[2]*deck_width/2,0]) scale([1,-q[2],1]) children();
}
module key_world(j,slide=0,dz=0,du=0){
    // 三个位移仅给诊断用，生产装配默认不施加偏移。
    at_joint(j) translate([du,slide,dz]) bridge(joint(j)[3],joint(j)[4]);
}
module beam(a,b,w=rib_width){
    // 背肋与皮层整体打印，禁止把接触但不相交的独立筋当一件。
    hull() for(p=[a,b]) translate([p[0],p[1],0]) cylinder(d=w,h=panel_thickness);
}
// 皮层连接所有肋，法兰保留燕尾唇；孔座与缝肋有连续实体路径。
module blank_deck(){
    // 孔座向两条缝法兰及外围连筋，形成可观察的实体传力路径。
    // 路径存在只证明连接连续，不能推断PLA层间/疲劳强度。
    union(){
        translate([xs[0],ys[0],panel_thickness-top_skin])
            cube([deck_length,deck_width,top_skin]);
        for(x=[xs[0]+2.5,xs[3]-2.5]) beam([x,ys[0]],[x,ys[2]]);
        for(y=[ys[0]+2.5,ys[2]-2.5]) beam([xs[0],y],[xs[3],y]);
        for(x=[-70,0]) translate([x-flange_width,ys[0],0])
            cube([2*flange_width,deck_width,panel_thickness]);
        translate([xs[0],-flange_width,0]) cube([deck_length,2*flange_width,panel_thickness]);
        for(p=mounts){
            translate([p[0],p[1],0]) cylinder(d=22,h=panel_thickness);
            beam(p,[p[0],0]);
            beam(p,[p[0]<0?-70:0,p[1]]);
            beam(p,[p[0],p[1]<0?ys[0]:ys[2]]);
        }
    }
}
// M3沉头锥45度，避免顶面翻床时出现水平封闭洞顶。
module stop_cut(xy){
    translate([xy[0],xy[1],-1]) cylinder(d=3.4,h=panel_thickness+2);
    translate([xy[0],xy[1],panel_thickness-1.55]) cylinder(d1=3.4,d2=6.5,h=1.56);
}
// 直壁工具窝保留平垫片座；翻床后窝底需局部可拆支撑，不能称全部免支撑。
module mount_cut(){
    // 底部薄夹层适配短外牙；全高外周仍连到背肋，不整座削薄。
    // 平座保留原垫片受压面，不能用锥面替代螺母的平稳支承。
    translate([0,0,-1]) cylinder(d=mount_hole,h=panel_thickness+2);
    translate([0,0,clamp_thickness]) cylinder(d=nut_well_diameter,h=panel_thickness+1);
}
module carved_deck(){
    // 先统一挖槽与孔，再裁片，所有相邻件共享全局轴线。
    difference(){
        blank_deck();
        for(j=[0:6]) at_joint(j) socket(joint(j)[3]);
        for(p=mounts) translate([p[0],p[1],0]) mount_cut();
        for(j=[0,3,4,5,6]) stop_cut(stop_xy(j));
    }
}
// 全板先切同一组槽孔再分片，避免接缝一侧漏切半个孔。
module panel_world(i){
    // 分缝留空而不是让两半共面重叠，实际间隙另由网格检验。
    b=panel_bounds(i);
    intersection(){carved_deck();translate([b[0],b[2],-1]) cube([b[1]-b[0],b[3]-b[2],panel_thickness+2]);}
}
module panel_print(i){
    // 绕X翻面保持正绕序，皮层先落床，背槽保持可清理的开放面。
    b=panel_bounds(i);
    translate([-(b[0]+b[1])/2,(b[2]+b[3])/2,panel_thickness]) rotate([180,0,0]) panel_world(i);
}
module key_print(j){
    // 有耳键包围框偏心，平移5mm只为居中，不改变孔与槽坐标。
    translate([joint(j)[4]?-5:0,-joint(j)[3]/2,3]) bridge(joint(j)[3],joint(j)[4]);
}
// 小试片直接调用正式socket/bridge，所有尺寸与板厚一起联动。
module coupon_block(side){
    // 短试片的闭端墙、止退孔和夹持厚度仍与正式板接口一致。
    difference(){
        translate([side<0?-28:seam_gap/2,0,0]) cube([28-seam_gap/2,36,panel_thickness]);
        socket(30);
        if(side>0) stop_cut([22,6]);
    }
}
module coupon_print(k){
    if(k==2) translate([-5,-15,3]) bridge(30,true);
    else translate([k==0?14.15:-14.15,18,panel_thickness]) rotate([180,0,0]) coupon_block(k==0?-1:1);
}
// 单座试片先核5mm短外牙、原螺母/垫片以及支撑清理可达性。
module mount_coupon(){
    // 先验证局部支撑能取净、孔能疏通，再把同工艺用到四安装窝。
    translate([0,0,panel_thickness]) rotate([180,0,0]) difference(){
        translate([-12,-12,0]) cube([24,24,panel_thickness]);
        mount_cut();
    }
}
// 紧固件为采购待核包络；四原柱已确认外牙，示意柱长不作实测。
module stop_bolt(j,tools=false){
    // 螺母和垫片仅显示包络，不作为已有紧固件规格的证据。
    p=stop_xy(j);
    translate([p[0],p[1],0]){
        translate([0,0,-10]) cylinder(d=tools?8:3,h=panel_thickness+10);
        if(!tools){
            translate([0,0,panel_thickness-1.55]) cylinder(d1=3,d2=6.5,h=1.55);
            translate([0,0,-3.8]) cylinder(d=7,h=0.8);
            translate([0,0,-6.2]) cylinder(d=6.35,h=2.4,$fn=6);
        }
    }
}
module assembly(explode=0){
    // 不显示垃圾斗/雷达/丝杆，避免误以为旧机构已适配此底板。
    // 半透明底板只是车体轮廓参考，旧上层板已按用户要求移除。
    for(i=[0:5]) color(i%3==0?"#ecb06b":i%3==1?"#65b6ae":"#7da9db")
        translate([(i%3-1)*explode,(floor(i/3)*2-1)*explode,0]) panel_world(i);
    for(j=[0:6]) if(assembly_stage==3 || j<3)
        color("#df734b") translate([0,0,-explode*0.8]) key_world(j);
    if(show_hardware && explode==0){
        for(j=[0,3,4,5,6]) color("#777777") stop_bolt(j);
        for(p=mounts) color("#999999") translate([p[0],p[1],0]){
            translate([0,0,clamp_thickness]) cylinder(d=6,h=0.5);
            translate([0,0,clamp_thickness+0.5]) cylinder(d=5.8,h=2,$fn=6);
            cylinder(d=2.5,h=stud_projection);
        }
    }
    if(show_reference && explode==0){
        for(p=mounts) color("#999999") translate([p[0],p[1],-pillar_height]) cylinder(d=7,h=pillar_height);
        color([0.4,0.4,0.4,0.15]) translate([body_offset_x-91.553737,-81.869997,-pillar_height-4])
            cube([183.107474,163.739994,4]);
    }
}
// 步骤1只沿列方向分开，横键随各列一起移动，不画成悬空错位。
module column_pairs(){
    // 内部横键必须先进入，三列合拢后其退出口才被邻列挡住。
    for(col=[0:2]) translate([(col-1)*20,0,0]){
        for(row=[0:1]) color(col==0?"#ecb06b":col==1?"#65b6ae":"#7da9db") panel_world(col+row*3);
        color("#df734b") key_world(col);
    }
}
// 数值入口优先，GUI保存单件状态不会改变导出清单。
if(part_id==-1) {} // 包含式诊断脚本只调用模块，不自动添加整机。
else if(part_id>=1 && part_id<=6) panel_print(part_id-1);
else if(part_id>=11 && part_id<=17) key_print(part_id-11);
else if(part_id>=21 && part_id<=23) coupon_print(part_id-21);
else if(part_id==24) mount_coupon();
else if(part_id==90) carved_deck();
else if(part_id==91) for(i=[0:5]) panel_world(i);
else if(part_id==92) key_world(part_index);
else if(part_id==93) panel_world(part_index);
else if(part_id==94) socket(30);
else if(part_id==95) bridge(30,true);
else if(view_mode==4){
    coupon_block(-1);coupon_block(1);color("orange") bridge(30,true);
}
else if(view_mode==2) assembly(16);
else if(view_mode==3 && assembly_stage==1) column_pairs();
else if(view_mode==3) assembly();
else assembly();
