from app.events import EventEmitter, ChangeFileEvent


def test_event_emitter_calls_handlers():
    emitter = EventEmitter()
    called = []

    def handler(cf_evt: ChangeFileEvent):
        called.append(cf_evt)

    emitter.add(handler)

    evt = ChangeFileEvent(event="created", src_path="a", dest_path=None, is_directory=False)
    emitter.emit(evt)

    assert called == [evt]


def test_change_file_event_to_dict_contains_fields():
    evt = ChangeFileEvent(event="moved", src_path="a", dest_path="b", is_directory=True)
    d = evt.to_dict()

    assert d["event"] == "moved"
    assert d["src_path"] == "a"
    assert d["dest_path"] == "b"
    assert d["is_directory"] is True
    assert "timestamp_utc" in d
