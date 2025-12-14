import types
from app.watcher import _parse_watch_dirs, HawkeyWatcher  # :contentReference[oaicite:10]{index=10}


def test_parse_watch_dirs():
    assert _parse_watch_dirs(None) == []
    assert _parse_watch_dirs("a; b ;;") == ["a", "b"]


def test_watcher_start_schedules_only_existing(monkeypatch):
    scheduled = []

    class FakeObserver:
        def schedule(self, handler, path, recursive=True):
            scheduled.append((path, recursive))

        def start(self):
            pass

        def is_alive(self):
            return False

        def stop(self):
            pass

    monkeypatch.setattr("app.watcher.Observer", FakeObserver)

    monkeypatch.setattr("app.watcher.os.path.exists", lambda p: p == "ok")

    w = HawkeyWatcher(watch_dirs=["ok", "missing"], recursive=True)
    w.start()

    assert scheduled == [("ok", True)]
