from zenml import pipeline, step
import subprocess
import argparse
import os
import sys

@step
def prepare_data(source_dir: str):
    print(f"✅ [prepare_data] 数据准备阶段，源目录: {source_dir}")
    
    # 检查是否存在 process.py
    process_file = os.path.join(source_dir, "process.py")
    if os.path.exists(process_file):
        print("🔍 发现 process.py，调用自定义数据处理函数")
        try:
            # 动态导入 process.py
            sys.path.insert(0, source_dir)
            import process
            
            # 调用 process_data 函数
            result = process.process_data(source_dir)
            if isinstance(result, tuple) and len(result) == 2:
                dataset_dir, dataset_eval_dir = result
                print(f"📁 训练数据目录: {dataset_dir}")
                print(f"📁 评估数据目录: {dataset_eval_dir}")
                return dataset_dir, dataset_eval_dir
            else:
                raise ValueError("process_data 函数必须返回包含两个元素的元组")
        except Exception as e:
            print(f"❌ 调用 process.py 失败: {e}")
            raise
        finally:
            # 清理 sys.path
            if source_dir in sys.path:
                sys.path.remove(source_dir)
    else:
        print("📂 未发现 process.py，使用默认目录结构")
        # 默认使用 source_dir/train 和 source_dir/eval
        dataset_dir = os.path.join(source_dir, "train")
        dataset_eval_dir = os.path.join(source_dir, "eval")
        
        # 检查目录是否存在
        if not os.path.exists(dataset_dir):
            print(f"⚠️  警告: 训练数据目录不存在: {dataset_dir}")
        if not os.path.exists(dataset_eval_dir):
            print(f"⚠️  警告: 评估数据目录不存在: {dataset_eval_dir}")
            
        print(f"📁 训练数据目录: {dataset_dir}")
        print(f"📁 评估数据目录: {dataset_eval_dir}")
        return dataset_dir, dataset_eval_dir

@step
def train_model(dataset_dirs: tuple, training_script: str, training_env: str = None):
    dataset_dir, dataset_eval_dir = dataset_dirs
    print(f"🚀 [train_model] 训练数据目录: {dataset_dir}")
    print(f"🚀 [train_model] 评估数据目录: {dataset_eval_dir}")
    print(f"🚀 [train_model] 训练脚本: {training_script}")
    
    # 准备环境变量
    env = os.environ.copy()
    
    # 检查环境变量是否已存在，如果不存在则设置
    if "DATASET_DIR" not in env:
        env["DATASET_DIR"] = dataset_dir
        print(f"🔧 设置环境变量 DATASET_DIR: {dataset_dir}")
    else:
        print(f"🔧 使用现有环境变量 DATASET_DIR: {env['DATASET_DIR']}")
        
    if "DATASET_EVAL_DIR" not in env:
        env["DATASET_EVAL_DIR"] = dataset_eval_dir
        print(f"🔧 设置环境变量 DATASET_EVAL_DIR: {dataset_eval_dir}")
    else:
        print(f"🔧 使用现有环境变量 DATASET_EVAL_DIR: {env['DATASET_EVAL_DIR']}")
    
    # 构建训练命令
    if training_env:
        print(f"🔧 使用训练环境: {training_env}")
        # 如果指定了 training_env，传递 --training_env 参数给训练脚本
        cmd = ["bash", training_script, "--training_env", training_env]
    else:
        cmd = ["bash", training_script]
    
    print(f"🚀 执行命令: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    
    print("📋 训练输出:")
    print(result.stdout)
    if result.returncode != 0:
        print("❌ 训练错误:")
        print(result.stderr)
        raise RuntimeError("训练失败")
    
    # 假设训练脚本输出 output_dir 到 stdout 的最后一行，或者使用默认路径
    output_lines = result.stdout.strip().split('\n')
    if output_lines and output_lines[-1].strip():
        # 尝试从最后一行获取输出目录
        potential_output = output_lines[-1].strip()
        if os.path.exists(potential_output):
            output_dir = potential_output
        else:
            # 使用默认输出目录
            output_dir = os.path.join(os.getcwd(), "output")
    else:
        # 使用默认输出目录
        output_dir = os.path.join(os.getcwd(), "output")
    
    print(f"📁 训练输出目录: {output_dir}")
    return output_dir

@step
def evaluate_model(output_dir: str):
    print(f"🧩 [evaluate_model] 模型输出目录: {output_dir}")
    print("📊 模型评估阶段（待实现）")
    
    # 检查输出目录是否存在
    if not os.path.exists(output_dir):
        print(f"⚠️  警告: 输出目录不存在: {output_dir}")
        return "evaluation_failed"
    
    # 这里可以添加具体的评估逻辑
    # 例如：加载模型、运行评估脚本等
    print(f"📁 评估模型，输出目录: {output_dir}")
    
    return "evaluation_done"

@pipeline(enable_cache=False)
def training_pipeline(source_dir: str, training_script: str, training_env: str = None):
    dataset_dirs = prepare_data(source_dir)
    output_dir = train_model(dataset_dirs, training_script, training_env)
    evaluate_model(output_dir)

if __name__ == "__main__":
    print("🌀 启动 ZenML Pipeline ...")
    parser = argparse.ArgumentParser(description="ZenML 训练管道")
    parser.add_argument("--source_dir", type=str, required=True, 
                       help="数据源目录路径")
    parser.add_argument("--training_script", type=str, default="run_training.sh",
                       help="训练脚本路径 (默认: run_training.sh)")
    parser.add_argument("--training_env", type=str, default=None,
                       help="训练环境脚本路径 (可选)")
    args = parser.parse_args()
    
    print(f"📂 数据源目录: {args.source_dir}")
    print(f"🚀 训练脚本: {args.training_script}")
    if args.training_env:
        print(f"🔧 训练环境: {args.training_env}")
    
    training_pipeline(args.source_dir, args.training_script, args.training_env)
