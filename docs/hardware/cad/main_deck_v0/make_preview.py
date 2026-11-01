"""把真实CAD渲染裁白边并加中文说明，不产生想象几何。"""
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageFont


def make_previews(out, report):
    # 字体来自系统，不把第三方字体或工具缓存写进Git。
    font_path='C:/Windows/Fonts/msyh.ttc'
    title=ImageFont.truetype(font_path,28)
    font=ImageFont.truetype(font_path,20)
    small=ImageFont.truetype(font_path,17)
    # 一张总览兼顾正面和背面，用户无需在大量验证图中找结构。
    canvas=Image.new('RGB',(1440,1240),'white')
    draw=ImageDraw.Draw(canvas)
    draw.text((24,10),'榫卯大底板 · 200×160设计稿 · 未切片 / 未实打 / 未加载',(20,35,45),font=title)
    # 每张卡的标题说明观察角度，颜色对应三列而非不同材料。
    cards=[('assembly_raw.png','上车：旧上层板移除，原四柱保留',
            '孔组O=(0,0)，外形中心X=-22.642；四M2.5用螺母锁紧'),
           ('bottom_raw.png','底面：六块厚肋板＋七根双燕尾桥键',
            'X负端无柱板 → X=-70燕尾 → 中列厚座 → 原柱'),
           ('top_raw.png','顶面：四个下沉安装窝',
            '窝Ø10 / 底厚2；约5mm外牙，啮合与工具须实配'),
           ('exploded_raw.png','拆分：P1..P6各1；H1..H3、V1..V4各1',
            'M3仅止退：5栓＋5母＋5下垫；没有金属条')]
    # 四卡只是四个视角，不表示能同时放进一张打印平台。
    for index,(name,heading,caption) in enumerate(cards):
        x=(index%2)*720
        y=60+(index//2)*540
        # 原始图来自本轮导出的STL，禁止AI图代替机械几何。
        im=Image.open(out/name).convert('RGB')
        # 用背景差分裁边，只做图像排版，实际模型由OpenSCAD渲染。
        # 容差阈值只去掉背景，不切掉细肋或螺丝。
        diff=ImageChops.difference(im,Image.new('RGB',im.size,im.getpixel((0,0)))).convert('L')
        mask=diff.point(lambda p:255 if p>18 else 0)
        box=mask.getbbox()
        if box:
            im=im.crop((max(box[0]-12,0),max(box[1]-12,0),min(box[2]+12,im.width),min(box[3]+12,im.height)))
        # 等比例缩放图片，不改变任何CAD或STL的毫米尺寸。
        im.thumbnail((690,410))
        def pos(xx,yy,bottom=False):
            # 只把已知设计坐标映射到完整正交板图，不从图片反推毫米。
            return (12+(im.width-24)*(xx+122.641541)/200,
                    12+(im.height-24)*((yy+80) if bottom else (80-yy))/160)
        if name=='top_raw.png':
            # 正交顶视与安装坐标线性对应，编号只是叠字，不改孔位几何。
            mark=ImageDraw.Draw(im)
            for number,(xx,yy) in enumerate([(-29,-43),(-29,43),(29,-43),(29,43)],1):
                # 孔旁数字刻意偏移避让，孔中心仍以真实CAD圆形为准。
                px,py=pos(xx,yy)
                mark.text((px+9,py-20),str(number),(185,25,25),font=font,stroke_width=1,stroke_fill='white')
            for row,yy in enumerate([-12,68]):
                # 面板编号与导出文件一一对应，避免只靠颜色区分两行。
                for col,xx in enumerate([-96.32077,-35,38.67923]):
                    px,py=pos(xx,yy)
                    mark.text((px-14,py-12),f'P{col+row*3+1}',(20,35,45),font=font,stroke_width=1,stroke_fill='white')
        if name=='bottom_raw.png':
            # 底视绕X翻转，Y映射相反；标签仍按正式安装坐标编号。
            mark=ImageDraw.Draw(im)
            for j,(xx,yy) in enumerate([(-101.32,0),(-40,0),(33.68,0)],1):
                # 横桥键先装，编号按X负端到正端依次递增。
                px,py=pos(xx,yy,True)
                mark.text((px-14,py-12),f'H{j}','white',font=font,stroke_width=1,stroke_fill='#7a321d')
            for j,(xx,yy) in enumerate([(-70,-52),(-70,52),(0,-52),(0,52)],1):
                # 竖桥键按每条缝的负Y/正Y外缘成对编号。
                px,py=pos(xx,yy,True)
                mark.text((px-14,py-12),f'V{j}','white',font=font,stroke_width=1,stroke_fill='#7a321d')
        canvas.paste(im,(x+(720-im.width)//2,y+42+(410-im.height)//2))
        draw.text((x+16,y),heading,(20,35,45),font=font)
        draw.text((x+16,y+462),caption,(40,50,60),font=small)
    draw.text((24,1150),'打印：面板已顶面朝床；安装窝底需要局部支撑并清理。桥键桥底朝床，燕尾槽保持开放。',(25,45,55),font=font)
    draw.text((24,1190),'先单安装座 → 同档燕尾三件试配 → 六板七键分别打印；四孔编号1/2为X=-29，3/4为X=+29。',(25,45,55),font=font)
    # 图中明确标未实打/加载，避免把漂亮图当承载验收。
    canvas.save(out/'overview.png')
    # 两个阶段图分别来自实际CAD，避免把爆炸图当装配顺序。
    steps=Image.new('RGB',(1440,590),'white')
    d=ImageDraw.Draw(steps)
    # 顺序图表现先横后竖，内部键的退出口必须最后才封住。
    captions=['1 先拼三列上下两片，插H1/H2/H3','2 三列并拢封住H2/H3出口，再插四V键']
    for i,name in enumerate(['step1_raw.png','step2_raw.png']):
        im=Image.open(out/name).convert('RGB')
        im.thumbnail((700,470))
        steps.paste(im,(i*720+(720-im.width)//2,40))
        d.text((i*720+15,10),captions[i],(20,35,45),font=font)
    d.text((20,535),'3 拧五M3止退 → 翻正 → 四柱外牙穿3mm孔 → 原M2.5螺母/垫片落入窝底锁紧；拆卸逆序。',(20,35,45),font=font)
    # 清理支撑与试夹紧先于上车，步骤图不能代替文字注意事项。
    steps.save(out/'assembly_steps.png')
