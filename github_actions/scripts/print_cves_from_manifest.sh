#!/bin/bash
# A helper script to scan Kubernetes manifest files for images and print all fixable critical and high vulnerabilities.
# Usage:
#   brew install aquasecurity/trivy/trivy
#   scripts/find_cves.sh <path_to_kubernetes_yaml>


# Check if an argument is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <path_to_kubernetes_yaml>"
  exit 1
fi

# Set the Kubernetes manifest file path from the argument
KUBE_MANIFEST="$1"

# Check if the file exists
if [ ! -f "$KUBE_MANIFEST" ]; then
  echo "File not found: $KUBE_MANIFEST"
  exit 1
fi

# Extract image names from the Kubernetes manifest using sed, then sort and deduplicate
IMAGES=$(sed -n 's/^[[:space:]]*image:[[:space:]]*//p' "$KUBE_MANIFEST" | sort | uniq)

# Check if any images were found
if [ -z "$IMAGES" ]; then
  echo "No images found in the manifest."
  exit 0
fi

# Loop through each unique image and scan with Trivy
for IMAGE in $IMAGES; do
  echo "Scanning image: $IMAGE"
  
  # Run Trivy, ignore unfixed vulnerabilities
  trivy image --severity HIGH,CRITICAL --ignore-unfixed --format json --quiet "$IMAGE" | jq -r '
    .Results[]?.Vulnerabilities[]?
    | select(.Severity == "HIGH" or .Severity == "CRITICAL")
    | "\(.VulnerabilityID) - \(.PkgName) (\(.InstalledVersion) -> \(.FixedVersion)) [\(.Severity)]"'

  echo ""
done
