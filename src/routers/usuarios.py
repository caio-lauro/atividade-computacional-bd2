from http import HTTPStatus
from fastapi import APIRouter, HTTPException, Response
from mysql.connector import errors as mysql_errors

from db import db_fetch_one, db_fetch_all, get_connection, db_transaction
from schemas import UsuarioSchema, StatusUsuario, AtualizarUsuarioSchema
from db_schemas import UsuarioDBSchema
from utils import cursor_criar_pessoa, stmt_atualizar_pessoa


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

    stmts = [stmt_atualizar_pessoa(id_usuario, usuario)]

    fields = []
    params = []

    if usuario.status:
        fields.append('status = %s')
        params.append(usuario.status == 'ativo')

    if usuario.limite_emprestimos is not None:
        fields.append('limite_emprestimos = %s')
        params.append(usuario.limite_emprestimos)

    if fields:
        params.append(id_usuario)
        stmts.append((
            f'UPDATE usuarios SET {','.join(fields)} WHERE id_usuario = %s',
            params
        ))

    if not stmts:
        response.status_code = HTTPStatus.NO_CONTENT

    return sum(db_transaction(stmts))


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

    return sum(db_transaction([
        ('DELETE FROM usuarios WHERE id_usuario = %s', (id_usuario,)),
        ('DELETE FROM pessoas WHERE id = %s', (id_usuario,))
    ]))
