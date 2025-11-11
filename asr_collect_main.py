import boto3
import pandas as pd
import requests
import os
import json
import bson
import time
import yaml
from botocore.exceptions import ClientError
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# --- 1. 配置加载 (通用) ---
def load_config(config_path="config.yaml"):
    """从 YAML 文件加载配置。"""
    print(f"[*] 正在从 '{config_path}' 加载配置...")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            print("[+] 配置加载成功。")
            return config
    except FileNotFoundError:
        print(f"[!] 错误：配置文件 '{config_path}' 未找到。程序退出。")
        exit()
    except yaml.YAMLError as e:
        print(f"[!] 错误：解析配置文件时出错: {e}。程序退出。")
        exit()

# ===============================================================================
# STAGE 1: DOWNLOAD BSON AND CONVERT TO JSONL
# ===============================================================================
def log_download_failure(log_path, key, error_message):
    """记录下载阶段的失败日志。"""
    try:
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Key: {key}\nError: {error_message}\n---\n")
    except Exception as e:
        print(f"[!] 致命错误：无法写入日志文件 '{log_path}': {e}")

def read_keys_from_excel(file_path, column, max_rows=-1):
    """从Excel文件中读取对象键。"""
    try:
        nrows = max_rows if max_rows > 0 else None
        df = pd.read_excel(file_path, usecols=[column], nrows=nrows)
        keys = [key for key in df[column].dropna().tolist() if isinstance(key, str) and key.endswith('.bson')]
        print(f"    - 从 '{os.path.basename(file_path)}' 读取了 {len(keys)} 个 .bson 对象键。")
        return keys
    except Exception as e:
        print(f"    - [!] 读取Excel文件时发生错误: {e}")
        return []

def generate_presigned_url(s3_client, bucket_name, object_key, expires_in):
    """生成预签名URL。"""
    try:
        return s3_client.generate_presigned_url(
            "get_object", Params={"Bucket": bucket_name, "Key": object_key}, ExpiresIn=expires_in
        )
    except ClientError as e:
        return None

def download_and_convert_bson_to_jsonl(log_path, object_key, url, download_folder):
    """下载BSON并转换为单个JSONL文件。"""
    try:
        base_name_no_ext = os.path.splitext(os.path.basename(object_key))[0]
        local_json_path = os.path.join(download_folder, f"{base_name_no_ext}.jsonl")
        tmp_json_path = local_json_path + ".tmp"
        if os.path.exists(local_json_path): return local_json_path
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        python_data = bson.decode_iter(response.content)
        with open(tmp_json_path, 'w', encoding='utf-8') as f:
            for document in python_data:
                f.write(json.dumps(document, default=str, ensure_ascii=False) + '\n')
        os.rename(tmp_json_path, local_json_path)
        return local_json_path
    except Exception as e:
        log_download_failure(log_path, object_key, f"下载或转换时出错: {e}")
        return None

def run_download_stage(config):
    """执行下载阶段的完整逻辑。"""
    print("\n" + "="*80)
    print(" " * 28 + "开始执行: [下载阶段]")
    print("="*80)

    # --- 获取配置 ---
    dl_cfg = config['download_stage']
    aws_cfg = dl_cfg['aws']
    src_cfg = dl_cfg['source']
    perf_cfg = config['performance']
    path_cfg = config['paths']

    all_keys = read_keys_from_excel(path_cfg['excel_file'], src_cfg['column_name'], src_cfg['rows_to_process'])
    if not all_keys: return

    download_dir = path_cfg['download_dir']
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
        print(f"    - 已创建下载目录: '{download_dir}'")
    
    keys_to_process = [k for k in all_keys if not os.path.exists(os.path.join(download_dir, f"{os.path.splitext(os.path.basename(k))[0]}.jsonl"))]
    
    print(f"    - 任务统计: 总计({len(all_keys)}), 已处理({len(all_keys) - len(keys_to_process)}), 新任务({len(keys_to_process)})")
    if not keys_to_process:
        print("[+] 下载阶段：所有文件均已存在，无需操作。")
        return

    s3_client = boto3.client("s3", region_name=aws_cfg['region'], aws_access_key_id=aws_cfg['access_key'], aws_secret_access_key=aws_cfg['secret_key'])
    
    # --- 生成URL ---
    urls = {}
    expires = dl_cfg['url_expires_in_minutes'] * 60
    with ThreadPoolExecutor(max_workers=perf_cfg['url_gen_workers']) as executor:
        future_map = {executor.submit(generate_presigned_url, s3_client, aws_cfg['bucket_name'], key, expires): key for key in keys_to_process}
        for future in tqdm(as_completed(future_map), total=len(keys_to_process), desc="    - 生成URL      "):
            key, url = future_map[future], future.result()
            if url: urls[key] = url
            else: log_download_failure(path_cfg['download_failed_log'], key, "生成URL失败")

    if not urls:
        print("    - [!] 未能生成任何有效的预签名URL。")
        return

    # --- 下载与转换 ---
    success_count = 0
    with ThreadPoolExecutor(max_workers=perf_cfg['download_workers']) as executor:
        future_map = {executor.submit(download_and_convert_bson_to_jsonl, path_cfg['download_failed_log'], key, url, download_dir): key for key, url in urls.items()}
        for future in tqdm(as_completed(future_map), total=len(urls), desc="    - 下载与转换   "):
            if future.result(): success_count += 1
    
    failure_count = len(urls) - success_count
    print(f"\n[+] 下载阶段完成: 成功 {success_count} 个, 失败 {failure_count} 个。")
    if failure_count > 0: print(f"    - 失败详情请查看: '{path_cfg['download_failed_log']}'")


