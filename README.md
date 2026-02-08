# AnkiVoiceRecorder

An Anki add-on that records microphone audio to WAV, lets you play back the last recording, and optionally saves to a custom folder.

## Features
- Record/stop toggle (default: Ctrl+R)
- Play last recording (default: Ctrl+Shift+R)
- Tools menu integration via the AnkiRecorder submenu
- Options submenu for recording folder and keybindings
- Optional gain boost after recording

## Install (development)
1. Clone this repo.
2. Symlink the add-on folder into Anki:

   ```bash
   ln -s /path/to/AnkiVoiceRecorder/myaddon ~/.local/share/Anki2/addons21/AnkiVoiceRecorder
   ```

3. Restart Anki.

## Usage
- Tools -> AnkiRecorder -> AnkiVoiceRecorder: Toggle Recording
- Tools -> AnkiRecorder -> AnkiVoiceRecorder: Play Last Recording
- Tools -> AnkiRecorder -> Options -> AnkiVoiceRecorder: Set Recording Folder...
- Tools -> AnkiRecorder -> Options -> AnkiVoiceRecorder: Set Keybindings...

## Config
Config is stored by Anki. Defaults are defined in myaddon/config.json:

```json
{
  "save_dir": "",
  "gain": 1.25,
  "record_shortcut": "Ctrl+R",
  "play_shortcut": "Ctrl+Shift+R"
}
```

- save_dir: empty means use the collection media folder.
- gain: multiplier applied after recording (1.0 = no change).
- record_shortcut: shortcut for Toggle Recording.
- play_shortcut: shortcut for Play Last Recording.

## Notes
- Recordings are WAV files named voice_YYYYMMDD_HHMMSS.wav.
- Add-ons must be run from inside Anki; they will not run from VS Code.

## Licenses / Credits
- Uses Anki's bundled APIs and its Qt/PyQt runtime at execution time.
- No third-party code is bundled by this add-on.
