#!/usr/bin/env bash
set -euo pipefail

# ============ 检查 .env 文件是否存在 ============
if [ ! -f training_env ]; then
  echo "❌ 错误: 找不到 training_env 文件，请在当前目录下创建一个 training_env 文件。"
  echo "   示例："
  echo "   WANDB_API_KEY=xxxx"
  echo "   MODEL_NAME=/path/to/model"
  echo "   DATASET_DIR=/path/to/data"
  exit 1
fi

# ============ 从 .env 加载所有环境变量 ============
echo "📦 正在加载 training_env 文件 ..."
export $(grep -v '^#' training_env | xargs)

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
