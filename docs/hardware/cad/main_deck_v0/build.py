"""榫卯底板的轻量导出入口；仅依赖项目已有numpy/trimesh/Pillow。"""
import argparse
import json
import subprocess
import tempfile
import hashlib
from pathlib import Path

import numpy as np
import trimesh

# 路径锚定源文件目录，用户从其他盘符启动也不会导出到错误位置。
ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'main_deck.scad'


def cad(exe, target, definitions=(), source=SOURCE, image=False,camera=None):
    # 每个返回码都检查；旧产物不会掩盖本次导出失败。
    # 输出路径作为参数直接传递，不通过第二层shell拼接。
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    # 标准输出和错误分别捕获，失败时保留真实CAD诊断。
    args = [str(exe), '-o', str(target)]
    # 图像仅用于布局阅读，封闭性/穿透由STL和实体见证验收。
    if image:
        args += ['--imgsize=1200,900', '--projection=o', '--colorscheme=Tomorrow']
        # 显式中心与视距避免导入STL后CLI自动取景放大裁切整板。
        args += ['--camera='+camera] if camera else ['--viewall','--autocenter']
    else:
        args += ['--export-format', 'binstl']
    # 数值定义避免Windows原生命令行对字符串引号的剥离。
    for d in definitions:
        args += ['-D', d]
    result = subprocess.run(args + [str(source)], capture_output=True, text=True,encoding='utf-8',errors='replace')
    # 返回零但缺文件也视为失败，防止空模型静默通过。
    if result.returncode or not target.exists() or target.stat().st_size == 0:
        raise RuntimeError(f'CAD {target.name}: rc={result.returncode}\n{result.stdout}\n{result.stderr}')
    # OpenSCAD断言有时仍返回零，必须再检查错误标记。
    if 'ERROR:' in result.stdout+result.stderr:
        raise RuntimeError(result.stdout+result.stderr)
    return result


def mesh_info(path):
    # 面邻接连通性不依赖scipy；焊接后的边邻接可识别独立实体。
    # 只焊接STL共享坐标，不自动修洞或更改用户要打印的形状。
    m = trimesh.load_mesh(path, process=True)
    # 共享边的面才并入同一实体，点接触不能冒充可靠连通。
    parents = np.arange(len(m.faces))
    def root(x):
        while parents[x] != x:
            parents[x] = parents[parents[x]]
            x = parents[x]
        return x
    # 路径压缩使几千三角面也能快速判断单体，无需重型框架。
    for a, b in m.face_adjacency:
        ra, rb = root(a), root(b)
        if ra != rb:
            parents[ra] = rb
    count = len({root(i) for i in range(len(m.faces))})
    # 将尺寸/最低点写入JSON，方便切片前与实际文件复核。
    info = {'size_mm': m.extents.round(5).tolist(), 'z_min': float(m.bounds[0, 2]),
            'volume_mm3': round(float(m.volume), 5), 'watertight': bool(m.is_watertight),
            'winding_consistent': bool(m.is_winding_consistent), 'components': count}
    # 封闭、正体积、法线和单体共同约束，任何一项异常都停止。
    assert info['watertight'] and info['winding_consistent'] and count == 1 and m.volume > 0, (path, info)
    # 生产件和试片都必须平底落床，尺寸不能靠比例缩放通过。
    assert abs(m.bounds[0, 2]) < .002 and max(m.extents[:2]) <= 90.001 and m.extents[2] <= 100, (path, info)
    return m, info


