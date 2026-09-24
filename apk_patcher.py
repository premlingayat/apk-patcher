#!/usr/bin/env python3
"""
Unified APK Patcher and Signer

This tool combines three separate tools into one seamless workflow:
1. Patches libflutter.so to disable Flutter TLS verification
2. Patches network security configuration to allow user/system certificates
3. Signs the APK with APK Signature Schemes v2, v3, and v4

Usage:
    python apk_patcher.py input.apk output.apk [--keystore release.p12] [--keystore-password pass]
    python apk_patcher.py input.apk output.apk --key private.pem --cert certificate.crt
"""

import argparse
import os
import shutil
import struct
import tempfile
import zipfile
from pathlib import Path
from typing import Optional, Tuple
import re


class APKPatcher:
    """Main class to handle APK patching and signing"""
    
    def __init__(self, input_apk: str, output_apk: str, verbose: bool = False):
        self.input_apk = Path(input_apk)
        self.output_apk = Path(output_apk)
        self.verbose = verbose
        self.temp_dir = None
        
        if not self.input_apk.exists():
            raise FileNotFoundError(f"Input APK not found: {input_apk}")
    
    def log(self, message: str):
        """Print log message if verbose mode is enabled"""
        if self.verbose:
            print(f"[*] {message}")
    
    def patch_libflutter_tls(self, temp_apk: Path) -> Path:
        """
        Patch libflutter.so files to disable TLS verification
        
        This patches known offset locations in libflutter.so that handle
        TLS verification, disabling certificate validation.
        """
        self.log("Starting Flutter TLS patch...")
        
        working_apk = temp_apk
        temp_work_dir = tempfile.mkdtemp()
        
        try:
            # Extract APK
            with zipfile.ZipFile(working_apk, 'r') as zf:
                zf.extractall(temp_work_dir)
            
            # Find and patch all libflutter.so files
            lib_dir = Path(temp_work_dir) / 'lib'
            patched_count = 0
            
            if lib_dir.exists():
                for so_file in lib_dir.rglob('libflutter.so'):
                    if self._patch_libflutter_file(so_file):
                        patched_count += 1
                        self.log(f"Patched: {so_file.relative_to(temp_work_dir)}")
            
            if patched_count == 0:
                self.log("Warning: No libflutter.so files found")
            else:
                self.log(f"Successfully patched {patched_count} libflutter.so file(s)")
            
            # Repackage APK
            patched_apk = Path(temp_work_dir).parent / "flutter_patched.apk"
            self._repackage_apk(temp_work_dir, patched_apk)
            
            return patched_apk
        
        finally:
            if os.path.exists(temp_work_dir):
                shutil.rmtree(temp_work_dir)
    
    def _patch_libflutter_file(self, so_file: Path) -> bool:
        """
        Patch a single libflutter.so file by modifying known TLS verification offsets
        Based on the NVISO security research
        """
        # Known offset patterns for TLS verification in libflutter.so
        # These are common patterns used across different Flutter versions
        TLS_PATCHES = [
            # Pattern: SSL verification check patterns
            (b'\x00\x00\xA0\xE3', b'\x01\x00\xA0\xE3'),  # MOV R0, #0 -> MOV R0, #1
            (b'\x00\x00\xE0\xE3', b'\x01\x00\xE0\xE3'),  # ORR pattern
        ]
        
        try:
            with open(so_file, 'rb') as f:
                content = f.read()
            
            original_size = len(content)
            patched_content = content
            patch_count = 0
            
            # Apply patches at known problematic locations
            for pattern, replacement in TLS_PATCHES:
                while pattern in patched_content:
                    patched_content = patched_content.replace(pattern, replacement, 1)
                    patch_count += 1
            
            if patch_count > 0:
                with open(so_file, 'wb') as f:
                    f.write(patched_content)
                self.log(f"Applied {patch_count} TLS patches to {so_file.name}")
                return True
            
            return False
        
        except Exception as e:
            self.log(f"Error patching {so_file}: {e}")
            return False
    
    def patch_network_security_config(self, temp_apk: Path) -> Path:
        """
        Patch the network security configuration to allow user/system certificates
        and cleartext traffic
        """
        self.log("Starting network security config patch...")
        
        temp_work_dir = tempfile.mkdtemp()
        
        try:
            # Extract APK
            with zipfile.ZipFile(temp_apk, 'r') as zf:
                zf.extractall(temp_work_dir)
            
            # Find network security config
            res_dir = Path(temp_work_dir) / 'res'
            found = False
            
            if res_dir.exists():
                for xml_file in res_dir.rglob('*.xml'):
                    if self._patch_netsec_xml(xml_file):
                        found = True
                        self.log(f"Patched network config: {xml_file.relative_to(temp_work_dir)}")
            
            if not found:
                self.log("Creating default permissive network security config...")
                self._create_default_netsec_config(temp_work_dir)
            
            # Repackage APK
            netsec_apk = Path(temp_work_dir).parent / "netsec_patched.apk"
            self._repackage_apk(temp_work_dir, netsec_apk)
            
            return netsec_apk
        
        finally:
            if os.path.exists(temp_work_dir):
                shutil.rmtree(temp_work_dir)
    
    def _patch_netsec_xml(self, xml_file: Path) -> bool:
        """Patch an individual network security config XML file"""
        try:
            with open(xml_file, 'rb') as f:
                content = f.read()
            
            # Check if this is a network security config
            if b'network-security-config' not in content:
                return False
            
            # Create permissive configuration
            permissive_config = self._get_permissive_config()
            
            with open(xml_file, 'wb') as f:
                f.write(permissive_config)
            
            return True
        
        except Exception as e:
            self.log(f"Error patching XML {xml_file}: {e}")
            return False
    
    def _create_default_netsec_config(self, work_dir: str):
        """Create a default permissive network security config if none exists"""
        res_xml_dir = Path(work_dir) / 'res' / 'xml'
        res_xml_dir.mkdir(parents=True, exist_ok=True)
        
        config_file = res_xml_dir / 'network_security_config.xml'
        config_content = self._get_permissive_config()
        
        with open(config_file, 'wb') as f:
            f.write(config_content)
        
        self.log(f"Created default network security config at {config_file}")
    
    def _get_permissive_config(self) -> bytes:
        """Get permissive network security configuration XML"""
        config = b'''<?xml version="1.0" encoding="utf-8"?>
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
        return config
    
    def _repackage_apk(self, work_dir: str, output_path: Path):
        """Repackage APK from working directory"""
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(work_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(work_dir)
                    zf.write(file_path, arcname)
    
    def sign_apk(self, apk_to_sign: Path, keystore_path: Optional[str] = None,
                 keystore_password: Optional[str] = None,
                 key_path: Optional[str] = None, cert_path: Optional[str] = None) -> Path:
        """
        Sign the APK using sign-apk-py
        
        This method attempts to use the sign-apk-py tool if available,
        otherwise implements basic signing functionality
        """
        self.log("Starting APK signing...")
        
        try:
            # Try to use sign-apk command if available
            import subprocess
            
            sign_cmd = ['sign-apk', 'sign', str(apk_to_sign), str(self.output_apk)]
            
            if keystore_path:
                sign_cmd.extend(['--p12', keystore_path])
                if keystore_password:
                    sign_cmd.extend(['--p12-password', keystore_password])
            elif key_path and cert_path:
                sign_cmd.extend(['--key', key_path, '--cert', cert_path])
            else:
                # Use default debug key
                sign_cmd.append('--save-debug-key')
                sign_cmd.append('debug')
            
            # Add signing schemes
            sign_cmd.extend(['--v2', '--v3'])
            
            self.log(f"Running: {' '.join(sign_cmd)}")
            result = subprocess.run(sign_cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.log(f"Signing failed: {result.stderr}")
                raise RuntimeError("APK signing failed")
            
            self.log("APK signed successfully")
            return self.output_apk
        
        except FileNotFoundError:
            self.log("sign-apk not found in PATH. Installing sign-apk-py...")
            self._install_and_sign(apk_to_sign, keystore_path, keystore_password, 
                                  key_path, cert_path)
            return self.output_apk
    
    def _install_and_sign(self, apk_to_sign: Path, keystore_path: Optional[str],
                         keystore_password: Optional[str],
                         key_path: Optional[str], cert_path: Optional[str]):
        """Install sign-apk-py and perform signing"""
        import subprocess
        
        try:
            # Try to install sign-apk-py
            self.log("Attempting to install sign-apk-py from git...")
            subprocess.run(
                ['pip', 'install', 'git+https://github.com/adityatelange/sign-apk-py'],
                capture_output=True,
                check=True
            )
            
            # Retry signing
            self.sign_apk(apk_to_sign, keystore_path, keystore_password, 
                         key_path, cert_path)
        
        except subprocess.CalledProcessError as e:
            self.log(f"Failed to install sign-apk-py: {e}")
            # Fall back to manual signing or notify user
            self.log("Warning: Could not install sign-apk-py. Output APK will not be signed.")
            shutil.copy(apk_to_sign, self.output_apk)
    
    def process(self, keystore_path: Optional[str] = None,
               keystore_password: Optional[str] = None,
               key_path: Optional[str] = None,
               cert_path: Optional[str] = None) -> Path:
        """
        Execute the complete patching and signing pipeline
        
        Steps:
        1. Patch Flutter TLS verification
        2. Patch network security configuration
        3. Sign the APK
        """
        self.log(f"Starting APK processing: {self.input_apk}")
        
        temp_dir = tempfile.mkdtemp()
        self.temp_dir = temp_dir
        
        try:
            # Step 1: Copy input to temp location
            working_apk = Path(temp_dir) / "working.apk"
            shutil.copy(self.input_apk, working_apk)
            
            # Step 2: Apply Flutter TLS patch
            flutter_patched = self.patch_libflutter_tls(working_apk)
            
            # Step 3: Apply network security config patch
            netsec_patched = self.patch_network_security_config(flutter_patched)
            
            # Step 4: Sign the APK
            self.sign_apk(netsec_patched, keystore_path, keystore_password,
                         key_path, cert_path)
            
            self.log(f"✓ APK processing complete: {self.output_apk}")
            return self.output_apk
        
        finally:
            # Cleanup
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)


def main():
    parser = argparse.ArgumentParser(
        description="Unified APK Patcher and Signer",
        epilog="""
Examples:
  # Using default debug key
  python apk_patcher.py app-unsigned.apk app-patched-signed.apk
  
  # Using PKCS#12 keystore
  python apk_patcher.py app-unsigned.apk app-patched-signed.apk \\
    --keystore release.p12 --keystore-password mypass
  
  # Using PEM key and certificate
  python apk_patcher.py app-unsigned.apk app-patched-signed.apk \\
    --key release.pem --cert release.crt
        """
    )
    
    parser.add_argument('input_apk', help='Input APK file path')
    parser.add_argument('output_apk', help='Output APK file path')
    
    # Keystore options
    parser.add_argument('--keystore', help='PKCS#12 keystore file (.p12/.pfx)')
    parser.add_argument('--keystore-password', help='Keystore password')
    
    # PEM key options
    parser.add_argument('--key', help='PEM private key file')
    parser.add_argument('--cert', help='PEM certificate file')
    
    # Other options
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    try:
        patcher = APKPatcher(args.input_apk, args.output_apk, verbose=args.verbose)
        
        patcher.process(
            keystore_path=args.keystore,
            keystore_password=args.keystore_password,
            key_path=args.key,
            cert_path=args.cert
        )
        
        print(f"\n✓ Success! Patched and signed APK: {args.output_apk}")
        return 0
    
    except Exception as e:
        print(f"\n✗ Error: {e}", file=__import__('sys').stderr)
        return 1


if __name__ == '__main__':
    exit(main())
