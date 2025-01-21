from moviepy.editor import VideoFileClip, concatenate_videoclips, ImageClip, AudioFileClip
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import os
from datetime import datetime
import gc
import csv
import logging
import sys
import platform
import subprocess  # 添加这行导入
from contextlib import contextmanager
import traceback

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('video_merger.log', encoding='utf-8')
    ]
)

# 设置第三方库的日志级别
logging.getLogger('PIL').setLevel(logging.WARNING)
logging.getLogger('moviepy').setLevel(logging.WARNING)

# 颜色方案配置
COLOR_SCHEMES = {
    'p1': {  # 经典黑白
        'background': '#FFFFFF',
        'text': '#333333',
        'name': '经典黑白'
    },
    'p2': {  # 柔和灰白
        'background': '#F5F5F5',
        'text': '#2C3E50',
        'name': '柔和灰白'
    },
    'p3': {  # 暖色调
        'background': '#FFF8F0',
        'text': '#8B4513',
        'name': '暖色调'
    },
    'p4': {  # 冷色调
        'background': '#F0F8FF',
        'text': '#1B4F72',
        'name': '冷色调'
    },
    'p5': {  # 现代灰白
        'background': '#333333',
        'text': '#FFFFFF',
        'name': '现代灰白'
    },
    'p6': {  # 经典白黑
        'background': '#000000',
        'text': '#FFFFFF',
        'name': '经典白黑'
    }
}

@contextmanager
def managed_resource(resource, resource_type="resource"):
    """资源管理器，确保资源被正确释放"""
    try:
        yield resource
    finally:
        if resource is not None:
            try:
                if isinstance(resource, (VideoFileClip, ImageClip, AudioFileClip)):
                    resource.close()
                elif isinstance(resource, Image.Image):
                    try:
                        resource.close()
                    except Exception as e:
                        if "Operation on closed image" not in str(e) and "'Image' object has no attribute 'fp'" not in str(e):
                            logging.debug(f"Error closing image: {str(e)}")
                elif hasattr(resource, 'close'):
                    resource.close()
                elif hasattr(resource, 'release'):
                    resource.release()
            except Exception as e:
                logging.debug(f"Error closing {resource_type}: {str(e)}")

def load_system_font(font_size):
    """跨平台字体加载函数"""
    system = platform.system()
    
    # Windows字体路径
    if system == "Windows":
        font_paths = [
            "C:\\Windows\\Fonts\\msyh.ttc",  # 微软雅黑
            "C:\\Windows\\Fonts\\simhei.ttf"  # 黑体
        ]
    # macOS字体路径
    elif system == "Darwin":
        font_paths = [
            "/System/Library/Fonts/PingFang.ttc",  # 苹方
            "/System/Library/Fonts/Supplemental/STHeiti Medium.ttc",  # 华文黑体
            "/Library/Fonts/Microsoft/msyh.ttf",  # 微软雅黑（需手动安装）
            "msyh.ttf"  # 项目本地字体
        ]
    else:  # Linux
        font_paths = [
            "/usr/share/fonts/truetype/msttcorefonts/msyh.ttf",
            "msyh.ttf"
        ]

    for path in font_paths:
        try:
            return ImageFont.truetype(path, font_size)
        except Exception as e:
            continue
    
    logging.warning("未找到系统字体，使用默认字体")
    return ImageFont.load_default()

