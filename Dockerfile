# 使用 Playwright 官方 Python 镜像（已带浏览器和依赖）
FROM mcr.microsoft.com/playwright/python:v1.42.0-jammy

# 设置工作目录
WORKDIR /app

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 复制整个项目
COPY . .

# 暴露端口
EXPOSE 8080

# 设置环境变量（防止生成 pyc 文件 + 日志立即输出）
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV SERVER_NAME=0.0.0.0
ENV HEADLESS=true

# 启动命令：运行 Web 界面
CMD ["python", "web_ui.py"]
