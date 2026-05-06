import mysql
from mysql.connector import pooling
from settings import Settings

settings = Settings()


def run_sql_file(cursor, path: str, separator: str=';'):
    with open(file=path, mode='r', encoding='utf-8') as fp:
        for stmt in fp.read().split(separator):
            if stmt.strip():
                cursor.execute(stmt)

def init_db():
    conn = mysql.connector.connect(
        host=settings.DB_HOST,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
    )

    cursor = conn.cursor()

    # Criar database caso não exista e usá-lo
    cursor.execute(f'CREATE DATABASE IF NOT EXISTS {settings.DATABASE}')
    cursor.execute(f'USE {settings.DATABASE}')

    # Executar instruções de init.sql
    run_sql_file(cursor, 'db/init.sql')
    
    conn.commit()
    cursor.close()
    conn.close()


connection_pool = None


def init_connection_pool():
    global connection_pool

    connection_pool = pooling.MySQLConnectionPool(
        pool_name='main_pool',
        pool_size=5,
        host=settings.DB_HOST,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DATABASE
    )


def get_connection() -> pooling.PooledMySQLConnection:
    global connection_pool

    if connection_pool is None:
        init_connection_pool()

    return connection_pool.get_connection()
