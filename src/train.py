import os

import torch
import argparse
from transformers import AutoTokenizer, AutoModelForCausalLM,TrainingArguments,Trainer,ProgressCallback
from datasets import load_dataset
from peft import LoraConfig, get_peft_model
import glob
from functools import partial
from torch.nn.utils.rnn import pad_sequence

from accelerate import Accelerator
def on_log(self, args, state, control, logs=None, **kwargs):
    if state.is_local_process_zero and self.training_bar is not None:
        _ = logs.pop("total_flos", None)
ProgressCallback.on_log = on_log

def mapper_tokenize(examples,tokenizer):
    input_ids = []
    output_ids = []
    inputs = examples['input']
    outputs = examples['output']
    for input_tex,output_tex in zip(inputs,outputs):
        input_ids.append(tokenizer.encode(input_tex,add_special_tokens=False))
        output_ids.append(tokenizer.encode(output_tex,add_special_tokens=False))
    return {
        "input_ids": input_ids,
        "labels": output_ids
    }

def data_collator(examples,eos_token_id,pad_token_id,total_max_length):
    input_ids_all = []
    labels_all = []
    attention_mask_all = []
    for example in examples:
        original_input_ids = example['input_ids']
        original_output_ids = example['labels']
        input_ids = original_input_ids+original_output_ids
        labels = [-100]*(len(original_input_ids)-1)+original_output_ids+[eos_token_id]
        attention_mask = [1]*len(input_ids)
        input_ids_all.append(torch.tensor(input_ids, dtype=torch.long))
        labels_all.append(torch.tensor(labels, dtype=torch.long))
        attention_mask_all.append(torch.tensor(attention_mask, dtype=torch.long))
    input_ids_tensor = pad_sequence(input_ids_all,batch_first=True,padding_value=pad_token_id,padding_side="left")
    labels_tensor = pad_sequence(labels_all,batch_first=True,padding_value=-100,padding_side="left")
    attention_mask_tensor = pad_sequence(attention_mask_all,batch_first=True,padding_value=0,padding_side="left")

    max_bs_size = total_max_length // input_ids_tensor.shape[1]
    if max_bs_size < input_ids_tensor.shape[0]:
        if max_bs_size < 1:
            max_bs_size = 1
            print(f'max_bs_size:{max_bs_size}, input_ids_tensor.shape[0]:{input_ids_tensor.shape[0]} truncate the batch size to {max_bs_size}')
            input_ids_tensor = input_ids_tensor[:max_bs_size,:total_max_length]
            labels_tensor = labels_tensor[:max_bs_size,:total_max_length]
            attention_mask_tensor = attention_mask_tensor[:max_bs_size,:total_max_length]
        else:
            print(f'max_bs_size:{max_bs_size}, input_ids_tensor.shape[0]:{input_ids_tensor.shape[0]} truncate the batch size to {max_bs_size}')
            input_ids_tensor = input_ids_tensor[:max_bs_size]
            labels_tensor = labels_tensor[:max_bs_size]
            attention_mask_tensor = attention_mask_tensor[:max_bs_size]
    
    # 确保张量在正确的设备上并且有正确的数据类型
    input_ids_tensor = input_ids_tensor.long()
    labels_tensor = labels_tensor.long()
    attention_mask_tensor = attention_mask_tensor.long()
    
    
    return {
        "input_ids": input_ids_tensor,
        "labels": labels_tensor,
        "attention_mask": attention_mask_tensor
    }


def compute_loss(outputs,
                labels,
                num_items_in_batch,
            ):
    logits = outputs.logits
    loss = torch.nn.functional.cross_entropy(logits, labels)
    return loss
