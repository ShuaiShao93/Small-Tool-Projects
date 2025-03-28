import hashlib
import logging
import os
import shutil
import tarfile
from urllib.parse import urlparse

import boto3
import yaml
from huggingface_hub import hf_hub_download

from deploy.models import (
    CustomerModelConfig,
    HuggingFaceModelSource,
    LocalModelSource,
    ModelBaseConfig,
)

HF_TOKEN = os.environ.get("HF_TOKEN")
ROOT_DIR_NAME = "galileo_models"


def parse_customer_config(config_path: str) -> CustomerModelConfig:
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    return CustomerModelConfig(**config)


def parse_base_config(config_path: str) -> ModelBaseConfig:
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    return ModelBaseConfig(**config)


def download_hf_file(
    repo_id: str, revision: str, filename: str, target_path: str
) -> None:
    logging.debug(
        f"Downloading {filename} from {repo_id} at revision {revision} to {target_path}"
    )
    local_file = hf_hub_download(
        repo_id=repo_id, filename=filename, revision=revision, token=HF_TOKEN
    )
    shutil.copy(local_file, target_path)


def build_model_dir(model_base_config: ModelBaseConfig, base_dir: str) -> str:
    model_dir = os.path.join(base_dir, model_base_config.wizard_path)
    logging.info(f"Building model {model_base_config.name} in {model_dir}")
    os.makedirs(model_dir, exist_ok=True)
    for model_source in model_base_config.model_sources:
        source = model_source.source
        target_subdirectory = (
            model_source.target_subdirectory if model_source.target_subdirectory else ""
        )
        subdir = os.path.join(model_dir, target_subdirectory)
        os.makedirs(subdir, exist_ok=True)
        if isinstance(source, HuggingFaceModelSource):
            for file in source.files:
                logging.debug(f"Downloading file {file.filename} to {subdir}")
                download_hf_file(
                    source.huggingface_repo,
                    source.huggingface_revision,
                    file.filename,
                    os.path.join(subdir, file.rename_to or file.filename),
                )
        elif isinstance(source, LocalModelSource):
            for file in source.files:
                logging.debug(f"Copying file {file.filename} to {subdir}")
                shutil.copy(
                    file.filename,
                    os.path.join(
                        subdir, file.rename_to or os.path.basename(file.filename)
                    ),
                )
    return model_dir


def md5_directory(directory: str) -> str:
    md5_hash = hashlib.md5()
    for root, dirs, files in sorted(os.walk(directory)):
        for file in sorted(files):
            file_path = os.path.join(root, file)
            # Get relative path to include directory structure
            rel_path = os.path.relpath(file_path, directory)
            # Update hash with file path
            md5_hash.update(rel_path.encode("utf-8"))

            # Update hash with file content
            with open(file_path, "rb") as f:
                while chunk := f.read(4096):
                    md5_hash.update(chunk)
    return md5_hash.hexdigest()


def package_tarball(dir_path: str, tarball_path: str) -> None:
    logging.info(f"Packaging {dir_path} to {tarball_path}")
    with tarfile.open(tarball_path, "w:gz") as tar:
        tar.add(dir_path, arcname=ROOT_DIR_NAME)


def push_package_to_s3(tarball_path: str, s3_path: str) -> None:
    if not s3_path.startswith("s3://"):
        raise ValueError("Invalid S3 path. It should start with 's3://'.")

    logging.info(f"Pushing {tarball_path} to {s3_path}")

    parts = s3_path[5:].split("/", 1)
    bucket_name, blob_path = parts[0], parts[1]

    s3_client = boto3.client("s3")
    s3_client.upload_file(tarball_path, bucket_name, blob_path)


def push_directory_to_cloudflare_r2(
    directory: str, access_key_id: str, access_key_secret: str, r2_path: str
) -> None:
    if "r2.cloudflarestorage.com" not in r2_path:
        raise ValueError("Invalid R2 path. It should be a Cloudflare R2 path.")

    md5_hash = md5_directory(directory)[:8]

    logging.info(f"Pushing {directory} to Cloudflare R2: {r2_path}/{md5_hash}")

    parsed_url = urlparse(r2_path)
    endpoint_url = f"https://{parsed_url.netloc}"
    path_parts = parsed_url.path.lstrip("/").split("/")
    bucket_name = path_parts[0]
    blob_path = "/".join(path_parts[1:] + [md5_hash])

    s3_client = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key_id,
        aws_secret_access_key=access_key_secret,
    )

    response = s3_client.list_objects_v2(
        Bucket=bucket_name, Prefix=blob_path, MaxKeys=1
    )
    if "Contents" in response:
        logging.info(f"Directory '{blob_path}' already exists. Skipping.")

    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, directory)
            target_path = f"{blob_path}/{rel_path}"
            s3_client.upload_file(file_path, bucket_name, target_path)
            logging.debug(
                f"Uploaded {rel_path} to bucket {bucket_name} at {target_path}"
            )
