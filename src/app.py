from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from db import init_db, init_connection_pool
from log import *


@asynccontextmanager
async def lifespan(app: FastAPI):
    log_info('Inicializando banco de dados.')
    init_db()
    log_info('Inicializando conexão com o banco de dados.')
    init_connection_pool()

    from routers import usuarios, funcionarios, estantes, exemplar_fisico, autores

    app.include_router(usuarios.router)
    app.include_router(funcionarios.router)
    app.include_router(autores.router)
    app.include_router(estantes.router)
    app.include_router(exemplar_fisico.router)

    # App recebe requests
    yield


app = FastAPI(
    lifespan=lifespan,
    swagger_ui_parameters={"tryItOutEnabled": True}
)


@app.get('/', include_in_schema=False)
def read_root():
    return RedirectResponse(url='/docs')
