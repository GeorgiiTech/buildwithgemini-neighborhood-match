from app.a2ui_utils import _extract_prose_and_messages

def test_extract_prose_and_messages_with_surrounding_text():
    sample = """Based on your criteria, here are the top neighborhoods in Austin:
1. Round Rock - Great schools and low crime.

```json
[
  {"beginRendering": {"surfaceId": "card1", "root": "r"}},
  {"surfaceUpdate": {"surfaceId": "card1", "components": []}}
]
```

Feel free to ask about commuting or amenities!"""

    prose, msgs = _extract_prose_and_messages(sample)
    assert "Based on your criteria" in prose
    assert "Feel free to ask" in prose
    assert len(msgs) == 2
    assert "beginRendering" in msgs[0]
    assert "surfaceUpdate" in msgs[1]

def test_extract_prose_and_messages_pure_json():
    sample = """[
  {"beginRendering": {"surfaceId": "card2", "root": "r"}},
  {"surfaceUpdate": {"surfaceId": "card2", "components": []}}
]"""
    prose, msgs = _extract_prose_and_messages(sample)
    assert prose == ""
    assert len(msgs) == 2
