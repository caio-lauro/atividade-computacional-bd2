from http import HTTPStatus
from fastapi import APIRouter, HTTPException, Response
from mysql.connector import errors as mysql_errors

from db import db_fetch_one, db_fetch_all, db_insert, db_transaction
from schemas import EstanteSchema, AtualizarEstanteSchema
from db_schemas import EstanteDBSchema


router = APIRouter(prefix='/estante', tags=['Estantes'])


@router.get('/', response_model=list[EstanteDBSchema])
def ler_estantes(
    id_estante: int | None = None,
    identificador_fisico: str | None = None,
    capacidade: int | None = None
):
    conditions = []
    params = []

    if id_estante:
        conditions.append('id = %s')
        params.append(id_estante)

    if identificador_fisico:
        conditions.append('identificador_fisico = %s')
        params.append(identificador_fisico)

    if capacidade is not None:
        conditions.append('capacidade = %s')
        params.append(capacidade)

    where = '' if not conditions else 'WHERE ' + ' AND '.join(conditions)
    fetch = db_fetch_all(
        'SELECT * FROM view_estantes '
        f'{where}',
        params
    )

    if not fetch:
        raise HTTPException(
            HTTPStatus.NOT_FOUND,
            'Nenhuma estante com esses critérios foi encontrada.'
        )

    for i in fetch:
        i['responsaveis'] = i['responsaveis'].split(', ')

    return fetch


@router.post('/', status_code=HTTPStatus.CREATED, response_model=int)
def criar_estantes(estante: EstanteSchema):
    try:
        id_estante = db_insert(
            'INSERT INTO estantes (identificador_fisico, capacidade) '
            'VALUES (%s, %s)',
            (estante.identificador_fisico, estante.capacidade)
        )

        for id_funcionario in estante.funcionarios_responsaveis:
            db_insert(
                'INSERT INTO organizadores_estantes (id_funcionario, id_estante) '
                'VALUES (%s, %s)',
                (id_funcionario, id_estante)
            )

        return id_estante
    except mysql_errors.IntegrityError:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT, detail="Identificador físico já cadastrado")
    except mysql_errors.Error as e:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e))


@router.put('/{id_estante}', response_model=int)
def atualizar_estantes(
    id_estante: int,
    estante: AtualizarEstanteSchema,
    response: Response
):
    # Buscar estante para ver se existe
    if db_fetch_one('SELECT id FROM estantes WHERE id = %s', (id_estante,)) is None:
        raise HTTPException(
            HTTPStatus.NOT_FOUND,
            'Nenhuma estante com esse ID foi encontrada.'
        )

    if not estante.funcionarios_responsaveis and not estante.identificador_fisico and estante.capacidade is None:
        response.status_code = HTTPStatus.NO_CONTENT

    stmts = []
    if estante.funcionarios_responsaveis:
        stmts.append((
            'DELETE FROM organizadores_estantes WHERE id_estante = %s',
            (id_estante,)
        ))

        for id_funcionario in estante.funcionarios_responsaveis:
            stmts.append((
                'INSERT INTO organizadores_estantes (id_funcionario, id_estante) '
                'VALUES (%s, %s)',
                (id_funcionario, id_estante)
            ))

    if estante.identificador_fisico:
        if db_fetch_one(
            'SELECT id FROM estantes WHERE identificador_fisico = %s',
            (estante.identificador_fisico,)
        ):
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT, detail="Identificador Fisico já cadastrado")

        stmts.append((
            'UPDATE estantes SET identificador_fisico = %s WHERE id = %s',
            (estante.identificador_fisico, id_estante)
        ))

    if estante.capacidade is not None:
        stmts.append((
            'UPDATE estantes SET capacidade = %s WHERE id = %s',
            (estante.capacidade, id_estante)
        ))

    return sum(db_transaction(stmts))


@router.delete('/{id_estante}', response_model=int)
def deletar_estante(id_estante: int):
    # Buscar estante para ver se existe
    if db_fetch_one('SELECT id FROM estantes WHERE id = %s', (id_estante,)) is None:
        raise HTTPException(
            HTTPStatus.NOT_FOUND,
            'Nenhuma estante com esse ID foi encontrada.'
        )

    return sum(
        db_transaction([
            ('DELETE FROM organizadores_estantes WHERE id_estante= %s', (id_estante,)),
            ('DELETE FROM estantes WHERE id = %s', (id_estante,))
        ])
    )
