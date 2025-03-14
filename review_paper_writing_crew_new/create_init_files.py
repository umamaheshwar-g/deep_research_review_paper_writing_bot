"""
Script to create clean __init__.py files without null bytes.
"""

def create_init_file(path):
    """Create a clean __init__.py file at the specified path."""
    with open(path, 'w', encoding='utf-8') as f:
        f.write('# Package initialization\n')
    print(f"Created {path}")

if __name__ == "__main__":
    paths = [
        './agents/__init__.py',
        './tasks/__init__.py',
        './tools/__init__.py',
        './utils/__init__.py'
    ]
    
    for path in paths:
        create_init_file(path) 