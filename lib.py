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

if not os.path.isdir("name_list"):
    os.mkdir("name_list")

if not os.path.isdir("paginated_list"):
    os.mkdir("paginated_list")

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

def parse():
    soup = BeautifulSoup(requests.get("https://thelastgame.ru/").content, 'html.parser')
    pages = int(soup.select_one('#page > div > div > div > section > div:nth-child(2) > nav > div > span.pages').decode_contents().replace('Страница 1 из ', ''))
    print(f"Pages: {pages}")

    threads = []

    for i in range(pages):
        thread = threading.Thread(target=parse_page, args=(i, pages))
        thread.daemon = True
        threads.append(thread)

    for thread in threads:
        thread.start()        

    for thread in threads:
        thread.join()        

    return allGamesName

def parse_page(i, pages):
    # print(f" Processing page {i + 1}/{pages} ({((i + 1) / pages * 100):.02f}%)")
    # print(f" Processing page {i + 1}")
    if i == 0:
        soup = BeautifulSoup(requests.get("https://thelastgame.ru/").content, 'html.parser')
    else:
        soup = BeautifulSoup(requests.get(f"https://thelastgame.ru/page/{i + 1}").content, 'html.parser')

    for j in [i.a.get("href") for i in soup.select("h2.post-title")]:
        subsoup = BeautifulSoup(requests.get(j).content, "html.parser")
        dl_link = subsoup.select_one(".btn_green").get("href")
        if dl_link.endswith(".torrent"):
            print("Processing \"" + j.split("/")[-2] + "\"")
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
            game["description"] = desc[0:200] if len(desc) > 199 else desc
            game["full_description"] = desc

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

