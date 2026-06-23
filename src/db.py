import mysql
from mysql.connector import pooling
from settings import Settings
from log import *
from fastapi import HTTPException
from mysql.connector import errors as mysql_errors

settings = Settings()


def run_sql_file(cursor, path: str, separator: str = ';'):
    with open(file=path, mode='r', encoding='utf-8') as fp:
        for stmt in fp.read().split(separator):
            if stmt.strip():
                try:
                    cursor.execute(stmt)
                except Exception as e:
                    log_error(f'Erro no statement:\n{stmt}\nErro: {e}')
                    raise


def init_db():
    conn = mysql.connector.connect(
        host=settings.DB_HOST,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
    )

    cursor = conn.cursor()

    log_info('Criando database caso não exista.')
    cursor.execute(f'CREATE DATABASE IF NOT EXISTS {settings.DATABASE}')
    cursor.execute(f'USE {settings.DATABASE}')

    log_info('Criando tabelas.')
    run_sql_file(cursor, 'db/init.sql')

    log_info('Criando visões.')
    run_sql_file(cursor, 'db/views.sql')

    log_info('Criando funções.')
    run_sql_file(cursor, 'db/functions.sql', separator='---')

    log_info('Criando procedures.')
    run_sql_file(cursor, 'db/procedures.sql', separator='---')

    log_info('Criando triggers.')
    run_sql_file(cursor, 'db/triggers.sql', separator='---')

    conn.commit()
    cursor.close()
    conn.close()

    log_info('Inicialização finalizada.')


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


def db_fetch_one(sql, params=()) -> dict | None:
    """Função usada para obter somente um valor através da query"""
    return _db_fetch(sql, params, False)


def db_fetch_all(sql, params=()) -> list[dict]:
    """Função usada para obter uma lista de valores através da query"""
    return _db_fetch(sql, params, True)


def _db_fetch(sql, params, return_multiple: bool) -> list[dict] | dict | None:
    """
    Função interna usada por `db_fetch_one` e `db_fetch_all`,
    a fim de evitar repetição de código.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(sql, params)
        return cursor.fetchall() if return_multiple else cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def db_insert(sql, params=()) -> int:
    """
    Função para inserir no banco de dados.

    Retorna o id da última inserção.
    """
    return _db_execute(sql, params, True)


def db_modify(sql, params=()) -> int:
    """
    Função para realizar modificações no banco de dados, como updates e deletes.

    Retorna o número de linhas afetados.
    """
    return _db_execute(sql, params, False)


def _db_execute(sql, params, is_insert) -> int:
    """
    Função interna para realizar atualizações: inserts, updates e deletes.

    Retorna lastrowid para insert e rowcount, caso contrário.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params)
        conn.commit()
        return cursor.lastrowid if is_insert else cursor.rowcount
    finally:
        cursor.close()
        conn.close()


def db_transaction(stmts: list[tuple[str, tuple]]) -> list[int]:
    """
    Função interna para realizar múltiplas instruções. \
    Usa internamente transações para reverter em caso de erro.

    Retorna lastrowid para insert e rowcount, caso contrário.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        results = []
        for stmt, params in stmts:
            cursor.execute(stmt, params)
            results.append(cursor.lastrowid or cursor.rowcount)
        conn.commit()
        return results
    except mysql_errors.Error as e:
        conn.rollback()
        log_error(f'Erro no SQL: {stmt}')
        log_error(f'Erro: {e}')
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()
