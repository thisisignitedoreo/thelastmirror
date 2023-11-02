#!/usr/bin/env python3

import json
import sys
import lib

if not "--parse" in sys.argv and not "--build" in sys.argv:
	print(f"usage: python {sys.argv[0]} <[--build] [--parse]>")

parse = "--parse" in sys.argv
build = "--build" in sys.argv

pages = "a"
if "--first" in sys.argv: pages = "1"
if "--few" in sys.argv: pages = "3"
if "--full" in sys.argv: pages = "a"

if parse:
	print("Parsing...\n")
	parsed = lib.parse(pages, "--threaded" in sys.argv)
	open("full.json", "w").write(json.dumps(parsed))

if build:
	print("Building...\n")
	game_library = json.load(open("full.json", "r"))
	lib.build(game_library, "--download" in sys.argv)
	print()
