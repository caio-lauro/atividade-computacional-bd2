from http import HTTPStatus
from fastapi import APIRouter, HTTPException, Query, Response
from mysql.connector import errors as mysql_errors
from typing import Annotated

from db import db_fetch_one, db_fetch_all, db_insert, db_modify
from schemas import FuncionarioSchema, CargoFuncionario, AtualizarFuncionarioSchema
from db_schemas import FuncionarioDBSchema
from utils import criar_pessoa, resolver_cargo
from auth import hash_senha


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
    return db_fetch_all(
        'SELECT e.id, e.identificador_fisico FROM '
        'estantes e INNER JOIN organizadores_estantes o '
        'ON e.id=o.id_estante '
        'WHERE o.id_funcionario = %s',
        (id_funcionario,)
    )


@router.post('/', status_code=HTTPStatus.CREATED, response_model=int)
def criar_funcionario(funcionario: FuncionarioSchema):
    try:
        id_cargo = resolver_cargo(funcionario.cargo)
        id = criar_pessoa(funcionario)
        db_insert(
            'INSERT INTO funcionarios (id_funcionario, id_cargo, data_contratacao) '
            'VALUES (%s, %s, %s)',
            (id, id_cargo, funcionario.data_contratacao)
        )
        return id
    except mysql_errors.IntegrityError:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT, detail="CPF ou email já cadastrado")
    except mysql_errors.Error as e:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e))


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

    fields = []
    params = []

    data = funcionario.model_dump(exclude_none=True)

    pessoa_fields = {'nome', 'CPF', 'email',
                     'senha', 'telefone', 'data_nascimento'}
    pessoas_data = {k: v for k, v in data.items() if k in pessoa_fields}

    if 'senha' in pessoas_data:
        pessoas_data['senha'] = hash_senha(pessoas_data['senha'])

    rows = 0
    if pessoas_data:
        fields = [f'{k} = %s' for k in pessoas_data]
        params = list(pessoas_data.values()) + [id_funcionario]
        try:
            rows = db_modify(
                f'UPDATE pessoas SET {', '.join(fields)} WHERE id = %s', params)
        except mysql_errors.IntegrityError:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT, detail="CPF ou email já cadastrado")
        except mysql_errors.Error as e:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e))

    funcionarios_fields = {'cargo', 'data_contratacao'}
    funcionarios_data = {k: v for k,
                         v in data.items() if k in funcionarios_fields}

    if 'cargo' in funcionarios_data:
        cargo = funcionarios_data['cargo']
        del funcionarios_data['cargo']
        funcionarios_data['id_cargo'] = resolver_cargo(cargo)

    if funcionarios_data:
        fields = [f'{k} = %s' for k in funcionarios_data]
        params = list(funcionarios_data.values()) + [id_funcionario]
        try:
            rows += db_modify(
                f'UPDATE funcionarios SET {', '.join(fields)} WHERE id_funcionario = %s', params)
        except mysql_errors.IntegrityError:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT, detail="CPF ou email já cadastrado")
        except mysql_errors.Error as e:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e))

    if rows == 0:
        response.status_code = HTTPStatus.NO_CONTENT

    return rows


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

    rows = db_modify(
        'DELETE FROM funcionarios WHERE id_funcionario = %s', (id_funcionario,)
    )

    rows += db_modify(
        'DELETE FROM pessoas WHERE id = %s', (id_funcionario,)
    )

    return rows
