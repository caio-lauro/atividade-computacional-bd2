from http import HTTPStatus
from fastapi import APIRouter, HTTPException, Response
from mysql.connector import errors as mysql_errors

from db import db_fetch_one, db_fetch_all, db_insert, db_modify
from schemas import AutorSchema, AtualizarAutorSchema
from db_schemas import AutorDBSchema


router = APIRouter(prefix='/autor', tags=['Autores'])


@router.get('/', response_model=list[AutorDBSchema])
def ler_autores(
    id_autor: int | None = None,
    nome: str | None = None,
    nacionalidade: str | None = None
):
    conditions = []
    params = []

    if id_autor:
        conditions.append('id = %s')
        params.append(id_autor)

    if nome:
        conditions.append('nome LIKE %s')
        params.append(f'%{nome}%')

    if nacionalidade:
        conditions.append('nacionalidade = %s')
        params.append(nacionalidade)

    where = '' if not conditions else 'WHERE ' + ' AND '.join(conditions)
    fetch = db_fetch_all(
        'SELECT * FROM autores '
        f'{where}',
        params
    )

    if not fetch:
        raise HTTPException(
            HTTPStatus.NOT_FOUND,
            'Nenhuma estante com esses critérios foi encontrada.'
        )
    
    return fetch


@router.post('/', status_code=HTTPStatus.CREATED, response_model=int)
def criar_autor(autor: AutorSchema):
    try:
        return db_insert(
            'INSERT INTO autores (nome, nacionalidade) VALUES (%s, %s)',
            (autor.nome, autor.nacionalidade)
        )
    except mysql_errors.Error as e:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e))
    

@router.put('/{id_autor}', response_model=int)
def atualizar_autor(
    id_autor: int,
    autor: AtualizarAutorSchema,
    response: Response
):
    # Buscar autor para ver se existe
    if db_fetch_one('SELECT id FROM autores WHERE id = %s', (id_autor,)) is None:
        raise HTTPException(
            HTTPStatus.NOT_FOUND,
            'Nenhum autor com esse ID foi encontrada.'
        )
    
    if not autor.nome and not autor.nacionalidade:
        response.status_code = HTTPStatus.NO_CONTENT

    if autor.nome and autor.nacionalidade:
        return db_modify(
            'UPDATE autores SET nome = %s, nacionalidade = %s WHERE id = %s',
            (autor.nome, autor.nacionalidade, id_autor)
        )
        
    if autor.nome:
        return db_modify(
            'UPDATE autores SET nome = %s WHERE id = %s',
            (autor.nome, id_autor)
        )

    return db_modify(
        'UPDATE autores SET nome = %s, nacionalidade = %s WHERE id = %s',
        (autor.nacionalidade, id_autor)
    )


@router.delete('/{id_autor}', response_model=int)
def deletar_autor(id_autor: int):
    # Buscar autor para ver se existe
    if db_fetch_one('SELECT id FROM autores WHERE id = %s', (id_autor,)) is None:
        raise HTTPException(
            HTTPStatus.NOT_FOUND,
            'Nenhum autor com esse ID foi encontrada.'
        )
    
    rows = db_modify(
        'DELETE FROM autores_livros WHERE id_autor = %s',
        (id_autor,)
    )

    rows += db_modify(
        'DELETE FROM autores WHERE id = %s',
        (id_autor,)
    )

    return rows