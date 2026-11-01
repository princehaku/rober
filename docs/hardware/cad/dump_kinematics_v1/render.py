"""生成可对照的整车姿态与往返动画；图中文字明确概念验证边界。"""
from pathlib import Path
import argparse
import json
import subprocess
import tempfile
import hashlib
import re
from PIL import Image, ImageDraw, ImageFont
from verify import parameters, geometry

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT/'dump_kinematics.scad'
OUT = ROOT/'exports'


def render(exe, path, angle, size='1200,900', extra=()):
    # 每张图直接由同一SCAD渲染，禁止后处理补画并不存在的机构。
    command = [exe,'-o',str(path),'--imgsize='+size,'--colorscheme=Tomorrow',
               '-D','animate=false','-D',f'dump_angle={angle}',*extra,str(SOURCE)]
    result = subprocess.run(command,capture_output=True,text=True,encoding='utf-8',errors='replace')
    # OpenSCAD部分版本错误时仍可能保留文件，因此同时核对返回值和错误文本。
    output = result.stdout+result.stderr
    assert result.returncode == 0 and 'ERROR:' not in output,output
    assert path.exists() and path.stat().st_size>0,path
    print(f'PASS render {angle:g} deg: {path.name}',flush=True)
    return output


def font(size):
    # 使用本机已有中文字体，仅用于图注，不修改CAD的几何与相机。
    return ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',size)


def captions(p):
    # 图注直接从当前SCAD参数与铰中心计算，用户改斗尺寸后不会留下旧数字。
    angles=[0,p['max_angle']/2,p['max_angle']]
    # 验证程序已限制最大角为整数，这里逐度计算真实所需行程范围。
    states=[geometry(p,a) for a in range(int(p['max_angle'])+1)]
    lengths=[float(sum((g['B']-g['A'])**2)**.5) for g in states]
    key_angles=list(range(0,int(p['max_angle']),10))+[p['max_angle']]
    # 最后一帧总取最大角，55度等非整十角也不会遗漏终点。
    return {'dimensions':[p[k] for k in ['bucket_length','bucket_width','bucket_height']],
            'angles':angles,'key_angles':key_angles,'lengths':[lengths[0],lengths[-1]],'stroke':max(lengths)-min(lengths)}


