#!/usr/bin/env python3
"""
ZenML 数据预处理脚本
此脚本在 apptainer 容器内运行，用于调用 process.py 中的 process_data 函数
"""

import os
import sys
import argparse

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="ZenML 数据预处理")
    parser.add_argument("data_path", help="容器内数据路径 (通常是 /data)")
    args = parser.parse_args()
    
    data_path = args.data_path
    print(f"🔧 [zenml_preprocess] 开始处理数据，路径: {data_path}")
    
    # 将数据路径添加到 Python 路径
    if data_path not in sys.path:
        sys.path.insert(0, data_path)
        print(f"📂 添加路径到 Python 路径: {data_path}")
    
    try:
        # 检查 process.py 是否存在
        process_file = os.path.join(data_path, "process.py")
        if not os.path.exists(process_file):
            print(f"❌ 错误: process.py 不存在于 {process_file}")
            sys.exit(1)
        
        print(f"🔍 发现 process.py: {process_file}")
        
        # 导入 process 模块
        import process
        print("✅ 成功导入 process 模块")
        
        # 调用 process_data 函数
        print("🚀 调用 process.process_data() 函数...")
        result = process.process_data(data_path)
        
        # 验证返回值
        if not isinstance(result, tuple) or len(result) != 2:
            print(f"❌ 错误: process_data 函数必须返回包含两个元素的元组，实际返回: {result}")
            sys.exit(1)
        
        dataset_dir, dataset_eval_dir = result
        
        # 验证目录是否存在
        if not os.path.exists(dataset_dir):
            print(f"⚠️  警告: 训练数据目录不存在: {dataset_dir}")
        else:
            print(f"✅ 训练数据目录存在: {dataset_dir}")
            
        if not os.path.exists(dataset_eval_dir):
            print(f"⚠️  警告: 评估数据目录不存在: {dataset_eval_dir}")
        else:
            print(f"✅ 评估数据目录存在: {dataset_eval_dir}")
        
        # 打印目录路径（供外部脚本提取）
        print("📁 处理完成，输出目录路径:")
        print(f"📁 训练数据目录: {dataset_dir}")
        print(f"📁 评估数据目录: {dataset_eval_dir}")
        
        # 输出纯路径（最后两行，供 prepare_data 函数提取）
        print(dataset_dir)
        print(dataset_eval_dir)
        
        print("✅ 数据预处理完成")
        
    except ImportError as e:
        print(f"❌ 导入 process 模块失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 处理数据时发生错误: {e}")
        sys.exit(1)
    finally:
        # 清理 sys.path
        if data_path in sys.path:
            sys.path.remove(data_path)

if __name__ == "__main__":
    main()
