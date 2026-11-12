FROM python:3.13-slim

WORKDIR /repo/apps/backend

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY packages/python /repo/packages/python
COPY apps/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV HF_HUB_DISABLE_XET=1
ENV HF_HOME=/root/.cache/huggingface

RUN python -c "\
import torch; \
from huggingface_hub import hf_hub_download; \
from transformers import AutoModelForCausalLM, AutoTokenizer; \
hf_hub_download(repo_id='timm/vit_small_patch16_224.augreg_in21k_ft_in1k', \
filename='model.safetensors', \
revision='7e2c55630205e1266030f18370f4c6ed1a514b52'); \
AutoTokenizer.from_pretrained('Qwen/Qwen2.5-0.5B-Instruct', \
revision='7ae557604adf67be50417f59c2c2f167def9a775'); \
AutoModelForCausalLM.from_pretrained('Qwen/Qwen2.5-0.5B-Instruct', \
revision='7ae557604adf67be50417f59c2c2f167def9a775', \
torch_dtype=torch.bfloat16); \
"

COPY apps/backend/ .
RUN chmod +x scripts/start.sh

CMD ["./scripts/start.sh"]
