from unittest.mock import Mock

from config import Config
from core.anti_spoofing import AntiSpoofingModel
from services.recognition_thread import RecognitionSession


def test_anti_spoofing_fails_closed_without_model(monkeypatch):
    model = AntiSpoofingModel.__new__(AntiSpoofingModel)
    model.session = None
    monkeypatch.setattr(Config, "ANTI_SPOOF_FAIL_OPEN", False)

    is_real, score, message = model.predict(None, [0, 0, 10, 10])

    assert is_real is False
    assert score == 0.0
    assert "chưa sẵn sàng" in message


def test_recognition_stop_uses_bounded_join():
    session = RecognitionSession.__new__(RecognitionSession)
    session._running = True
    session._thread = Mock()
    session._thread.is_alive.return_value = False
    session.lop_id = 1

    session.stop()

    session._thread.join.assert_called_once_with(
        timeout=Config.WORKER_STOP_TIMEOUT_SEC
    )
    assert session._running is False
