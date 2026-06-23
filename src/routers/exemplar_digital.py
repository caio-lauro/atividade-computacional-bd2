from http import HTTPStatus
from fastapi import APIRouter, HTTPException, Response, Query
from mysql.connector import errors as mysql_errors

from db import db_fetch_one, db_fetch_all, db_transaction
from schemas import ExemplarDigitalSchema, AtualizarExemplarDigitalSchema
from db_schemas import ExemplarDigitalDBSchema
from utils import stmt_criar_livro, buscar_autores_inexistentes, stmts_adicionar_autores_a_livro, stmts_atualizar_livro


router = APIRouter(prefix='/livros/digital', tags=['Livro Digital'])


@router.get('/', response_model=list[ExemplarDigitalDBSchema])
def ler_livro_digital(
    id_livro_digital: int | None = None,
    ISBN: str | None = None,
    titulo: str | None = None,
    estante: str | None = None,
    autores: list[str] | None = Query(default=None)
):
    conditions = []
    params = []

    if id_livro_digital:
        conditions.append('id = %s')
        params.append(id_livro_digital)

    if ISBN:
        conditions.append('ISBN = %s')
        params.append(ISBN)

    if titulo:
        conditions.append('titulo LIKE %s')
        params.append(f'%{titulo}%')

    if estante:
        conditions.append('Estante = %s')
        params.append(estante)

    if autores:
        likes = ' OR '.join(['a.nome LIKE %s'] * len(autores))
        conditions.append(
            'view_digital.id IN (SELECT al.id_livro FROM autores_livros al '
            'INNER JOIN autores a ON al.id_autor=a.id '
            f'WHERE {likes})'
        )
        params.extend([f'%{autor}%' for autor in autores])

    where = '' if not conditions else 'WHERE ' + ' AND '.join(conditions)
    fetch = db_fetch_all(
        'SELECT * FROM view_digital '
        f'{where}',
        params
    )

    if not fetch:
        raise HTTPException(
            HTTPStatus.NOT_FOUND,
            'Nenhum exemplar digital com esses critérios foi encontrado.'
        )

    for i in fetch:
        i['autores'] = i['autores'].split(', ')

    return fetch


@router.post('/', status_code=HTTPStatus.CREATED, response_model=int)
def criar_livro_digital(livro_digital: ExemplarDigitalSchema):
    try:
        autor_inexistente = buscar_autores_inexistentes(livro_digital.autores)
        if autor_inexistente != -1:
            raise HTTPException(
                HTTPStatus.NOT_FOUND,
                f'Nenhum autor(a) com o ID {autor_inexistente} foi encontrado(a).'
            )

        stmts = [stmt_criar_livro(livro_digital)]
        stmts.append((
            'INSERT INTO exemplar_digital (id_digital, numero_acessos, URL) VALUES (%s, %s, %s)',
            (id, livro_digital.numero_acessos, str(livro_digital.URL))
        ))

        stmts.extend(stmts_adicionar_autores_a_livro(id, livro_digital.autores))

        return db_transaction(stmts)[0]
    except mysql_errors.IntegrityError:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT, detail="ISBN ou URL já cadastrado(s)")
    except mysql_errors.Error as e:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e))


@router.put('/{id_livro_digital}', response_model=int)
def atualizar_livro_digital(
    id_livro_digital: int,
    livro_digital: AtualizarExemplarDigitalSchema,
    response: Response
):
    # Buscar livro e exemplar digital para ver se existe
    if db_fetch_one('SELECT id FROM livros WHERE id = %s', (id_livro_digital,)) is None \
        or db_fetch_one(
            'SELECT id_digital FROM exemplar_digital WHERE id_digital = %s',
            (id_livro_digital,)
    ) is None:
        raise HTTPException(
            HTTPStatus.NOT_FOUND,
            'Nenhum livro com esse ID foi encontrado.'
        )

    stmts = stmts_atualizar_livro(id_livro_digital, livro_digital)

    fields = []
    params = []

    if livro_digital.numero_acessos:
        fields.append('numero_acessos = %s')
        params.append(livro_digital.numero_acessos)

    if livro_digital.URL:
        fields.append('URL = %s')
        params.append(str(livro_digital.URL))

    if fields:
        params.append(id_livro_digital)
        stmts.append((
            f'UPDATE exemplar_digital SET {','.join(fields)} WHERE id_digital = %s', 
            params
        ))

    if not stmts:
        response.status_code = HTTPStatus.NO_CONTENT

    return sum(db_transaction(stmts))


@router.delete('/{id_livro_digital}', response_model=int)
def deletar_livro_digital(id_livro_digital: int):
    # Buscar livro e exemplar digital para ver se existe
    if db_fetch_one('SELECT id FROM livros WHERE id = %s', (id_livro_digital,)) is None \
        or db_fetch_one(
            'SELECT id_digital FROM exemplar_digital WHERE id_digital = %s',
            (id_livro_digital,)
    ) is None:
        raise HTTPException(
            HTTPStatus.NOT_FOUND,
            'Nenhum livro com esse ID foi encontrado.'
        )

    return sum(db_transaction([
        ('DELETE FROM exemplar_digital WHERE id_digital = %s', (id_livro_digital,)),
        ('DELETE FROM autores_livros WHERE id_livro = %s', (id_livro_digital,)),
        ('DELETE FROM livros WHERE id = %s', (id_livro_digital,))
    ]))
