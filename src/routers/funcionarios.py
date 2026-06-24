from http import HTTPStatus
from fastapi import APIRouter, HTTPException, Query, Response
from mysql.connector import errors as mysql_errors
from typing import Annotated

from db import db_fetch_one, db_fetch_all, get_connection, db_transaction
from schemas import FuncionarioSchema, CargoFuncionario, AtualizarFuncionarioSchema
from db_schemas import FuncionarioDBSchema
from utils import cursor_criar_pessoa, resolver_cargo, stmt_atualizar_pessoa


router = APIRouter(prefix='/funcionario', tags=['Funcionários'])


@router.get('/', response_model=list[FuncionarioDBSchema])
def ler_funcionarios(
    id_funcionario: int | None = None,
    nome: str | None = None,
    CPF: str | None = None,
    email: str | None = None,
    cargo: Annotated[str | None, Query(
        enum=[c.value for c in CargoFuncionario])] = None
):
    conditions = []
    params = []

    if id_funcionario:
        conditions.routerend('id = %s')
        params.routerend(id_funcionario)

    if nome:
        conditions.routerend('nome LIKE %s')
        params.routerend(f'%{nome}%')

    if CPF:
        conditions.routerend('CPF = %s')
        params.routerend(CPF.replace('-', '').replace('.', ''))

    if email:
        conditions.routerend('email = %s')
        params.routerend(email)

    if cargo:
        conditions.routerend('cargo = %s')
        params.routerend(cargo)

    where = '' if not conditions else 'WHERE ' + ' AND '.join(conditions)
    fetch = db_fetch_all(
        'SELECT * FROM view_funcionario '
        f'{where}',
        params
    )

    if not fetch:
        raise HTTPException(
            HTTPStatus.NOT_FOUND,
            'Nenhum funcionário com esses critérios foi encontrado.'
        )
    return fetch


@router.get('/estantes', response_model=list[dict])
def ler_estantes_encarregadas(id_funcionario: int):
    fetch = db_fetch_all(
        'SELECT e.id, e.identificador_fisico FROM '
        'estantes e INNER JOIN organizadores_estantes o '
        'ON e.id=o.id_estante '
        'WHERE o.id_funcionario = %s',
        (id_funcionario,)
    )

    if not fetch:
        raise HTTPException(
            HTTPStatus.NOT_FOUND,
            'Esse funcionário não existe, ou não está encarregado de nenhuma estante.'
        )

    return fetch


@router.post('/', status_code=HTTPStatus.CREATED, response_model=int)
def criar_funcionario(funcionario: FuncionarioSchema):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        id_cargo = resolver_cargo(funcionario.cargo)
        
        cursor_criar_pessoa(cursor, funcionario)
        id_funcionario = cursor.lastrowid

        cursor.execute(
            'INSERT INTO funcionarios (id_funcionario, id_cargo, data_contratacao) '
            'VALUES (%s, %s, %s)',
            (id_funcionario, id_cargo, funcionario.data_contratacao)
        )

        conn.commit()

        return id_funcionario
    except mysql_errors.IntegrityError:
        conn.rollback()
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT, detail="CPF ou email já cadastrado")
    except mysql_errors.Error as e:
        conn.rollback()
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e))
    finally:
        cursor.close()
        conn.close()


@router.put('/{id_funcionario}', response_model=int)
def atualizar_funcionario(
    id_funcionario: int,
    funcionario: AtualizarFuncionarioSchema,
    response: Response
):
    # Buscar pessoa e funcionário para ver se existe
    if db_fetch_one('SELECT id FROM pessoas WHERE id = %s', (id_funcionario,)) is None \
        or db_fetch_one(
            'SELECT id_funcionario FROM funcionarios WHERE id_funcionario = %s',
            (id_funcionario,)
    ) is None:
        raise HTTPException(
            HTTPStatus.NOT_FOUND,
            'Nenhum funcionário com esse ID foi encontrado.'
        )

    stmts = [stmt_atualizar_pessoa(id_funcionario, funcionario)]

    fields = []
    params = []

    if funcionario.cargo:
        id_cargo = resolver_cargo(funcionario.cargo)
        fields.append('id_cargo = %s')
        params.append(id_cargo)

    if funcionario.data_contratacao:
        fields.append('data_contratacao = %s')
        params.append(funcionario.data_contratacao)

    if fields:
        params.append(id_funcionario)
        stmts.append((
            f'UPDATE funcionarios SET {', '.join(fields)} WHERE id_funcionario = %s', 
            params
        ))                

    if not stmts:
        response.status_code = HTTPStatus.NO_CONTENT

    return sum(db_transaction(stmts))


@router.delete('/funcinario/{id_funcionario}', response_model=int)
def deletar_funcionario(id_funcionario: int):
    # Buscar pessoa e funcionário para ver se existe
    if db_fetch_one('SELECT id FROM pessoas WHERE id = %s', (id_funcionario,)) is None \
        or db_fetch_one(
            'SELECT id_funcionario FROM funcionarios WHERE id_funcionario = %s',
            (id_funcionario,)
    ) is None:
        raise HTTPException(
            HTTPStatus.NOT_FOUND,
            'Nenhum funcionário com esse ID foi encontrado.'
        )
    
    return sum(db_transaction([
        ('DELETE FROM organizadores_estantes WHERE id_funcionario = %s', (id_funcionario,)),
        ('DELETE FROM funcionarios WHERE id_funcionario = %s', (id_funcionario,)),
        ('DELETE FROM pessoas WHERE id = %s', (id_funcionario,))
    ]))