def main():
    # 初始化 Accelerator
    accelerator = Accelerator()
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name", type=str, required=True)
    parser.add_argument("--dataset_dir", type=str, required=True)
    parser.add_argument("--dataset_eval_dir", type=str, required=True)
    parser.add_argument("--total_max_length", type=int, default=1)
    parser.add_argument("--batch_size", type=int, default=1)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--lora_rank",type=int, default=8)
    parser.add_argument("--lora_alpha",type=int, default=32)
    parser.add_argument("--lora_dropout",type=float, default=0.05)
    parser.add_argument("--lora_trainable",type=str, default="q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj")
    parser.add_argument("--lora_init_method",type=str, default=None)
    parser.add_argument("--output_dir",type=str, default="output")
    parser.add_argument("--shuffle_data", action="store_true", help="启用数据随机化")
    parser.add_argument("--shuffle_seed", type=int, default=42, help="数据随机化种子")
    parser.add_argument("--learning_rate", type=float, default=5e-5, help="学习率")
    parser.add_argument("--save_steps", type=int, default=2000, help="保存步数")
    parser.add_argument("--logging_steps", type=int, default=1, help="日志步数")
    parser.add_argument("--eval_steps", type=int, default=2000, help="评估步数")
    parser.add_argument("--save_total_limit", type=int, default=5, help="保存总限制")

    args = parser.parse_args()
    args.total_max_length = args.total_max_length*1024
    print(args)
    # 使用 Accelerator 兼容的模型加载设置
    model = AutoModelForCausalLM.from_pretrained(
        args.model_name, 
        torch_dtype=torch.bfloat16,
        trust_remote_code=True
    )
    model.train()
    model.config.use_cache = False
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    
    # 确保tokenizer有pad_token
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    jsonl_files = glob.glob(os.path.join(args.dataset_dir, "*.jsonl"))
    print(jsonl_files)
    ds = load_dataset("json", data_files=jsonl_files)['train']
    
    # 在数据集层面添加随机化
    if args.shuffle_data:
        print(f"启用数据随机化，种子: {args.shuffle_seed}")
        # 方法1: 使用 shuffle 方法打乱数据集
        ds = ds.shuffle(seed=args.shuffle_seed)  # 使用指定种子确保可重现性
    
    tokenized_ds = ds.map(partial(mapper_tokenize,tokenizer=tokenizer),batched=True,batch_size=args.batch_size,remove_columns=ds.column_names)
    tokenized_ds = tokenized_ds.filter(lambda x: len(x['input_ids']) <= 2048)
    

    jsonl_files_eval = glob.glob(os.path.join(args.dataset_eval_dir, "*.jsonl"))
    print(jsonl_files_eval)
    ds_eval = load_dataset("json", data_files=jsonl_files_eval)['train']
    tokenized_ds_eval = ds_eval.map(partial(mapper_tokenize,tokenizer=tokenizer),batched=True,batch_size=args.batch_size,remove_columns=ds_eval.column_names)
    tokenized_ds_eval = tokenized_ds_eval.filter(lambda x: len(x['input_ids']) <= 2048)
    print(tokenized_ds_eval)
    print(tokenized_ds_eval[0])
    print(tokenized_ds)
    print(tokenized_ds[0])
    print(tokenized_ds[1])
    print(model)
    print(tokenizer)
    lora_config = LoraConfig(
            r=args.lora_rank,
            lora_alpha=args.lora_alpha,
            lora_dropout=args.lora_dropout,
            init_lora_weights=bool(args.lora_init_method) if args.lora_init_method == 'True' or args.lora_init_method == 'False' else args.lora_init_method,
            target_modules=args.lora_trainable.split(","),
            task_type="CAUSAL_LM",  # 明确指定任务类型
            bias="none",  # 不训练bias
        )
    print(lora_config)
    peft_model = get_peft_model(model, lora_config)
    
    # 确保模型处于训练模式
    peft_model.train()
    
    # 打印可训练参数信息
    peft_model.print_trainable_parameters()
    
    # 检查并修复梯度设置
    trainable_params = 0
    total_params = 0
    for name, param in peft_model.named_parameters():
        total_params += param.numel()
        if param.requires_grad:
            trainable_params += param.numel()
            # 确保参数有梯度
            param.requires_grad = True
            print(f"Trainable param: {name}, shape: {param.shape}, requires_grad: {param.requires_grad}")
    
    print(f"Trainable parameters: {trainable_params:,} || Total parameters: {total_params:,} || Trainable%: {100 * trainable_params / total_params:.2f}")
    peft_model.enable_input_require_grads()


    training_args = TrainingArguments(
        output_dir=args.output_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        save_steps=args.save_steps,
        save_total_limit=args.save_total_limit,
        logging_dir=args.output_dir,
        logging_steps=args.logging_steps,
        logging_first_step=True,
        log_level="error",  
        logging_strategy="steps",
        do_train=True,
        load_best_model_at_end=True,
        do_eval=True,
        eval_strategy="steps",
        eval_steps=args.eval_steps,
        save_strategy="steps",
        metric_for_best_model="eval_loss",
        bf16=True,
        gradient_checkpointing=True,  # 启用gradient_checkpointing节省显存
        dataloader_drop_last=False,
        remove_unused_columns=False,
        # 数据随机化设置
        dataloader_pin_memory=False,  # 减少内存使用
        dataloader_persistent_workers=False,  # 禁用持久化工作进程
        # 内存优化设置
        dataloader_num_workers=0,  # 减少数据加载器工作进程
        max_grad_norm=1.0,  # 梯度裁剪
        warmup_steps=100,  # 预热步数
        learning_rate=args.learning_rate,  # 学习率
        lr_scheduler_type="cosine",
        weight_decay=0.01,  # 权重衰减
        adam_beta1=0.9,
        adam_beta2=0.999,
        adam_epsilon=1e-8,
        report_to="wandb",
        project=os.getenv("WANDB_PROJECT", "default-project"),
        run_name=os.getenv("WANDB_RUN_NAME", "default-run"),
        disable_tqdm=False,
    )
    print(training_args)
    trainer = Trainer(
        model=peft_model,
        args=training_args,
        train_dataset=tokenized_ds,
        eval_dataset=tokenized_ds_eval,
        data_collator=partial(data_collator,eos_token_id=tokenizer.eos_token_id,pad_token_id=tokenizer.pad_token_id,total_max_length=args.total_max_length),
        compute_loss_func=compute_loss,

    )
    print(trainer)
    # 确保模型在训练前正确设置
    peft_model.train()
    
    # 验证模型参数设置
    print("验证模型参数设置...")
    for name, param in peft_model.named_parameters():
        if param.requires_grad:
            print(f"✓ {name}: requires_grad={param.requires_grad}, shape={param.shape}")
    
    trainer.train()
    peft_model.save_pretrained(args.output_dir)
if __name__ == "__main__":
    main()