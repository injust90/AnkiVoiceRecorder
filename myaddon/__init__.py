"""AnkiVoiceRecorder: record mic audio into Anki's media folder."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import wave
import audioop

from aqt import mw
from aqt.qt import QAction, QFileDialog, QInputDialog, QKeySequence, QMenu, Qt, QUrl
from aqt.utils import showInfo, showWarning, tooltip
from PyQt6.QtMultimedia import (
    QAudioInput,
    QAudioOutput,
    QMediaCaptureSession,
    QMediaDevices,
    QMediaFormat,
    QMediaPlayer,
    QMediaRecorder,
)


class VoiceRecorder:
    def __init__(self) -> None:
        self._capture = QMediaCaptureSession()
        device = QMediaDevices.defaultAudioInput()
        if device.isNull():
            devices = QMediaDevices.audioInputs()
            names = [d.description() for d in devices]
            print(f"AnkiVoiceRecorder audio inputs: {names}")
            self._audio_input = None
        else:
            self._audio_input = QAudioInput(device)
        self._recorder = QMediaRecorder()
        if self._audio_input is not None:
            self._capture.setAudioInput(self._audio_input)
        self._capture.setRecorder(self._recorder)
        self._audio_output = QAudioOutput()
        self._player = QMediaPlayer()
        self._player.setAudioOutput(self._audio_output)
        self._recording = False
        self._last_path: Path | None = None

    def toggle(self) -> None:
        if self._recording:
            self.stop()
        else:
            self.start()

    def start(self) -> None:
        if mw.col is None:
            showWarning("No collection is open.")
            return
        if self._audio_input is None:
            showWarning("No audio input device available.")
            return

        media_dir = _get_save_dir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"voice_{timestamp}.wav"
        path = media_dir / filename

        fmt = QMediaFormat()
        fmt.setFileFormat(QMediaFormat.FileFormat.Wave)
        self._recorder.setMediaFormat(fmt)
        self._recorder.setOutputLocation(QUrl.fromLocalFile(str(path)))
        self._recorder.record()

        self._recording = True
        self._last_path = path
        record_shortcut = _get_record_shortcut()
        tooltip(f"Recording started ({record_shortcut} to stop)", parent=mw, period=2000)

    def stop(self) -> None:
        self._recorder.stop()
        self._recording = False

        if self._last_path is not None:
            _amplify_wav(self._last_path, _get_gain())
            print(f"AnkiVoiceRecorder saved: {self._last_path}")
            tooltip(f"Recording saved: {self._last_path.name}", parent=mw, period=2000)
        else:
            tooltip("Recording stopped.", parent=mw, period=2000)

    def play_last(self) -> None:
        if self._last_path is None:
            showWarning("No recording available yet.")
            return
        if not self._last_path.exists():
            showWarning("Last recording file is missing.")
            return
        self._player.setSource(QUrl.fromLocalFile(str(self._last_path)))
        self._player.play()
        tooltip("Playing last recording", parent=mw, period=2000)


_recorder = VoiceRecorder()

DEFAULT_RECORD_SHORTCUT = "Ctrl+R"
DEFAULT_PLAY_SHORTCUT = "Ctrl+Shift+R"


def _addon_id() -> str:
    return mw.addonManager.addonFromModule(__name__)


def _get_config() -> dict:
    config = mw.addonManager.getConfig(_addon_id())
    if config is None:
        config = {
            "save_dir": "",
            "gain": 1,
            "record_shortcut": DEFAULT_RECORD_SHORTCUT,
            "play_shortcut": DEFAULT_PLAY_SHORTCUT,
        }
        _write_config(config)
    return config


def _write_config(config: dict) -> None:
    if hasattr(mw.addonManager, "writeConfig"):
        mw.addonManager.writeConfig(_addon_id(), config)
    else:
        mw.addonManager.setConfig(_addon_id(), config)


def _get_save_dir() -> Path:
    config = _get_config()
    raw_path = str(config.get("save_dir", "")).strip()
    if raw_path:
        return Path(raw_path)
    return Path(mw.col.media.dir())


def _get_gain() -> float:
    config = _get_config()
    try:
        gain = float(config.get("gain", 1.25))
    except (TypeError, ValueError):
        gain = 1.25
    if gain < 0.1:
        return 0.1
    if gain > 5.0:
        return 5.0
    return gain


def _is_valid_shortcut(text: str) -> bool:
    return not QKeySequence(text).isEmpty()


def _get_record_shortcut() -> str:
    config = _get_config()
    raw = str(config.get("record_shortcut", DEFAULT_RECORD_SHORTCUT)).strip()
    if raw and _is_valid_shortcut(raw):
        return QKeySequence(raw).toString()
    return DEFAULT_RECORD_SHORTCUT


def _get_play_shortcut() -> str:
    config = _get_config()
    raw = str(config.get("play_shortcut", DEFAULT_PLAY_SHORTCUT)).strip()
    if raw and _is_valid_shortcut(raw):
        return QKeySequence(raw).toString()
    return DEFAULT_PLAY_SHORTCUT


def _set_save_dir() -> None:
    current = str(_get_save_dir())
    chosen = QFileDialog.getExistingDirectory(mw, "Select Recording Folder", current)
    if not chosen:
        return
    config = _get_config()
    config["save_dir"] = chosen
    _write_config(config)
    tooltip(f"Recording folder set to: {chosen}", parent=mw, period=2500)


def _apply_shortcuts() -> None:
    action_recording.setShortcut(QKeySequence(_get_record_shortcut()))
    action_playback.setShortcut(QKeySequence(_get_play_shortcut()))


def _set_keybindings() -> None:
    config = _get_config()
    current_record = str(config.get("record_shortcut", DEFAULT_RECORD_SHORTCUT)).strip() or DEFAULT_RECORD_SHORTCUT
    record_text, ok = QInputDialog.getText(
        mw,
        "Recording Shortcut",
        "Set shortcut for Toggle Recording:",
        text=current_record,
    )
    if not ok:
        return
    record_text = record_text.strip()
    if not _is_valid_shortcut(record_text):
        showWarning("Invalid shortcut for recording.")
        return

    current_play = str(config.get("play_shortcut", DEFAULT_PLAY_SHORTCUT)).strip() or DEFAULT_PLAY_SHORTCUT
    play_text, ok = QInputDialog.getText(
        mw,
        "Playback Shortcut",
        "Set shortcut for Play Last Recording:",
        text=current_play,
    )
    if not ok:
        return
    play_text = play_text.strip()
    if not _is_valid_shortcut(play_text):
        showWarning("Invalid shortcut for playback.")
        return

    config["record_shortcut"] = QKeySequence(record_text).toString()
    config["play_shortcut"] = QKeySequence(play_text).toString()
    _write_config(config)
    _apply_shortcuts()
    tooltip("Shortcuts updated.", parent=mw, period=2000)


def _amplify_wav(path: Path, gain: float) -> None:
    if not path.exists():
        return
    try:
        with wave.open(str(path), "rb") as reader:
            params = reader.getparams()
            frames = reader.readframes(reader.getnframes())

        amplified = audioop.mul(frames, params.sampwidth, gain)
        with wave.open(str(path), "wb") as writer:
            writer.setparams(params)
            writer.writeframes(amplified)
    except Exception as exc:
        print(f"AnkiVoiceRecorder gain failed: {exc}")

action_recording = QAction("AnkiVoiceRecorder: Toggle Recording", mw)
action_recording.setShortcut(QKeySequence(_get_record_shortcut()))
action_recording.triggered.connect(_recorder.toggle)

action_playback = QAction("AnkiVoiceRecorder: Play Last Recording", mw)
action_playback.setShortcut(QKeySequence(_get_play_shortcut()))
action_playback.triggered.connect(_recorder.play_last)

settings_action = QAction("AnkiVoiceRecorder: Set Recording Folder...", mw)
settings_action.triggered.connect(_set_save_dir)

keybindings_action = QAction("AnkiVoiceRecorder: Set Keybindings...", mw)
keybindings_action.triggered.connect(_set_keybindings)

tools_menu = mw.form.menuTools
anki_menu = QMenu("AnkiRecorder", mw)
options_menu = QMenu("Options", mw)

anki_menu.addAction(action_recording)
anki_menu.addAction(action_playback)
anki_menu.addSeparator()
anki_menu.addMenu(options_menu)

options_menu.addAction(settings_action)
options_menu.addAction(keybindings_action)

tools_menu.addMenu(anki_menu)
