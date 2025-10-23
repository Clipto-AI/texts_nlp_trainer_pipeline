from zenml import pipeline, step
import subprocess
import argparse

@step
def prepare_data():
    print("✅ [prepare_data] 数据准备阶段")
    return "data_ready"

@step
def train_model(data_status: str, training_script: str):
    print(f"🚀 [train_model] 数据状态: {data_status}")
    print(f"🚀 [train_model] 训练脚本: {training_script}")
    result = subprocess.run(["bash", training_script], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        raise RuntimeError("训练失败")
    return "training_done"

@step
def evaluate_model(train_status: str):
    print(f"🧩 [evaluate_model] 状态: {train_status}")
    print("📊 模型评估阶段（待实现）")
    return "evaluation_done"

@pipeline(enable_cache=False)
def training_pipeline(training_script: str):
    data_status = prepare_data()
    train_status = train_model(data_status, training_script)
    evaluate_model(train_status)

if __name__ == "__main__":
    print("🌀 启动 ZenML Pipeline ...")
    parser = argparse.ArgumentParser()
    parser.add_argument("--training_script", type=str, default="run_training.sh")
    args = parser.parse_args()
    training_pipeline(args.training_script)
