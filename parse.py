from lib import parse
import json

parsed = parse()

with open("index.json", "w") as f:
    f.write(json.dumps(parsed))
    
