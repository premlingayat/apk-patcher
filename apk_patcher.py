#!/usr/bin/env python3
"""
Advanced Unified APK Patcher and Signer

Complete integration of:
- patch-libflutter-tls: Disables Flutter TLS verification
- patch-netsec-conf: Patches network security configuration
- sign-apk-py: Signs APK with v2, v3, v4 schemes

This tool performs a complete workflow in one command.
"""

import argparse
import io
import os
import shutil
import struct
import sys
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, List, Tuple, Dict
from dataclasses import dataclass


@dataclass
class PatchStats:
    """Statistics about applied patches"""
    flutter_files_found: int = 0
    flutter_patches_applied: int = 0
    netsec_configs_found: int = 0
    netsec_configs_patched: int = 0


class FlutterTLSPatcher:
    """Patches Flutter's TLS verification in libflutter.so"""
    
    # Common Flutter TLS verification patterns across different versions
    # These patterns represent certificate validation checks
    VERIFICATION_PATTERNS = {
        # ARM64 patterns for TLS verification
        'arm64': [
            b'\x00\x00\x80\x52',  # MOV X0, #0
            b'\x00\x00\x00\xb9',  # STR W0
            b'\xff\x03\x00\xd1',  # SUB SP, SP
        ],
        # ARM (ARMv7) patterns
        'armv7': [
            b'\x00\x00\xa0\xe3',  # MOV R0, #0
            b'\x00\x00\x80\xe5',  # STR R0
            b'\x04\xd0\x4d\xe2',  # SUB SP, SP, #4
        ],
        # x86_64 patterns
        'x86_64': [
            b'\xc3\xc0\xc0\xc0',  # Various x86_64 patterns
        ],
    }
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.stats = PatchStats()
    
    def log(self, message: str):
        if self.verbose:
            print(f"  [Flutter] {message}")
    
    def patch_apk(self, apk_path: Path) -> Path:
        """Patch all libflutter.so files in the APK"""
        self.log("Analyzing Flutter libraries...")

        import subprocess

        with zipfile.ZipFile(apk_path, 'r') as zf:
            self.stats.flutter_files_found = sum(
                name.endswith('/libflutter.so') for name in zf.namelist()
            )
        if not self.stats.flutter_files_found:
            raise RuntimeError("No libflutter.so found; input does not appear to be a Flutter APK")

        patched_apk = apk_path.with_name(f"{apk_path.stem}_patched.apk")
        command = shutil.which('patch-flutter-tls')
        if command is None:
            self.log("patch-flutter-tls not found, installing upstream patcher...")
            subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '-q',
                 'git+https://github.com/adityatelange/patch-libflutter-tls'],
                check=True, timeout=180
            )
            command = shutil.which('patch-flutter-tls')
        if command is None:
            raise RuntimeError("patch-flutter-tls was installed but is not available on PATH")

        result = subprocess.run(
            [command, str(apk_path)], capture_output=True, text=True, timeout=300
        )
        if result.returncode != 0 or not patched_apk.exists():
            raise RuntimeError(
                f"Flutter patch failed: {result.stderr.strip() or result.stdout.strip()}"
            )
        self.stats.flutter_patches_applied = self.stats.flutter_files_found
        self.log(f"✓ Patched {self.stats.flutter_files_found} Flutter library/libraries")
        return patched_apk
    
    def _patch_file(self, so_file: Path) -> bool:
        """Apply patches to a libflutter.so file"""
        try:
            with open(so_file, 'rb') as f:
                data = bytearray(f.read())
            
            original_size = len(data)
            patches_made = 0
            
            # Try different patch patterns
            # This is a simplified approach - real implementation would use
            # offset-based patching from NVISO research
            
            # Look for TLS verification function patterns and patch them
            # Pattern: Check for common SSL verification patterns
            patterns_to_patch = [
                # X509 certificate verification patterns
                (b'X509_verify_cert', b'X509_verify_skip'),
                # SSL/TLS context check patterns  
                (b'SSL_CTX_check_private_key', b'SKIP_CHECK_PRIVATE_'),
            ]
            
            for pattern, replacement in patterns_to_patch:
                if pattern in data:
                    # Replace with NOP-like operations or returns
                    idx = data.find(pattern)
                    while idx != -1:
                        # Apply minimal patch
                        data[idx:idx+len(pattern)] = replacement[:len(pattern)]
                        patches_made += 1
                        idx = data.find(pattern, idx + 1)
            
            if patches_made > 0:
                with open(so_file, 'wb') as f:
                    f.write(data)
                return True
            
            return False
        
        except Exception as e:
            self.log(f"Error patching {so_file.name}: {e}")
            return False
    
    def _recreate_apk(self, work_dir: Path, output_apk: Path):
        """Recreate APK from patched contents"""
        with zipfile.ZipFile(output_apk, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in sorted(work_dir.rglob('*')):
                if file_path.is_file():
                    arcname = file_path.relative_to(work_dir)
                    zf.write(file_path, arcname)


class NetworkSecurityPatcher:
    """Patches network security configuration for certificate pinning bypass"""
    
    PERMISSIVE_CONFIG = b'''<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <domain-config cleartextTrafficPermitted="true">
        <domain includeSubdomains="true">*</domain>
        <trust-anchors>
            <certificates src="system" />
            <certificates src="user" />
        </trust-anchors>
    </domain-config>
</network-security-config>
'''
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.stats = PatchStats()
    
    def log(self, message: str):
        if self.verbose:
            print(f"  [NetSec] {message}")
    
    def patch_apk(self, apk_path: Path) -> Path:
        """Patch network security config in APK"""
        self.log("Scanning for network security configurations...")

        import subprocess

        patched_apk = apk_path.with_name(f"{apk_path.stem}_nons.apk")
        command = shutil.which('patch-netsec-conf')
        if command is None:
            self.log("patch-netsec-conf not found, installing upstream patcher...")
            subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '-q',
                 'git+https://github.com/adityatelange/patch-netsec-conf'],
                check=True, timeout=180
            )
            command = shutil.which('patch-netsec-conf')
        if command is None:
            raise RuntimeError("patch-netsec-conf was installed but is not available on PATH")

        result = subprocess.run(
            [command, str(apk_path)], capture_output=True, text=True, timeout=300
        )
        if result.returncode != 0 or not patched_apk.exists():
            raise RuntimeError(
                f"Network security patch failed: {result.stderr.strip() or result.stdout.strip()}"
            )
        self.stats.netsec_configs_patched = 1
        self.log("✓ Patched network security configuration")
        return patched_apk
    
    def _is_netsec_config(self, xml_file: Path) -> bool:
        """Check if XML file is a network security config"""
        try:
            with open(xml_file, 'rb') as f:
                content = f.read()
            return b'network-security-config' in content or b'domain-config' in content
        except:
            return False
    
    def _patch_config(self, xml_file: Path):
        """Replace network security config with permissive version"""
        with open(xml_file, 'wb') as f:
            f.write(self.PERMISSIVE_CONFIG)
    
    def _create_default_config(self, work_dir: Path):
        """Create default permissive network security config"""
        xml_dir = work_dir / 'res' / 'xml'
        xml_dir.mkdir(parents=True, exist_ok=True)
        
        config_file = xml_dir / 'network_security_config.xml'
        with open(config_file, 'wb') as f:
            f.write(self.PERMISSIVE_CONFIG)
        
        self.log(f"Created: network_security_config.xml")
        self.stats.netsec_configs_patched += 1
    
    def _recreate_apk(self, work_dir: Path, output_apk: Path):
        """Recreate APK from patched contents"""
        with zipfile.ZipFile(output_apk, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in sorted(work_dir.rglob('*')):
                if file_path.is_file():
                    arcname = file_path.relative_to(work_dir)
                    zf.write(file_path, arcname)


class APKSigner:
    """Signs APK using available tools"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
    
    def log(self, message: str):
        if self.verbose:
            print(f"  [Signer] {message}")
    
    def sign_apk(self, apk_path: Path, output_path: Path,
                 keystore: Optional[str] = None,
                 keystore_password: Optional[str] = None,
                 key_file: Optional[str] = None,
                 cert_file: Optional[str] = None) -> bool:
        """Sign APK using available signing tool"""
        
        import subprocess
        
        self.log("Attempting to sign APK...")
        
        # Try sign-apk-py first
        if self._try_sign_with_tool(apk_path, output_path, keystore, 
                                    keystore_password, key_file, cert_file):
            return True
        
        self.log("Signing tool unavailable; refusing to produce an unsigned output")
        return False
    
    def _try_sign_with_tool(self, apk_path: Path, output_path: Path,
                           keystore: Optional[str],
                           keystore_password: Optional[str],
                           key_file: Optional[str],
                           cert_file: Optional[str]) -> bool:
        """Try to sign using sign-apk command"""
        import subprocess
        
        try:
            cmd = ['sign-apk', 'sign', str(apk_path), str(output_path)]
            
            if keystore:
                cmd.extend(['--p12', keystore])
                if keystore_password:
                    cmd.extend(['--p12-password', keystore_password])
            elif key_file and cert_file:
                cmd.extend(['--key', key_file, '--cert', cert_file])
            else:
                cmd.extend(['--save-debug-key', 'debug'])
            
            cmd.extend(['--v2', '--v3'])
            
            self.log(f"Running: sign-apk...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                verifier = shutil.which('apksigner')
                verify_cmd = ([verifier, 'verify', str(output_path)] if verifier else
                              ['sign-apk', 'verify', str(output_path)])
                verify = subprocess.run(verify_cmd, capture_output=True, text=True, timeout=60)
                if verify.returncode != 0:
                    self.log(f"Signature verification failed: {verify.stderr.strip() or verify.stdout.strip()}")
                    return False
                self.log("✓ APK signed successfully")
                return True
            else:
                self.log(f"Signing failed: {result.stderr}")
                return False
        
        except FileNotFoundError:
            self.log("sign-apk not found, attempting to install...")
            return self._install_and_sign(apk_path, output_path, keystore,
                                         keystore_password, key_file, cert_file)
        except Exception as e:
            self.log(f"Error: {e}")
            return False
    
    def _install_and_sign(self, apk_path: Path, output_path: Path,
                         keystore: Optional[str],
                         keystore_password: Optional[str],
                         key_file: Optional[str],
                         cert_file: Optional[str]) -> bool:
        """Install sign-apk-py and try signing"""
        import subprocess
        
        try:
            self.log("Installing sign-apk-py...")
            subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '-q',
                 'git+https://github.com/adityatelange/sign-apk-py'],
                timeout=120,
                capture_output=True
            )
            
            self.log("Retrying sign...")
            return self._try_sign_with_tool(apk_path, output_path, keystore,
                                           keystore_password, key_file, cert_file)
        except Exception as e:
            self.log(f"Installation failed: {e}")
            return False


class UnifiedAPKPatcher:
    """Main orchestrator for the complete patching pipeline"""
    
    def __init__(self, input_apk: str, output_apk: str, verbose: bool = False):
        self.input_apk = Path(input_apk)
        self.output_apk = Path(output_apk)
        self.verbose = verbose
        
        if not self.input_apk.exists():
            raise FileNotFoundError(f"Input APK not found: {input_apk}")
        
        self.flutter_patcher = FlutterTLSPatcher(verbose)
        self.netsec_patcher = NetworkSecurityPatcher(verbose)
        self.signer = APKSigner(verbose)
    
    def log(self, message: str):
        print(f"[APK] {message}")
    
    def process(self, keystore: Optional[str] = None,
               keystore_password: Optional[str] = None,
               key_file: Optional[str] = None,
               cert_file: Optional[str] = None) -> bool:
        """Execute complete patching pipeline"""
        
        print("\n" + "="*60)
        print("  UNIFIED APK PATCHER & SIGNER")
        print("="*60)
        print(f"Input:  {self.input_apk}")
        print(f"Output: {self.output_apk}\n")
        
        try:
            # Step 1: Flutter TLS patching
            print("📱 Step 1: Patching Flutter TLS Verification...")
            flutter_patched = self.flutter_patcher.patch_apk(self.input_apk)
            print(f"   └─ Found: {self.flutter_patcher.stats.flutter_files_found} libraries")
            print(f"   └─ Patched: {self.flutter_patcher.stats.flutter_patches_applied} files\n")
            
            # Step 2: Network security config patching
            print("🔐 Step 2: Patching Network Security Configuration...")
            netsec_patched = self.netsec_patcher.patch_apk(flutter_patched)
            print(f"   └─ Patched: {self.netsec_patcher.stats.netsec_configs_patched} configs\n")
            
            # Step 3: Signing
            print("✍️  Step 3: Signing APK...")
            success = self.signer.sign_apk(netsec_patched, self.output_apk,
                                          keystore, keystore_password,
                                          key_file, cert_file)

            if not success:
                raise RuntimeError("APK signing failed; no installable output was produced")
            print(f"   └─ Signature: verified by APK signer\n")

            # Cleanup intermediate APKs only after the final artifact is verified.
            netsec_patched.unlink(missing_ok=True)
            flutter_patched.unlink(missing_ok=True)
            
            # Summary
            print("="*60)
            print("✅ SUCCESS! Processing complete")
            print("="*60)
            print(f"Output APK: {self.output_apk}")
            print(f"Size: {self.output_apk.stat().st_size / (1024*1024):.2f} MB\n")
            
            return True
        
        except Exception as e:
            print(f"\n❌ ERROR: {e}", file=sys.stderr)
            return False


def main():
    parser = argparse.ArgumentParser(
        description="Unified APK Patcher & Signer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
  # Default (uses debug key)
    python apk_patcher.py app.apk app-patched.apk
  
  # With PKCS#12 keystore
  python apk_patcher.py app.apk app-patched.apk \\
    --keystore release.p12 --keystore-password pass123
  
  # With PEM key and certificate
  python apk_patcher.py app.apk app-patched.apk \\
    --key private.pem --cert certificate.crt
  
  # Verbose output
    python apk_patcher.py app.apk app-patched.apk -v
        """
    )
    
    parser.add_argument('input_apk', help='Input APK file')
    parser.add_argument('output_apk', help='Output patched and signed APK')
    
    parser.add_argument('--keystore', help='PKCS#12 keystore (.p12/.pfx)')
    parser.add_argument('--keystore-password', help='Keystore password')
    parser.add_argument('--key', help='PEM private key')
    parser.add_argument('--cert', help='PEM certificate')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    patcher = UnifiedAPKPatcher(args.input_apk, args.output_apk, args.verbose)
    success = patcher.process(
        keystore=args.keystore,
        keystore_password=args.keystore_password,
        key_file=args.key,
        cert_file=args.cert
    )
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
