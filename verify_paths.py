import os
import sys

# Add app directory to path
sys.path.append(os.path.abspath("app"))

from config import Config
from utils import get_yt_dlp_options

def verify_options():
    print("Verifying yt-dlp options...")
    opts = get_yt_dlp_options()
    
    # Check paths
    if 'paths' not in opts:
        print("❌ 'paths' key missing in options")
        return False
        
    paths = opts['paths']
    print(f"Paths config: {paths}")
    
    if paths.get('home') != Config.DOWNLOAD_DIR:
        print(f"❌ 'home' path mismatch. Expected {Config.DOWNLOAD_DIR}, got {paths.get('home')}")
        return False
        
    if paths.get('temp') != Config.TEMP_DOWNLOAD_DIR:
        print(f"❌ 'temp' path mismatch. Expected {Config.TEMP_DOWNLOAD_DIR}, got {paths.get('temp')}")
        return False
    
    # Check outtmpl
    print(f"Output template: {opts['outtmpl']}")
    if Config.DOWNLOAD_DIR in opts['outtmpl']:
        print(f"❌ Output template should not contain absolute path when using 'paths'")
        return False
        
    print("✅ Verification passed!")
    return True

if __name__ == "__main__":
    success = verify_options()
    sys.exit(0 if success else 1)
