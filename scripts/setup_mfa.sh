#!/bin/bash
# Setup Montreal Forced Aligner (MFA)
# Run this script to install MFA and download required models

set -e

echo "=== Installing Montreal Forced Aligner ==="

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo "Error: conda not found. Please install Miniconda or Anaconda first."
    echo "Visit: https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

# Create MFA environment
conda create -n mfa -c conda-forge montreal-forced-aligner -y

# Activate and download models
conda run -n mfa mfa model download acoustic english_mfa
conda run -n mfa mfa model download dictionary english_mfa

echo ""
echo "=== MFA Setup Complete ==="
echo "Models downloaded:"
echo "  - Acoustic model: english_mfa"
echo "  - Dictionary: english_mfa"
echo ""
echo "To use MFA, activate the environment:"
echo "  conda activate mfa"
