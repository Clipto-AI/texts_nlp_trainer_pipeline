import json
import os
import concurrent.futures
import time
from openai import OpenAI
from tqdm import tqdm

# 尝试导入 PyYAML 库
try:
    import yaml
except ImportError:
    print("错误: PyYAML 库未安装。")
    print("请先通过命令 'pip install pyyaml' 进行安装。")
    exit()

CONFIG_FILE_PATH = "config.yaml"

def load_config(path):
    """从指定的路径加载 YAML 配置文件。"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"错误: 配置文件 '{path}' 未找到。")
        print("请确保 'config.yaml' 和 'process_data.py' 在同一个文件夹下。")
        exit()
    except Exception as e:
        print(f"解析配置文件 '{path}' 时出错: {e}")
        exit()

def get_processed_inputs(output_file_path):
    """读取已存在的输出文件，返回一个包含所有已处理过的 'input' 的集合，用于断点续传。"""
    if not os.path.exists(output_file_path):
        return set()
    
    processed_inputs = set()
    with open(output_file_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                data = json.loads(line)
                if "input" in data:
                    processed_inputs.add(data["input"])
            except json.JSONDecodeError:
                continue
    return processed_inputs

def process_single_item(item, config):
    """处理单个数据项，调用API并返回结果。"""
    raw_text_content = item.get("text")
    user_prompt = f"<Input>\n{raw_text_content}\n</Input>"
    
    os.environ.pop('http_proxy', None)
    os.environ.pop('https_proxy', None)
    
    client = OpenAI(api_key=config['api_settings']['key'], base_url=config['api_settings']['base_url'])
    model_params = config['model_parameters']
    max_retries = config['performance']['max_retries']

    last_exception = None
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model_params['name'],
                messages=[
                    {"role": "system", "content": model_params['system_prompt']},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=model_params['temperature'],
                top_p=model_params['top_p'],
                extra_body=model_params['extra_body']
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                tqdm.write(f"\nAPI 调用失败 (尝试 {attempt + 1}/{max_retries})，1秒后重试: '{str(raw_text_content)[:30]}...' - 错误: {e}")
                time.sleep(1)

    raise Exception(f"API request failed after {max_retries} retries for input '{str(raw_text_content)[:30]}...'. Last error: {last_exception}") from last_exception
    
def main():
    """主函数：读取、并发处理并写入JSONL文件。"""
    # 从 YAML 文件加载配置
    config = load_config(CONFIG_FILE_PATH)
    
    input_file = config['paths']['input_file']
    output_file = config['paths']['output_file']
    max_workers = config['performance']['max_workers']
    
    print(f"正在检查 '{output_file}' 中的已处理数据...")
    processed_inputs = get_processed_inputs(output_file)
    print(f"发现 {len(processed_inputs)} 条已处理的数据。")

    tasks_to_process = []
    try:
        with open(input_file, "r", encoding="utf-8") as infile:
            for line in infile:
                try:
                    data = json.loads(line)
                    if data.get("text") and data["text"] not in processed_inputs:
                        tasks_to_process.append(data)
                except json.JSONDecodeError:
                    tqdm.write(f"解析JSON失败，已跳过此行: {line.strip()}")
    except FileNotFoundError:
        print(f"错误: 输入文件 '{input_file}' 未找到。请检查 config.yaml 中的路径配置。")
        return

    if not tasks_to_process:
        print("没有需要处理的新数据。")
        return
        
    print(f"总共有 {len(tasks_to_process)} 条新数据待处理。")

    with open(output_file, "a", encoding="utf-8") as outfile:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_item = {executor.submit(process_single_item, item, config): item for item in tasks_to_process}
            
            progress_bar = tqdm(concurrent.futures.as_completed(future_to_item), total=len(tasks_to_process), desc="处理进度")
            
            for future in progress_bar:
                original_item = future_to_item[future]
                try:
                    result_text = future.result()
                    if result_text:
                        output_data = {
                            "input": original_item.get("text"),
                            "output": result_text
                        }
                        outfile.write(json.dumps(output_data, ensure_ascii=False) + "\n")
                        outfile.flush()
                except Exception as exc:
                    tqdm.write(f"\n任务处理失败 (所有重试均告失败): {exc}")

    print(f"\n所有新数据处理完成！结果已追加至 '{output_file}'")

if __name__ == "__main__":
    main()
