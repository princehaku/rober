// 一体代打试装稿：沿用已交付厚肋轮廓，仅保留四处原柱接口。
// 依据本地WAVE ROVER两张DXF的58×86轴线，单位毫米。
// 200×160/厚度/肋截面均为设计值，未证明2kg垃圾与斗架总载荷。

/* [板面设计参数] */
deck_length=200;
deck_width=160;
panel_thickness=12;
top_skin=4;
rib_width=5;
flange_width=26;

/* [原四柱安装座] */
// 外形中心与孔组中心不同，禁止把四孔跟着外形重新居中。
body_offset_x=-22.641541;
mount_pitch_x=58;
mount_pitch_y=86;
mount_hole=3;
seat_diameter=22;
nut_well_diameter=10;
clamp_thickness=2; // 外牙约5毫米为用户近似量，剩余啮合须试片实配。

/* [显示] */
print_pose=false;
part_id=0; // 1为脚本打印入口，始终将安装顶面朝床。
$fn=48;

// 参数约束只保证几何可行，不能当强度/螺母啮合批准。
assert(deck_length>=170 && deck_width>=130,"板长宽不足以保留原四座和厚肋");
assert(panel_thickness>=8 && top_skin>=3 && top_skin<panel_thickness);
assert(clamp_thickness>=2 && clamp_thickness<panel_thickness);
assert(mount_hole>2.5 && nut_well_diameter>=9 && seat_diameter>=nut_well_diameter+8);
assert(rib_width>=4 && flange_width>=22);
assert(abs(body_offset_x)+mount_pitch_x/2+seat_diameter/2<deck_length/2);
assert(mount_pitch_y/2+seat_diameter/2<deck_width/2);

mounts=[for(x=[-mount_pitch_x/2,mount_pitch_x/2]) for(y=[-mount_pitch_y/2,mount_pitch_y/2]) [x,y]];
xlo=body_offset_x-deck_length/2;
xhi=body_offset_x+deck_length/2;

module beam2d(a,b,w=rib_width){
    // 圆端筋与原版一致；外围最终统一裁剪，不让端圆越过200×160。
    hull() for(p=[a,b]) translate(p) circle(d=w);
}
module rib_outline(){
    // 原分块版靠每片边界裁剪；一体版保留一次整板边界裁剪。
    intersection(){
        translate([xlo,-deck_width/2]) square([deck_length,deck_width]);
        union(){
            for(x=[xlo+rib_width/2,xhi-rib_width/2]) beam2d([x,-deck_width/2],[x,deck_width/2]);
            for(y=[-deck_width/2+rib_width/2,deck_width/2-rib_width/2]) beam2d([xlo,y],[xhi,y]);
            for(x=[-70,0]) translate([x-flange_width,-deck_width/2]) square([2*flange_width,deck_width]);
            translate([xlo,-flange_width]) square([deck_length,2*flange_width]);
            for(p=mounts){
                translate(p) circle(d=seat_diameter);
                beam2d(p,[p[0],0]);
                beam2d(p,[p[0]<0?-70:0,p[1]]);
                beam2d(p,[p[0],p[1]<0?-deck_width/2:deck_width/2]);
            }
        }
    }
}
module blank_deck(){
    // 整体皮层与背肋相交合并，没有板缝、键槽或独立桥键。
    // 背面肋间凹区保留原轮廓，它们不是供接头插入的槽。
    union(){
        translate([xlo,-deck_width/2,panel_thickness-top_skin]) cube([deck_length,deck_width,top_skin]);
        linear_extrude(panel_thickness) rib_outline();
    }
}
module mounting_cut(){
    // 平底窝保留垫片受压面，外周全高连接厚肋。
    // 下沉窝使短外牙只穿薄底，原螺母不能压在12毫米板顶。
    translate([0,0,-1]) cylinder(d=mount_hole,h=panel_thickness+2);
    translate([0,0,clamp_thickness]) cylinder(d=nut_well_diameter,h=panel_thickness+1);
}
module onepiece(){
    // 仅减四座；不调用旧carved_deck或七socket/五stop_cut。
    difference(){blank_deck();for(p=mounts) translate([p[0],p[1],0]) mounting_cut();}
}
// 顶面朝床使背肋向上开放，四窝底环形桥仍需要局部可拆支撑。
// 使用姿态与打印姿态均保持Z最低为0，四轴关于Y对称。
if(part_id==1 || print_pose) translate([0,0,panel_thickness]) rotate([180,0,0]) onepiece();
else onepiece();
