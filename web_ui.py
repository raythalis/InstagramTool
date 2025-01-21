import os
import tempfile
import json
import importlib  # 添加这一行
from typing import Optional, List
import gradio as gr
import video_down_play  # 修改这一行
from video_merger import merge_videos, COLOR_SCHEMES

def download_only(links: str, output_folder: str) -> str:
    """仅下载视频"""
    try:
        # 重新加载模块以获取最新代码
        importlib.reload(video_down_play)
        
        # 确保输出文件夹存在
        os.makedirs(output_folder, exist_ok=True)
        
        # 从文本中提取链接
        links_list = video_down_play.extract_video_links(links)  # 修改这一行
        if not links_list:
            return "未找到有效的视频链接，请确保链接格式正确。"
        
        print(f"找到 {len(links_list)} 个有效链接：")
        for link in links_list:
            print(f"- {link}")
        
        # 使用新的下载方法
        return video_down_play.download_videos_with_playwright(links_list, output_folder)  # 修改这一行
        
    except Exception as e:
        return f"下载过程中出错: {str(e)}"

def merge_only(input_folder: str, output_path: str, title: str, author: str) -> str:
    """仅合并视频"""
    try:
        merge_videos(input_folder, output_path, title, author)
        return f"合并完成！视频已保存到: {output_path}"
    except Exception as e:
        return f"合并过程中出错: {str(e)}"

def download_and_merge(links: str, output_folder: str, output_path: str, title: str, author: str) -> str:
    """下载并合并视频"""
    try:
        # 先下载
        download_result = download_only(links, output_folder)
        if "错误" in download_result:
            return download_result
        
        # 再合并
        merge_result = merge_only(output_folder, output_path, title, author)
        return merge_result
    except Exception as e:
        return f"处理过程中出错: {str(e)}"

