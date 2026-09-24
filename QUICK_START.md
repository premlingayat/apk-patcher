# Quick Start Guide

Get started in 5 minutes!

## Installation

### Step 1: Clone or Download

```bash
git clone https://github.com/yourusername/unified-apk-patcher.git
cd unified-apk-patcher
```

Or download the files manually.

### Step 2: Setup

```bash
# Make setup script executable
chmod +x setup.sh

# Run setup
./setup.sh
```

Or manually:

```bash
pip install -r requirements.txt
pip install git+https://github.com/adityatelange/sign-apk-py
```

### Step 3: Verify Installation

```bash
python apk_patcher_advanced.py --help
```

## First Use

### 1. Quick Patch (Debug Key)

```bash
python apk_patcher_advanced.py input.apk output.apk
```

✅ Done! Your patched APK is ready in `output.apk`

### 2. Patch with Your Keystore

```bash
python apk_patcher_advanced.py input.apk output.apk \
  --keystore release.p12 \
  --keystore-password yourpassword
```

### 3. Patch with PEM Files

```bash
python apk_patcher_advanced.py input.apk output.apk \
  --key release.pem \
  --cert release.crt
```

## What Gets Patched?

The tool automatically:

1. ✅ **Disables Flutter TLS Verification**
   - Patches `libflutter.so` files
   - Works with arm64-v8a, armeabi-v7a, x86_64, x86 architectures
   - Allows HTTPS traffic interception

2. ✅ **Patches Network Security Config**
   - Allows user/system certificates
   - Enables cleartext (HTTP) traffic
   - Trusts all certificate sources

3. ✅ **Signs the APK**
   - Uses v2 and v3 signature schemes
   - Compatible with all Android devices
   - Ready to install on any device

## Output

A new APK file ready for:
- 📱 Installation on Android devices
- 🔍 Traffic interception (Burp Suite, Fiddler, etc.)
- 🧪 Security testing
- 📊 Reverse engineering analysis

## Common Tasks

### Install on Device

```bash
adb install output.apk
```

### Uninstall Previous Version

```bash
adb uninstall com.example.app
adb install output.apk
```

### Test Multiple Architectures

```bash
# Device info
adb shell getprop ro.product.cpu.abi

# Forces specific architecture
adb install output.apk
```

## Troubleshooting

### Error: "Input APK not found"

```bash
# Make sure file exists
ls -la input.apk

# Use full path if needed
python apk_patcher_advanced.py /full/path/input.apk output.apk
```

### Error: "sign-apk not found"

```bash
# Install it
pip install git+https://github.com/adityatelange/sign-apk-py

# Or run setup again
./setup.sh
```

### APK Installation Fails

- ✅ Ensure you uninstalled the previous version
- ✅ Check device storage space
- ✅ Try on emulator first
- ✅ Check Android version compatibility

### Large File Size

- Normal! Size increase of 5-15% is expected
- Patched libraries and signing metadata add size
- Still fully functional and installable

## Performance Tips

### Speed Up Processing

```bash
# Use fast mode (no verification)
# Add to your command

# Skip intermediate files
# Tool cleans up automatically
```

### For Large APKs (>100MB)

```bash
# Use SSD for temp files
# Ensure 2-3x free disk space

# Monitor progress
python apk_patcher_advanced.py input.apk output.apk -v
```

## Security Notes

### Always Keep Original

```bash
# Make backup
cp original.apk original.apk.backup

# Or use version control
git add original.apk
```

### Signing Key Protection

```bash
# NEVER commit keys to git
echo "*.pem" >> .gitignore
echo "*.p12" >> .gitignore

# Use secure key storage
# - GitHub Secrets
# - GitLab CI/CD Variables
# - Jenkins Credentials
# - HashiCorp Vault
```

### Testing Before Production

```bash
# Test on emulator first
emulator -avd MyEmulator &
adb install output.apk

# Then test on real device
adb -d install output.apk
```

## Next Steps

