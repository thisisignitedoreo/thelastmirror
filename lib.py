from bs4 import BeautifulSoup
from operator import mul
from functools import reduce
import threading
import requests
import string
import math
import json
import os
import re

if not os.path.isdir("name-list"):
    os.mkdir("name-list")

if not os.path.isdir("paginated-list"):
    os.mkdir("paginated-list")

if not os.path.isdir("games"):
    os.mkdir("games")

def reshape(lst, shape):
    if len(shape) == 1:
        return lst
    n = reduce(mul, shape[1:])
    return [reshape(lst[i*n:(i+1)*n], shape[1:]) for i in range(len(lst)//n)]


def fix_name(name):
    res = ""
    for i in name:
        if i in string.ascii_letters or i in string.digits:
            res += i
        else:
            res += "-"
    return res.lower()

allGamesName = []

pages = 0

def parse(one_only, threaded):
    global pages
    soup = BeautifulSoup(requests.get("https://thelastgame.ru/").content, 'html.parser')
    pages = int(soup.select_one('#page > div > div > div > section > div:nth-child(2) > nav > div > span.pages').decode_contents().replace('Страница 1 из ', ''))
    print(f"Pages: { {"a": pages, "1": 1, "3": 3}[one_only]}")

    if threaded:
        threads = []

        for i in range({"a": pages, "1": 1, "3": 3}[one_only]):
            thread = threading.Thread(target=parse_page, args=(i, {"a": pages, "1": 1, "3": 3}[one_only]))
            thread.daemon = True
            threads.append(thread)

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

    else:
        for i in range({"a": pages, "1": 1, "3": 3}[one_only]):
            parse_page(i, {"a": pages, "1": 1, "3": 3}[one_only])

    return allGamesName

def parse_page(i, pages):
    # print(f" Processing page {i + 1}/{pages} ({((i + 1) / pages * 100):.02f}%)")
    # print(f" Processing page {i + 1}")

    soup = BeautifulSoup(requests.get(f"https://thelastgame.ru/page/{i + 1}").content, 'html.parser')

    for j in [i.a.get("href") for i in soup.select("h2.post-title")]:
        subsoup = BeautifulSoup(requests.get(j).content, "html.parser")
        dl_link = subsoup.select_one(".btn_green").get("href")
        if dl_link.endswith(".torrent"):
            string = "Processing \"" + j.split("/")[-2] + "\" (" + f"{i + 1}/{pages} {(i + 1) / pages * 100:.2f}%" + ")"
            print(string + (" " * (os.get_terminal_size()[0] - len(string) - 1)), end="\r")
            try:
                if not subsoup.select(
                    "#page > div > div > div > section > div:nth-child(2) > article > div > div.entry.themeform > div.entry-inner > p > strong"):
                    desc = subsoup.select_one(
                        '#page > div > div > div > section > div:nth-child(2) > article > div > div.entry.themeform > div.entry-inner > p').findAll(
                        text=True, recursive=False)[0]
                elif subsoup.select(
                    "#page > div > div > div > section > div:nth-child(2) > article > div > div.entry.themeform > div.entry-inner > p > strong > a"):
                    desc = subsoup.select_one(
                        '#page > div > div > div > section > div:nth-child(2) > article > div > div.entry.themeform > div.entry-inner > p > strong').findAll(
                        text=True, recursive=False)[0] + subsoup.select_one(
                        '#page > div > div > div > section > div:nth-child(2) > article > div > div.entry.themeform > div.entry-inner > p').findAll(
                        text=True, recursive=False)[0]
                elif subsoup.select(
                    "#page > div > div > div > section > div:nth-child(2) > article > div > div.entry.themeform > div.entry-inner > p > a"):
                    desc = subsoup.select_one(
                        '#page > div > div > div > section > div:nth-child(2) > article > div > div.entry.themeform > div.entry-inner > p > strong').findAll(
                        text=True, recursive=False)[0] + subsoup.select_one(
                        '#page > div > div > div > section > div:nth-child(2) > article > div > div.entry.themeform > div.entry-inner > p').findAll(
                        text=True, recursive=False)[0]
                else:
                    desc = subsoup.select_one(
                        '#page > div > div > div > section > div:nth-child(2) > article > div > div.entry.themeform > div.entry-inner > p > strong').findAll(
                        text=True, recursive=False)[0] + subsoup.select_one(
                        '#page > div > div > div > section > div:nth-child(2) > article > div > div.entry.themeform > div.entry-inner > p').findAll(
                        text=True, recursive=False)[1]
            except:
                continue

            game = {}
            game["dl_link"] = dl_link
            game["name"] = subsoup.select('.btn_blue')[1].decode_contents().replace('<div style=\"position:absolute;bottom:-6px;right:0px;font-size:12px;margin-right: 10px;color: #eee;\"><em>через uFiler</em></div>', '').replace('Скачать игру ', '')
            game["description"] = desc

            game["screenshots"] = [i.get("href") for i in subsoup.select('#gamepics > p > a')]  # [i.get("href") for i in subsoup.select('#gamepics > p')]

            game["slug"] = j.split("/")[-2]

            try:
                if subsoup.select(
                    "#page > div > div > div > section > div:nth-child(2) > article > div > div.entry.themeform > div.entry-inner > p > a"):
                    game["image"] = subsoup.select_one('#page > div > div > div > section > div:nth-child(2) > article > div > div.entry.themeform > div.entry-inner > p > a').get("href")
                if subsoup.select(
                    "#page > div > div > div > section > div:nth-child(2) > article > div > div.entry.themeform > div.entry-inner > p > img"):
                    game["image"] = subsoup.select_one('#page > div > div > div > section > div:nth-child(2) > article > div > div.entry.themeform > div.entry-inner > p > img').get("src")
                else:
                    game["image"] = subsoup.select_one('#page > div > div > div > section > div:nth-child(2) > article > div > div.entry.themeform > div.entry-inner > p > strong > a').get("href")
            except AttributeError:
                game["image"] = "bad_image.png"

            allGamesName.append(game)

def build(allGamesName, down_all):
    games_unsorted = allGamesName
    allGamesName = sorted(allGamesName, key=lambda gms: gms["name"].strip())

    filtered_words = ["horny", "hentai", "голые", "сиськ", "dragon ball", "counter-strike", "street fighter", "freaky", "undress", "seduc"]
    mask = "*"

    print("Deleting bad words")
    for i in allGamesName:
        for j in filtered_words:
            i["name"] = re.sub(j, mask * len(j), i["name"], flags=re.IGNORECASE)
            i["description"] = re.sub(j, mask * len(j), i["description"], flags=re.IGNORECASE)

        i["name"] = i["name"].strip()
        
    for i in games_unsorted:
        for j in filtered_words:
            i["name"] = re.sub(j, mask * len(j), i["name"], flags=re.IGNORECASE)
            i["description"] = re.sub(j, mask * len(j), i["description"], flags=re.IGNORECASE)

        i["name"] = i["name"].strip()

    page = 0
    game_per_page = 16
    max_page = len(games_unsorted) // game_per_page
    pages = []
    
    page_games = []

    for i in games_unsorted:
        page_games.append(i)
        
        if len(page_games) == game_per_page:
            pages.append(page_games)
            page_games = []

    pages.append(page_games)

    print("Constructing index")

    index_html = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">

    <link rel="stylesheet" href="/css/style.css">
    <link rel="stylesheet" href="/css/index.css">
    <title>TheLastMirror</title>
</head>
<body>
    <div class="wrapper">
        <header>

            <a class="logo" href="/">TheLastMirror</a>

            <ul>
                <li><a href="/paginated-list/">Страничный список</a></li>
                <li><a href="/name-list/">Одностраничный список</a></li>
            </ul>

        </header>

        <main>

            <a href="/paginated-list/">
                <div class="heading">Страничный список</div>
                <div class="subheading">Список с логотипами и описаниями, поделенный на страницы.</div>
            </a>
            <a href="/name-list/">
                <div class="heading">Одностраничный список</div>
                <div class="subheading">Список только с названиями игр, для старого-доброго поиска по Ctrl-F</div>
            </a>

        </main>
    
    </div>
</body>
</html>
"""

    open("index.html", "w", encoding="utf-8").write(index_html)

    print("Constructing name list")
    name_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">

    <link rel="stylesheet" href="/css/style.css">
    <link rel="stylesheet" href="/css/list.css">
    <title>Одностраничный список - TheLastMirror</title>
</head>
<body>
    <div class="wrapper">
    
        <header>

            <a class="logo" href="/">TheLastMirror</a>

        </header>

        <main>
            <ul>"""

    for game in allGamesName:
        tname = game['dl_link'].split('/')[-1]
        for j in filtered_words:
            tname = re.sub(j, '-' * len(j), tname.replace('.torrent', ''), flags=re.IGNORECASE) + ".torrent"

        name_html += f"""
                <li>
                    <a href="/games/{game["slug"]}">{game["name"]}</a>
                    <a href="/games/{game["slug"]}/{tname}"><img src="/img/download.svg" alt="Скачать"></a>
                </li>"""

    name_html += """
            </ul>
        </main>

    </div>
</body>
</html>"""

    with open("name-list/index.html", "w", encoding="utf-8") as f:
        f.write(name_html)

    print("Constructing paginated list")
    for page, pg in enumerate(pages):
        paginated_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">

    <link rel="stylesheet" href="/css/style.css">
    <link rel="stylesheet" href="/css/page.css"> """ + f"""
    <title>Страница {page + 1} из {max_page + 1} - TheLastMirror</title> """ + r"""
</head>
<body>
    <div class="wrapper">

        <header>

            <a class="logo" href="/">TheLastMirror</a>

            <ul>
                <li>""" + f"""
                    <{'a' if page != 0 else 'span'} href="{page - 1 if page - 1 != 0 else "index"}.html"><div class="back"></div></{'a' if page != 0 else 'span'}>

                    <span>{page + 1} / {max_page + 1}</span>

                    <{'a' if page != max_page else 'span'} href="{page + 1}.html"><div class="forward"></div></{'a' if page != max_page else 'span'}>
                </li>""" + r"""
            </ul>

        </header>

        <main>

            <ul class="grid">"""

        for k, i in enumerate(pg):
            # paginated_html += f"""
            #         <div>
            #             <a href="/games/{i['slug']}/">
            #                 <img src="{'https://thelastmirror.uk.to/bad_image.png' if i["image"] == "bad_image.png" else i["image"]}">
            #             </a>
            #             <h3>{i["name"]}</h3>
            #             <p>{i["description"]}...</p>
            #             <a href="/games/{i['slug']}/" class="big_a">Подробнее...</a>
            #         </div>"""
            paginated_html += f"""
                <li>
                    <a style="background-image: linear-gradient(180deg, rgba(0,0,0,0), #000), url({'/bad_image.png' if i["image"] == "bad_image.png" else i["image"]});" href="/games/{i['slug']}/">
                        <span>{i["name"]}</span>
                        <span>{i["description"][:80].strip()}...</span>
                    </a>
                </li>"""

        paginated_html += """
            </ul>

        </main>

    </div>
</body>
</html>
"""

        with open(f"paginated-list/{page}.html" if page != 0 else f"paginated-list/index.html", "w", encoding="utf-8") as f:
            f.write(paginated_html)

    print("Constructing game pages")
    for k, game in enumerate(allGamesName):
        print(f"Processing: {k + 1}/{len(allGamesName)}", end="\r")
        orig = game['dl_link'].split('/')[-1]
        tname = orig
        for j in filtered_words:
            tname = re.sub(j, '-' * len(j), tname.replace('.torrent', ''), flags=re.IGNORECASE) + ".torrent"

        if not game["dl_link"].endswith(".torrent") or "?" in game["image"]:
            continue

        if not os.path.isdir(f"games/{game['slug']}/"):
            os.mkdir(f"games/{game['slug']}/")

        for i in game["screenshots"]:
            if os.path.isfile(f"games/{game['slug']}/{i.split('/')[-1]}"):
                try:
                    os.remove(f"games/{game['slug']}/{i.split('/')[-1]}")
                except:
                    print("Nope")

        if os.path.isfile(f"games/{game['slug']}/{game['image'].split('/')[-1]}"):
            if game["image"] != "bad_image.png":
                try:
                    os.remove(f"games/{game['slug']}/{game['image'].split('/')[-1]}")
                except:
                    print("Nope")
        try:
            if not os.path.isfile(f"games/{game['slug']}/{tname}"):
                with open(f"games/{game['slug']}/{tname}", "wb") as f:
                    f.write(requests.get(game['dl_link']).content)
            elif down_all:
                new_file = requests.get(game["dl_link"]).content
                open(f"games/{game['slug']}/{tname}", "wb").write(new_file)
        except requests.exceptions.ReadTimeout:
            print(f"Could not download .torrent for \"{game['slug']}\", skipping")

        with open(f"games/{game['slug']}/index.html", "w", encoding="utf-8") as f:
            f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">

    <link rel="stylesheet" href="/css/style.css">
    <link rel="stylesheet" href="/css/game.css">""" + f"""
    <title>{game['name']} - TheLastMirror</title>""" + r"""
</head>
<body>
    <div class="wrapper">
    
        <header>

            <a class="logo" href="/">TheLastMirror</a>

        </header>

        <main>

            <div class="line">""" + f"""
                <span class="header">{game["name"]}</span>
                <a class="header download" href="/games/{game['slug']}/{tname}">Скачать .torrent</a>
            </div>

            <div class="line main">
                <div class="row">
                    <img width="460" src="{'/bad_image.png' if game["image"] == "bad_image.png" else game["image"]} " alt="Баннер" class="image">
                    <div class="screenshots">
                        {'''
'''.join([f'<img width="460" src="{i}" alt="Скриншот">' for i in game["screenshots"]])}
                    </div>
                </div>
                <div class="row">
                    <div class="description">
                        {game['description']}
                    </div>
                </div>
            </div>

        </main>
    </div>
</body>
</html>""")
    print("\nDone!")
