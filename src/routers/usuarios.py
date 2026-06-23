from http import HTTPStatus
from fastapi import APIRouter, HTTPException, Response
from mysql.connector import errors as mysql_errors

from db import db_fetch_one, db_fetch_all, db_modify, get_connection
from schemas import UsuarioSchema, StatusUsuario, AtualizarUsuarioSchema
from db_schemas import UsuarioDBSchema
from utils import cursor_criar_pessoa
from auth import hash_senha


router = APIRouter(prefix='/usuario', tags=['Usuários'])


@router.get('/', response_model=list[UsuarioDBSchema])
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


@router.post('/', status_code=HTTPStatus.CREATED, response_model=int)
def criar_usuario(usuario: UsuarioSchema):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor_criar_pessoa(cursor, usuario)
        id_usuario = cursor.lastrowid

        cursor.execute(
            'INSERT INTO usuarios (id_usuario) VALUES (%s)',
            (id_usuario,)
        )

        conn.commit()

        return id_usuario
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


@router.put('/{id_usuario}', response_model=int)
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

    if 'senha' in pessoas_data:
        pessoas_data['senha'] = hash_senha(pessoas_data['senha'])

    rows = 0
    if pessoas_data:
        fields = [f'{k} = %s' for k in pessoas_data]
        params = list(pessoas_data.values()) + [id_usuario]
        try:
            rows = db_modify(
                f'UPDATE pessoas SET {', '.join(fields)} WHERE id = %s', params)
        except mysql_errors.IntegrityError:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT, detail="CPF ou email já cadastrado")
        except mysql_errors.Error as e:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e))

    usuario_fields = {'status', 'limite_emprestimos'}
    usuarios_data = {k: v for k, v in data.items() if k in usuario_fields}

    if usuarios_data:
        fields = [f'{k} = %s' for k in usuarios_data]
        params = list(usuarios_data.values()) + [id_usuario]
        try:
            rows += db_modify(
                f'UPDATE usuarios SET {', '.join(fields)} WHERE id_usuario = %s', params)
        except mysql_errors.IntegrityError:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT, detail="CPF ou email já cadastrado")
        except mysql_errors.Error as e:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e))

    if rows == 0:
        response.status_code = HTTPStatus.NO_CONTENT

    return rows


@router.delete('/{id_usuario}', response_model=int)
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
