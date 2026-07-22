# TF2 Jukebox

python app that reads Team Fortress 2 console logs and allows players to queue and control music directly through Media Player Classic (MPC-HC) using chat commands. 
This is not including how to play music thourgh your mic (check 'vb cable' for transfering music from MPHC to TF2 mic.)

## Features
- **Log Tailing:** Actively monitors TF2's `console.log` for chat commands.
- **Queue System:** Automatically queues requested tracks so multiple players can add songs sequentially without interruption.
- **MPC-HC Integration:** Fast HTTP session management execute playback, stopping, skipping, and volume adjustments.
- **Bandwidth Control:** Download rate-limiting to eliminate in-game lag or ping spikes.

## Prerequisites
- **Python 3.x** installed on your system.
- **Team Fortress 2** obviously
- **Media Player Classic (MPC-HC)** rn it only works with mpc, with the Web Interface enabled.

## Installation & Setup

1. Clone or download this repository.
2. Install the required Python packages via pip:
   ```bash
   pip install yt-dlp requests
   ```

## Configuration

Open `main.py` and modify the top configuration to match your local setup:

```python
# The exact path to your game console log
LOG_FILE_PATH = r"C:\Program Files (x86)\Steam\steamapps\common\Team Fortress 2\tf\console.log"

# Chat command prefix to trigger queueing
COMMAND_PREFIX = "!play "

# MPC-HC Web API URL (Requires Web Interface enabled)
MPC_URL = "http://localhost:13579"

# Audio download quality ('low', 'medium', 'high')
MUSIC_QUALITY = "low"
```

### Enabling MPC-HC Web Interface
1. Open MPC-HC.
2. Press `O` to open **Options**.
3. Go to **Player** -> **Web Interface**.
4. Check **"Listen on port"** and set it to your locahost for example: `13579`.
5. Check **"Allow access from localhost only"**.

## Usage

1. Launch Media Player Classic (MPC-HC).
2. Start Team Fortress 2.
3. Run the Python script:
   ```bash
   python main.py
   ```
4. Use the following commands in the in-game chat:
   - `!play [song name or URL]` - Adds a track to the queue if already a song playing.
   - `!skip` - Skips the current track moves on the next song.
   - `!stop` - Stops playback and clears the queue.
   - `!vol [0-100]` - Adjusts the exact volume like !vol 50.
   - `!vol up` / `!vol down` - Adjusts volume.
   - `!mute` / `!unmute` - Toggles  muting.
