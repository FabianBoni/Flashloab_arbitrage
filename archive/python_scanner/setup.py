"""
Setup script for Python BSC Arbitrage Scanner
"""

import subprocess
import sys
import os

def install_requirements():
    """Install required Python packages"""
    print("🐍 Installing Python requirements...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ All packages installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install packages: {e}")
        return False

def setup_environment():
    """Setup environment configuration"""
    print("🔧 Setting up environment...")
    
    if not os.path.exists('.env'):
        print("⚠️ .env file not found. Please configure your environment variables.")
        print("📝 Copy .env.example to .env and fill in your values")
        return False
        
    print("✅ Environment configuration found")
    return True

def main():
    """Main setup function"""
    print("🚀 BSC Arbitrage Scanner Setup")
    print("=" * 50)
    
    # Install requirements
    if not install_requirements():
        return False
        
    # Setup environment
    if not setup_environment():
        return False
        
    print("\n🎉 Setup completed successfully!")
    print("🔧 To run the scanner: python arbitrage_scanner.py")
    print("⚠️ Make sure to configure your .env file with your private key and settings")
    
    return True

if __name__ == "__main__":
    main()
