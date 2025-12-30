import subprocess
import sys
from pathlib import Path

def main():
    # Define the base directory relative to this script
    # This script is in scr/plotting/
    # The scripts to run are in scr/plotting/v2_html/
    current_dir = Path(__file__).parent
    deploy_dir = current_dir / "v2_html"
    scripts = [
        deploy_dir / "ducker.py",
        deploy_dir / "plotter_v2.py"
    ]

    print("Starting sequential execution of plotter v2 scripts...")

    for script in scripts:
        print(f"\n--- Running {script.name} ---")
        try:
            # Run the script using the same python interpreter
            result = subprocess.run([sys.executable, str(script)], check=True)
        except subprocess.CalledProcessError as e:
            print(f"\n❌ Error encountered while running {script.name}.")
            print(f"Exit code: {e.returncode}")
            sys.exit(e.returncode)
        except Exception as e:
            print(f"\n❌ Unexpected error running {script.name}: {e}")
            sys.exit(1)
        else:
            print(f"✔ {script.name} finished successfully.")

    print("\nAll scripts executed successfully.")

if __name__ == "__main__":
    main()
