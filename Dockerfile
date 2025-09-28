# 五好伴学 - 生产环境多阶段Dockerfile
# Multi-stage Docker build for production deployment

# ================================
# Stage 1: Builder - 构建阶段
# ================================
FROM python:3.11-slim as builder

LABEL maintainer="wuhao-tutor@example.com"
LABEL description="五好伴学 - 基于AI的初高中学情管理系统"
LABEL version="0.1.0"

# 设置构建参数
ARG BUILD_ENV=production
ARG POETRY_VERSION=1.6.1

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libpq-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv (快速Python包管理器)
RUN pip install uv

# 创建工作目录
WORKDIR /app

# 复制依赖文件
COPY pyproject.toml uv.lock ./

# 创建虚拟环境并安装依赖
RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 安装Python依赖
RUN uv pip install --no-cache-dir -r uv.lock

# ================================
# Stage 2: Runtime - 运行阶段
# ================================
FROM python:3.11-slim as runtime

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    ENVIRONMENT=production

# 安装运行时依赖
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 创建非root用户
RUN groupadd -r wuhao && useradd -r -g wuhao -d /app -s /bin/bash wuhao

# 创建应用目录
WORKDIR /app

# 从构建阶段复制虚拟环境
COPY --from=builder /opt/venv /opt/venv

# 复制应用代码
COPY --chown=wuhao:wuhao . .

# 创建必要的目录
RUN mkdir -p /app/logs /app/uploads /app/tmp && \
    chown -R wuhao:wuhao /app

# 切换到非root用户
USER wuhao

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# ================================
# Stage 3: Development - 开发阶段
# ================================
FROM runtime as development

USER root

# 安装开发工具
RUN apt-get update && apt-get install -y \
    vim \
    htop \
    postgresql-client \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# 安装开发依赖
RUN uv pip install --no-cache-dir \
    pytest \
    pytest-asyncio \
    pytest-cov \
    black \
    isort \
    flake8 \
    mypy

# 设置开发环境变量
ENV ENVIRONMENT=development \
    DEBUG=true \
    LOG_LEVEL=DEBUG

USER wuhao

# 开发环境启动命令（支持热重载）
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
