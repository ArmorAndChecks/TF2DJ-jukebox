import os
import time
import queue
import yt_dlp
import requests
import threading

# CONFIG
# path for console log
LOG_FILE_PATH = r"C:\Program Files (x86)\Steam\steamapps\common\Team Fortress 2\tf\console.log"

# Chat command prefix to queue audio / (bugged) also fetches !play command anywhere in a sentence also
COMMAND_PREFIX = "!play "

# MPC-HC Web API URL, Web Interface must be enabled, rn it only works with mphc
MPC_URL = "http://localhost:13579"

# Audio download quality
# options: 'low' (fastest injection, low quality), 'medium' (balanced), 'high' (best audio quality)
MUSIC_QUALITY = "low"

# VIP EXPRESS CONNECTION
mpc_session = requests.Session()

# QUEUE SYSTEM
song_queue = queue.Queue()


def send_to_mpc(action, params=None):
    """Sends an instant request to Media Player Classic."""
    try:
        mpc_session.post(f"{MPC_URL}/command.html", data=params, timeout=2)
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to MPC-HC.")
        print("Ensure MPC-HC is open and the 'Web Interface' is enabled on port 13579.")


def handle_volume_command(command_text):
    """
     volume commands from chat and sends to MPC-HC.
    !mute, !unmute, !vol up, !vol down, and exact numbers like !vol 50
    """
    if "!mute" in command_text or "!unmute" in command_text:
        print("Mute/Unmute command received.")
        send_to_mpc('mute', {'wm_command': '909'})
        return

    if "!vol up" in command_text:
        print("Volume UP command received.")
        send_to_mpc('vol_up', {'wm_command': '907'})
        return

    if "!vol down" in command_text:
        print("Volume DOWN command received.")
        send_to_mpc('vol_down', {'wm_command': '908'})
        return

    if "!vol " in command_text:
        parts = command_text.split("!vol ", 1)
        if len(parts) > 1:
            val_str = parts[1].strip()

            if val_str.isdigit():
                volume_level = int(val_str)

                if volume_level > 100:
                    volume_level = 100
                elif volume_level < 0:
                    volume_level = 0

                print(f"Setting volume to {volume_level}%")
                send_to_mpc('set_vol', {'wm_command': '-2', 'volume': str(volume_level)})
            else:
                print(f"Ignored invalid volume number: '{val_str}'")


def clean_old_tracks():
    """removes old audio files in the background."""
    for f in os.listdir('.'):
        if f.startswith("jukebox_track_"):
            try:
                os.remove(f)
            except Exception:
                pass


def wait_for_mpc_to_finish():
    """Polls MPC-HC to check when playback ends so the next song can start."""
    # Give MPC-HC time to load the local file and transition out of any prior Stopped state
    time.sleep(3)

    while True:
        try:
            resp = mpc_session.get(f"{MPC_URL}/variables.html", timeout=2)
            html_content = resp.text

            # State 1 usually means Stopped in MPC-HC, indicating the track finished
            if 'id="state">1<' in html_content or 'id="statestring">Stopped<' in html_content:
                break
        except requests.exceptions.RequestException:
            # If MPC-HC is closed or unreachable, break to prevent hanging the queue
            break

        time.sleep(2)


def search_and_stream(search_query):
    """
    Downloads audio and sends to player. Returns True if successful.
    """
    try:
        print(f"Searching YouTube for: '{search_query}'...")

        send_to_mpc('stop', {'wm_command': '890'})
        clean_old_tracks()

        unique_id = int(time.time())
        unique_filename = f"jukebox_track_{unique_id}"

        # Determine download format based on MUSIC_QUALITY setting
        if MUSIC_QUALITY.lower() == 'low':
            audio_format = 'bestaudio[abr<=64][ext=m4a]/bestaudio[ext=m4a]/bestaudio'
        elif MUSIC_QUALITY.lower() == 'high':
            audio_format = 'bestaudio/best'
        else:
            audio_format = 'bestaudio[abr<=130][ext=m4a]/bestaudio[ext=m4a]/bestaudio'

        ydl_opts = {
            'format': audio_format,
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'ytsearch1',
            'outtmpl': f'{unique_filename}.%(ext)s',
            'noprogress': True,

            # change if lagging
            'concurrent_fragment_downloads': 1,  # changed from 3 to 1 to reduce lag. (22.07.2026)
            'ratelimit': 500000,  # speed cap
            # -------------------------
            'buffersize': 1024 * 1024,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_query, download=True)
            video_data = info['entries'][0] if 'entries' in info else info

            ext = video_data.get('ext', 'm4a')
            local_path = os.path.abspath(f"{unique_filename}.{ext}")

            print(f"Download Complete: {video_data.get('title')}")
            print("Injecting into MPC-HC...")

            mpc_session.get(f"{MPC_URL}/browser.html", params={'path': local_path}, timeout=2)
            return True

    except Exception as e:
        print(f"Error during search/play: {e}")
        return False


def queue_worker():
    """Background worker that processes songs from the queue."""
    while True:
        # Blocks until a new song request is available
        song_request = song_queue.get()

        print(f"\n[Queue] Processing next track: '{song_request}'")

        # Stream the song if successful, wait until playback finishes before continuing.
        success = search_and_stream(song_request)
        if success:
            wait_for_mpc_to_finish()

        song_queue.task_done()


def main_loop():
    """monitors the console log with low CPU."""
    if not os.path.exists(LOG_FILE_PATH):
        print(f"Waiting for game to create log file at: {LOG_FILE_PATH}")
        while not os.path.exists(LOG_FILE_PATH):
            time.sleep(1)

    print("Jukebox Online, watching console.log.")
    print("-----------------------------------------------------------------")

    with open(LOG_FILE_PATH, "r", encoding="utf-8", errors="ignore") as f:
        f.seek(0, os.SEEK_END)

        while True:
            line = f.readline()
            if not line:
                time.sleep(0.05)
                continue

            clean_line = line.strip()

            if "!stop" in clean_line:
                print("Stop command received. Stopping playback and clearing queue.")
                with song_queue.mutex:
                    song_queue.queue.clear()
                send_to_mpc('stop', {'wm_command': '890'})
                continue

            if "!skip" in clean_line:
                print("Skip command received. Moving to next track in queue...")
                send_to_mpc('stop', {'wm_command': '890'})
                continue

            if any(cmd in clean_line for cmd in ["!vol", "!mute", "!unmute"]):
                handle_volume_command(clean_line)
                continue

            if COMMAND_PREFIX in clean_line:
                parts = clean_line.split(COMMAND_PREFIX, 1)
                if len(parts) > 1:
                    song_request = parts[1].strip()
                    if not song_request:
                        continue

                    position = song_queue.qsize() + 1
                    print(f"\nAdded to Queue: '{song_request}' (Position: {position})")
                    song_queue.put(song_request)


if __name__ == "__main__":
    print("Booting Jukebox...")

    # Start queue processing
    worker = threading.Thread(target=queue_worker, daemon=True)
    worker.start()

    try:
        main_loop()
    except KeyboardInterrupt:
        print("\nShutting down.")