def build(allGamesName):
    allGamesName = sorted(allGamesName, key=lambda gms: gms["name"])

    filtered_words = ["horny", "hentai", "голые", "сиськ", "dragon ball", "counter-strike", "street fighter", "freaky", "undress", "seduc"]
    mask = "*"

    print("Deleting bad words")
    lowered_name, lowered_desc, lowered_fdesc = "", "", ""
    for i in allGamesName:
        for j in filtered_words:
            i["name"] = re.sub(j, "*" * len(j), i["name"], flags=re.IGNORECASE)
            i["description"] = re.sub(j, "*" * len(j), i["description"], flags=re.IGNORECASE)
            i["full_description"] = re.sub(j, "*" * len(j), i["full_description"], flags=re.IGNORECASE)

    page = 0
    game_per_page = 28
    max_page = len(allGamesName) // game_per_page
    pages = reshape(allGamesName, [1, game_per_page])

    print("Constructing name list")
    name_html = """<!doctype html>
    <html>
        <head>
            <style>
                @import url('https://fonts.googleapis.com/css?family=Lato&display=swap');
                :root {
                    font-family: "Lato", sans-serif;
                    background-color: rgb(18, 18, 18);
                    color: #ffffff;
                }
                a {
                    color: #9999ff;
                }
                .grid {
                    display: grid;
                    grid-template-columns: 1fr 1fr 1fr;
                    column-gap: 10px;
                    row-gap: 10px;
                    margin-top: 10px;
                    margin-bottom: 10px;
                }
                img {
                    object-fit: cover;
                    width: 100%;
                    max-height: 100%;
                }
                .big_a {
                    font-size: 24px;
                }
            </style>
            <link rel="icon" type="image/x-icon" href="https://raw.githubusercontent.com/thisisignitedoreo/thelastmirror/master/favicon.ico">
            <title>Список названий - The Last Mirror</title>
        </head>
        <body>
            <div style="text-align: center">"""

    for game in allGamesName:
        tname = game['dl_link'].split('/')[-1]
        for j in filtered_words:
            tname = re.sub(j, '-' * len(j), tname.replace('.torrent', ''), flags=re.IGNORECASE) + ".torrent"

        name_html += f"""
                <p><a href="/games/{game['slug']}/index.html">{game["name"]}</a> <a href="/games/{game['slug']}/{tname}">(скачать)</a></p>"""

    name_html += """
            </div>
        </body>
    </html>
    """

    with open("name_list/index.html", "w", encoding="utf-8") as f:
        f.write(name_html)

    print("Constructing paginated list")
    for pg in pages:
        paginated_html = """<!doctype html>
        <html>
            <head>
                <style>
                    @import url('https://fonts.googleapis.com/css?family=Lato&display=swap');
                    :root {
                        font-family: "Lato", sans-serif;
                        background-color: rgb(18, 18, 18);
                        color: #ffffff;
                    }
                    a {
                        color: #9999ff;
                    }
                    .grid {
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                        column-gap: 10px;
                        row-gap: 10px;
                    }
                    img {
                        object-fit: cover;
                        width: 100%;
                        max-height: 100%;
                    }
                    .big_a {
                        font-size: 24px;
                    }
                </style>
                <link rel="icon" type="image/x-icon" href="https://raw.githubusercontent.com/thisisignitedoreo/thelastmirror/master/favicon.ico">""" + f"""
                <title>Подробный список, страница {page} - The Last Mirror</title>
            </head>
            <body>""" + f"""
                <div style="text-align:center">
                    <a href="index.html"><<</a> {f'<a href="{page - 1 if page - 1 != 0 else "index"}.html">' if page != 0 else ''}<{'</a>' if page != 0 else ''} Страница {page}/{max_page - 1} {f'<a href="{page + 1}.html">' if page != max_page - 1 else ''}>{'</a>' if page != max_page - 1 else ''} <a href="{max_page - 1}.html">>></a>
                </div>""" + """
                <div class="grid">"""

        for k, i in enumerate(pg):
            paginated_html += f"""
                    <div>
                        <a href="/games/{i['slug']}/index.html">
                            <img src="{'https://thelastmirror.tk/bad_image.png' if i["image"] == "bad_image.png" else i["image"]}">
                        </a>
                        <h3>{i["name"]}</h3>
                        <p>{i["description"]}...</p>
                        <a href="/games/{i['slug']}/index.html" class="big_a">Подробнее...</a>
                    </div>"""

        paginated_html += """</div>
                    """ + f"""
                    <div style="text-align:center">
                        <a href="index.html"><<</a> {f'<a href="{page - 1 if page - 1 != 0 else "index"}.html">' if page != 0 else ''}<{'</a>' if page != 0 else ''} Страница {page}/{max_page - 1} {f'<a href="{page + 1}.html">' if page != max_page - 1 else ''}>{'</a>' if page != max_page - 1 else ''} <a href="{max_page - 1}.html">>></a>
                    </div>""" + """
                </div>
            </body>
        </html>
        """

        with open(f"paginated_list/{page}.html" if page != 0 else f"paginated_list/index.html", "w", encoding="utf-8") as f:
            f.write(paginated_html)

        page += 1

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
        except requests.exceptions.ReadTimeout:
            print(f"Could not download .torrent for \"{game['slug']}\", skipping")

        with open(f"games/{game['slug']}/index.html", "w", encoding="utf-8") as f:
            f.write("""<!doctype html>
    <html>
        <head>
            <style>
                @import url('https://fonts.googleapis.com/css?family=Lato&display=swap');
                :root {
                    font-family: "Lato", sans-serif;
                    background-color: rgb(18, 18, 18);
                    color: #ffffff;
                }
                a {
                    color: #9999ff;
                }
                .screenshot {
                    object-fit: cover;
                    width: 75%;
                    max-height: 75%;
                }
                .gbanner {
                    object-fit: cover;
                    width: 35%;
                    max-height: 35%;
                }
                .grid {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    column-gap: 10px;
                    row-gap: 10px;
                }
                .big_a {
                    font-size: 24px;
                }
            </style>
            <link rel="icon" type="image/x-icon" href="https://raw.githubusercontent.com/thisisignitedoreo/thelastmirror/master/favicon.ico">""" + f"""
            <title>{game["name"]} - The Last Mirror</title>
        </head>
        <body>
            <div style="text-align: center">
                <img class="gbanner" src="{'https://thelastmirror.tk/bad_image.png' if game["image"] == "bad_image.png" else game["image"]}">
                <h1>{game["name"]}</h1>
                <h5>{game["full_description"]}</h5>""" + f"""
                {'''
    '''.join(['<img class="screenshot" src="' + i + '"><br><p>Скриншот #' + str(k) + '</p>' for k, i in enumerate(game["screenshots"])])}<br>""" + f"""
                <a class="big_a" href="/games/{game['slug']}/{tname}">Скачать .torrent</a>
            </div>
        </body>
    </html>
    """)
    print("\nDone!")