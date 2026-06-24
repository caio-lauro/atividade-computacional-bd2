from http import HTTPStatus
from fastapi import APIRouter, HTTPException, Response, Query
from mysql.connector import errors as mysql_errors

from db import db_fetch_one, db_fetch_all, db_transaction, get_connection
from schemas import ExemplarFisicoSchema, StatusExemplarFisico, AtualizarExemplarFisicoSchema
from db_schemas import ExemplarFisicoDBSchema
from utils import cursor_criar_livro, buscar_estante, buscar_autores_inexistentes, stmts_adicionar_autores_a_livro, stmts_atualizar_livro


router = APIRouter(prefix='/livros/fisico', tags=['Livro Físico'])


@router.get('/', response_model=list[ExemplarFisicoDBSchema])
def ler_livro_fisico(
    id_livro_fisico: int | None = None,
    ISBN: str | None = None,
    titulo: str | None = None,
    status: StatusExemplarFisico | None = None,
    estante: str | None = None,
    autores: list[str] | None = Query(default=None)
):
    conditions = []
    params = []

    if id_livro_fisico:
        conditions.append('id = %s')
        params.append(id_livro_fisico)

    if ISBN:
        conditions.append('ISBN = %s')
        params.append(ISBN)

    if titulo:
        conditions.append('titulo LIKE %s')
        params.append(f'%{titulo}%')

    if status:
        conditions.append('disponivel = %s')
        params.append(status == 'disponível')

    if estante:
        conditions.append('Estante = %s')
        params.append(estante)

    if autores:
        likes = ' OR '.join(['a.nome LIKE %s'] * len(autores))
        conditions.append(
            'view_fisico.id IN (SELECT al.id_livro FROM autores_livros al '
            'INNER JOIN autores a ON al.id_autor=a.id ' 
            f'WHERE {likes})'
        )
        params.extend([f'%{autor}%' for autor in autores])

    where = '' if not conditions else 'WHERE ' + ' AND '.join(conditions)
    fetch = db_fetch_all(
        'SELECT * FROM view_fisico '
        f'{where}',
        params
    )

    if not fetch:
        raise HTTPException(
            HTTPStatus.NOT_FOUND,
            'Nenhum exemplar físico com esses critérios foi encontrado.'
        )
    
    for i in fetch:
        i['autores'] = i['autores'].split(', ')

    return fetch


@router.post('/', status_code=HTTPStatus.CREATED, response_model=int)
def criar_livro_fisico(livro_fisico: ExemplarFisicoSchema):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        autor_inexistente = buscar_autores_inexistentes(livro_fisico.autores)
        if autor_inexistente != -1:
            raise HTTPException(
                HTTPStatus.NOT_FOUND,
                f'Nenhum autor(a) com o ID {autor_inexistente} foi encontrado(a).'
            )
        

        id_estante = buscar_estante(livro_fisico.estante)
        if not id_estante:
            raise HTTPException(
                HTTPStatus.NOT_FOUND,
                'Nenhuma estante com esse identificador foi encontrada.'
            )

        id_estante = id_estante['id']

        espacos = db_fetch_one(
            'SELECT fn_calcular_espacos_disponiveis(%s) AS espacos',
            (id_estante,)
        )['espacos']

        if espacos == 0:
            raise HTTPException(
                HTTPStatus.CONFLICT,
                detail='Essa estante já está lotada.'
            )

        cursor_criar_livro(cursor, livro_fisico)
        id_livro_fisico = cursor.lastrowid

        cursor.execute(
            'INSERT INTO exemplar_fisico (id_fisico, id_estante_associada) VALUES (%s, %s)',
            (id_livro_fisico, id_estante)
        )
        
        for sql, params in stmts_adicionar_autores_a_livro(id_livro_fisico, livro_fisico.autores):
            cursor.execute(sql, params)

        conn.commit()

        return id_livro_fisico
    except mysql_errors.IntegrityError:
        conn.rollback()
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT, detail="ISBN já cadastrado")
    except mysql_errors.Error as e:
        conn.rollback()
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e))
    finally:
        cursor.close()
        conn.close()


@router.put('/{id_livro_fisico}', response_model=int)
def atualizar_livro_fisico(
    id_livro_fisico: int,
    livro_fisico: AtualizarExemplarFisicoSchema,
    response: Response
):
    # Buscar livro e exemplar físico para ver se existe
    if db_fetch_one('SELECT id FROM livros WHERE id = %s', (id_livro_fisico,)) is None \
        or db_fetch_one(
            'SELECT id_fisico FROM exemplar_fisico WHERE id_fisico = %s',
            (id_livro_fisico,)
    ) is None:
        raise HTTPException(
            HTTPStatus.NOT_FOUND,
            'Nenhum livro com esse ID foi encontrado.'
        )
    
    stmts = stmts_atualizar_livro(id_livro_fisico, livro_fisico)

    fields = []
    params = []

    if livro_fisico.status:
        fields.append('disponivel = %s')
        params.append(livro_fisico.status == 'disponível')

    if livro_fisico.estante:
        id_estante = buscar_estante(livro_fisico.estante)
        if not id_estante:
            raise HTTPException(
                HTTPStatus.NOT_FOUND,
                'Nenhuma estante com esse identificador foi encontrada.'
            )

        fields.append('id_estante_associada = %s')
        params.append(id_estante['id'])

    if fields:
        params.append(id_livro_fisico)
        stmts.append((
            f'UPDATE exemplar_fisico SET {','.join(fields)} WHERE id_fisico = %s', 
            params
        ))

    if not stmts:
        response.status_code = HTTPStatus.NO_CONTENT
    
    return sum(db_transaction(stmts))


@router.delete('/{id_livro_fisico}', response_model=int)
def deletar_livro_fisico(id_livro_fisico: int):
    # Buscar livro e exemplar físico para ver se existe
    if db_fetch_one('SELECT id FROM livros WHERE id = %s', (id_livro_fisico,)) is None \
        or db_fetch_one(
            'SELECT id_fisico FROM exemplar_fisico WHERE id_fisico = %s',
            (id_livro_fisico,)
    ) is None:
        raise HTTPException(
            HTTPStatus.NOT_FOUND,
            'Nenhum livro com esse ID foi encontrado.'
        )

    return sum(db_transaction([
        ('DELETE FROM emprestimos WHERE id_fisico = %s', (id_livro_fisico,)),
        ('DELETE FROM exemplar_fisico WHERE id_fisico = %s', (id_livro_fisico,)),
        ('DELETE FROM autores_livros WHERE id_livro = %s', (id_livro_fisico,)),
        ('DELETE FROM livros WHERE id = %s', (id_livro_fisico,))
    ]))
