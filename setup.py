import subprocess
import sys
import os

def install_requirements():
    """Install all required dependencies for the Research Paper Finder application."""
    print("Installing required Python packages...")
    
    # Install main requirements
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    # Install NLTK resources
    print("\nInstalling NLTK resources...")
    import nltk
    nltk.download('punkt')
    nltk.download('stopwords')
    
    # Check if .env file exists and prompt user to configure it
    if not os.path.exists(".env"):
        print("\nWARNING: No .env file found. Creating a template .env file...")
        with open(".env", "w") as f:
            f.write("""# API Keys for Research Paper Finder
# Replace the placeholder values with your actual API keys

# Email addresses for various APIs
CROSSREF_EMAIL=your_email@example.com
PUBMED_EMAIL=your_email@example.com

# API Keys
SEMANTIC_SCHOLAR_API_KEY=your_semantic_scholar_api_key
SERPER_API_KEY=your_serper_api_key

# Application Settings
DEBUG=False
SAVE_RAW_RESPONSES=False
""")
        print("A template .env file has been created. Please edit it with your actual API keys.")
    
    print("\nAll dependencies installed successfully!")
    print("You can now run the application with: python run_app.py")

if __name__ == "__main__":
    # Check if running from the correct directory
    if not os.path.exists("requirements.txt"):
        print("Error: This script must be run from the clean_project directory.")
        print("Please navigate to the clean_project directory and run this script again.")
        sys.exit(1)
    
    install_requirements() 