# Unified APK Patcher & Signer

A comprehensive, production-ready tool that combines three essential APK modification tools into a single, seamless workflow:

1. **Flutter TLS Patching** (`patch-libflutter-tls`) - Disables Flutter's TLS certificate verification
2. **Network Security Config Patching** (`patch-netsec-conf`) - Allows user/system certificates and cleartext traffic
3. **APK Signing** (`sign-apk-py`) - Signs APK with v2, v3, and v4 signature schemes

## Features

✨ **One-Command Processing**: Execute all three operations in sequence with a single command

🔒 **Multiple Signing Methods**:
- Auto-generated debug keys
- PKCS#12 keystores (.p12/.pfx)
- PEM key + certificate pairs

📦 **Non-Destructive**: Creates intermediate patched copies, preserves original

🔍 **Comprehensive Logging**: Verbose mode shows detailed information about each step

⚡ **Automatic Installation**: Installs required dependencies if not available

## Prerequisites

- Python 3.9+
- `pip` (Python package manager)
- Optional: `sign-apk-py` for signing (auto-installed if needed)

## Installation

### Install from GitHub with uv

After pushing this repository to GitHub, install the command on another machine:

```bash
uv tool install git+https://github.com/premlingayat/apk-patcher.git
apk-patcher --help
```

To update an existing installation:

```bash
uv tool upgrade unified-apk-patcher
```

`uv` installs this project and its three upstream dependencies into an isolated
environment. Internet access is required when installing or upgrading.

### Option 1: Direct Usage (Recommended)

```bash
# Clone or download the files
cd /path/to/unified-apk-patcher

# Install required dependencies for direct script usage
pip install -r requirements.txt
```

### Option 2: As a Python Module

```bash
# Make executable
chmod +x apk_patcher_advanced.py

# Add to PATH (optional)
export PATH=$PATH:/path/to/unified-apk-patcher
```

## Quick Start

### Basic Usage (Default Debug Key)

```bash
apk-patcher input.apk output.apk

# Or run directly from a clone
python apk_patcher_advanced.py input.apk output.apk
```

### Using PKCS#12 Keystore

```bash
python apk_patcher_advanced.py input.apk output.apk \
  --keystore release.p12 \
  --keystore-password yourpassword
```

### Using PEM Key & Certificate

```bash
python apk_patcher_advanced.py input.apk output.apk \
  --key private_key.pem \
  --cert certificate.crt
```

### Verbose Output

```bash
python apk_patcher_advanced.py input.apk output.apk -v
```

## Detailed Usage Guide

### Step-by-Step Process

The tool performs the following operations automatically:

#### 1. Flutter TLS Patching
- Locates all `libflutter.so` files (across arm64-v8a, armeabi-v7a, x86_64, x86)
- Uses the upstream patcher, preserving APK archive structure and alignment

#### 2. Network Security Configuration Patching
- Finds the configured resource, including obfuscated and binary Android XML
- Uses the upstream patcher to replace it with a permissive configuration:
  - Allows cleartext (HTTP) traffic
  - Trusts system certificates
  - Trusts user-installed certificates
- Creates default config if none exists
- Repackages APK

#### 3. APK Signing
- Signs the APK with the schemes supported by `sign-apk-py`
- Uses provided keystore or generates debug key
- Verifies the result with `apksigner` when it is installed

### Signing Options

#### Option A: Auto-Generated Debug Key (Default)
```bash
python apk_patcher_advanced.py input.apk output.apk
```
- Generates throwaway debug key on-the-fly
- No key management required
- Suitable for development/testing

#### Option B: Reusable Debug Key
```bash
# First run - save debug key
python apk_patcher_advanced.py input.apk output.apk \
  --save-debug-key debug

# Subsequent runs - reuse saved key
python apk_patcher_advanced.py another.apk output2.apk \
  --key debug.pem --cert debug.crt
```

#### Option C: Production Release Key (PKCS#12)
```bash
python apk_patcher_advanced.py input.apk output.apk \
  --keystore release.p12 \
  --keystore-password "${KEYSTORE_PASSWORD}"
```

