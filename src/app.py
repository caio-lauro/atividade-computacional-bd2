from http import HTTPStatus
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from mysql.connector import errors as mysql_errors

from db import init_db, init_connection_pool, db_fetch_one, db_fetch_all, db_insert, db_modify
from schemas import UsuarioSchema, FuncionarioSchema
from db_schemas import UsuarioLista
from log import *
from auth import hash_senha
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


@app.get('/usuario/', response_model=UsuarioLista)
def ler_usuarios():
    ...


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
            'INSERT INTO funcionarios (id_funcionario, id_cargo, data_contratacao) ' \
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
