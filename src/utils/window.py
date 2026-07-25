import subprocess
import re

class TibiaWindow:
    def __init__(self, window_id: str, title: str):
        self.window_id = window_id
        self.title = title

    def activate(self):
        try:
            # Activate window (brings to front/workspace) and focus it
            subprocess.run(['xdotool', 'windowactivate', self.window_id], check=True)
            subprocess.run(['xdotool', 'windowfocus', self.window_id], check=True)
            return True
        except Exception as e:
            print(f"Failed to activate window {self.window_id} ({self.title}): {e}")
            return False

def get_tibia_windows() -> list[TibiaWindow]:
    """Finds all windows whose title starts with 'Tibia' and returns a list of TibiaWindow objects."""
    try:
        # Search for windows with name starting with "Tibia"
        result = subprocess.run(['xdotool', 'search', '--name', '^Tibia'], capture_output=True, text=True)
        # If no window is found, xdotool search returns exit code 1 and empty output
        if result.returncode != 0 or not result.stdout.strip():
            return []
        
        window_ids = [w.strip() for w in result.stdout.strip().split('\n') if w.strip()]
        tibia_windows = []
        for wid in window_ids:
            title_res = subprocess.run(['xdotool', 'getwindowname', wid], capture_output=True, text=True)
            if title_res.returncode == 0:
                title = title_res.stdout.strip()
                if re.match(r"^Tibia.*", title):
                    tibia_windows.append(TibiaWindow(wid, title))
        return tibia_windows
    except FileNotFoundError:
        print("Warning: xdotool is not installed. Please install it using: sudo apt install xdotool")
        return []
    except Exception as e:
        print(f"Error listing Tibia windows: {e}")
        return []
