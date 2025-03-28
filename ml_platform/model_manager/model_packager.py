import argparse
import logging
import os
import tempfile

from deploy.models import ModelArtifactConfig
from deploy.utils import (
    build_model_dir,
    md5_directory,
    package_tarball,
    parse_base_config,
    parse_customer_config,
    push_package_to_s3,
)


def _build_artifact_tarball(
    artifact_config: ModelArtifactConfig, tarball_path: str
) -> str:
    """Returns the md5 hash of the directory"""
    with tempfile.TemporaryDirectory() as artifact_base_dir:
        for model in artifact_config.models:
            base_config = parse_base_config(model.base)
            build_model_dir(base_config, artifact_base_dir)
        md5_hash = md5_directory(artifact_base_dir)
        for root, dirs, files in os.walk(artifact_base_dir):
            for file in files:
                logging.info(
                    f"File: {os.path.relpath(os.path.join(root, file), artifact_base_dir)}"
                )

        package_tarball(artifact_base_dir, tarball_path)
    return md5_hash


def package_customer(customer_name: str) -> None:
    logging.info(f"Packaging customer {customer_name}")
    customer_config = parse_customer_config(f"config/customers/{customer_name}.yaml")
    for artifact in customer_config.artifacts:
        tarball_path = tempfile.mktemp(suffix=".tar.gz")
        md5_hash = _build_artifact_tarball(artifact, tarball_path)

        artifact_name = artifact.name
        target_path = artifact.target_path
        assert target_path, "Target path must be specified in the customer config"

        md5_hash_short = md5_hash[:8]
        logging.info(f"MD5 hash of artifact: {md5_hash_short}")
        target_path = os.path.join(
            target_path, f"{customer_name}-{artifact_name}-{md5_hash_short}.tar.gz"
        )
        push_package_to_s3(tarball_path, target_path)


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--customer", type=str, required=True)
    args = arg_parser.parse_args()
    package_customer(args.customer)
