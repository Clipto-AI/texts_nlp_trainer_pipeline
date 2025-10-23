#!/bin/bash

# 检查参数
if [ $# -ne 1 ]; then
    echo "用法: $0 <source_dir>"
    echo "示例: $0 /path/to/data"
    exit 1
fi

SOURCE_DIR="$1"

# 检查 source_dir 是否存在
if [ ! -d "$SOURCE_DIR" ]; then
    echo "错误: 源目录不存在: $SOURCE_DIR"
    exit 1
fi

# 检查 apptainer 镜像是否存在
SIF_PATH="env/apptainer.sif"
if [ ! -f "$SIF_PATH" ]; then
    echo "错误: Apptainer 镜像不存在: $SIF_PATH"
    exit 1
fi

echo "🔧 使用 Apptainer 处理数据..."
echo "📂 源目录: $SOURCE_DIR"
echo "🐳 镜像路径: $SIF_PATH"

# 使用 apptainer 运行镜像，将 source_dir 挂载到容器中
# 调用 zenml_preprocess.py 脚本处理数据，并捕获输出
echo "🚀 执行 apptainer 命令..."
apptainer run --bind "$SOURCE_DIR:/data" "$SIF_PATH" python zenml_preprocess.py /data

# 检查返回码
if [ $? -eq 0 ]; then
    echo "✅ 数据处理完成"
else
    echo "❌ 数据处理失败"
    exit 1
fi