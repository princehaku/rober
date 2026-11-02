"""串行导出打印试装件，拒绝破面、断开的功能件和超过打印床的零件。"""
# 打印零件与标准件分开，电机本体不会被误导出为塑料件。
# 所有实体由同一参数源产生，导出器不单独修改螺纹或齿形尺寸。
# 网格需要封闭、正体积、单连通，不能用表面截图代替检查。
# 半壳的分型平面朝床；螺杆竖直打印时高度仍在设备范围内。
# 每个零件的实际边界保留在JSON，便于切片前核对比例。
# 标准件接触不参与打印件单连通计数，装配碰撞另行判断。
# 真正空交集会使OpenSCAD返回一，只有同时出现空集文本才认可。
# 错误半圈相位应产生实体交集，否则正例检测可能根本没有工作。
# 爆炸图移动真实零件展示装配次序，不改变原始STL的打印尺寸。
# 临时拟合文件使用项目内自动清理目录，不进入最终压缩包。
# 图片是结构预览，不能证明PLA在真实电机负载下不会变形。
# 标准紧固件由README列出，打印包不代替装车实配和逐级试载。
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import tempfile
import zipfile
import trimesh
from verify import parameters

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'drive.scad'
OUT=ROOT/'exports'
PARTS=['lower_shell','upper_shell','screw','slider','input_gear','washer','thread_coupon','male_coupon','shaft_coupon','lower_mount','upper_mount']


def component_count(mesh):
    # 本机没有可选图算法依赖，用面邻接并查集检查单一连通功能件。
    parent=list(range(len(mesh.faces)))
    def root(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    for a,b in mesh.face_adjacency:
        ra,rb=root(int(a)),root(int(b))
        if ra!=rb:parent[ra]=rb
    return len({root(i) for i in range(len(parent))})


def run(exe,path,definitions=(),empty=False):
    # 使用同一个源文件生成实体；空交集是几何配合测试的成功条件。
    args=[exe,'-o',str(path),'--imgsize=1100,850','--colorscheme=Tomorrow']
    for expression in definitions:args+=['-D',expression]
    result=subprocess.run(args+[str(SOURCE)],capture_output=True,text=True,encoding='utf-8',errors='replace')
    log=result.stdout+result.stderr
    if empty and 'Current top level object is empty' in log:return None
    # 返回码与错误文本同时检查，防止复用旧输出误判成功。
    assert result.returncode==0 and 'ERROR:' not in log,log
    assert path.exists() and path.stat().st_size>0
    return path


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--openscad',required=True);args=parser.parse_args()
    OUT.mkdir(exist_ok=True);records={};p=parameters()
    # 整批记录开始时的源摘要，导出期间源改动就拒绝发布混合批次。
    initial_hash=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    for name in PARTS:
        path=OUT/(name+'.stl');run(args.openscad,path,[f'part="{name}"'])
        # 用实际输出三角网格检查，不用设计参数代替制造文件的尺寸。
        mesh=trimesh.load_mesh(path,process=True)
        assert mesh.is_watertight and mesh.is_volume and mesh.volume>0,name
        count=component_count(mesh);assert count==1,(name,'断开的实体',count)
        # 两半壳以分型面为底；其余件都从打印Z零平面起，不允许负Z悬空摆放。
        assert abs(mesh.bounds[0,2])<.002,(name,mesh.bounds)
        assert max(mesh.extents)<=95,(name,mesh.extents)
        records[name]={'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bounds_mm':mesh.bounds.tolist(),
                       'extents_mm':mesh.extents.tolist(),'volume_mm3':float(mesh.volume),'watertight':True,'connected_components':1}
        print('PASS STL',name,mesh.extents.round(3),flush=True)
    # 实际布尔相交验证螺母运动与轴转向，而不只比对同一公式中的变量。
    intersections=[]
    with tempfile.TemporaryDirectory(prefix='fit-',dir=ROOT) as tmp:
        for extension in [0,p['working_stroke']/2,p['working_stroke']]:
            result=run(args.openscad,Path(tmp)/'fit.stl',['part="thread_intersection"',f'extension={extension}'],empty=True)
            assert result is None,('实际螺纹穿透',extension)
            intersections.append(extension)
            # 内部总装碰撞包含真实壳与滑块、齿轮、轴和电机，捕捉合壳螺柱侵入滑道。
            result=run(args.openscad,Path(tmp)/'internal.stl',['part="internal_intersection"',f'extension={extension}'],empty=True)
            assert result is None,('驱动内部硬碰撞',extension)
        # 故意错半圈应发生穿透，证明负例确实能触发牙形检查。
        wrong=run(args.openscad,Path(tmp)/'wrong.stl',['part="thread_intersection"','phase_error=180'])
        assert trimesh.load_mesh(wrong).volume>.01
    # 独立装配和爆炸图都来自实际分件，不绘制缺少结构的示意圆筒。
    run(args.openscad,OUT/'assembly.png')
    run(args.openscad,OUT/'extended.png',[f'extension={p["working_stroke"]}','$vpt=[7,0,55]','$vpd=360'])
    run(args.openscad,OUT/'exploded.png',['exploded=true','$vpt=[7,0,55]','$vpd=400'])
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==initial_hash,'导出期间源已变更，请重新执行'
    # 压缩包严格按打印清单创建，调试交集和中间图不会进入用户打印包。
    archive=OUT/'n20-print-fit-parts.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for name in PARTS:z.write(OUT/(name+'.stl'),name+'.stl')
    # 再读压缩包检查清单和CRC，不能仅以ZIP文件存在作为交付证据。
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and sorted(z.namelist())==sorted(name+'.stl' for name in PARTS)
    report={'source_sha256':initial_hash,'parts':records,'thread_no_intersection_extensions_mm':intersections,
            'internal_no_intersection_extensions_mm':intersections,'wrong_half_turn_detected':True,
            'archive':{'file':archive.name,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'entries':len(PARTS),'crc_pass':True},
            'scope':'PLA空载拟合件；网格通过不代表实际配合、承载或电机匹配通过'}
    (OUT/'export_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'PASS {len(PARTS)} printable meshes / 3 thread and assembly phases / negative control / ZIP',flush=True)


if __name__=='__main__':main()