def create_ui():
    """创建用户界面"""
    
    def list_videos(folder_path: str) -> tuple:
        """列出文件夹中的视频文件并返回视频列表和预览组件"""
        if not os.path.exists(folder_path):
            return [], None, "文件夹不存在"
        
        video_files = [f for f in os.listdir(folder_path) if f.endswith(('.mp4', '.MP4'))]
        if not video_files:
            return [], None, "文件夹中没有找到视频文件"
            
        # 构建视频列表的HTML
        videos_data = []
        for idx, video in enumerate(video_files):
            video_path = os.path.join(folder_path, video)
            videos_data.append({
                "path": video_path,
                "name": video,
                "is_first": False
            })
            
        return videos_data, os.path.join(folder_path, video_files[0]), "找到 {} 个视频文件".format(len(video_files))
    
    def set_first_video(videos_data: List[dict], video_idx: int) -> List[dict]:
        """设置指定索引的视频为第一个"""
        if not videos_data or video_idx >= len(videos_data):
            return videos_data
        
        # 重置所有视频的is_first状态
        for video in videos_data:
            video["is_first"] = False
            
        # 设置选中的视频为第一个
        videos_data[video_idx]["is_first"] = True
        return videos_data
    
    def get_final_video_order(videos_data: List[dict]) -> List[str]:
        """根据is_first标记获取最终的视频顺序"""
        if not videos_data:
            return []
            
        # 找到标记为第一个的视频
        first_video = next((v for v in videos_data if v["is_first"]), None)
        other_videos = [v for v in videos_data if not v["is_first"]]
        
        # 如果有设置第一个视频，将其放在最前面
        if first_video:
            return [first_video["path"]] + [v["path"] for v in other_videos]
        else:
            return [v["path"] for v in videos_data]
    
    with gr.Blocks(title="Instagram视频批量下载器 欢迎关注视频号@Cynvann") as app:
        gr.Markdown("# 📱 Instagram视频批量下载器 欢迎关注视频号@Cynvann")
        
        with gr.Tabs():
            # 下载标签页
            with gr.Tab("📥 下载视频"):
                with gr.Column():
                    links_input = gr.Textbox(
                        label="Instagram视频链接",
                        placeholder="粘贴Instagram视频链接，每行一个...",
                        lines=5
                    )
                    # 使用当前日期作为默认下载目录
                    from datetime import datetime
                    default_folder = datetime.now().strftime("%m-%d")
                    download_output_folder = gr.Textbox(
                        label="下载保存路径",
                        placeholder="视频保存的文件夹路径",
                        value=default_folder
                    )
                    download_btn = gr.Button("开始下载", variant="primary")
                    download_output = gr.Textbox(label="下载结果")
                    
                    download_btn.click(
                        fn=download_only,
                        inputs=[links_input, download_output_folder],
                        outputs=download_output
                    )
            
            # 合并标签页
            with gr.Tab("🔄 合并视频"):
                with gr.Column():
                    input_folder = gr.Textbox(
                        label="视频文件夹",
                        placeholder="包含要合并的视频的文件夹路径",
                        value="downloads"
                    )
                    
                    refresh_btn = gr.Button("刷新视频列表")
                    status_text = gr.Textbox(label="状态", interactive=False)
                    
                    # 视频预览和选择区域
                    videos_state = gr.State([])  # 存储视频列表数据
                    gallery = gr.Gallery(
                        label="视频列表（点击选择要设为第一个的视频）",
                        columns=3,
                        rows=2,
                        height=400,
                        object_fit="contain",
                        show_label=True,
                        elem_id="video-gallery"
                    )
                    selected_video = gr.State(None)  # 存储当前选中的视频
                    set_first_btn = gr.Button("设为第一个视频", variant="primary")
                    
                    def update_video_list(folder):
                        videos_data, _, status = list_videos(folder)
                        if not videos_data:
                            return videos_data, [], None, status
                            
                        # 为每个视频创建预览信息
                        gallery_data = []
                        for video in videos_data:
                            label = "[第一个] " if video["is_first"] else ""
                            label += video["name"]
                            gallery_data.append((video["path"], label))
                            
                        return videos_data, gallery_data, None, status
                    
                    def handle_gallery_select(evt: gr.SelectData, videos_data: List[dict]):
                        """处理Gallery的选择事件"""
                        if not videos_data:
                            return None
                        return videos_data[evt.index]["name"]
                    
                    def handle_set_first(videos_data: List[dict], selected_name: str):
                        """设置选中的视频为第一个"""
                        if not videos_data or selected_name is None:
                            gallery_data = [(v["path"], f"{'[第一个] ' if v['is_first'] else ''}{v['name']}") 
                                          for v in videos_data]
                            return videos_data, gallery_data, None
                            
                        # 根据名称找到索引
                        selected_idx = next((i for i, v in enumerate(videos_data) if v['name'] == selected_name), None)
                        if selected_idx is None:
                            gallery_data = [(v["path"], f"{'[第一个] ' if v['is_first'] else ''}{v['name']}") 
                                          for v in videos_data]
                            return videos_data, gallery_data, None
                            
                        # 更新视频顺序
                        updated_videos = set_first_video(videos_data, selected_idx)
                        gallery_data = [(v["path"], f"{'[第一个] ' if v['is_first'] else ''}{v['name']}") 
                                      for v in updated_videos]
                        return updated_videos, gallery_data, None
                    
                    def update_preview(videos_data: List[dict], selected_name: str):
                        """更新视频预览"""
                        if not videos_data or selected_name is None:
                            return None
                        # 根据名称找到对应的视频
                        video = next((v for v in videos_data if v['name'] == selected_name), None)
                        return video['path'] if video else None
                    
                    def handle_merge(videos_data: List[dict], output_path: str, title: str, author: str, color_scheme: str):
                        if not videos_data:
                            return "没有找到要合并的视频"
                        
                        video_paths = get_final_video_order(videos_data)
                        
                        try:
                            # 确保输出路径是绝对路径
                            if not os.path.isabs(output_path):
                                # 如果是相对路径，则相对于第一个视频所在目录
                                input_folder = os.path.dirname(video_paths[0])
                                output_path = os.path.abspath(os.path.join(input_folder, output_path))
                            
                            # 确保输出目录存在
                            output_dir = os.path.dirname(output_path)
                            os.makedirs(output_dir, exist_ok=True)
                            
                            # 将所有视频文件复制到临时目录，按照指定顺序重命名
                            with tempfile.TemporaryDirectory() as temp_dir:
                                # 按顺序复制并重命名视频文件
                                for idx, video_path in enumerate(video_paths):
                                    new_name = f"{idx+1:03d}_{os.path.basename(video_path)}"
                                    new_path = os.path.join(temp_dir, new_name)
                                    try:
                                        os.link(video_path, new_path)
                                    except OSError:
                                        import shutil
                                        shutil.copy2(video_path, new_path)
                                
                                # 使用临时目录进行合并，确保使用绝对路径
                                merge_videos(temp_dir, output_path, title, author, color_scheme)
                                
                                if not os.path.exists(output_path):
                                    return f"合并失败：未找到输出文件 {output_path}"
                                
                                import time
                                time.sleep(1)
                            
                            if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                                return f"合并失败：输出文件无效 {output_path}"
                            
                            return f"合并完成！视频已保存到: {output_path}"
                        except Exception as e:
                            return f"合并过程中出错: {str(e)}"
                    
                    # 事件处理
                    refresh_btn.click(
                        fn=update_video_list,
                        inputs=[input_folder],
                        outputs=[videos_state, gallery, selected_video, status_text]
                    )
                    
                    gallery.select(
                        fn=handle_gallery_select,
                        inputs=[videos_state],
                        outputs=[selected_video]
                    )
                    
                    set_first_btn.click(
                        fn=handle_set_first,
                        inputs=[videos_state, selected_video],
                        outputs=[videos_state, gallery, selected_video]
                    )
                    
                    output_path = gr.Textbox(
                        label="输出文件路径",
                        placeholder="合并后的视频保存路径（包含文件名）",
                        value="merged_video.mp4"
                    )
                    title = gr.Textbox(
                        label="视频标题",
                        placeholder="合并后的视频标题",
                        value="今日份快乐"
                    )
                    author = gr.Textbox(
                        label="作者",
                        placeholder="视频作者",
                        value="Cynvann"
                    )
                    
                    # 添加颜色方案选择下拉框
                    color_scheme = gr.Dropdown(
                        label="颜色方案",
                        choices=[
                            f"p1 - 经典黑白 ({COLOR_SCHEMES['p1']['background']}/{COLOR_SCHEMES['p1']['text']})",
                            f"p2 - 柔和灰白 ({COLOR_SCHEMES['p2']['background']}/{COLOR_SCHEMES['p2']['text']})",
                            f"p3 - 暖色调 ({COLOR_SCHEMES['p3']['background']}/{COLOR_SCHEMES['p3']['text']})",
                            f"p4 - 冷色调 ({COLOR_SCHEMES['p4']['background']}/{COLOR_SCHEMES['p4']['text']})",
                            f"p5 - 现代灰白 ({COLOR_SCHEMES['p5']['background']}/{COLOR_SCHEMES['p5']['text']})",
                            f"p6 - 经典白黑 ({COLOR_SCHEMES['p6']['background']}/{COLOR_SCHEMES['p6']['text']})"
                        ],
                        value=f"p6 - 经典白黑 ({COLOR_SCHEMES['p6']['background']}/{COLOR_SCHEMES['p6']['text']})",
                        type="value"
                    )
                    
                    merge_btn = gr.Button("开始合并", variant="primary")
                    merge_output = gr.Textbox(label="合并结果")
                    
                    # 处理颜色方案选择值
                    def process_merge(*args):
                        videos_data, output_path, title, author, color_scheme = args
                        # 从选择值中提取颜色方案代码
                        scheme_code = color_scheme.split(" - ")[0]
                        return handle_merge(videos_data, output_path, title, author, scheme_code)
                    
                    merge_btn.click(
                        fn=process_merge,
                        inputs=[videos_state, output_path, title, author, color_scheme],
                        outputs=[merge_output]
                    )

    return app

if __name__ == "__main__":
    app = create_ui()
    app.launch(
        server_name="127.0.0.1",  # 本地服务器地址
        server_port=8080,         # 端口号
        share=False,              # 不生成公共链接
        inbrowser=True,           # 自动打开浏览器
        show_api=False,           # 关闭API界面
        auth=None,                # 不设置访问密码
        favicon_path=None,        # 默认网站图标
        quiet=True,               # 减少命令行输出
        # enable_queue=True,        # 启用队列处理请求
    )
