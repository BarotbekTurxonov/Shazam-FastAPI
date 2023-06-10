from fastapi import APIRouter, HTTPException, FastAPI, Response
import aiohttp
from bs4 import BeautifulSoup
import asyncio
import requests

app = FastAPI()


async def get_html(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()


async def shorten_url(url):
    response = await get_html(f"https://is.gd/create.php?format=simple&url={url}")
    return response.strip()


async def search_music(name: str):
    query_split = name.split()

    if len(query_split) >= 2:
        name = '%20'.join(query_split)

    url = f'https://nevomusic.net/music/?search={name}'
    html_content = await get_html(url)
    soup = BeautifulSoup(html_content, 'html.parser')
    pagination = soup.find(class_='paginator')

    if pagination:
        urls = []
        musics = []

        pages = pagination.find_all('a')
        for page in pages:
            urls.append(page['href'])

        data = soup.find_all(class_='icon__radius type--shadow outlink')
        found_music = len(data) - 12
        actual_music = data[:found_music]
        musics.extend([f'http://nevomusic.net{element.get("href")}' for element in actual_music])

        async def get_music_urls(url):
            html_content = await get_html(url)
            page_soup = BeautifulSoup(html_content, 'html.parser')
            elements = page_soup.find_all(class_='icon__radius type--shadow outlink')
            found_music = len(elements) - 12
            actual_music = elements[:found_music]
            return [f'http://nevomusic.net{element.get("href")}' for element in actual_music]

        # To get musics from pagination
        tasks = [get_music_urls(page_url) for page_url in urls]
        results = await asyncio.gather(*tasks)
        for result in results:
            musics.extend(result)

        shortened_urls = []
        for music_url in musics:
            shortened_url = await shorten_url(music_url)
            shortened_urls.append(shortened_url)

        if len(shortened_urls) == 0:
            return {
                "telegram": "@ai_junior",
                "success" : False,
                "data" : "Ushbu so'rov bo'yicha hech qanday qo'shiq topilmadi"
            }
        else:
            return {
                "telegram": "@ai_junior",
                "musics": shortened_urls,
                "success" : True,
                "musics_count": len(shortened_urls),
            }
    else:
        elements = soup.find_all(class_='icon__radius type--shadow outlink')
        found_music = len(elements) - 12
        actual_music = elements[:found_music]
        musics = [f'http://nevomusic.net{element.get("href")}' for element in actual_music]

        shortened_urls = []
        for music_url in musics:
            shortened_url = await shorten_url(music_url)
            shortened_urls.append(shortened_url)

        if len(shortened_urls) == 0:
            return {
                "telegram": "@ai_junior",
                "success" : False,
                "data" : "Ushbu so'rov bo'yicha hech qanday qo'shiq topilmadi"
            }
        else:
            return {
                "telegram": "@ai_junior",
                "success" : True,
                "musics": shortened_urls,
                "musics_count": len(shortened_urls)
            }


@app.get("/music")
async def search_music_endpoint(name: str):
    return await search_music(name)


@app.get("/")
async def Home():
    return {'data' : "Telegram: @ai_junior"}
