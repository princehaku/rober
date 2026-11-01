// 整车展示：厂家底盘/车轮STL＋四柱参考＋最新一体底座。
// 本文件仅保留历史静态参照；当前0.5kg小侧斗见../compact_dump_v2/compact_dump.scad。
// 不改变任何打印源或STL；斗体制造设计仍按用户要求暂停。
// 来源：WAVE ROVER DXF与WAVE ROVER_MODEL_STL.stl，详见本目录README。

/* [展示开关] */
show_bucket=true;
show_deck=true;
show_pillars=true;
pillar_height=24; // 未实测的示意柱高，可改；不代表实际安装净空。
bucket_length=400;
bucket_width=200;
bucket_height=200;
bucket_gap=8; // 仅为看清层次的显示间隙，没有设计连续承托或翻转支点。

/* [Hidden] */
offset_x=-22.641541;
vendor_top_z=52.7359;
deck_t=12;
mounts=[[-29,-43],[-29,43],[29,-43],[29,43]];
$fn=24;
// 初次打开就看全车；使用显式中心/视距，避免继承单底座近景。
$vpt=[offset_x,0,78];
$vpr=[65,0,30];
$vpd=1200;

module chassis(){
    // STL截面Z50.9/51.1/51.7：四孔X±43，Y=-6.35844/51.64156。
    // DXF四轴86×58匹配1:1，刚体换轴后为共用X±29/Y±43。
    // 不使用全车包围盒中心代替孔组中心，保留22.641541偏置。
    color("#66747e") multmatrix([[0,1,0,offset_x],[ -1,0,0,0],
        [0,0,1,-vendor_top_z],[0,0,0,1]])
        import("../../../vendor/waveshare_wave_rover/WAVE ROVER_MODEL_STL.stl");
}
module latest_deck(){
    // 生产STL已顶面朝床，这里只作逆变换恢复使用姿态。
    // 四柱底落在已核对的厂家顶平面；柱长度仍是未测占位。
    if(show_pillars) for(p=mounts) color("#c7a03b")
        translate([p[0],p[1],0]) cylinder(d=7,h=pillar_height);
    if(show_deck) color("#58a6cc") translate([0,0,pillar_height+deck_t])
        rotate([180,0,0]) import("exports/main_deck_onepiece.stl");
}
module edge(a,b){
    // 线框只表达外包络，不包含可用底板/斗壁或任何承载连接。
    hull() for(p=[a,b]) translate(p) sphere(d=1.4);
}
module bucket_envelope(){
    // 用户选择40×20×20厘米；没有恢复旧小斗或金属梁整机。
    // 边框不遮住车体，开关关闭后可单独旋转检查底盘与一体板。
    z0=pillar_height+deck_t+bucket_gap;
    xl=offset_x-bucket_length/2;
    xh=offset_x+bucket_length/2;
    yl=-bucket_width/2;
    yh=bucket_width/2;
    color([0.96,0.45,0.12,0.55]){
        for(z=[z0,z0+bucket_height]){
            edge([xl,yl,z],[xh,yl,z]);edge([xl,yh,z],[xh,yh,z]);
            edge([xl,yl,z],[xl,yh,z]);edge([xh,yl,z],[xh,yh,z]);
        }
        for(x=[xl,xh]) for(y=[yl,yh]) edge([x,y,z0],[x,y,z0+bucket_height]);
    }
}
chassis();
latest_deck();
if(show_bucket) bucket_envelope();
