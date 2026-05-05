import mysql
from mysql.connector import pooling
from settings import Settings

settings = Settings()


def init_db():
    conn = mysql.connector.connect(
        host=settings.DB_HOST,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
    )
    cursor = conn.cursor()
    with open(file='db/init.sql', mode='r', encoding='utf-8') as fp:
        for stmt in fp.read().split(';'):
            if stmt.strip():
                cursor.execute(stmt)
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
