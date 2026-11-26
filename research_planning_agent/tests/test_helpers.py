import json
from app.graph import _json_from_text

def test_json_parser_handles_fenced_array():
    data = _json_from_text('```json\n[{"title":"A","query":"a"}]\n```')
    assert data[0]["query"] == "a"

def test_json_parser_handles_plain_array():
    assert json.loads(json.dumps(_json_from_text('[{"title":"B","query":"b"}]')))[0]["title"] == "B"
