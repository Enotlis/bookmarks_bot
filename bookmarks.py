import re
import exceptions
import db
import parse_mangalib


async def add_bookmark(chat_id: int, raw_message: str) -> str:
    """Добавляет мангу в закладки"""
    url_manga = _parse_message(raw_message)
    conn = await db.connect_db()

    result = await conn.execute("SELECT * FROM bookmark "
                    f"WHERE manga_id='{url_manga}' AND "
                    f"chat_id='{chat_id}'")
    if result[-1] == '1':
        return "Mанга уже есть в закладках"

    result = await conn.fetchrow("SELECT manga_name FROM manga "
                    f"WHERE url_manga='{url_manga}'")
    await conn.close()

    if not result:
        manga_name = await _add_manga(url_manga)
    else:
        manga_name = result[0]

    await db.insert("bookmark", {
                'chat_id': chat_id,
                'manga_id': url_manga
    })

    return f'"{manga_name}" добалена в закладки'

async def get_bookmarks_user(chat_id: int) -> tuple:
    """Возвращает кортеж содержащий закладки пользователя"""
    conn = await db.connect_db()

    rows = await conn.fetch("SELECT bookmark.id, manga.manga_name,"
                            "manga.last_chapte, bookmark.manga_id "
                            "FROM bookmark LEFT JOIN manga "
                            "ON bookmark.manga_id=manga.url_manga "
                            f"WHERE bookmark.chat_id='{chat_id}'")

    await conn.close()

    bookmarks_user = tuple(row for row in rows)

    return bookmarks_user

async def delete_bookmark(chat_id: str, id_row: str) -> str:
    """Удаляет мангу из закладок пользователя"""
    conn = await db.connect_db()
    result = await conn.execute("SELECT id FROM bookmark "
                   f"WHERE id='{id_row}' AND "
                   f"chat_id='{chat_id}'")

    if result[-1] == '0':
        return "Данной манги нет в ваших закладках"

    await db.delete('bookmark',
                   'id',
                   id_row)

    return 'Манга удалена из закладок'

async def _add_manga(url_manga: str) -> str:
    """Добавлет мангу в БД"""
    manga_info = await parse_mangalib.parse_manga_page(url_manga)
    await db.insert("manga", {
                  'url_manga': url_manga,
                  'manga_name': manga_info.name,
                  'last_chapte': manga_info.last_chapte,
    })

    return manga_info.name

def _parse_message(raw_message: str) -> str:
    """Парсит текст пришедшего сообщения с сылкой на мангу"""
    regexp_result = re.search(r'https://desu\.me/manga/[\w\d\.-]+/', raw_message)
    if regexp_result is None:
        raise exceptions.NotCorrectMessage(
            "Не могу понять сообщение. Напишите сообщение в формате, "
            "например:\n /add https://desu.me/manga/blade-of-demon-destruction-colored.3433/")
    url_manga = regexp_result[0]
    return url_manga
 