def main():
    # 工具路径显式传入，不下载新软件或修改系统关联。
    parser = argparse.ArgumentParser()
    parser.add_argument('--openscad',required=True)
    args = parser.parse_args()
    # 要求先更新数值报告；源哈希漂移时拒绝把旧验证贴到新图片上。
    p=parameters()
    source_hash=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    verified=json.loads((OUT/'verification.json').read_text(encoding='utf-8'))
    assert verified['source_sha256']==source_hash,'请先运行verify.py更新当前源的验证报告'
    labels=captions(p)
    # 展示开关从当前源读取，防止整斗/剖切画面与文字互相矛盾。
    source_text=SOURCE.read_text(encoding='utf-8')
    cutaway=bool(re.search(r'^cutaway=true;',source_text,re.M))
    show_cg=bool(re.search(r'^show_cg=true;',source_text,re.M))
    # 显示开关也进入图注；整斗显示时不能仍声称近侧被剖开。
    display_note=('近侧壁已剖开以显示机构' if cutaway else '完整三壁斗显示')+'；'+('红点仅为均匀垃圾假设重心' if show_cg else '垃圾重心点已隐藏')+'。'
    OUT.mkdir(exist_ok=True)
    # 保留三张原始姿态图，可单独放大检查每个铰接关系。
    # 固定镜头分别显示运输、途中、卸料，避免每帧自动缩放造成运动错觉。
    images = []
    for a,name in zip(labels['angles'],['transport','mid','dump']):
        path=OUT/(name+'.png')
        render(args.openscad,path,a)
        images.append(Image.open(path).convert('RGB'))
    # 并排图给用户直接比较两端姿态；近侧壁为剖切展示，实际验证保留完整三壁。
    board=Image.new('RGB',(1800,1040),'#f8f8f8')
    # 图例颜色对应SCAD材料颜色，读图不需要先理解代码变量名。
    d=ImageDraw.Draw(board)
    size='×'.join(f'{v:g}' for v in labels['dimensions'])
    d.text((24,15),f'整车可调翻斗 · {size} mm 斗 · 单丝杆 + 双侧门连杆',(25,40,50),font=font(32))
    d.text((24,65),'蓝：固定架   橙：转动斗   绿：丝杆   紫：后门连杆   黄：后门 / 铰轴',(45,60,70),font=font(26))
    for i,(im,title) in enumerate([(images[0],'放平运输 0°：后门闭合'),(images[2],f'卸料姿态 {p["max_angle"]:g}°：后门随连杆开启')]):
        # 只作统一缩放，不逐帧裁切到不同大小。
        im=im.resize((900,675))
        board.paste(im,(i*900,155))
        d.text((i*900+25,115),title,(25,40,50),font=font(26))
    # 重要限制放在整张图内，脱离聊天转发时仍保留证据边界。
    d.text((24,845),display_note+' 图中未计算整车重心。',(45,60,70),font=font(25))
    l0,l1=labels['lengths']
    d.text((24,895),f'丝杆铰距约 {l0:.0f} → {l1:.0f} mm；几何所需行程约 {labels["stroke"]:.0f} mm，实际型号 / 制动 / 限位待定。',(45,60,70),font=font(25))
    d.text((24,945),'2 kg 装载稳定性未验证：需后支撑 / 重心方案；本稿不可直接作为整机代打定型文件。',(185,55,38),font=font(26))
    board.save(OUT/'overview.png')
    # 动画中也显示同样边界；去程结束后原路回零，避免循环跳变。
    frames=[]
    with tempfile.TemporaryDirectory(prefix='render-',dir=ROOT) as tmp:
        # 中间帧使用临时目录，避免把无关渲染缓存误提交到仓库。
        for a in labels['key_angles']:
            path=Path(tmp)/f'{a}.png'
            render(args.openscad,path,a,'800,600')
            canvas=Image.new('RGB',(800,700),'#f8f8f8')
            canvas.paste(Image.open(path).convert('RGB'),(0,45))
            draw=ImageDraw.Draw(canvas)
            draw.text((12,8),f'翻斗 {a:g}° · 后门由双侧平行四杆同步开启',(30,45,55),font=font(23))
            draw.text((12,640),('近侧剖切' if cutaway else '完整三壁')+' / 2kg装载稳定性未验证',(185,55,38),font=font(20))
            frames.append(canvas)
        sequence=frames+list(reversed(frames[1:-1]))
        # 倒序复用同一姿态保证展示连续；真实回程数值另由verify独立计算。
        # 首末姿态停留略久，使用户看清闭门和打开后的落料方向。
        durations=[700 if i in [0,len(frames)-1] else 240 for i in range(len(sequence))]
        sequence[0].save(OUT/'motion.gif',save_all=True,append_images=sequence[1:],duration=durations,loop=0,optimize=False)
        # 直接对SCAD运行非法参数护栏，证明失败并非仅由Python重复公式给出。
        invalid=[]
        # 三个失效来源分别覆盖倾角、行程和支座落点，错误应明确可见。
        for expression in ['dump_angle=80','actuator_stroke=5','pivot_x=-180']:
            result=subprocess.run([args.openscad,'-o',str(Path(tmp)/'invalid.csg'),'-D',expression,str(SOURCE)],
                                  capture_output=True,text=True,encoding='utf-8',errors='replace')
            output=result.stdout+result.stderr
            assert 'ERROR: Assertion' in output,output
            invalid.append(expression)
    # 记录可复用命令结果，避免把图文件存在当成解析通过的唯一依据。
    # 回归非默认图注数据，覆盖斗高和最大角变化而无需重复渲染厂家大网格。
    changed_max=p['max_angle']-5
    # 相对当前最大角选择回归值，用户已经改成40度时也不会误报失败。
    changed=captions(dict(p,bucket_height=p['bucket_height']+20,max_angle=changed_max))
    assert changed['dimensions'][2]==p['bucket_height']+20 and changed['angles']==[0,changed_max/2,changed_max]
    assert changed['lengths'][1] != labels['lengths'][1] and changed['key_angles'][-1]==changed_max
    (OUT/'render_check.json').write_text(json.dumps({'source_sha256':source_hash,'captions':labels,'variation_captions':changed,
        'rendered_angles':labels['angles'],'animation_angles':labels['key_angles']+list(reversed(labels['key_angles'][1:-1])),
        'scad_rejected':invalid,'scope':'OpenSCAD预览渲染与参数断言；无打印切片/实物验证'},ensure_ascii=False,indent=2),encoding='utf-8')
    print('PASS overview / motion.gif / 3 SCAD invalid-parameter checks',flush=True)


if __name__=='__main__':
    main()
