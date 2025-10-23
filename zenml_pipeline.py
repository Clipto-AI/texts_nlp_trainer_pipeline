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
        print("🔍 发现 process.py，调用 preprocess_data.sh 脚本")
        try:
            # 获取当前脚本所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            preprocess_script = os.path.join(current_dir, "preprocess_data.sh")
            
            # 检查 preprocess_data.sh 是否存在
            if not os.path.exists(preprocess_script):
                raise FileNotFoundError(f"preprocess_data.sh 脚本不存在: {preprocess_script}")
            
            # 确保脚本有执行权限
            os.chmod(preprocess_script, 0o755)
            
            # 调用 preprocess_data.sh 脚本
            cmd = ["bash", preprocess_script, source_dir]
            print(f"🚀 执行命令: {' '.join(cmd)}")
            
            # 使用 Popen 来实时显示输出，同时捕获输出
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                     text=True, bufsize=1, universal_newlines=True)
            
            output_lines = []
            print("📋 数据处理输出:")
            print("-" * 50)
            
            # 实时读取并显示输出
            for line in iter(process.stdout.readline, ''):
                if line:
                    print(line.rstrip())  # 实时显示输出
                    output_lines.append(line.rstrip())  # 保存到列表
            
            # 等待进程完成
            return_code = process.wait()
            
            print("-" * 50)
            
            if return_code != 0:
                print(f"❌ 数据处理失败，返回码: {return_code}")
                raise RuntimeError("数据处理失败")
            
            # 从输出中提取目录路径
            # 查找 "✅ 数据预处理完成" 这一行，然后取前两行作为目录路径
            dataset_dir = None
            dataset_eval_dir = None
            
            # 从后往前查找 "✅ 数据预处理完成" 这一行
            completion_line_index = -1
            for i in range(len(output_lines) - 1, -1, -1):
                if "✅ 数据预处理完成" in output_lines[i]:
                    completion_line_index = i
                    break
            
            if completion_line_index >= 2:
                # 取前两行作为目录路径
                dataset_eval_dir = output_lines[completion_line_index - 1].strip()
                dataset_dir = output_lines[completion_line_index - 2].strip()
                dataset_eval_dir = dataset_eval_dir.replace("/data", source_dir)
                dataset_dir = dataset_dir.replace("/data", source_dir)
            
            # 如果无法从输出中提取路径，使用默认路径
            if dataset_dir is None or dataset_eval_dir is None:
                print("⚠️  无法从输出中提取目录路径，使用默认路径")
                dataset_dir = os.path.join(source_dir, "processed_train")
                dataset_eval_dir = os.path.join(source_dir, "processed_eval")
                
            print(f"📁 训练数据目录: {dataset_dir}")
            print(f"📁 评估数据目录: {dataset_eval_dir}")
            return dataset_dir, dataset_eval_dir
            
        except Exception as e:
            print(f"❌ 调用 preprocess_data.sh 失败: {e}")
            raise
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
    
    # 使用 Popen 来实时显示输出，同时捕获最后一行
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                             text=True, env=env, bufsize=1, universal_newlines=True)
    
    output_lines = []
    print("📋 训练输出:")
    print("-" * 50)
    
    # 实时读取并显示输出
    for line in iter(process.stdout.readline, ''):
        if line:
            print(line.rstrip())  # 实时显示输出
            output_lines.append(line.rstrip())  # 保存到列表
    
    # 等待进程完成
    return_code = process.wait()
    
    print("-" * 50)
    
    if return_code != 0:
        print("❌ 训练失败，返回码:", return_code)
        raise RuntimeError("训练失败")
    
    # 从输出中提取最后一行作为输出目录
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