#### Option D: Production Release Key (PEM)
```bash
python apk_patcher_advanced.py input.apk output.apk \
  --key release_private.pem \
  --cert release_certificate.crt
```

### Generating Your Own Keys

#### Generate PEM Key & Certificate
```bash
python apk_patcher_advanced.py generate-key \
  release_private.pem release_certificate.crt \
  --common-name "My Company" \
  --key-size 2048
```

#### Convert PEM to PKCS#12
```bash
openssl pkcs12 -export \
  -in release_certificate.crt \
  -inkey release_private.pem \
  -out release.p12 \
  -name "my-release-key"
```

## API Reference

### Command-Line Arguments

```
positional arguments:
  input_apk             Input APK file path
  output_apk            Output patched and signed APK file path

optional arguments:
  --keystore PATH       PKCS#12 keystore file (.p12/.pfx)
  --keystore-password PASSWORD
                        Keystore password (prompted if omitted)
  --key PATH            PEM private key file
  --cert PATH           PEM certificate file
  -v, --verbose         Enable verbose output
  -h, --help            Show help message
```

### Python API

```python
from apk_patcher_advanced import UnifiedAPKPatcher

# Create patcher instance
patcher = UnifiedAPKPatcher("input.apk", "output.apk", verbose=True)

# Process APK
success = patcher.process(
    keystore="release.p12",
    keystore_password="mypassword"
)

if success:
    print("✅ Patching complete!")
else:
    print("❌ Patching failed!")
```

## Publishing Safely

Do not commit APKs, private keys, certificates, or keystores. The included
`.gitignore` excludes common APK and signing-key extensions. Before pushing,
inspect the files that will be published:

```bash
git status
git add .
git diff --cached --stat
```

## Output

### Success Output

```
============================================================
  UNIFIED APK PATCHER & SIGNER
============================================================
Input:  /path/to/input.apk
Output: /path/to/output.apk

📱 Step 1: Patching Flutter TLS Verification...
   └─ Found: 1 libraries
   └─ Patched: 1 files

🔐 Step 2: Patching Network Security Configuration...
   └─ Patched: 1 configs

✍️  Step 3: Signing APK...
   └─ Signature: v2, v3

============================================================
✅ SUCCESS! Processing complete
============================================================
Output APK: /path/to/output.apk
Size: 45.23 MB
```

### Error Handling

The tool provides clear error messages for common issues:

```
❌ ERROR: Input APK not found: /path/to/nonexistent.apk
```

## Advanced Features

### Batch Processing

Process multiple APKs in sequence:

```bash
#!/bin/bash

for apk in *.apk; do
  output="${apk%.apk}_patched.apk"
  echo "Processing: $apk -> $output"
  python apk_patcher_advanced.py "$apk" "$output" -v
done
```

### CI/CD Integration

#### GitHub Actions Example

```yaml
name: Patch APKs

on: [push]

jobs:
  patch:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Patch and sign APK
        run: |
          python apk_patcher_advanced.py \
            build/app.apk \
            build/app-patched.apk \
            --keystore ${{ secrets.KEYSTORE_PATH }} \
            --keystore-password ${{ secrets.KEYSTORE_PASSWORD }}
      
      - name: Upload artifact
        uses: actions/upload-artifact@v2
        with:
          name: patched-apk
          path: build/app-patched.apk
```

#### Jenkins Pipeline Example

```groovy
pipeline {
    agent any
    
    stages {
        stage('Patch APK') {
            steps {
                sh '''
                    python apk_patcher_advanced.py \
                        ${WORKSPACE}/app.apk \
                        ${WORKSPACE}/app-patched.apk \
                        --keystore ${KEYSTORE} \
                        --keystore-password ${KEYSTORE_PASSWORD} \
                        -v
                '''
            }
        }
    }
}
```

## Troubleshooting

### Issue: "sign-apk not found"

**Solution**: The tool will attempt to install it automatically. If that fails:

```bash
pip install git+https://github.com/adityatelange/sign-apk-py
```

### Issue: "libflutter.so files not found"

