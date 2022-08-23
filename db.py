from typing import Dict
import psycopg2
import asyncpg
import yaml

with open('config_db.yaml', 'r') as file:
    config = yaml.load(file, Loader=yaml.FullLoader)

async def insert(table: str, columns_values: Dict):
    conn = await connect_db()
    columns = ', '.join(columns_values.keys())
    values = tuple(columns_values.values())
    placeholder = ', '.join([f'${i+1}' for i in range(len(columns_values.keys()))])
    try:
        await conn.execute(
                 f"INSERT INTO {table} "
                 f"({columns}) "
                 f"VALUES ({placeholder})",
                 *values)
    except asyncpg.exceptions.UniqueViolationError:
        pass
    await conn.close()

async def delete(table: str, name_id_column: str, row_id: int):
    conn = await connect_db()
    await conn.execute(f"DELETE FROM {table} "
                   f"WHERE {name_id_column}='{row_id}'")
    await conn.close()

async def update(table: str, columns_values: Dict):
    conn = await connect_db()
    
    id_column = tuple(columns_values.keys())[-1]+f'=${len(columns_values.keys())}'
    columns = ', '.join(map(lambda column: column[1]+f'=${column[0]}', 
                            enumerate(tuple(columns_values.keys())[:-1], start=1)
                        ))
    values = tuple(columns_values.values())
    await conn.execute(
             f"UPDATE {table} SET "
             f"{columns} "
             f"WHERE {id_column}",
             *values)

    await conn.close()

async def connect_db():
    conn = await asyncpg.connect(**config)
    return conn

def _init_db(conn):
    """инициализирует БД"""
    cursor = conn.cursor()

    with open('createdb.sql','r') as f:
        sql = f.read()
    cursor.execute(sql)
    conn.commit()
    conn.close()

def check_db_exists():
    """проверяет инициализирована БД, если нет инициализирует"""
    conn = psycopg2.connect(**config)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM pg_tables "
                   "WHERE tablename='manga'")
    table_exists = cursor.fetchall()
    if table_exists:
        conn.close()
        return
    _init_db(conn)

check_db_exists()
