import itertools
from datetime import datetime

from slurmpy import Slurm

BASE_PYTHON_CMD = """
PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512 \
python run.py \
--experiment corrector_encoder \
--per_device_train_batch_size {batch_size} \
--per_device_eval_batch_size {batch_size} \
--max_seq_length {max_seq_length} \
--model_name_or_path {model_name} \
--embedder_model_name {emb_model_name} \
--num_repeat_tokens {num_repeat_tokens} \
--embedder_no_grad {embedder_no_grad} \
--exp_group_name {exp_group_name} \
--learning_rate {learning_rate} \
--freeze_strategy {freeze_strategy} \
--embedder_fake_with_zeros {embedder_fake_with_zeros} \
--randomly_truncate_train_inputs {truncate} \
--use_frozen_embeddings_as_input False \
--encoder_dropout_disabled False \
--decoder_dropout_disabled False \
--use_less_data {use_less_data} \
--num_train_epochs 60 \
--max_eval_samples 500 \
--eval_steps 25000 \
--warmup_steps 200000 \
--bf16=1 \
--use_lora=0 \
--use_wandb=1 \
--corrector_model_alias "dpr_nq__msl32_beta" \
--corrector_ignore_hypothesis_embedding True
"""
# --resume_from_checkpoint "saves/f1fe315f3727514ba39bcc4376d56307/checkpoint-160000"


models = [
    # 't5-small',
    "t5-base",
    # 't5-large',
    # "t5-3b",
    # "t5-11b",
]

# emb_models = ['dpr', 'ance_tele']
# emb_models = ['dpr']
# emb_models = ['gtr_base__random_init']
emb_models = ["gtr_base"]


##########################################
# exp_group_name = 'feb27-t5-size'
# exp_group_name = 'feb27-token-num-3'
# exp_group_name = 'feb28-emb'
# exp_group_name = 'mar1-msl-eng'
# exp_group_name = 'mar2-gtr'
# exp_group_name = 'mar3-freeze'
# exp_group_name = 'mar9-bert'
# exp_group_name = 'mar9-freeze'
# exp_group_name = 'mar13-freeze-2'
# exp_group_name = 'mar17-baselines'
# exp_group_name = 'mar19-random'
# exp_group_name = 'mar21-bn-drop'
# exp_group_name = "apr16-huge"
# exp_group_name = "may11-mem-test-2"
exp_group_name = "may25-correct-ignore-hypothesis"
##########################################

batch_size = 256
max_seq_length = [32]

use_less_data = [-1]  # [-1]
embedder_no_grad = [True]
learning_rates = [2e-3]  # [2e-3, 2e-4]
num_repeat_tokens = [16]
freeze_strategies = ["none"]
fake_embedding_with_zeros = [False]
do_truncation = [False]

ACTUALLY_RUN_COMMAND = True


def run_cmd(cmd: str, job_desc: str):
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    job_name = f"{dt_string} {job_desc}"
    ##
    print("job_name >>", job_name)
    print("cmd >>", cmd.strip())
    ##

    if ACTUALLY_RUN_COMMAND:
        slurm = Slurm(
            job_name,
            slurm_kwargs={
                "partition": "rush",
                "gres": "gpu:a6000:1",
                # "gres": "gpu:1",
                # "constraint": "a40|3090|a6000|a5000|a100-40",
                "ntasks": 1,
                "cpus-per-task": 4,
                "mem": "48G",
                "nodelist": "rush-compute-03",
                # "time": "24:00:00",
                # "time": "72:00:00",
                "time": "168:00:00",  # 168 hours --> 2 weeks
                # "time": "504:00:00",  # 504 hours --> 3 weeks
            },
            slurm_flags=[
                "requeue",
            ],
        )
        slurm.run(
            f"""
        {cmd}
        """
        )
    ##
    print("\n\n")


total = 0
for args in itertools.product(
    models,
    emb_models,
    learning_rates,
    use_less_data,
    num_repeat_tokens,
    max_seq_length,
    embedder_no_grad,
    freeze_strategies,
    fake_embedding_with_zeros,
    do_truncation,
):
    m, e, lr, uld, n, msl, eng, frs, emb_fake, truncate = args
    total += 1
    cmd = BASE_PYTHON_CMD.format(
        batch_size=batch_size,
        max_seq_length=msl,
        #
        model_name=m,
        emb_model_name=e,
        num_repeat_tokens=n,
        learning_rate=lr,
        #
        embedder_no_grad=eng,
        embedder_fake_with_zeros=emb_fake,
        #
        use_less_data=uld,
        #
        exp_group_name=exp_group_name,
        freeze_strategy=frs,
        truncate=truncate,
    )
    cmd = cmd.replace("\n", " ")
    job_desc = ".".join(map(str, args))
    run_cmd(cmd, job_desc=job_desc)


if ACTUALLY_RUN_COMMAND:
    print(f"successfully queued {total} jobs.")
else:
    print(f"successfully queued {total} jobs. (pretend)")
