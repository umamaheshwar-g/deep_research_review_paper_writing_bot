try:
    from dotenv import load_dotenv
    print("Successfully imported dotenv")
except ImportError as e:
    print(f"Error importing dotenv: {e}")

try:
    import os
    print("Successfully imported os")
except ImportError as e:
    print(f"Error importing os: {e}")

try:
    import sys
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    print(f"Python path: {sys.path}")
except ImportError as e:
    print(f"Error importing sys: {e}") 