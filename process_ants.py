"""处理蚂蚁原型图：去背景、缩放、锐化、加描边、统一风格（纯Pillow实现）"""

from PIL import Image, ImageFilter, ImageEnhance, ImageDraw
import os

INPUT_DIR = 'images/ant'
OUTPUT_DIR = 'images/ant_processed'
TARGET_SIZE = 256


def remove_background(img, threshold=230):
    """去除白色/浅色背景，返回带透明通道的RGBA图"""
    img = img.convert('RGBA')
    w, h = img.size
    pixels = list(img.getdata())

    # 采样四角+四边中点确定背景色
    samples = []
    for pos in [(0, 0), (w-1, 0), (0, h-1), (w-1, h-1),
                (w//2, 0), (w//2, h-1), (0, h//2), (w-1, h//2)]:
        samples.append(pixels[pos[1] * w + pos[0]])
    bg_r = sum(p[0] for p in samples) // len(samples)
    bg_g = sum(p[1] for p in samples) // len(samples)
    bg_b = sum(p[2] for p in samples) // len(samples)

    new_pixels = []
    for r, g, b, a in pixels:
        # 策略1：接近背景色
        dist = ((r - bg_r) ** 2 + (g - bg_g) ** 2 + (b - bg_b) ** 2) ** 0.5
        if dist < 55:
            new_pixels.append((0, 0, 0, 0))
            continue
        # 策略2：高亮+低饱和 = 近白
        max_c = max(r, g, b)
        min_c = min(r, g, b)
        if max_c > threshold and (max_c - min_c) < 25:
            new_pixels.append((0, 0, 0, 0))
            continue
        new_pixels.append((r, g, b, a))

    result = Image.new('RGBA', (w, h))
    result.putdata(new_pixels)
    return result


def crop_to_content(img):
    """裁剪到内容边界框（留少量padding）"""
    bbox = img.getbbox()
    if bbox is None:
        return img
    content_w = bbox[2] - bbox[0]
    content_h = bbox[3] - bbox[1]
    size = max(content_w, content_h)
    cx = (bbox[0] + bbox[2]) // 2
    cy = (bbox[1] + bbox[3]) // 2
    pad = int(size * 0.08)
    size += pad * 2
    left = max(0, cx - size // 2)
    top = max(0, cy - size // 2)
    right = min(img.width, left + size)
    bottom = min(img.height, top + size)
    return img.crop((left, top, right, bottom))


def add_outline(img, outline_width=2, outline_color=(40, 30, 20, 255)):
    """给蚂蚁主体添加深色描边"""
    alpha = img.split()[3]
    # 膨胀alpha
    outline_alpha = alpha.filter(ImageFilter.MaxFilter(outline_width * 2 + 1))
    # 描边 = 膨胀 - 原始
    oa = list(outline_alpha.getdata())
    aa = list(alpha.getdata())
    outline_mask = [(oa[i] > 0) and (aa[i] == 0) for i in range(len(aa))]

    result_data = list(img.getdata())
    for i, is_outline in enumerate(outline_mask):
        if is_outline:
            result_data[i] = outline_color

    result = Image.new('RGBA', img.size)
    result.putdata(result_data)
    return result


def sharpen_and_enhance(img):
    """锐化 + 提升对比度和饱和度"""
    img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
    img = ImageEnhance.Contrast(img).enhance(1.2)
    img = ImageEnhance.Color(img).enhance(1.15)
    img = ImageEnhance.Brightness(img).enhance(1.05)
    return img


def flatten_style(img):
    """微卡通风格化：量化色彩层次"""
    data = img.getdata()
    new_data = []
    for r, g, b, a in data:
        if a > 10:
            # 色彩量化到8的倍数
            r = round(r / 8) * 8
            g = round(g / 8) * 8
            b = round(b / 8) * 8
            r = max(0, min(255, r))
            g = max(0, min(255, g))
            b = max(0, min(255, b))
        new_data.append((r, g, b, a))
    result = Image.new('RGBA', img.size)
    result.putdata(new_data)
    return result


def clean_white_edges(img):
    """去除半透明白边"""
    data = list(img.getdata())
    new_data = []
    for r, g, b, a in data:
        if 0 < a < 255 and r > 200 and g > 200 and b > 200:
            a = min(a, 100)
        new_data.append((r, g, b, a))
    result = Image.new('RGBA', img.size)
    result.putdata(new_data)
    return result


def process_ant(input_path, output_path):
    """完整处理单张蚂蚁图"""
    img = Image.open(input_path)
    print(f"  原始: {img.size} {img.mode}")

    img = remove_background(img)
    print(f"  去背景: OK")

    img = crop_to_content(img)
    print(f"  裁剪: {img.size}")

    img = img.resize((TARGET_SIZE, TARGET_SIZE), Image.LANCZOS)
    print(f"  缩放: {img.size}")

    img = flatten_style(img)
    print(f"  风格化: OK")

    img = sharpen_and_enhance(img)
    print(f"  锐化增强: OK")

    img = add_outline(img)
    print(f"  描边: OK")

    img = clean_white_edges(img)
    print(f"  清理白边: OK")

    img.save(output_path, 'PNG')
    print(f"  保存: {output_path}")
    return img


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for i in range(1, 6):
        input_path = os.path.join(INPUT_DIR, f'ant{i}.png')
        output_path = os.path.join(OUTPUT_DIR, f'ant{i}.png')
        if not os.path.exists(input_path):
            print(f"跳过 ant{i}.png: 文件不存在")
            continue
        print(f"\n处理 ant{i}.png:")
        process_ant(input_path, output_path)

    print("\n=== 验证输出 ===")
    for i in range(1, 6):
        output_path = os.path.join(OUTPUT_DIR, f'ant{i}.png')
        if os.path.exists(output_path):
            img = Image.open(output_path)
            size_kb = os.path.getsize(output_path) / 1024
            print(f"ant{i}.png: {img.size} {img.mode} {size_kb:.0f}KB")


if __name__ == '__main__':
    main()
