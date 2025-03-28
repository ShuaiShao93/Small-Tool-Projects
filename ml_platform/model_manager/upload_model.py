import argparse
import logging
import os
import tempfile

from deploy.utils import (
    build_model_dir,
    parse_base_config,
    push_directory_to_cloudflare_r2,
)

MODEL_CONFIG_DIR = "config/base"
CLOUDFLARE_R2_ACCESS_KEY_ID = os.getenv("CLOUDFLARE_R2_ACCESS_KEY_ID")
CLOUDFLARE_R2_ACCESS_KEY_SECRET = os.getenv("CLOUDFLARE_R2_ACCESS_KEY_SECRET")


def upload_model(model_config_path: str) -> None:
    logging.info(f"Uploading model {model_config_path}")

    assert os.path.exists(
        model_config_path
    ), f"Model config not found at {model_config_path}"
    assert model_config_path.startswith(
        MODEL_CONFIG_DIR
    ), f"Model config path must start with {MODEL_CONFIG_DIR}"
    assert CLOUDFLARE_R2_ACCESS_KEY_ID, "CLOUDFLARE_R2_ACCESS_KEY_ID must be set"
    assert (
        CLOUDFLARE_R2_ACCESS_KEY_SECRET
    ), "CLOUDFLARE_R2_ACCESS_KEY_SECRET must be set"

    if not model_config_path.endswith(".yaml"):
        logging.info("Model config path must be a yaml file, skipping")
        return

    model_base_config = parse_base_config(model_config_path)

    if not model_base_config.target_path:
        logging.info("No target path specified, skipping")
        return

    with tempfile.TemporaryDirectory() as target_base_dir:
        build_model_dir(model_base_config, target_base_dir)
        push_directory_to_cloudflare_r2(
            target_base_dir,
            CLOUDFLARE_R2_ACCESS_KEY_ID,
            CLOUDFLARE_R2_ACCESS_KEY_SECRET,
            model_base_config.target_path,
        )


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--model_config_path", type=str, required=True)
    args = arg_parser.parse_args()
    upload_model(args.model_config_path)
