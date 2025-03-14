import os
import sys
import socket
import random
import subprocess
import argparse

def find_available_port(start=8501, end=8599):
    """Find an available port in the given range."""
    for port in range(start, end + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', port))
                return port
            except OSError:
                continue
    return random.randint(9000, 9999)  # Fallback to a random port

def run_streamlit_app(port=None, script_path=None):
    """Run the Streamlit app with the specified port."""
    if port is None:
        port = find_available_port()
    
    # Get the directory of the current script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    if script_path is None:
        script_path = os.path.join(current_dir, "final_script.py")
    
    print(f"Starting Research Paper Finder app on port {port}...")
    
    # Set environment variables
    os.environ['STREAMLIT_SERVER_PORT'] = str(port)
    os.environ['STREAMLIT_SERVER_ADDRESS'] = 'localhost'
    os.environ['STREAMLIT_SERVER_HEADLESS'] = 'false'  # Set to false to open browser
    os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
    
    # Add the project root to Python path
    if current_dir not in sys.path:
        sys.path.append(current_dir)
    
    # Add the review_paper_writing_crew_new directory to Python path
    review_crew_dir = os.path.join(current_dir, "review_paper_writing_crew_new")
    if os.path.exists(review_crew_dir) and review_crew_dir not in sys.path:
        sys.path.append(review_crew_dir)
        print(f"Added {review_crew_dir} to Python path")
    
    # Build the command
    cmd = [sys.executable, "-m", "streamlit", "run", script_path, 
           "--server.port", str(port),
           "--server.address", "localhost"]
    
    # Set PYTHONPATH environment variable to include the current directory and review_crew_dir
    env = os.environ.copy()
    python_path = env.get('PYTHONPATH', '')
    if python_path:
        env['PYTHONPATH'] = f"{current_dir}{os.pathsep}{review_crew_dir}{os.pathsep}{python_path}"
    else:
        env['PYTHONPATH'] = f"{current_dir}{os.pathsep}{review_crew_dir}"
    
    try:
        # Run the command
        process = subprocess.Popen(cmd, env=env)
        print(f"App is running at http://localhost:{port}")
        print("Press Ctrl+C to stop the app")
        process.wait()
    except KeyboardInterrupt:
        print("\nStopping the app...")
        process.terminate()
    except Exception as e:
        print(f"Error running the app: {str(e)}")
        # Try with a different port if there was an error
        if port < 9000:  # Only retry if we're not already using a random port
            new_port = random.randint(9000, 9999)
            print(f"Retrying with port {new_port}...")
            run_streamlit_app(new_port, script_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Research Paper Finder app")
    parser.add_argument("--port", type=int, help="Port to run the app on (default: auto-detect)")
    parser.add_argument("--script", type=str, help="Path to the Streamlit script (default: final_script.py)")
    args = parser.parse_args()
    
    run_streamlit_app(args.port, args.script) 