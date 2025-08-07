#!/usr/bin/env python3
"""
Setup script for WhatsApp RAG Chatbot
Automates the installation and configuration process.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ required. Current version: {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def install_dependencies():
    """Install Python dependencies"""
    if not run_command("pip install -r requirements.txt", "Installing Python dependencies"):
        return False
    return True

def check_ollama():
    """Check if Ollama is installed and running"""
    print("🤖 Checking Ollama installation...")
    
    # Check if ollama command exists
    if shutil.which("ollama") is None:
        print("❌ Ollama not found. Installing...")
        if os.name == 'nt':  # Windows
            print("⚠️  Please install Ollama manually from https://ollama.ai")
            return False
        else:  # macOS/Linux
            if not run_command("curl -fsSL https://ollama.ai/install.sh | sh", "Installing Ollama"):
                return False
    
    # Check if Ollama server is running
    if not run_command("ollama list", "Checking Ollama server"):
        print("🔄 Starting Ollama server...")
        if not run_command("ollama serve &", "Starting Ollama server"):
            return False
        import time
        time.sleep(3)  # Wait for server to start
    
    # Pull required model
    if not run_command("ollama pull gemma:2b", "Pulling Gemma 2B model"):
        return False
    
    return True

def setup_environment():
    """Set up environment variables"""
    print("⚙️  Setting up environment...")
    
    env_file = Path(".env")
    env_example = Path("env_example.txt")
    
    if not env_example.exists():
        print("❌ env_example.txt not found")
        return False
    
    if not env_file.exists():
        shutil.copy(env_example, env_file)
        print("✅ Created .env file from template")
        print("⚠️  Please edit .env file with your Twilio credentials")
    else:
        print("✅ .env file already exists")
    
    return True

def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    
    directories = ["logs", "data"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created {directory}/ directory")
    
    return True

def test_setup():
    """Test the setup by running basic checks"""
    print("🧪 Testing setup...")
    
    try:
        # Test imports
        import flask
        import twilio
        import langchain
        print("✅ All required packages imported successfully")
        
        # Test database creation
        import sqlite3
        conn = sqlite3.connect('db.sqlite3')
        conn.close()
        print("✅ Database connection test passed")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Setup test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 WhatsApp RAG Chatbot Setup")
    print("=" * 50)
    
    steps = [
        ("Python Version Check", check_python_version),
        ("Install Dependencies", install_dependencies),
        ("Ollama Setup", check_ollama),
        ("Environment Setup", setup_environment),
        ("Create Directories", create_directories),
        ("Test Setup", test_setup)
    ]
    
    for step_name, step_func in steps:
        print(f"\n{'='*20} {step_name} {'='*20}")
        if not step_func():
            print(f"\n❌ Setup failed at: {step_name}")
            print("Please fix the issue and run setup again.")
            sys.exit(1)
    
    print("\n" + "="*50)
    print("🎉 Setup completed successfully!")
    print("="*50)
    print("\nNext steps:")
    print("1. Edit .env file with your Twilio credentials")
    print("2. Run: python app.py")
    print("3. Test with: python test_bot.py")
    print("\nFor detailed instructions, see README.md")

if __name__ == "__main__":
    main() 