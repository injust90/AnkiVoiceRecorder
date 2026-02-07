"""AnkiVoiceRecorder: record mic audio into Anki's media folder."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import wave
import audioop

from aqt import mw
from aqt.qt import QAction, QFileDialog, QKeySequence, Qt, QUrl
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
        tooltip("Recording started (Ctrl+R to stop)", parent=mw, period=2000)

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


def _addon_id() -> str:
    return mw.addonManager.addonFromModule(__name__)


def _get_config() -> dict:
    config = mw.addonManager.getConfig(_addon_id())
    if config is None:
        config = {"save_dir": "", "gain": 1}
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


def _set_save_dir() -> None:
    current = str(_get_save_dir())
    chosen = QFileDialog.getExistingDirectory(mw, "Select Recording Folder", current)
    if not chosen:
        return
    config = _get_config()
    config["save_dir"] = chosen
    _write_config(config)
    tooltip(f"Recording folder set to: {chosen}", parent=mw, period=2500)


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
action_recording.setShortcut(QKeySequence("Ctrl+R"))
action_recording.triggered.connect(_recorder.toggle)
mw.form.menuTools.addAction(action_recording)

action_playback = QAction("AnkiVoiceRecorder: Play Last Recording", mw)
action_playback.setShortcut(QKeySequence("Ctrl+Shift+R"))
action_playback.triggered.connect(_recorder.play_last)
mw.form.menuTools.addAction(action_playback)

settings_action = QAction("AnkiVoiceRecorder: Set Recording Folder...", mw)
settings_action.triggered.connect(_set_save_dir)
mw.form.menuTools.addAction(settings_action)
