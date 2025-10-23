#!/usr/bin/env bash
set -euo pipefail

# ============ 解析命令行参数 ============
TRAINING_ENV_FILE="training_env"  # 默认值

# 解析参数
while [[ $# -gt 0 ]]; do
  case $1 in
    --training_env)
      TRAINING_ENV_FILE="$2"
      shift 2
      ;;
    *)
      echo "❌ 未知参数: $1"
      echo "用法: $0 [--training_env <env_file>]"
      exit 1
      ;;
  esac
done

# ============ 检查环境变量文件是否存在 ============
if [ ! -f "$TRAINING_ENV_FILE" ]; then
  echo "❌ 错误: 找不到 $TRAINING_ENV_FILE 文件"
  echo "   示例："
  echo "   WANDB_API_KEY=xxxx"
  echo "   MODEL_NAME=/path/to/model"
  echo "   DATASET_DIR=/path/to/data"
  exit 1
fi

# ============ 保存现有的 DATASET_DIR 和 DATASET_EVAL_DIR ============
SAVED_DATASET_DIR=""
SAVED_DATASET_EVAL_DIR=""

if [ -n "${DATASET_DIR:-}" ]; then
  SAVED_DATASET_DIR="$DATASET_DIR"
  echo "💾 保存现有 DATASET_DIR: $DATASET_DIR"
fi

if [ -n "${DATASET_EVAL_DIR:-}" ]; then
  SAVED_DATASET_EVAL_DIR="$DATASET_EVAL_DIR"
  echo "💾 保存现有 DATASET_EVAL_DIR: $DATASET_EVAL_DIR"
fi

# ============ 从指定文件加载所有环境变量 ============
echo "📦 正在加载 $TRAINING_ENV_FILE 文件 ..."
export $(grep -v '^#' "$TRAINING_ENV_FILE" | xargs)

# ============ 恢复保存的环境变量 ============
if [ -n "$SAVED_DATASET_DIR" ]; then
  export DATASET_DIR="$SAVED_DATASET_DIR"
  echo "🔄 恢复 DATASET_DIR: $DATASET_DIR"
fi

if [ -n "$SAVED_DATASET_EVAL_DIR" ]; then
  export DATASET_EVAL_DIR="$SAVED_DATASET_EVAL_DIR"
  echo "🔄 恢复 DATASET_EVAL_DIR: $DATASET_EVAL_DIR"
fi

# ============ 路径映射处理 ============
echo "🗺️  处理路径映射..."

