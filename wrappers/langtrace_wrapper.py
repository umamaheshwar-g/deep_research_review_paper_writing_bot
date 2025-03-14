
# Wrapper for langtrace to avoid Unicode encoding issues
import os
import sys

# Patch the langtrace init function to avoid Unicode characters
def patch_langtrace():
    try:
        from langtrace_python_sdk import langtrace
        original_init = langtrace.init
        
        def safe_init(*args, **kwargs):
            # Set stdout and stderr to use utf-8 encoding
            if sys.stdout.encoding != 'utf-8':
                sys.stdout.reconfigure(encoding='utf-8')
            if sys.stderr.encoding != 'utf-8':
                sys.stderr.reconfigure(encoding='utf-8')
                
            try:
                return original_init(*args, **kwargs)
            except UnicodeEncodeError:
                print("Initialized Langtrace SDK (Unicode characters suppressed)")
                return True
        
        langtrace.init = safe_init
        print("Langtrace patched successfully")
    except ImportError:
        print("Langtrace SDK not found, continuing without patching")
    except Exception as e:
        print(f"Error patching langtrace: {e}")

# Apply the patch
patch_langtrace()

# Import and run the original main module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from review_paper_writing_crew_new.main import main

if __name__ == "__main__":
    main()
