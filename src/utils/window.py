import re
import subprocess


class TibiaWindow:
    def __init__(self, window_id: str, title: str):
        self.window_id = window_id
        self.title = title

    def activate(self):
        try:
            subprocess.run(
                ['xdotool', 'windowactivate', self.window_id],
                check=True,
            )
            subprocess.run(
                ['xdotool', 'windowfocus', self.window_id],
                check=True,
            )
            return True
        except Exception as error:
            print(
                f'Failed to activate window {self.window_id} '
                f'({self.title}): {error}'
            )
            return False


def get_tibia_windows() -> list[TibiaWindow]:
    try:
        result = subprocess.run(
            ['xdotool', 'search', '--name', '^Tibia'],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return []

        window_ids = [
            window_id.strip()
            for window_id in result.stdout.strip().split('\n')
            if window_id.strip()
        ]
        tibia_windows = []
        for window_id in window_ids:
            titleResult = subprocess.run(
                ['xdotool', 'getwindowname', window_id],
                capture_output=True,
                text=True,
            )
            if titleResult.returncode != 0:
                continue
            title = titleResult.stdout.strip()
            if re.match(r'^Tibia.*', title):
                tibia_windows.append(TibiaWindow(window_id, title))
        return tibia_windows
    except FileNotFoundError:
        print(
            'Warning: xdotool is not installed. '
            'Install it with: sudo apt install xdotool'
        )
        return []
    except Exception as error:
        print(f'Error listing Tibia windows: {error}')
        return []