def render_images(exe,out,report):
    # 预览使用刚导出的真实网格，避免F5重复实体内部接触面的条纹。
    # 导入实际STL显示配色，消除F5内部未合并面的接触条纹。
    with tempfile.TemporaryDirectory(prefix='rober-deck-image-') as temp:
        preview=Path(temp)/'preview.scad'
        prefix=f'include <{SOURCE.as_posix()}>;\n'
        for name, mode, angles in [('top',0,'0,0,0'),('bottom',1,'180,0,0'),
                                  ('exploded',2,'55,0,25'),('assembly',0,'80,0,25'),
                                  ('step1',3,'180,0,0'),('step2',3,'180,0,0')]:
            lines=[]
            for i in range(6):
                # 与源的打印变换互逆，分件图只加明确的爆炸位移。
                shift=f'[{(i%3-1)*16},{(i//3*2-1)*16},0]' if mode==2 else f'[{(i%3-1)*20},0,0]' if name=='step1' else '[0,0,0]'
                lines.append(f'b{i}=panel_bounds({i}); color("'+['#ecb06b','#65b6ae','#7da9db'][i%3]+f'") translate({shift}) translate([(b{i}[0]+b{i}[1])/2,(b{i}[2]+b{i}[3])/2,panel_thickness]) rotate([180,0,0]) import("{(out/"print"/f"P{i+1}_panel.stl").as_posix()}");')
            for j in range(7):
                if name in ['step1','step2'] and j>=3:
                    continue
                key=f'H{j+1}_bridge' if j<3 else f'V{j-2}_bridge'
                shift=f'[0,0,-12.8]' if mode==2 else f'[{(j-1)*20},0,0]' if name=='step1' else '[0,0,0]'
                lines.append(f'color("#df734b") translate({shift}) at_joint({j}) translate([joint({j})[4]?5:0,joint({j})[3]/2,-3]) import("{(out/"print"/f"{key}.stl").as_posix()}");')
            # 原柱作为示意参照；柱高不从图片估算、不计入制造BOM。
            if name=='assembly':
                lines.append('for(p=mounts) color("#999999") translate([p[0],p[1],-pillar_height]) cylinder(d=7,h=pillar_height);')
                lines.append('color([0.4,0.4,0.4,0.15]) translate([body_offset_x-91.553737,-81.869997,-pillar_height-4]) cube([183.107474,163.739994,4]);')
            if name in ['assembly','top','bottom']:
                lines.append('for(j=[0,3,4,5,6]) color("#777777") stop_bolt(j);')
                lines.append('for(p=mounts) color("#999999") translate([p[0],p[1],clamp_thickness]) { cylinder(d=6,h=0.5);translate([0,0,0.5]) cylinder(d=5.8,h=2,$fn=6);}')
            preview.write_text(prefix+'\n'.join(lines),encoding='utf-8')
            distance=650 if name in ['exploded','step1'] else 560
            cad(exe,out/f'{name}_raw.png',['part_id=-1'],source=preview,image=True,
                camera=f'-22.641541,0,0,{angles},{distance}')
    # 排版只裁边和标注，不补画任何未建模的结构。
    from make_preview import make_previews
    make_previews(out, report)


