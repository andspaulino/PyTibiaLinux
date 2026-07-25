import sys
import time
from tinydb import TinyDB, Query
from src.gameplay.context import context as initial_context
from src.gameplay.core.load import loadContextFromConfig
from src.gameplay.threads.pyTibia import PyTibiaThread
from src.utils.window import get_tibia_windows

class CLIContext:
    def __init__(self, context_dict):
        self.context = context_dict

def main():
    print("Initializing PyTibia (Linux CLI Mode)...")
    
    # Load configuration from TinyDB
    db_path = 'file.json'
    try:
        db = TinyDB(db_path)
    except Exception as e:
        print(f"Error opening TinyDB configuration file '{db_path}': {e}")
        sys.exit(1)
        
    profiles = db.search(Query().enabled == True)
    if not profiles:
        print("Error: No enabled profile found in file.json.")
        sys.exit(1)
        
    enabled_profile = profiles[0]
    print(f"Loaded profile: {enabled_profile.get('name', 'Default')}")
    
    # Load configuration into initial context
    context = loadContextFromConfig(enabled_profile['config'], initial_context)
    
    # Window selection using xdotool
    print("Searching for active Tibia windows...")
    tibia_windows = get_tibia_windows()
    if not tibia_windows:
        print("Error: No Tibia window found. Make sure the Tibia client is open and running.")
        sys.exit(1)
        
    selected_window = None
    if len(tibia_windows) == 1:
        selected_window = tibia_windows[0]
        print(f"Automatically selected the only active Tibia window: {selected_window.title}")
    else:
        print("Multiple Tibia windows detected. Please select one:")
        for idx, win in enumerate(tibia_windows):
            print(f"[{idx + 1}] ID: {win.window_id} — {win.title}")
        
        while True:
            try:
                choice = input("Enter choice number: ").strip()
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(tibia_windows):
                    selected_window = tibia_windows[choice_idx]
                    break
                else:
                    print("Invalid choice. Try again.")
            except ValueError:
                print("Please enter a valid number.")
            except (KeyboardInterrupt, EOFError):
                print("\nAborted.")
                sys.exit(0)
                
    # Activate and focus window
    print(f"Activating window: {selected_window.title}...")
    if selected_window.activate():
        print("Window activated. Waiting 1 second...")
        time.sleep(1)
    else:
        print("Warning: Could not activate target window. Proceeding anyway...")
        
    # Store window in context
    context['window'] = selected_window
    context['pause'] = False
    
    # Start gameplay thread loop
    cli_context = CLIContext(context)
    pytibia_thread = PyTibiaThread(cli_context)
    
    print("\nStarting bot engine gameplay loop. Press Ctrl+C to stop.")
    pytibia_thread.mainloop()

if __name__ == '__main__':
    main()
