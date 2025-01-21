from PIL import Image, ImageDraw, ImageFont
import sys

# 参数设置（保持不变）
IMG_WIDTH = 375
IMG_HEIGHT = 445
BG_COLOR = (245, 245, 245)
BOX_COLOR = (150, 150, 150)
TEXT_COLOR = (50, 50, 50)

# 创建画布
img = Image.new('RGB', (IMG_WIDTH, IMG_HEIGHT), color=BG_COLOR)
draw = ImageDraw.Draw(img)

# 绘制方框
box_margin = 20
draw.rectangle(
    [(box_margin, 50), (IMG_WIDTH - box_margin, IMG_HEIGHT - 80)],
    outline=BOX_COLOR, 
    width=2
)

# 字体设置（关键修改）
try:
    # 尝试新版苹方字体路径
    font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 32)
except Exception as e:
    try:
        # 尝试新版华文黑体路径
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/STHeiti Medium.ttc", 32)
    except:
        print("字体加载失败，请执行以下命令确认字体是否存在：")
        print("ls /System/Library/Fonts/PingFang.ttc")
        print("ls /System/Library/Fonts/Supplemental/STHeiti*")
        sys.exit(1)

# 文字绘制（保持不变）
texts = [
    ("01-21", (box_margin + 15, 70)),
    ("今日份快乐", (box_margin + 15, 130)),
    ("@Cynvann", (box_margin + 15, 190))
]
for text, position in texts:
    draw.text(position, text, fill=TEXT_COLOR, font=font)

img.save('output_mac.jpg')
print("图片生成成功！")