def run():
    # 默认完整执行；跳过回归仅供定位失败，不作为完整收口命令。
    parser = argparse.ArgumentParser()
    parser.add_argument('--openscad', required=True)
    parser.add_argument('--output', type=Path, default=ROOT / 'exports')
    parser.add_argument('--skip-regression', action='store_true')
    parser.add_argument('--verify-existing', action='store_true')
    parser.add_argument('--images-only', action='store_true')
    args = parser.parse_args()
    # 临时回归使用独立目录，用户可保留先前已确认的生产输出。
    out = args.output.resolve()
    if args.images_only:
        # 仅重新排图不覆盖几何报告，方便已验收网格的低影响文案调整。
        render_images(args.openscad,out,json.loads((out/'validation.json').read_text(encoding='utf-8')))
        print('PASS images regenerated from existing production STL')
        return
    version=subprocess.run([args.openscad, '--version'], capture_output=True, text=True,encoding='utf-8',errors='replace')
    print((version.stdout+version.stderr).strip(), flush=True)
    # 源哈希与版本随报告保存，避免不同稿的几何证据混用。
    report = {'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'openscad':(version.stdout+version.stderr).strip(),
              'numpy':np.__version__,'trimesh':trimesh.__version__,'production': {}, 'coupons': {}}
    # 打印目录只有六板七键，不放整板或诊断参考，避免用户误选。
    names = [f'P{i+1}_panel' for i in range(6)] + [f'H{i+1}_bridge' for i in range(3)] + [f'V{i+1}_bridge' for i in range(4)]
    # 编号在源与清单保持固定，装配时不凭零件外观猜位置。
    for index, name in enumerate(names):
        pid = index + 1 if index < 6 else index + 5
        path = out / 'print' / f'{name}.stl'
        if not args.verify_existing:
            cad(args.openscad, path, [f'part_id={pid}'])
        _, report['production'][name] = mesh_info(path)
        print(f'PASS mesh {name}: {report["production"][name]["size_mm"]}', flush=True)
    # 三套小试片和正式件共用同一榫槽模块，先试配再打印全板。
    # 三档必须各自成套试配，不将不同公差件混成一套。
    for c in [.2, .3, .4]:
        for k, name in enumerate(['left', 'right', 'bridge']):
            path = out / 'coupons' / f'fit_{c:.1f}_{name}.stl'
            if not args.verify_existing:
                cad(args.openscad, path, [f'part_id={21+k}', f'fit_clearance={c}'])
            _, report['coupons'][path.stem] = mesh_info(path)
    print('PASS nine coupon meshes: shared socket/bridge modules', flush=True)
    # 短外牙安装先试这个单座，不能用燕尾试片代替柱顶啮合检查。
    mount_path=out/'coupons'/'mount_seat_first.stl'
    if not args.verify_existing:
        cad(args.openscad,mount_path,['part_id=24'])
    _,report['coupons']['mount_seat_first']=mesh_info(mount_path)
    # 几何验证读实际STL，再补CGAL实体碰撞/插入见证。
    # 验证器恢复打印翻面后的装配坐标，再进行真实截面测量。
    from verify import verify_all
    # 诊断STL不放打印目录，用户看到的生产清单保持干净。
    with tempfile.TemporaryDirectory(prefix='rober-deck-') as temp:
        report['geometry'] = verify_all(args.openscad, out, Path(temp), cad, not args.skip_regression)
    # 只有核心检查成功才写报告，失败异常不会伪造PASS记录。
    (out / 'validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    render_images(args.openscad,out,report)
    # 数量清单随真实网格尺寸生成，不把示意整板列为可打印件。
    lines = ['# Tina2C打印清单', '', '先打coupons/mount_seat_first.stl，清理窝内局部支撑后在原短外牙柱上试夹紧；再打同档fit_0.3三件。',
             '正式件随源fit_clearance导出（本稿默认0.3）。若选0.2/0.4试片档，先修改源fit_clearance并重新export，之后再打印新生成整套件。',
             '所有文件单位mm、100%，逐件导入，分别打印；每件1个。面板顶面已翻到床面，桥键桥底已落床，安装窝底仍需局部支撑。', '', '| 文件 | 数量 | 实际尺寸mm |', '|---|---|---|']
    # 尺寸直接来自真实网格，不把设计名义值写成实测产物尺寸。
    for name, data in report['production'].items():
        lines.append(f'| print/{name}.stl | 1 | ' + ' × '.join(f'{v:.3f}' for v in data['size_mm']) + ' |')
    lines += ['', '先在coupons目录选择同一间隙值的left/right/bridge各1件试配；不要混用不同档。',
              '五套M3沉头螺栓/螺母/下垫片只止退，四M2.5锁到现有柱，原柱外牙约5mm，螺母/啮合/下方净空待实配。']
    (out/'PRINT_LIST.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('PASS MAIN DECK: 13 production + 10 coupons; mesh/interface/path/lock/regression checks', flush=True)


if __name__ == '__main__':
    run()
