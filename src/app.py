from http import HTTPStatus
from contextlib import asynccontextmanager
from fastapi import FastAPI

from db import init_db, init_connection_pool
from schemas import UsuarioSchema
from db_schemas import UsuarioLista
from log import *

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
    ...


@app.put('/usuario/{id_usuario}', response_model=UsuarioSchema)
def atualizar_usuario(id_usuario: int, usuario: UsuarioSchema):
    ...


@app.delete('/usuario/{id_usuario}', response_model=int)
def deletar_usuario(id_usuario: int):
    ...
