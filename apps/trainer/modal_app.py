"""
Author: Sean Froning
Created Date: 8.21.2026
Modal app deployment
"""

import modal
from typing import Dict

app = modal.App("fiery-trainer")

image = (
    modal.Image.debian_slim(python_version="3.13")
    .uv_pip_install("torch", "timm", "peft", "webdataset")
    .add_local_dir(
        "../../packages/python",
        remote_path="/opt/packages/python",
        copy=True,
    )
    .run_commands("uv pip install --system -e /opt/packages/python")
    .add_local_python_source("src")
)

secrets = [modal.Secret.from_name("Fiery-Environment")]


@app.function(image=image, gpu="T4", timeout=3600, secrets=secrets)
def train_deformation(spec: Dict) -> Dict:
    from src.entrypoint import train_deformation

    return train_deformation(spec)


@app.local_entrypoint()
def main() -> None:
    print(train_deformation.remote({"smoke": True}))
