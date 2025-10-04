# Instagram 视频批量下载器（二次开发版）

> 二次开发自 [insGenerate](https://github.com/kakaoxy/insGenerate) ，特别感谢 @kakaoxy 的开源贡献！

## 项目简介

本项目基于原仓库进行了二次开发，实现了在 **无浏览器 GUI 环境下**，通过模拟用户点击 **SnapInsta** 下载按钮来批量下载 Instagram 视频的功能。

主要功能包括：

- 批量下载 Instagram 视频和图片
- 使用 Playwright 模拟点击下载按钮，无需手动操作
- 自定义下载目录，并支持 Docker 容器化运行
- 支持视频合并功能，方便制作合集

## 改动说明

相比原仓库，本项目主要做了以下改动：

1. **Docker 支持更便捷**
    - 提供 `Dockerfile`，用户可以快速构建镜像并运行
    - 支持目录映射（`-v /宿主机路径/downloads:/app/downloads`），方便管理下载文件

2. **修复 SnapInsta 页面元素变动问题**
    - 原仓库在新版 SnapInsta 页面中，输入 URL 和点击下载按钮无法正常工作，本项目修复了该问题，确保能正确识别下载按钮和链接

3. **修复视频下载问题**
    - 改进下载逻辑，通过按钮文本区分 “Download Photo” 与 “Download Video”，确保视频和图片都能正确下载

4. **新增 `downloads` 文件夹**
    - 默认下载路径为 `./downloads`，在 Docker 中可直接映射到宿主机目录
    - 用户可在界面中自定义子目录，方便分类管理下载内容

## 快速开始

### 1. 本地运行

```bash
git clone <本仓库地址>
cd <仓库目录>
pip install -r requirements.txt
python web_ui.py
```
### 2.Docker构建并运行

```bash
docker build -t instagram-tool:latest .
docker run -it -p 8080:8080 -v /宿主机路径/downloads:/app/downloads instagram-tool:latest
```
> 注：/宿主机路径/downloads 替换成你本地希望保存视频的路径
> 
> Docker 方式运行时，环境变量 HEADLESS 和 SERVER_NAME 保持默认值，不要修改，确保浏览器和服务器设置正常

访问 http://localhost:8080 即可使用界面。

### 3.从 Docker Hub 拉取并运行（无需本地构建）

1. 拉取镜像
```bash
docker pull yourusername/instagram-downloader:latest
```

2. 运行容器并映射下载目录
```bash
docker run -it -p 8080:8080 -v /宿主机路径/downloads:/app/downloads yourusername/insta-downloader:latest
```

## 使用示例

#### 下载视频

1. 在文本框中粘贴 Instagram 视频链接，每行一个
2. 设置下载子目录（可选）
3. 点击**开始下载**
4. 下载完成后，可在 downloads/<子目录> 中找到文件

#### 合并视频

1. 选择包含视频的文件夹
2. 刷新视频列表
3. 选择要设为第一个的视频（可选）
4. 设置输出文件路径和视频标题/作者
5. 选择颜色方案
6. 点击**开始合并**

### 文件说明
```bash
├─ web_ui.py              # 主程序入口
├─ video_down_play.py     # 下载逻辑
├─ video_merger.py        # 视频合并逻辑
├─ requirements.txt       # Python依赖
├─ Dockerfile             # Docker镜像构建文件
├─ downloads/             # 默认下载目录，可映射到宿主机

```
