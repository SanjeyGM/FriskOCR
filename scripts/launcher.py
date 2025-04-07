import os
import sys
import subprocess
import logging
import platform

def get_base_dir():
    """Get the correct base directory whether running as script or exe"""
    if getattr(sys, 'frozen', False):
        # Running as executable
        return os.path.dirname(sys.executable)
    else:
        # Running as script
        return os.path.dirname(os.path.abspath(__file__))

# Set up basic logging
base_dir = get_base_dir()
logs_dir = os.path.join(base_dir, 'logs')
os.makedirs(logs_dir, exist_ok=True)  # Ensure logs directory exists

logging.basicConfig(
    filename=os.path.join(logs_dir, 'friskocr_launcher.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def check_python_version():
    """Check if the running Python is 3.10.x"""
    major, minor = sys.version_info.major, sys.version_info.minor
    if major != 3 or minor != 10:
        logging.error(f"Incompatible Python version: {sys.version}")
        return False
    return True

def ensure_virtual_env(venv_dir):
    """Ensure virtual environment exists and has correct Python version"""
    if not os.path.exists(venv_dir):
        logging.info(f"Creating virtual environment at {venv_dir}")
        try:
            # Use python3.10 specifically if available
            python_command = "python3.10" if sys.platform != "win32" else "python"
            subprocess.run([python_command, "-m", "venv", venv_dir], check=True)
            logging.info("Virtual environment created successfully")
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to create virtual environment: {e}")
            return False
    return True

def run_main():
    try:
        # Get the actual directory where the exe/script is located
        base_dir = get_base_dir()
        logging.info(f"Base directory: {base_dir}")
        
        # Check Python version first
        if not check_python_version():
            message = (
                "Error: FriskoOCR requires Python 3.10.\n"
                f"Current Python version: {sys.version}\n"
                "Please install Python 3.10 and try again."
            )
            print(message)
            logging.error(message)
            return False
        
        # Set up paths
        venv_dir = os.path.join(base_dir, "friskocr")
        main_script = os.path.join(base_dir, "main.py")
        logging.info(f"Virtual environment path: {venv_dir}")
        logging.info(f"Main script path: {main_script}")
        
        # Ensure virtual environment exists
        if not ensure_virtual_env(venv_dir):
            message = "Failed to create or verify virtual environment."
            print(message)
            logging.error(message)
            return False
        
        if sys.platform == "win32":
            python_path = os.path.join(venv_dir, "Scripts", "python.exe")
            activate_script = os.path.join(venv_dir, "Scripts", "activate.bat")
        else:
            python_path = os.path.join(venv_dir, "bin", "python")
            activate_script = os.path.join(venv_dir, "bin", "activate")

        # Verify paths exist
        if not os.path.exists(activate_script):
            logging.error(f"Virtual environment not found. Checking paths:")
            logging.error(f"Activate script path: {activate_script}")
            logging.error(f"Base directory contents: {os.listdir(base_dir)}")
            raise FileNotFoundError(f"Virtual environment not found at: {venv_dir}")
            
        if not os.path.exists(main_script):
            logging.error(f"main.py not found at: {main_script}")
            raise FileNotFoundError(f"main.py not found at: {main_script}")

        # Handle PyArmor runtime location - ensure it's in PYTHONPATH
        pyarmor_dir = os.path.join(base_dir, "pytransform")
        os.environ["PYTHONPATH"] = pyarmor_dir + os.pathsep + os.environ.get("PYTHONPATH", "")
        logging.info(f"Set PYTHONPATH to include: {pyarmor_dir}")

        # Run main.py with activated venv
        if sys.platform == "win32":
            cmd = f'"{activate_script}" && set PYTHONPATH={pyarmor_dir};%PYTHONPATH% && "{python_path}" "{main_script}"'
            logging.info(f"Running command: {cmd}")
            process = subprocess.Popen(
                cmd,
                shell=True,
                cwd=base_dir,  # Set working directory
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
        else:
            cmd = f'source "{activate_script}" && export PYTHONPATH={pyarmor_dir}:$PYTHONPATH && "{python_path}" "{main_script}"'
            logging.info(f"Running command: {cmd}")
            process = subprocess.Popen(
                ['/bin/bash', '-c', cmd],
                cwd=base_dir,  # Set working directory
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

        # Get output
        stdout, stderr = process.communicate()
        
        if stdout:
            print(stdout)
            logging.info(stdout)
        if stderr:
            print(stderr, file=sys.stderr)
            logging.error(stderr)
            
        if process.returncode != 0:
            raise RuntimeError(f"Error running main.py: {stderr}")
        
        return True

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        # Check if --check-python-version flag is passed (used by installer)
        if len(sys.argv) > 1 and sys.argv[1] == '--check-python-version':
            if check_python_version():
                sys.exit(0)  # Success - correct Python version
            else:
                sys.exit(1)  # Failed - wrong Python version
        
        success = run_main()
        if not success:
            input("Press Enter to exit...")
            sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        logging.error(str(e))
        input("Press Enter to exit...")
        sys.exit(1)