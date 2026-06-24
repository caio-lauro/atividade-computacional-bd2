from http import HTTPStatus
from fastapi import APIRouter, HTTPException, Response, Query
from mysql.connector import errors as mysql_errors

from db import db_fetch_one, db_fetch_all, db_insert, db_modify
from schemas import EmprestimoSchema, AtualizarEmprestimoSchema
from db_schemas import EmprestimoDBSchema


router = APIRouter(prefix='/emprestimos', tags=['Empréstimos'])


@router.get('/', response_model=list[EmprestimoDBSchema])
def ler_emprestimos(
    id_emprestimo: int | None = None,
    id_usuario: int | None = None,
    id_livro_fisico: int | None = None,
    devolvido: bool | None = None,
):
    conditions = []
    params = []

    if id_emprestimo:
        conditions.append('id = %s')
        params.append(id_emprestimo)

    if id_usuario:
        conditions.append('id_usuario = %s')
        params.append(id_usuario)

    if id_livro_fisico:
        conditions.append('id_fisico = %s')
        params.append(id_livro_fisico)

    if devolvido is not None:
        conditions.append('devolvido = %s')
        params.append(devolvido)

    where = '' if not conditions else 'WHERE ' + ' AND '.join(conditions)
    fetch = db_fetch_all(
        'SELECT * FROM view_emprestimo WHERE id IN ('
        'SELECT id FROM emprestimos '
        f'{where}'
        ') ',
        params
    )

    if not fetch:
        raise HTTPException(
            HTTPStatus.NOT_FOUND,
            'Nenhum empréstimo com esses critérios foi encontrado.'
        )

    return fetch


@router.post('/', status_code=HTTPStatus.CREATED, response_model=int)
def criar_emprestimo(emprestimo: EmprestimoSchema):
    try:
        if not db_fetch_one(
            'SELECT id_usuario FROM usuarios WHERE id_usuario = %s',
            (emprestimo.id_usuario,)
        ):
            raise HTTPException(
                HTTPStatus.NOT_FOUND,
                'Nenhum usuário com esse ID foi encontrado.'
            )

        if not db_fetch_one(
            'SELECT id_fisico FROM exemplar_fisico WHERE id_fisico = %s',
            (emprestimo.id_livro_fisico,)
        ):
            raise HTTPException(
                HTTPStatus.NOT_FOUND,
                'Nenhum livro físico com esse ID foi encontrado.'
            )

        return db_insert(
            'INSERT INTO emprestimos (id_usuario, id_fisico) VALUES (%s, %s)',
            (emprestimo.id_usuario, emprestimo.id_livro_fisico)
        )
    except mysql_errors.Error as e:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e))


@router.put('/{id_emprestimo}', response_model=int)
def atualizar_emprestimo(
    id_emprestimo: int,
    emprestimo: AtualizarEmprestimoSchema,
    response: Response
):
    if not db_fetch_one(
        'SELECT id FROM emprestimos WHERE id = %s',
        (id_emprestimo,)
    ):
        raise HTTPException(
            HTTPStatus.NOT_FOUND,
            'Nenhum empréstimo com esse ID foi encontrado.'
        )
    
    fields = []
    params = []

    if emprestimo.data_devolucao:
        fields.append('data_devolucao = %s')
        params.append(emprestimo.data_devolucao)

    if emprestimo.devolvido is not None:
        fields.append('devolvido = %s')
        params.append(emprestimo.devolvido)

    if not fields:
        response.status_code = HTTPStatus.NO_CONTENT
        return 0
    
    params.append(id_emprestimo)
    return db_modify(
        f'UPDATE emprestimos SET {','.join(fields)} WHERE id = %s',
        (params)
    )


@router.delete('/{id_emprestimo}', response_model=int)
def deletar_emprestimo(id_emprestimo: int, devolvido: bool | None = None):
    if not db_fetch_one(
        'SELECT id FROM emprestimos WHERE id = %s',
        (id_emprestimo,)
    ):
        raise HTTPException(
            HTTPStatus.NOT_FOUND,
            'Nenhum empréstimo com esse ID foi encontrado.'
        )
    
    rows = 0
    if devolvido:
        rows += db_modify(
            'UPDATE emprestimos SET devolvido = %s WHERE id = %s',
            (True, id_emprestimo)
        )

    rows += db_modify(
        'DELETE FROM emprestimos WHERE id = %s',
        (id_emprestimo,)
    )

    return rows