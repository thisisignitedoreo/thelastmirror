from bs4 import BeautifulSoup
from bs4 import Comment
import requests
import json
import os

nl_ = "\n"

def flatten_list(_2d_list):
    flat_list = []
    for element in _2d_list:
        if type(element) is list:
            for item in element:
                flat_list.append(item)
        else:
            flat_list.append(element)
    return flat_list

def parse():
    problem_count = 0
    all = []
    try:
        website = "https://thelastgame.ru"
        
        soup = BeautifulSoup(requests.get(website).content, "html.parser")
        
        pages_count = int(soup.select_one("#page > div > div > div > section > div:nth-child(2) > nav > div > span.pages").getText().split(" ")[-1])
        for nm in range(1, pages_count):
            print(f"- Processing page {nm}")
            subsoup = BeautifulSoup(requests.get(website if nm == 1 else website + f"/page/{nm}/").content, "html.parser")
            all_soups = []
            
            for i in subsoup.select("article.grid-item"):
                if i.name == "div":
                    for j in i:
                        all_soups.append(j)
                elif i.name == "article":
                    all_soups.append(i)
            
            for i in all_soups:
                try:
                    url_to_game = i.select_one("div.post-thumbnail > a")["href"]
                    print(f"- Processing game: {website}/{url_to_game.replace(website, '')[1:-1]}/")
                    gamesoup = BeautifulSoup(requests.get(url_to_game).content, "html.parser")
                    try:
                        title = gamesoup.select_one("#page > div > div > div > section > div:nth-child(2) > article > div > div.entry.themeform > div.entry-inner > center:nth-child(9) > h2").text[8:-11]
                    except AttributeError:
                        try:
                            title = gamesoup.select_one("#page > div > div > div > section > div:nth-child(2) > article > div > div.entry.themeform > div.entry-inner > center:nth-child(10) > h2").text[8:-11]
                        except AttributeError:
                            try:
                                title = gamesoup.select_one("#page > div > div > div > section > div:nth-child(2) > article > div > div.entry.themeform > div.entry-inner > center:nth-child(11) > h2").text[8:-11]
                            except AttributeError:
                                title = gamesoup.select_one("#page > div > div > div > section > div:nth-child(2) > article > div > div.entry.themeform > div.entry-inner > center:nth-child(12) > h2").text[8:-11]
                    
                    try:
                        game_info = gamesoup.select_one("#page > div > div > div > section > div:nth-child(2) > article > div > div.entry.themeform > div.entry-inner > div:nth-child(5)").text
                        
                        if game_info.startswith("\nМинимальные системные требованияОперационная система"):
                            game_info = gamesoup.select_one("#page > div > div > div > section > div:nth-child(2) > article > div > div.entry.themeform > div.entry-inner > div:nth-child(4)").text
                    except AttributeError:
                        game_info = gamesoup.select_one("#page > div > div > div > section > div:nth-child(2) > article > div > div.entry.themeform > div.entry-inner > div:nth-child(6)").text
                    
                    try:
                        banner = gamesoup.select_one("#page > div > div > div > section > div:nth-child(2) > article > div > div.entry.themeform > div.entry-inner > p > strong > a")["href"]
                    except AttributeError:
                        banner = gamesoup.select_one("#page > div > div > div > section > div:nth-child(2) > article > div > div.entry.themeform > div.entry-inner > p > a")["href"]
                    
                    all.append({
                        "title": title,
                        "description": gamesoup.select_one("#page > div > div > div > section > div:nth-child(2) > article > div > div.entry.themeform > div.entry-inner > p").text,
                        "dl_link": gamesoup.select_one(".btn_green")["href"],
                        "banner": banner,
                        "screenshots": [i["href"] for i in gamesoup.select_one("#gamepics > p") if i.name == "a"],
                        "game_info": game_info.replace("\nИнформация о игре", "Информация о игре\n")[:-2],
                        "game_id": url_to_game.replace(website, "")[1:-1]
                    })
                    print(all)
                    exit()
                except Exception as err:
                    problem_count += 1
                    print(f"Skipped! Cause: {err}")
    except KeyboardInterrupt:
        print("OK, aborting...")
        if problem_count != 0:
            print(f"Skipped games: {problem_count}")
    finally:
        return all

def build(tree, download):
    if not os.path.isdir("games"):
        os.mkdir("games")
    
    open("index.html", w).write("""<html>
<head>
    <title>TheLastMirror</title>
    <style>
        @import url('https://fonts.googleapis.com/css?family=Rubik&display=swap');
        :root {
            font-family: "Rubik", sans-serif;
            background-color: rgb(18, 18, 18);
            color: #ffffff;
        }
        
        .banner {
            object-fit: cover;
            width: 15%;
            max-height: 15%;
        }
    </style>
</head>
<body>
    <div style="text-align: center;">""" + "\n".join([f"""
        <a href="/games/{i["game_id"]}/"><img src="{i["banner"]}" class="banner"><br><h2>{i["title"]}</h2></a> <a href="{"/games/{i["game_id"]}/{i["game_id"]}.torrent" if download else i["dl_link"]}">(скачать)</a>
        <hr>""" for i in tree]) + f"""
    <div>
</body>
</html>""")
    
    for i in tree:
        # game pages
        if not os.path.isdir(f"games/{i['game_id']}"):
            os.mkdir(f"games/{i['game_id']}")
        
        if download:
            open(f"games/{i['game_id']}/{i['game_id']}.torrent", "wb").write(requests.get(i["dl_link"]).content)
        
        open(f"games/{i['game_id']}/index.html", "w").write("""<html>
<head>
    <title>title - TheLastMirror</title>
    <style>
        @import url('https://fonts.googleapis.com/css?family=Rubik&display=swap');
        :root {
            font-family: "Rubik", sans-serif;
            background-color: rgb(18, 18, 18);
            color: #ffffff;
        }
        
        .screenshot {
            object-fit: cover;
            width: 75%;
            max-height: 75%;
        }
        .banner {
            object-fit: cover;
            width: 35%;
            max-height: 35%;
        }
    </style>
</head>
<body>
    <div style="text-align: center;">""" + f"""
        <img src="{i["banner"]}" class="banner"><br>
        <h1>title</h1>
        <h5>description</h5>
        {nl_.join([f'''<img src="{j}" class="screenshot"><br>
        <p style="font-size: 10px;">Скриншот {k}</p>''' for k, j in enumerate(i["screenshots"])])}
        <a href="{f"/games/{i['game-id']}/{i['game-id']}.torrent" if download else i["dl_link"]}"><h1>Скачать .torrent</h1></a>
    </div>
</body>
</html>""")


parsed = parse()

with open("index.json", "w") as f:
    f.write(json.dumps(parsed))

# build([{"title": "title", "description": "description", "dl_link": "https://example.com ", "banner": "http://placekitten.com/1281/720", "screenshots": ["http://placekitten.com/1280/721", "http://placekitten.com/1280/720"], "game_info": "game_info", "game_id": "game-id"}], False)

build(parsed, True)