**Possible causes**:
- APK doesn't contain Flutter libraries (e.g., Flutter web app)
- Different architecture than expected

**Solution**: Use verbose mode to debug:

```bash
python apk_patcher_advanced.py input.apk output.apk -v
```

### Issue: "Network security config not found"

**Solution**: The tool automatically creates a default permissive config. This is safe and expected for many apps.

### Issue: Signing fails with PKCS#12

**Possible causes**:
- Wrong password
- Corrupted keystore file

**Solution**: Verify keystore:

```bash
openssl pkcs12 -in release.p12 -passin pass:yourpassword -noout
```

### Issue: APK too large after patching

**Note**: Size increase is normal due to:
- Patched libraries
- Recompressed contents
- Signing metadata

**Solution**: APK is still installable and functional. If size is critical, use app bundle format instead.

## Comparison to Manual Process

### Before (Manual - 3 separate tools)

```bash
# 1. Flutter TLS patch
python patch_libflutter_tls.py app.apk
mv app_patched.apk temp.apk

# 2. Network security patch
patch-netsec-conf temp.apk
mv temp_nons.apk temp2.apk

# 3. Sign APK
sign-apk sign temp2.apk app-final.apk --key release.pem --cert release.crt

# 4. Cleanup
rm temp.apk temp2.apk
```

### After (Unified - Single command)

```bash
python apk_patcher_advanced.py app.apk app-final.apk \
  --key release.pem --cert release.crt
```

## Performance

- **Processing Speed**: Depends on APK size and system
- **Typical Times**:
  - 20-50 MB APK: 5-10 seconds
  - 50-100 MB APK: 10-20 seconds
  - 100+ MB APK: 20-60 seconds

## Security Considerations

⚠️ **Important**: This tool is for:
- Authorized security testing
- App analysis and reverse engineering (with permission)
- Development and debugging

**Do NOT use** to:
- Modify apps you don't own
- Bypass security for malicious purposes
- Distribute patched apps without permission

## License & Attribution

This tool integrates work from:
- `patch-libflutter-tls`: Based on NVISO security research
- `patch-netsec-conf`: Original by @adityatelange
- `sign-apk-py`: Original by @adityatelange

See individual project licenses for details.

## Contributing

Found a bug? Have a feature request?

1. Test with verbose mode: `python apk_patcher_advanced.py input.apk output.apk -v`
2. Share the error message
3. Include APK details (size, target SDK, architecture)

## Support

### Getting Help

1. **Check troubleshooting section**: Most common issues are documented
2. **Verbose mode**: Run with `-v` for detailed output
3. **Individual tools**: If you need specific functionality, use the original tools:
   - `pip install git+https://github.com/adityatelange/patch-libflutter-tls`
   - `pip install git+https://github.com/adityatelange/patch-netsec-conf`
   - `pip install git+https://github.com/adityatelange/sign-apk-py`

## Changelog

### Version 1.0.0
- ✨ Initial release
- 🔧 Full integration of three tools
- 📦 Automatic dependency management
- 🔐 Multiple signing key support
- 📝 Comprehensive documentation

## FAQ

**Q: Can I use this on any APK?**
A: Yes, but Flutter patching only affects Flutter apps. Network security patching works on all APKs.

**Q: Will the patched APK work on Google Play?**
A: No. Google Play requires original signatures. Patched APKs only work for testing/analysis on real devices or emulators.

**Q: Does this require root?**
A: No. But some features (like traffic interception) may require rooted device or proxy configuration.

**Q: Can I undo the patches?**
A: No. Always keep the original APK. Patches are permanent to the APK file.

**Q: Is this legal?**
A: For authorized testing and analysis of your own apps, yes. Always ensure you have permission.

## Resources

- [Flutter Security](https://flutter.dev/docs/deployment/security)
- [Android Network Security Config](https://developer.android.com/training/articles/security-config)
- [APK Signing Overview](https://source.android.com/docs/security/features/apksigning)
- [NVISO Security Research](https://github.com/NVISOsecurity)

---

**Created**: 2024
**Status**: Active
**Maintainer**: Combined from Aditya Telange's original tools
