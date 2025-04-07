import subprocess
import sys
import os
from pathlib import Path

def create_exe():
    # Verify PyInstaller is installed
    try:
        subprocess.run(['pyinstaller', '--version'], capture_output=True, text=True)
    except FileNotFoundError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
    
    # Get the current working directory
    current_dir = os.getcwd()
    
    # Setup paths
    icon_path = os.path.join(current_dir, 'assets', 'icon.ico')
    launcher_path = os.path.join(current_dir, 'launcher.py')
    main_path = os.path.join(current_dir, 'main.py')
    
    # Print paths for debugging
    print(f"Looking for icon at: {icon_path}")
    print(f"Looking for launcher at: {launcher_path}")
    print(f"Looking for main at: {main_path}")
    
    # Verify paths exist
    if not os.path.exists(launcher_path):
        print(f"Launcher script not found at {launcher_path}")
        return
    if not os.path.exists(main_path):
        print(f"Main script not found at {main_path}")
        return

    # Create a manifest file for admin privileges
    manifest_content = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
    <security>
      <requestedPrivileges>
        <requestedExecutionLevel level="requireAdministrator" uiAccess="false"/>
      </requestedPrivileges>
    </security>
  </trustInfo>
</assembly>"""

    # Write manifest file
    manifest_path = os.path.join(current_dir, 'uac_manifest.manifest')
    with open(manifest_path, 'w') as f:
        f.write(manifest_content)

    # PyInstaller command
    pyinstaller_cmd = [
        'pyinstaller',
        '--onefile',
        '--noconsole',  # Add this flag to hide console window
        '--name=FriskOCR',
        '--clean',
        '--noconfirm',
        '--add-data', f'{main_path}{os.pathsep}.',  # Include main.py
        '--uac-admin',  # Request UAC elevation
        '--manifest', manifest_path,  # Use our custom manifest
        launcher_path
    ]
    
    if os.path.exists(icon_path):
        pyinstaller_cmd.extend(['--icon', icon_path])
    
    # Run PyInstaller
    try:
        subprocess.check_call(pyinstaller_cmd)
        print("Build completed successfully! Check 'dist' directory for the executable.")
    except subprocess.CalledProcessError as e:
        print(f"Error creating executable: {e}")
    finally:
        # Clean up manifest file
        if os.path.exists(manifest_path):
            os.remove(manifest_path)

if __name__ == '__main__':
    create_exe()