import re
import db
import exceptions
import schedule
import asyncio
from typing import NamedTuple
from bs4 import BeautifulSoup
import aiohttp
import queue
import psycopg2
from bookmarks_bot import send_notify

class MangaInfo(NamedTuple):
    """"""
    name: str
    last_chapte: str

async def _get_chats_id(url_manga: str) -> tuple:
    """Получает список всех чатов пользователей у которых 
        манга находится в закладках"""
    conn = await db.connect_db()
    rows = await conn.fetch("SELECT chat_id FROM bookmark "
                   f"WHERE manga_id='{url_manga}'")
    await conn.close()

    chats_id = tuple(row[0] for row in rows)

    return chats_id

async def _notify_users(url_manga: str, message: str):
    '''Уведомляет пользователей о статусе манги'''
    chats_id = await _get_chats_id(url_manga)
    
    if chats_id:
        await asyncio.gather(*[
                    send_notify(chat_id, message)
                    for chat_id in chats_id
              ])

async def parse_manga_page(url_manga: str)->MangaInfo:
    '''Получает информацию о манге с deus.me'''
    async with aiohttp.ClientSession() as session:
        async with session.get(url_manga) as page:
            if str(page.status)[0] == '5':
                raise exceptions.TechnicalWorks((
                    "Сервер недоступен. Попробуйте позже"))
            if page.status == 404:
                raise exceptions.NotCorrectUrl(
                    "Не могу найти мангу. Данной ссылки не существует, "
                    "проверти ее корректность")
            text = await page.text()
    page_soup = BeautifulSoup(text, 'html.parser')

    info_of_manga = page_soup.find('div', class_='b-entry-info').text
    name_manga = page_soup.find('div', class_='titleBar').text.strip('\n')
    info_of_chapters = page_soup.find('div', class_='c-info-right').text
    
    regexp_result = re.search(r'Глава \d{1,4}\.?\d{1,3}', info_of_chapters)
    if regexp_result is not None:
        number_chapter = regexp_result[0].split(' ')[1]
    else:
        raise exceptions.MangaStoppedReleased(
                f'Манга "{name_manga}" перестала публиковаться')

    if 'завершён' in info_of_manga:
        raise exceptions.MangaComplete(
                f'"{name_manga}" завершена. '
                f"Вышло {number_chapter} глав.")

    return MangaInfo(name=name_manga, last_chapte=number_chapter)

async def check_update_mangas(mangas: queue.Queue):
    '''Проверят мангу на наличие обновлений'''
    print('Start')
    while True:
        try:
            manga = mangas.get_nowait()
        except queue.Empty:
            break
        url_manga, last_chapte = manga

        try:
            manga_info = await parse_manga_page(url_manga)
            if last_chapte != manga_info.last_chapte:
                await db.update('manga',{
                                'last_chapte': manga_info.last_chapte,
                                'url_manga': url_manga
                })
                message = (f'"{manga_info.name}" вышла '
                           f"{manga_info.last_chapte} глава\n"
                           f"<a href='{url_manga}'>Читать</a>")
                await _notify_users(url_manga, message)
        except (exceptions.MangaStoppedReleased,
                exceptions.MangaComplete) as e:
            await _notify_users(url_manga, str(e))
            await db.delete('manga',
                            'url_manga',
                            url_manga)

def main():
    conn = psycopg2.connect(**db.config)
    cursor = conn.cursor()
    cursor.execute("SELECT url_manga, last_chapte FROM manga")
    rows = cursor.fetchall()
    conn.close()
    if rows:
        mangas = queue.Queue()
        for row in rows:
            mangas.put(row)

        loop = asyncio.get_event_loop()
        futures = [loop.create_task(check_update_mangas(mangas)) for _ in range(10)]
        group = asyncio.gather(*futures)
        try:
            loop.run_until_complete(group)
        except exceptions.TechnicalWorks:
            pass
        finally:
            loop.close()
            print('Complete')

if __name__ == "__main__":
    schedule.every(6).hours.do(main).run()
    
    while True:
        schedule.run_pending()