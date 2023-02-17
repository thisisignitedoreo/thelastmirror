from lib import build
import json

with open("index.json", "r") as f:
    parsed = json.loads(f.read())

build(parsed, True)
