#!/bin/bash

# Unified APK Patcher & Signer - Setup Script
# This script sets up the tool for first-time use

set -e

echo "========================================"
echo "Unified APK Patcher & Signer"
echo "Setup & Installation"
echo "========================================"
echo ""

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Python version: $python_version"

# Check if Python 3.9+ is available
min_version="3.9"
if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= tuple(map(int, '${min_version}'.split('.'))) else 1)" 2>/dev/null; then
    echo "   ❌ Error: Python 3.9 or higher required"
    exit 1
fi
echo "   ✅ Python version OK"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "   ✅ Dependencies installed"
else
    echo "   ⚠️  requirements.txt not found"
    echo "   Installing minimum dependencies..."
    pip install cryptography
fi
echo ""

# Install optional signing tool
echo "🔑 Installing APK signing tool..."
echo "   (This enables advanced signing features)"

if command -v sign-apk &> /dev/null; then
    echo "   ✅ sign-apk already installed"
else
    echo "   Installing sign-apk-py..."
    if pip install git+https://github.com/adityatelange/sign-apk-py 2>/dev/null; then
        echo "   ✅ sign-apk-py installed successfully"
    else
        echo "   ⚠️  Failed to install sign-apk-py automatically"
        echo "      It will be installed when needed"
    fi
fi
echo ""

# Make scripts executable
echo "🔧 Setting up scripts..."
chmod +x apk_patcher_advanced.py 2>/dev/null || true
chmod +x setup.sh 2>/dev/null || true
echo "   ✅ Scripts configured"
echo ""

# Create optional symlink
if [ "$1" == "--install" ]; then
    echo "🚀 Creating global command..."
    script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
    
    if [ -w "/usr/local/bin" ]; then
        ln -sf "$script_dir/apk_patcher_advanced.py" /usr/local/bin/apk-patcher
        echo "   ✅ Created: apk-patcher"
        echo "   Usage: apk-patcher input.apk output.apk [options]"
    else
        echo "   ⚠️  Cannot write to /usr/local/bin (requires sudo)"
        echo "   Usage: python apk_patcher_advanced.py input.apk output.apk [options]"
    fi
    echo ""
fi

# Final checks
echo "✅ Verifying installation..."
echo ""

# Test imports
if python3 -c "import zipfile, struct, tempfile" 2>/dev/null; then
    echo "   ✅ Core modules available"
else
    echo "   ❌ Core modules missing"
    exit 1
fi

if python3 -c "import cryptography" 2>/dev/null; then
    echo "   ✅ Cryptography module available"
else
    echo "   ⚠️  Cryptography module not available"
    echo "      Installing..."
    pip install cryptography
fi

echo ""
echo "========================================"
echo "✅ Setup Complete!"
echo "========================================"
echo ""
echo "You're ready to patch APKs!"
echo ""
echo "Quick start:"
echo "  python apk_patcher_advanced.py input.apk output.apk"
echo ""
echo "For more options:"
echo "  python apk_patcher_advanced.py --help"
echo ""
echo "See README.md for detailed documentation"
echo ""
