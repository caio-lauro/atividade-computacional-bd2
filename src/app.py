from http import HTTPStatus
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.responses import RedirectResponse
from mysql.connector import errors as mysql_errors
from typing import Annotated

from db import init_db, init_connection_pool, db_fetch_one, db_fetch_all, db_insert, db_modify
from schemas import UsuarioSchema, StatusUsuario, AtualizarUsuarioSchema, FuncionarioSchema, CargoFuncionario, AtualizarFuncionarioSchema
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


app = FastAPI(
    lifespan=lifespan,
    swagger_ui_parameters={"tryItOutEnabled": True}
)


@app.get('/', include_in_schema=False)
def read_root():
    return RedirectResponse(url='/docs')


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
    fetch = db_fetch_all(
        'SELECT * FROM view_usuario '
        f'{where}',
        params
    )

    if not fetch:
        raise HTTPException(
            HTTPStatus.NOT_FOUND,
            'Nenhum usuário com esses critérios foi encontrado.'
        )
    return fetch


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


@app.put('/usuario/{id_usuario}', response_model=int)
def atualizar_usuario(
    id_usuario: int,
    usuario: AtualizarUsuarioSchema,
    response: Response
):
    # Buscar pessoa e usuário para ver se existe
    if db_fetch_one('SELECT id FROM pessoas WHERE id = %s', (id_usuario,)) is None \
        or db_fetch_one(
            'SELECT id_usuario FROM usuarios WHERE id_usuario = %s',
            (id_usuario,)
    ) is None:
        raise HTTPException(
            HTTPStatus.NOT_FOUND,
            'Nenhum usuário com esse ID foi encontrado.'
        )

    fields = []
    params = []

    data = usuario.model_dump(exclude_none=True)

    pessoa_fields = {'nome', 'CPF', 'email',
                     'senha', 'telefone', 'data_nascimento'}
    pessoas_data = {k: v for k, v in data.items() if k in pessoa_fields}

    rows = 0
    if pessoas_data:
        fields = [f'{k} = %s' for k in pessoas_data]
        params = list(pessoas_data.values()) + [id_usuario]
        rows = db_modify(
            f'UPDATE pessoas SET {', '.join(fields)} WHERE id = %s', params)

    usuario_fields = {'status', 'limite_emprestimos'}
    usuarios_data = {k: v for k, v in data.items() if k in usuario_fields}

    if usuarios_data:
        fields = [f'{k} = %s' for k in usuarios_data]
        params = list(usuarios_data.values()) + [id_usuario]
        rows += db_modify(
            f'UPDATE usuarios SET {', '.join(fields)} WHERE id_usuario = %s', params)

    if rows == 0:
        response.status_code = HTTPStatus.NO_CONTENT

    return rows


@app.put('/funcionario/{id_funcionario}', response_model=int)
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

    rows = 0
    if pessoas_data:
        fields = [f'{k} = %s' for k in pessoas_data]
        params = list(pessoas_data.values()) + [id_funcionario]
        rows = db_modify(
            f'UPDATE pessoas SET {', '.join(fields)} WHERE id = %s', params)

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
        rows += db_modify(
            f'UPDATE funcionarios SET {', '.join(fields)} WHERE id_funcionario = %s', params)

    if rows == 0:
        response.status_code = HTTPStatus.NO_CONTENT

    return rows


@app.delete('/usuario/{id_usuario}', response_model=int)
def deletar_usuario(id_usuario: int):
    # Buscar pessoa e usuário para ver se existe
    if db_fetch_one('SELECT id FROM pessoas WHERE id = %s', (id_usuario,)) is None \
        or db_fetch_one(
            'SELECT id_usuario FROM usuarios WHERE id_usuario = %s',
            (id_usuario,)
    ) is None:
        raise HTTPException(
            HTTPStatus.NOT_FOUND,
            'Nenhum usuário com esse ID foi encontrado.'
        )

    rows = db_modify(
        'DELETE FROM usuarios WHERE id_usuario = %s', (id_usuario,)
    )

    rows += db_modify(
        'DELETE FROM pessoas WHERE id = %s', (id_usuario,)
    )

    return rows


@app.delete('/funcinario/{id_funcionario}', response_model=int)
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