# 处理 DATASET_DIR 路径映射
if [[ "$DATASET_DIR" == /DATA_A/* ]]; then
  ORIGINAL_DATASET_DIR="$DATASET_DIR"
  DATASET_DIR="${DATASET_DIR//\/DATA_A\//\/data\/}"
  echo "🔄 映射 DATASET_DIR: $ORIGINAL_DATASET_DIR -> $DATASET_DIR"
  export DATASET_DIR
elif [[ "$DATASET_DIR" == /DATA_B/* ]]; then
  ORIGINAL_DATASET_DIR="$DATASET_DIR"
  DATASET_DIR="${DATASET_DIR//\/DATA_B\//\/workspace\/}"
  echo "🔄 映射 DATASET_DIR: $ORIGINAL_DATASET_DIR -> $DATASET_DIR"
  export DATASET_DIR
fi

# 处理 DATASET_EVAL_DIR 路径映射
if [[ "$DATASET_EVAL_DIR" == /DATA_A/* ]]; then
  ORIGINAL_DATASET_EVAL_DIR="$DATASET_EVAL_DIR"
  DATASET_EVAL_DIR="${DATASET_EVAL_DIR//\/DATA_A\//\/data\/}"
  echo "🔄 映射 DATASET_EVAL_DIR: $ORIGINAL_DATASET_EVAL_DIR -> $DATASET_EVAL_DIR"
  export DATASET_EVAL_DIR
elif [[ "$DATASET_EVAL_DIR" == /DATA_B/* ]]; then
  ORIGINAL_DATASET_EVAL_DIR="$DATASET_EVAL_DIR"
  DATASET_EVAL_DIR="${DATASET_EVAL_DIR//\/DATA_B\//\/workspace\/}"
  echo "🔄 映射 DATASET_EVAL_DIR: $ORIGINAL_DATASET_EVAL_DIR -> $DATASET_EVAL_DIR"
  export DATASET_EVAL_DIR
fi

# 处理 OUTPUT_DIR 路径映射
if [[ "$OUTPUT_DIR" == /DATA_A/* ]]; then
  ORIGINAL_OUTPUT_DIR="$OUTPUT_DIR"
  OUTPUT_DIR="${OUTPUT_DIR//\/DATA_A\//\/data\/}"
  echo "🔄 映射 OUTPUT_DIR: $ORIGINAL_OUTPUT_DIR -> $OUTPUT_DIR"
  export OUTPUT_DIR
elif [[ "$OUTPUT_DIR" == /DATA_B/* ]]; then
  ORIGINAL_OUTPUT_DIR="$OUTPUT_DIR"
  OUTPUT_DIR="${OUTPUT_DIR//\/DATA_B\//\/workspace\/}"
  echo "🔄 映射 OUTPUT_DIR: $ORIGINAL_OUTPUT_DIR -> $OUTPUT_DIR"
  export OUTPUT_DIR
fi

# ============ 检查关键变量是否存在 ============
REQUIRED_VARS=(MODEL_NAME DATASET_DIR OUTPUT_DIR)
for var in "${REQUIRED_VARS[@]}"; do
  if [ -z "${!var:-}" ]; then
    echo "❌ 错误: 环境变量 $var 未在 .env 中定义"
    exit 1
  fi
done

# ============ 打印当前配置 ============
echo "✅ 环境变量加载完成："
echo "  WANDB_PROJECT=${WANDB_PROJECT:-undefined}"
echo "  MODEL_NAME=${MODEL_NAME}"
echo "  DATASET_DIR=${DATASET_DIR}"
echo "  OUTPUT_DIR=${OUTPUT_DIR}"
echo "  EPOCHS=${EPOCHS:-10}"
echo "  BATCH_SIZE=${BATCH_SIZE:-2}"
echo "  LEARNING_RATE=${LEARNING_RATE:-3e-4}"

# ============ 启动训练 ============
echo "🚀 开始训练 ..."
apptainer run --bind /DATA_B:/workspace,/DATA_A:/data --nv env/apptainer.sif \
 accelerate launch --config_file default_config.yaml\
  src/train.py \
  --model_name "${MODEL_NAME}" \
  --dataset_dir "${DATASET_DIR}" \
  --epochs "${EPOCHS}" \
  --lora_init_method "${LORA_INIT_METHOD}" \
  --batch_size "${BATCH_SIZE}" \
  --total_max_length "${TOTAL_MAX_LENGTH}" \
  --save_steps "${SAVE_STEPS}" \
  --eval_steps "${EVAL_STEPS}" \
  --output_dir "${OUTPUT_DIR}" \
  --learning_rate "${LEARNING_RATE}" \
  --lora_rank "${LORA_RANK}" \
  --dataset_eval_dir "${DATASET_EVAL_DIR}" \
  --save_total_limit "${SAVE_TOTAL_LIMIT}"

echo "🎉 训练完成！"

# ============ 输出最新的模型目录 ============
echo "📁 查找最新的模型检查点..."
if [ -d "${OUTPUT_DIR}" ]; then
  # 查找 output_dir 下最新的目录（按修改时间排序）
  LATEST_CHECKPOINT=$(find "${OUTPUT_DIR}" -maxdepth 1 -type d -name "checkpoint-*" | sort -V | tail -1)
  
  if [ -n "$LATEST_CHECKPOINT" ]; then
    # 将容器内路径映射回主机路径
    if [[ "$LATEST_CHECKPOINT" == /data/* ]]; then
      HOST_CHECKPOINT="${LATEST_CHECKPOINT//\/data\//\/DATA_A\/}"
    elif [[ "$LATEST_CHECKPOINT" == /workspace/* ]]; then
      HOST_CHECKPOINT="${LATEST_CHECKPOINT//\/workspace\//\/DATA_B\/}"
    else
      HOST_CHECKPOINT="$LATEST_CHECKPOINT"
    fi
    
    echo "✅ 找到最新检查点: $LATEST_CHECKPOINT"
    echo "🔄 映射到主机路径: $HOST_CHECKPOINT"
    echo "$HOST_CHECKPOINT"  # 输出主机路径到 stdout，供 zenml_pipeline.py 捕获
  else
    echo "⚠️  警告: 在 $OUTPUT_DIR 中未找到 checkpoint-* 目录"
    # 映射输出目录到主机路径
    if [[ "$OUTPUT_DIR" == /data/* ]]; then
      HOST_OUTPUT_DIR="${OUTPUT_DIR//\/data\//\/DATA_A\/}"
    elif [[ "$OUTPUT_DIR" == /workspace/* ]]; then
      HOST_OUTPUT_DIR="${OUTPUT_DIR//\/workspace\//\/DATA_B\/}"
    else
      HOST_OUTPUT_DIR="$OUTPUT_DIR"
    fi
    echo "$HOST_OUTPUT_DIR"  # 输出主机路径作为备选
  fi
else
  echo "❌ 错误: 输出目录不存在: $OUTPUT_DIR"
  # 映射输出目录到主机路径
  if [[ "$OUTPUT_DIR" == /data/* ]]; then
    HOST_OUTPUT_DIR="${OUTPUT_DIR//\/data\//\/DATA_A\/}"
  elif [[ "$OUTPUT_DIR" == /workspace/* ]]; then
    HOST_OUTPUT_DIR="${OUTPUT_DIR//\/workspace\//\/DATA_B\/}"
  else
    HOST_OUTPUT_DIR="$OUTPUT_DIR"
  fi
  echo "$HOST_OUTPUT_DIR"  # 输出主机路径作为备选
fi