def create_number_transition(number, duration=1.0, size=(720, 1280), is_final=False, video_count=None, title_text="今日份快乐", author_name="", color_scheme='p6'):
    """创建带数字的过渡画面（跨平台版）"""
    try:
        scheme = COLOR_SCHEMES.get(color_scheme, COLOR_SCHEMES['p6'])
        bg_color = scheme['background']
        text_color = scheme['text']

        width, height = size
        background = Image.new('RGB', (width, height), bg_color)
        draw = ImageDraw.Draw(background)

        if not is_final:
            # 主字体加载
            font = load_system_font(80)
            
            # 动态计算布局
            text = str(number)
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            ascent, descent = font.getmetrics()

            # 平台垂直位置补偿
            vertical_offset = 30 if platform.system() == "Darwin" else 0
            circle_radius = max(text_width, text_height) * 0.8
            circle_x = width // 2
            circle_y = height // 2 + vertical_offset

            # 绘制圆形
            draw.ellipse(
                [circle_x - circle_radius, circle_y - circle_radius,
                 circle_x + circle_radius, circle_y + circle_radius],
                outline=text_color,
                width=5
            )

            # 文字位置计算
            text_offset = (ascent - descent) // 2
            text_x = circle_x - text_width // 2
            text_y = circle_y - text_height // 2 - text_offset + (15 if platform.system() == "Darwin" else 0)

            draw.text((text_x, text_y), text, font=font, fill=text_color)

            # 作者信息
            if number == 1 and author_name:
                author_font = load_system_font(40)
                author_text = f"@{author_name}"
                author_bbox = draw.textbbox((0, 0), author_text, font=author_font)
                author_x = (width - (author_bbox[2] - author_bbox[0])) // 2
                author_y = circle_y + circle_radius + (340 if platform.system() == "Darwin" else 320)
                draw.text((author_x, author_y), author_text, font=author_font, fill=text_color)

            # 标题框
            if number == 1:
                title_font = load_system_font(60)
                today = datetime.now().strftime("%m-%d")

                # 动态计算标题框尺寸
                title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
                date_bbox = draw.textbbox((0, 0), today, font=title_font)
                
                padding = 20
                box_width = max(title_bbox[2], date_bbox[2]) + padding*2
                box_height = (title_bbox[3] + date_bbox[3] + padding*3)
                
                # 平台垂直偏移
                box_y_offset = -300 if platform.system() == "Darwin" else -320
                box_y = circle_y - circle_radius + box_y_offset

                # 绘制标题框
                draw.rectangle(
                    [(width//2 - box_width//2, box_y),
                     (width//2 + box_width//2, box_y + box_height)],
                    outline=text_color,
                    width=3
                )

                # 绘制文字
                date_x = (width - date_bbox[2]) // 2
                date_y = box_y + padding
                draw.text((date_x, date_y), today, font=title_font, fill=text_color)

                title_x = (width - title_bbox[2]) // 2
                title_y = date_y + title_bbox[3] + padding
                draw.text((title_x, title_y), title_text, font=title_font, fill=text_color)

        else:
            # 最终画面
            font = load_system_font(80)
            texts = ["★ 点赞支持 ★", "☆ 关注收藏 ☆", "◆ 转发分享 ◆"]
            
            total_height = sum(draw.textbbox((0,0), t, font=font)[3] for t in texts)
            start_y = (height - total_height - 100) // 2  # 100为总行间距
            
            for text in texts:
                bbox = draw.textbbox((0,0), text, font=font)
                text_x = (width - bbox[2]) // 2
                draw.text((text_x, start_y), text, fill=text_color, font=font)
                start_y += bbox[3] + 50

        image_path = f'transition_{number}.png'
        background.save(image_path)
        
        # 修改音效处理逻辑
        clip = ImageClip(image_path).set_duration(duration)
        try:
            if not is_final:
                # 普通过渡画面使用 ding 音效
                audio = AudioFileClip("ding.wav")
                # 只使用音效的前0.5秒
                audio = audio.subclip(0, min(0.5, audio.duration))
                # 将音效设置在画面开始时播放
                audio = audio.set_start(0)
                clip = clip.set_audio(audio)
            else:
                # 最终画面使用不同的音效
                try:
                    audio = AudioFileClip("end.wav")
                    audio = audio.subclip(0, min(1.0, audio.duration))
                    audio = audio.set_start(0)
                    clip = clip.set_audio(audio)
                except:
                    pass
        except:
            logging.warning("未找到音效文件")
        
        return clip

    except Exception as e:
        logging.error(f"创建过渡画面时出错: {str(e)}")
        return None


def merge_videos(input_dir=None, output_path=None, title="今日份快乐", author="", color_scheme='p6'):
    """合并视频文件，添加过渡画面"""
    try:
        # 1. 输入准备阶段
        input_dir = os.path.abspath(input_dir if input_dir else "./11-23")
        if not os.path.exists(input_dir):
            logging.error(f"输入目录不存在: {input_dir}")
            return False

        # 处理输出路径
        if not output_path:
            output_path = os.path.join(input_dir, f"{datetime.now().strftime('%m-%d')}_merged.mp4")
        output_path = os.path.abspath(output_path)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # 扫描并过滤视频文件
        video_files = []
        for file in os.listdir(input_dir):
            if file.endswith(('.mp4', '.MP4', '.mov', '.MOV')):
                if not (file.startswith('merged-') or file.startswith('temp_')):
                    video_files.append(file)

        if not video_files:
            logging.error(f"未找到视频文件: {input_dir}")
            return False

        video_files.sort()
        
        # 创建临时目录
        temp_dir = os.path.join(input_dir, "temp_transitions")
        os.makedirs(temp_dir, exist_ok=True)

        try:
            processed_clips = []  # 存储处理后的视频片段路径

            # 2. 处理每个视频片段
            for i, video_file in enumerate(video_files):
                # 生成过渡画面
                transition = create_number_transition(
                    i + 1,
                    duration=0.5,  # 过渡画面固定0.5秒
                    title_text=title if i == 0 else None,
                    author_name=author if i == 0 else None,
                    color_scheme=color_scheme
                )

                # 加载原始视频
                video_path = os.path.join(input_dir, video_file)
                video = VideoFileClip(video_path)

                # 合并过渡画面和视频
                segment_path = os.path.join(temp_dir, f'segment_{i+1}.mp4')
                combined = concatenate_videoclips([transition, video])
                combined.write_videofile(
                    segment_path,
                    codec='libx264',
                    audio_codec='aac',
                    fps=30
                )

                # 清理资源
                transition.close()
                video.close()
                combined.close()

                processed_clips.append(segment_path)

            # 3. 添加最终点赞画面
            final_transition = create_number_transition(
                len(video_files) + 1,
                duration=2.0,
                is_final=True,
                color_scheme=color_scheme
            )
            final_path = os.path.join(temp_dir, 'final.mp4')
            final_transition.write_videofile(
                final_path,
                codec='libx264',
                audio_codec='aac',
                fps=30
            )
            final_transition.close()
            processed_clips.append(final_path)

            # 4. 使用ffmpeg合并所有处理好的片段
            list_file = os.path.join(temp_dir, "list.txt")
            with open(list_file, 'w', encoding='utf-8') as f:
                for clip in processed_clips:
                    f.write(f"file '{clip}'\n")

            cmd = [
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-i', list_file,
                '-c', 'copy',
                output_path
            ]

            result = subprocess.run(
                cmd,
                cwd=input_dir,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                raise Exception(f"合并失败: {result.stderr}")

            logging.info("\n=== 合并成功 ===")
            logging.info(f"输出文件: {output_path}")

        finally:
            # 清理所有临时文件
            try:
                import shutil
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                # 清理可能残留的PNG文件
                for i in range(1, len(video_files) + 2):
                    png_file = os.path.join(input_dir, f'transition_{i}.png')
                    if os.path.exists(png_file):
                        os.remove(png_file)
            except Exception as e:
                logging.warning(f"清理临时文件时出错: {str(e)}")

        return True

    except Exception as e:
        logging.error(f"发生错误: {str(e)}")
        raise

def test_transition():
    """测试过渡画面创建功能"""
    try:
        logging.info("开始测试过渡画面创建...")

        # 测试第一个过渡画面（带标题和作者）
        with managed_resource(create_number_transition(1, duration=0.8, author_name="Cynvann"), "过渡画面1") as clip1:
            logging.info("  √ 第一个过渡画面创建成功")

            # 测试普通过渡画面（不带作者）
            with managed_resource(create_number_transition(2, duration=0.3), "过渡画面2") as clip2:
                logging.info("  √ 第二个过渡画面创建成功")

                # 测试最后的过渡画面（点赞关注）
                with managed_resource(create_number_transition(3, duration=1.0, is_final=True), "最终过渡画面") as final_clip:
                    logging.info("  √ 最终过渡画面创建成功")

        logging.info("\n=== 测试完成 ===")
        logging.info("生成的测试文件：")
        logging.info("1. test_transition.mp4 - 第一个过渡画面（带标题和作者）")
        logging.info("2. test_transition2.mp4 - 普通过渡画面")
        logging.info("3. test_final_transition.mp4 - 最终过渡画面（点赞关注）")

    except Exception as e:
        logging.error("\n测试过程中发生错误:")
        logging.error(f"错误类型: {type(e).__name__}")
        logging.error(f"错误信息: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='视频合并工具')
    parser.add_argument('--input_dir', '-i', type=str, help='输入视频文件夹路径')
    parser.add_argument('--output_path', '-o', type=str, help='输出视频文件名（将保存在输入目录中）')
    parser.add_argument('--title', '-t', type=str, default="今日份快乐", help='视频标题')
    parser.add_argument('--author', '-a', type=str, default="Cynvann", help='作者名称')
    parser.add_argument('--color_scheme', '-c', type=str, choices=['p1', 'p2', 'p3', 'p4', 'p5', 'p6'], 
                      default='p6', help='颜色方案选择：\n' + '\n'.join([f"{k}: {v['name']}" for k, v in COLOR_SCHEMES.items()]))
    parser.add_argument('--test', action='store_true', help='运行测试模式')
    
    args = parser.parse_args()
    
    if args.test:
        test_transition()
    else:
        try:
            # 打印参数信息
            print("\n🎬 开始处理视频...")
            print(f"输入目录: {args.input_dir or '默认目录'}")
            print(f"输出文件: {args.output_path or '默认输出.mp4'}")
            print(f"标题: {args.title}")
            print(f"作者: {args.author}")
            print(f"颜色方案: {COLOR_SCHEMES[args.color_scheme]['name']}")
            
            # 获取输入目录的绝对路径
            input_dir = args.input_dir
            if input_dir is None:
                input_dir = os.path.abspath("./downloads")
                print(f"\n⚠️ 未指定输入目录，使用默认目录: {input_dir}")
            else:
                input_dir = os.path.abspath(input_dir)
            
            # 确保输入目录存在
            if not os.path.exists(input_dir):
                os.makedirs(input_dir)
                print(f"\n📁 创建输入目录: {input_dir}")
            
            # 获取输出文件名（不包含路径）
            if args.output_path:
                # 只使用文件名部分，忽略任何路径
                output_filename = os.path.basename(args.output_path)
            else:
                # 生成默认输出文件名
                current_time = datetime.now().strftime("%m%d-%H%M")
                output_filename = f"merged-video-{current_time}.mp4"
                print(f"\n⚠️ 未指定输出文件，使用默认文件名: {output_filename}")
            
            # 构建最终输出路径（在输入目录中）
            final_output = os.path.join(input_dir, output_filename)
            print(f"\n📁 最终输出路径: {final_output}")
            
            # 运行合并
            merge_videos(
                input_dir=input_dir,
                output_path=final_output,
                title=args.title,
                author=args.author,
                color_scheme=args.color_scheme
            )
            
            # 检查最终文件
            if os.path.exists(final_output):
                print(f"\n✨ 视频合并完成！输出文件：{final_output}")
            else:
                print("\n❌ 视频合并失败！")
                
        except Exception as e:
            print(f"\n❌ 发生错误: {str(e)}")
            logging.error(traceback.format_exc())