# AnkiVoiceRecorder

An Anki add-on that records microphone audio to WAV, lets you play back the last recording, and optionally saves to a custom folder.

## Features
- Record/stop toggle (default: Ctrl+R)
- Play last recording (default: Ctrl+Shift+R)
- Tool menu actions for recording, playback, and folder selection
- Optional gain boost after recording

## Install (development)
1. Clone this repo.
2. Symlink the add-on folder into Anki:

   ```bash
   ln -s /path/to/AnkiVoiceRecorder/myaddon ~/.local/share/Anki2/addons21/AnkiVoiceRecorder
   ```

3. Restart Anki.

## Usage
- Tools -> AnkiVoiceRecorder: Toggle Recording
- Tools -> AnkiVoiceRecorder: Play Last Recording
- Tools -> AnkiVoiceRecorder: Set Recording Folder...

## Config
Config is stored by Anki. Defaults are defined in myaddon/config.json:

```json
{
  "save_dir": "",
  "gain": 1.25
}
```

- save_dir: empty means use the collection media folder.
- gain: multiplier applied after recording (1.0 = no change).

## Notes
- Recordings are WAV files named voice_YYYYMMDD_HHMMSS.wav.
- Add-ons must be run from inside Anki; they will not run from VS Code.

## Licenses / Credits
- Uses Anki's bundled APIs and its Qt/PyQt runtime at execution time.
- No third-party code is bundled by this add-on.
