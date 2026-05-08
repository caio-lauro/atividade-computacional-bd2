from http import HTTPStatus
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from mysql.connector import errors as mysql_errors
from typing import Annotated

from db import init_db, init_connection_pool, db_fetch_one, db_fetch_all, db_insert, db_modify
from schemas import UsuarioSchema, StatusUsuario, FuncionarioSchema, CargoFuncionario
from db_schemas import UsuarioDBSchema, FuncionarioDBSchema
from log import *
from utils import criar_pessoa, resolver_cargo


@asynccontextmanager
async def lifespan(app: FastAPI):
    log_info('Inicializando banco de dados.')
    init_db()
    log_info('Inicializando conexão com o banco de dados.')
    init_connection_pool()

    # App recebe requests
    yield


app = FastAPI(lifespan=lifespan)


@app.get('/')
def read_root():
    return {'mensagem': 'Olá mundo!'}


@app.get('/usuario/', response_model=list[UsuarioDBSchema])
def ler_usuarios(
    id_usuario: int | None = None,
    nome: str | None = None,
    CPF: str | None = None,
    email: str | None = None,
    status: StatusUsuario | None = None
):
    conditions = []
    params = []

    if id_usuario:
        conditions.append('id = %s')
        params.append(id_usuario)

    if nome:
        conditions.append('nome LIKE %s')
        params.append(f'%{nome}%')

    if CPF:
        conditions.append('CPF = %s')
        params.append(CPF.replace('-', '').replace('.', ''))

    if email:
        conditions.append('email = %s')
        params.append(email)

    if status:
        conditions.append('status = %s')
        params.append(status == 'ativo')

    where = '' if not conditions else 'WHERE ' + ' AND '.join(conditions)
    print(where)
    return db_fetch_all(
        'SELECT * FROM view_usuario '
        f'{where}',
        params
    )


@app.get('/funcionario/', response_model=list[FuncionarioDBSchema])
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
        conditions.append('id = %s')
        params.append(id_funcionario)

    if nome:
        conditions.append('nome LIKE %s')
        params.append(f'%{nome}%')

    if CPF:
        conditions.append('CPF = %s')
        params.append(CPF.replace('-', '').replace('.', ''))

    if email:
        conditions.append('email = %s')
        params.append(email)

    if cargo:
        conditions.append('cargo = %s')
        params.append(cargo)

    where = '' if not conditions else 'WHERE ' + ' AND '.join(conditions)
    print(where)
    return db_fetch_all(
        'SELECT * FROM view_funcionario '
        f'{where}',
        params
    )


@app.post('/usuario/', status_code=HTTPStatus.CREATED, response_model=int)
def criar_usuario(usuario: UsuarioSchema):
    try:
        id = criar_pessoa(usuario)
        db_insert(
            'INSERT INTO usuarios (id_usuario) VALUES (%s)',
            (id,)
        )
        return id
    except mysql_errors.IntegrityError:
        raise HTTPException(
            status_code=409, detail="CPF ou email já cadastrado")
    except mysql_errors.Error as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/funcionario/', status_code=HTTPStatus.CREATED, response_model=int)
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
            status_code=409, detail="CPF ou email já cadastrado")
    except mysql_errors.Error as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put('/usuario/{id_usuario}', response_model=UsuarioSchema)
def atualizar_usuario(id_usuario: int, usuario: UsuarioSchema):
    ...


@app.delete('/usuario/{id_usuario}', response_model=int)
def deletar_usuario(id_usuario: int):
    ...
