from lib import parse

parsed = parse()

with open("index.json", "w") as f:
    f.write(json.dumps(parsed))
    
