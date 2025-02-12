import argparse
import re
import random
import math
from pathlib import Path
from PIL import Image, ImageDraw
from rich.progress import Progress, BarColumn, TimeRemainingColumn, TextColumn
from rich.console import Console
from rich.style import Style
import numpy as np

console = Console()

# 颜色处理正则
COLOR_REGEX = re.compile(r"^#([0-9a-f]{6,8})$", re.IGNORECASE)

def parse_color(color_str):
    """处理十六进制颜色并转换为RGBA元组"""
    if color_str.lower() == "random":
        return tuple(random.randint(0, 255) for _ in range(4))
    
    match = COLOR_REGEX.match(color_str)
    if not match:
        raise ValueError("颜色格式错误")
    
    hex_str = match.group(1).ljust(8, 'f')  # 补全透明度
    if len(hex_str) == 6:
        hex_str += 'ff'
    return tuple(int(hex_str[i:i+2], 16) for i in range(0, 8, 2))

def generate_shape(draw, pos, size, shape, color):
    """生成不同形状"""
    x, y = pos
    size = max(1, size)
    if shape == 'pixel':
        draw.point((x, y), fill=color)
    elif shape == 'circle':
        draw.ellipse([x-size, y-size, x+size, y+size], fill=color)
    elif shape == 'square':
        draw.rectangle([x-size, y-size, x+size, y+size], fill=color)
    elif shape == 'triangle':
        points = [
            (x, y - size*2),
            (x + size, y + size),
            (x - size, y + size)
        ]
        draw.polygon(points, fill=color)
    elif shape == 'star':
        outer = size
        inner = size//2
        points = []
        for i in range(5):
            angle = math.radians(72 * i - 90)
            points.extend([
                (x + outer * math.cos(angle), y + outer * math.sin(angle)),
                (x + inner * math.cos(angle + math.radians(36)), 
                 y + inner * math.sin(angle + math.radians(36)))
            ])
        draw.polygon(points, fill=color)

def blend_pixel(original, overlay):
    """合并半透明颜色"""
    alpha = overlay[3] / 255.0
    return tuple(
        int(original[i] * (1 - alpha) + overlay[i] * alpha)
        for i in range(3)
    ) + (255,)

def generate_coordinates(img, distribution, num_points):
    """不同分布算法生成坐标"""
    width, height = img.size
    if distribution == 'uniform':
        return [(random.randint(0, width-1), random.randint(0, height-1)) 
                for _ in range(num_points)]
    elif distribution == 'normal':
        return [
            (int(np.random.normal(width/2, width/4)),
             int(np.random.normal(height/2, height/4)))
            for _ in range(num_points)
        ]

def main():
    parser = argparse.ArgumentParser(description="图片散点生成器")
    
    # 基础参数
    parser.add_argument('-i', '--input', help="输入图片路径")
    parser.add_argument('-o', '--output', required=True, help="输出图片路径")
    parser.add_argument('-s', '--size', nargs=2, type=int, help="生成底图尺寸 (需与输入图互斥)")
    parser.add_argument('-bg', '--background', help="底图颜色 (十六进制)")
    
    # 散点参数
    parser.add_argument('-n', '--num', type=int, help="散点数量")
    parser.add_argument('-d', '--density', type=float, help="密度 (点数/每平方像素)")
    parser.add_argument('-c', '--color', required=True, help="颜色 (十六进制或random)")
    parser.add_argument('-ps', '--pointsize', nargs='+', type=int, required=True,help="点大小 (支持范围)")
    parser.add_argument('-sh', '--shape', required=True, choices=['pixel','circle','square','triangle','star','random'],help="点形状")
    parser.add_argument('-m', '--mode', choices=['replace','blend'], required=True,help="覆盖模式")
    parser.add_argument('-dist', '--distribution', default='uniform',choices=['uniform','normal'], help="分布算法")

    args = parser.parse_args()

    try:
        # 基础校验
        if args.input and args.size:
            raise ValueError("输入图片和底图尺寸参数互斥")
        if not (args.input or (args.size and args.background)):
            raise ValueError("缺少必要参数: 需要输入图片或底图参数")
        if not (args.num or args.density):
            raise ValueError("需要指定点数或密度")
        if len(args.pointsize) not in [1,2]:
            raise ValueError("点尺寸参数错误")

        # 创建或加载底图
        if args.input:
            img = Image.open(args.input).convert("RGBA")
        else:
            img = Image.new("RGBA", tuple(args.size), parse_color(args.background))

        width, height = img.size
        
        # 计算点数
        if args.num:
            num_points = args.num
        else:
            area = width * height
            num_points = int(area * args.density)
        
        # 点参数解析
        if len(args.pointsize) == 1:
            point_size = lambda: args.pointsize[0]
        else:
            point_size = lambda: random.randint(args.pointsize[0], args.pointsize[1])
        
        color = parse_color(args.color)
        draw = ImageDraw.Draw(img)
        pixels = img.load()

        # 进度条配置
        progress = Progress(
            TextColumn("[bold blue]{task.fields[status]}", justify="right"),
            BarColumn(bar_width=40),
            "[progress.percentage]{task.percentage:>3.0f}%",
            TimeRemainingColumn(),
            TextColumn("[green]速度: {task.fields[speed]:.1f}点/秒"),
            console=console,
            refresh_per_second=30
        )

        with progress:
            task = progress.add_task("[cyan]生成散点", total=num_points, status="初始化...", speed=0)
            
            coordinates = generate_coordinates(img, args.distribution, num_points)
            start_time = progress.tasks[task].start_time
            point_color = parse_color(args.color) if args.color.lower() != 'random' else None
            
            
            for i, (x, y) in enumerate(coordinates):
                final_color = parse_color("random") if args.color.lower() == 'random' else point_color
                
                # 边界检查
                if not (0 <= x < width and 0 <= y < height):
                    continue
                
                size = point_size()
                shape = args.shape if args.shape != 'random' else random.choice(
                    ['pixel','circle','square','triangle','star']
                )
                
                # 覆盖模式处理
                if args.mode == 'replace':
                    generate_shape(draw, (x, y), size//2, shape, final_color)
                else:
                    overlay = Image.new("RGBA", img.size, (0,0,0,0))
                    overlay_draw = ImageDraw.Draw(overlay)
                    generate_shape(overlay_draw, (x, y), size//2, shape, final_color)
                    img = Image.alpha_composite(img, overlay)
                    draw = ImageDraw.Draw(img)
                    pixels = img.load()
                
                # 进度更新
                elapsed = progress.tasks[task].elapsed
                speed = (i+1) / elapsed if elapsed else 0
                progress.update(task, advance=1, speed=speed, status=f"已生成 {i+1}/{num_points}")

        img.save(args.output)
        console.print(f"[bold green]✅ 图片已保存至 {args.output}")

    except Exception as e:
        console.print(f"[bold red]🚨 错误: {str(e)}", style=Style(color="red"))

if __name__ == "__main__":
    main()
