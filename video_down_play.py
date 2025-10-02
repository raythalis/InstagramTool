import os
from typing import List
from playwright.sync_api import sync_playwright
import random
import time
from datetime import datetime  # 添加这一行

def extract_video_links(text: str) -> List[str]:
    """从文本中提取视频链接"""
    import re
    # 匹配 http 或 https 开头的链接
    pattern = r'https?://[^\s<>"]+'
    links = re.findall(pattern, text)
    return [link for link in links if link.strip()]

def download_videos_with_playwright(links_list: List[str], output_folder: str) -> str:
    try:
        # 确保输出目录存在
        os.makedirs(output_folder, exist_ok=True)

        with sync_playwright() as p:
            # 初始化浏览器
            browser = p.chromium.launch(
                headless=False,
                args=['--start-maximized']
            )
            context = browser.new_context(
                accept_downloads=True,
                viewport={'width': 1920, 'height': 1080}
            )
            page = context.new_page()

            success_count = 0
            failed_links = []

            for video_url in links_list:
                try:
                    # 访问下载网站
                    page.goto("https://snapinsta.to/", wait_until='networkidle')
                    time.sleep(2)

                    # 输入视频URL
                    page.fill("#s_input", video_url)
                    time.sleep(0.2)

                    # 点击提交按钮
                    download_button = page.locator("button:has-text('Download')")
                    download_button.click()
                    time.sleep(10)

                    # 关闭可能出现的模态框
                    try:
                        modal = page.query_selector("#closeModalBtn")
                        if modal:
                            modal.click()
                    except:
                        pass

                    # 等待所有下载项出现
                    download_items = page.query_selector_all("ul.download-box > li > div.download-items")

                    if not download_items:
                        raise Exception("下载项未找到")

                    for item in download_items:
                        download_button = item.query_selector(".download-items__btn > a")
                        if not download_button:
                            print("下载按钮未找到，跳过该项")
                            continue

                        # 生成带时间戳的文件名
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"snapinsta_{timestamp}.jpg"  # 如果是视频，改成 .mp4
                        save_path = os.path.join(output_folder, filename)

                        # 设置下载处理
                        with page.expect_download(timeout=60000) as download_info:
                            download_button.click()

                        download = download_info.value
                        print(f"正在下载到: {save_path}")
                        download.save_as(save_path)
                        print("下载完成！")

                        success_count += 1

                        # 每次下载后添加随机延迟
                        time.sleep(random.uniform(1, 3))

                except Exception as e:
                    print(f"下载失败 {video_url}: {str(e)}")
                    failed_links.append(video_url)
                    continue

            # 最后才关闭浏览器
            context.close()
            browser.close()

            # 生成结果报告
            result = f"下载完成！成功: {success_count}个媒体/{len(links_list)}条链接\n"
            if failed_links:
                result += "失败的链接:\n" + "\n".join(failed_links)

            return result

    except Exception as e:
        return f"启动浏览器出错: {str(e)}"