# ===============================================================================
# STAGE 2: PROCESS AND COMBINE JSONL FILES
# ===============================================================================
def extract_and_combine_text(jsonl_file_path):
    """从单个 JSONL 文件中提取所有 "formattedString" 字段。"""
    try:
        all_strings = []
        with open(jsonl_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip(): continue
                data = json.loads(line)
                if 'items' in data and isinstance(data['items'], list):
                    for item in data['items']:
                        if 'formattedString' in item and item['formattedString']:
                            all_strings.append(item['formattedString'])
        return " ".join(all_strings) if all_strings else None
    except Exception:
        # 错误在调用处统一处理和打印，这里保持静默
        return None

def process_single_file(file_path):
    """处理单个文件，返回文件名和提取的文本。"""
    combined_text = extract_and_combine_text(file_path)
    if combined_text:
        # 使用文件名作为唯一标识符，而不是包含路径
        file_identifier = os.path.basename(file_path)
        return file_identifier, {"source_file": file_identifier, "text": combined_text}
    return os.path.basename(file_path), None

def run_process_stage(config):
    """执行处理和合并阶段的完整逻辑。"""
    print("\n" + "="*80)
    print(" " * 28 + "开始执行: [处理阶段]")
    print("="*80)
    
    # --- 获取配置 ---
    path_cfg = config['paths']
    perf_cfg = config['performance']
    
    source_dir = path_cfg['download_dir']
    output_file = path_cfg['final_output_file']
    log_file = output_file + '.log'

    if not os.path.exists(source_dir):
        print(f"    - [!] 输入目录 '{source_dir}' 不存在，跳过处理阶段。")
        return

    processed_files = set()
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8') as f:
            processed_files = {line.strip() for line in f}
    
    files_to_process = [os.path.join(source_dir, f) for f in sorted(os.listdir(source_dir)) if f.endswith(".jsonl") and f not in processed_files]
    
    print(f"    - 任务统计: 已处理({len(processed_files)}), 新任务({len(files_to_process)})")
    if not files_to_process:
        print("[+] 处理阶段：所有文件均已处理，无需操作。")
        return

    newly_processed_count = 0
    error_count = 0
    try:
        with open(output_file, 'a', encoding='utf-8') as out_f, \
             open(log_file, 'a', encoding='utf-8') as log_f, \
             ThreadPoolExecutor(max_workers=perf_cfg['processing_workers']) as executor:

            future_map = {executor.submit(process_single_file, fp): fp for fp in files_to_process}
            
            pbar = tqdm(as_completed(future_map), total=len(files_to_process), desc="    - 提取与合并   ")
            for future in pbar:
                filename, result = future.result()
                if result:
                    out_f.write(json.dumps(result, ensure_ascii=False) + '\n')
                    log_f.write(filename + '\n')
                    newly_processed_count += 1
                else:
                    error_count += 1
                pbar.set_postfix({"新增": newly_processed_count, "失败": error_count})
    
    except Exception as e:
        print(f"\n    - [!] 处理阶段发生严重错误: {e}")

    print(f"\n[+] 处理阶段完成: 新增 {newly_processed_count} 个, 失败 {error_count} 个。")
    print(f"    - 输出文件: '{output_file}'")
    print(f"    - 日志文件: '{log_file}'")


# ===============================================================================
# MAIN ORCHESTRATOR
# ===============================================================================
if __name__ == "__main__":
    CONFIG = load_config()
    if CONFIG:
        start_time = time.time()
        
        if CONFIG.get('stages', {}).get('run_download', False):
            run_download_stage(CONFIG)
        else:
            print("\n[*] 根据配置，跳过[下载阶段]。")

        if CONFIG.get('stages', {}).get('run_process', False):
            run_process_stage(CONFIG)
        else:
            print("\n[*] 根据配置，跳过[处理阶段]。")
            
        end_time = time.time()
        print("\n" + "="*80)
        print(f"所有已启用的任务完成，总耗时: {end_time - start_time:.2f} 秒。")
        print("="*80)