- 📖 Read [README.md](README.md) for detailed documentation
- 💡 Check [EXAMPLES.md](EXAMPLES.md) for use cases
- 🔧 Explore [Advanced Features](#advanced-features)

## Advanced Features

### Batch Processing

```bash
for apk in *.apk; do
  python apk_patcher_advanced.py "$apk" "patched_$apk"
done
```

### CI/CD Integration

See EXAMPLES.md for:
- GitHub Actions
- GitLab CI
- Jenkins Pipeline

### Python API

```python
from apk_patcher_advanced import UnifiedAPKPatcher

patcher = UnifiedAPKPatcher("input.apk", "output.apk")
patcher.process(key_file="release.pem", cert_file="release.crt")
```

## FAQ

**Q: Do I need Android SDK?**
A: No! This tool is pure Python, no Android SDK required.

**Q: Works with all APKs?**
A: Flutter TLS patch only works on Flutter apps. Network config patch works on all APKs.

**Q: Can I undo patches?**
A: No. Keep the original APK. Patches are permanent.

**Q: Does it require rooted device?**
A: No. Works on any Android device.

**Q: Is this legal?**
A: For authorized testing and analysis, yes. Always get permission first.

## Support & Help

### Getting Help

1. **Check docs first**
   - README.md - Full documentation
   - EXAMPLES.md - Common scenarios
   - This guide - Quick reference

2. **Enable verbose mode**
   ```bash
   python apk_patcher_advanced.py input.apk output.apk -v
   ```

3. **Check individual tools**
   - https://github.com/adityatelange/patch-libflutter-tls
   - https://github.com/adityatelange/patch-netsec-conf
   - https://github.com/adityatelange/sign-apk-py

### Report Issues

Include:
- ✅ Error message (full output)
- ✅ APK size and target SDK
- ✅ Python version: `python --version`
- ✅ OS info: `uname -a` or `ver` (Windows)
- ✅ Output of: `python apk_patcher_advanced.py input.apk output.apk -v`

## Uninstall

If you want to remove the tool:

```bash
# Remove files
rm -rf unified-apk-patcher/

# Remove installed packages
pip uninstall sign-apk-py cryptography
```

## What's Next?

### Learn More

- [Android Security Architecture](https://developer.android.com/security/architecture)
- [Flutter Security Best Practices](https://flutter.dev/docs/deployment/security)
- [APK Signing Guide](https://source.android.com/docs/security/features/apksigning)

### Use Cases

- 🔍 **Security Testing**: Intercept and analyze app traffic
- 🧪 **Quality Assurance**: Test app behavior without network restrictions
- 📊 **Research**: Analyze Flutter app internals
- 🛡️ **Penetration Testing**: Authorized security assessments

### Tools to Pair With

- **Burp Suite**: Network traffic interception
- **Frida**: Runtime hooking and instrumentation
- **Apktool**: APK decompilation and analysis
- **MobSF**: Mobile app security framework
- **Androguard**: Android app analysis

---

## Pro Tips 💡

### Tip 1: Use Environment Variables

```bash
export APK_KEYSTORE="release.p12"
export APK_KEYSTORE_PASSWORD="yourpass"

python apk_patcher_advanced.py app.apk app-patched.apk \
  --keystore $APK_KEYSTORE \
  --keystore-password $APK_KEYSTORE_PASSWORD
```

### Tip 2: Create Aliases

Add to `~/.bashrc` or `~/.zshrc`:

```bash
alias apk-patch='python /path/to/apk_patcher_advanced.py'

# Usage: apk-patch input.apk output.apk
```

### Tip 3: Monitor Tool Updates

```bash
# Check for updates
pip install --upgrade git+https://github.com/adityatelange/sign-apk-py

# Or check releases on GitHub
# https://github.com/adityatelange/sign-apk-py/releases
```

### Tip 4: Create Test Harness

```bash
#!/bin/bash

test_patch() {
    local apk="$1"
    local name="${apk%.apk}"
    
    echo "Testing: $apk"
    python apk_patcher_advanced.py "$apk" "$name-patched.apk" -v
    
    if [ -f "$name-patched.apk" ]; then
        echo "✅ Success!"
        adb install "$name-patched.apk"
    else
        echo "❌ Failed!"
        return 1
    fi
}

test_patch "$1"
```

---

**Ready to patch? Run:**

```bash
python apk_patcher_advanced.py input.apk output.apk
```

**Questions? Check:**
- README.md - Detailed documentation
- EXAMPLES.md - Real-world examples
- Run with `-v` flag for verbose output

---

**Happy patching! 🎉**
