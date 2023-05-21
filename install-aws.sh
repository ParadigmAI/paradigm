#!/bin/bash

# Install Argo Workflows CLI
echo "Installing..."
mv setup-aws.py setup.py
kubectl create namespace paradigm
kubectl create namespace argo
kubectl apply -f rbac.yaml
kubectl apply -n argo -f https://github.com/argoproj/argo-workflows/releases/download/v3.4.7/install.yaml
kubectl patch deployment \
  argo-server \
  --namespace argo \
  --type='json' \
  -p='[{"op": "replace", "path": "/spec/template/spec/containers/0/args", "value": [
  "server",
  "--auth-mode=server"
]}]'
# kubectl -n paradigm port-forward deployment/argo-server 2746:2746

# Detect the running operating system
os_name="$(uname)"

# Execute commands according to the detected OS
case "${os_name}" in
  Darwin) # MacOS
    echo "Detected MacOS"
    # Download the binary
    curl -sLO https://github.com/argoproj/argo-workflows/releases/download/v3.4.7/argo-darwin-amd64.gz

    # Unzip
    gunzip argo-darwin-amd64.gz

    # Make binary executable
    chmod +x argo-darwin-amd64

    # Move binary to path
    mv ./argo-darwin-amd64 /usr/local/bin/argo
    ;;
  Linux)
    echo "Detected Linux"
    # Download the binary
    curl -sLO https://github.com/argoproj/argo-workflows/releases/download/v3.4.7/argo-linux-amd64.gz

    # Unzip
    gunzip argo-linux-amd64.gz

    # Make binary executable
    chmod +x argo-linux-amd64

    # Move binary to path
    sudo mv ./argo-linux-amd64 /usr/local/bin/argo
    ;;
  *)
    echo "Unsupported operating system: ${os_name}"
    exit 1
    ;;
esac

#Installing Paradigm Utility

# Install requirements
pip install -r requirements.txt

# Install command-line utility
pip install -e .

echo "Installation complete! You can now use the 'paradigm' commands."
