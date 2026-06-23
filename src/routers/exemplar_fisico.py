from http import HTTPStatus
from fastapi import APIRouter, HTTPException, Response, Query
from mysql.connector import errors as mysql_errors

from db import db_fetch_one, db_fetch_all, db_insert, db_modify
from schemas import ExemplarFisicoSchema, StatusExemplarFisico, AtualizarExemplarFisicoSchema
from db_schemas import ExemplarFisicoDBSchema
from utils import criar_livro, buscar_estante, buscar_autores_inexistentes, adicionar_autores_a_livro


router = APIRouter(prefix='/livros/fisico', tags=['Livro Físico'])


@router.get('/', response_model=list[ExemplarFisicoDBSchema])
def ler_livro_fisico(
    id_livro_fisico: int | None = None,
    ISBN: str | None = None,
    titulo: str | None = None,
    status: StatusExemplarFisico | None = None,
    estante: str | None = None,
    autores: list[str] | None = Query(default=None)
):
    conditions = []
    params = []

    if id_livro_fisico:
        conditions.append('id = %s')
        params.append(id_livro_fisico)

    if ISBN:
        conditions.append('ISBN = %s')
        params.append(ISBN)

    if titulo:
        conditions.append('titulo LIKE %s')
        params.append(f'%{titulo}%')

    if status:
        conditions.append('disponivel = %s')
        params.append(status == 'disponível')

    if estante:
        conditions.append('Estante = %s')
        params.append(estante)

    if autores:
        likes = ' OR '.join(['a.nome LIKE %s'] * len(autores))
        conditions.append(
            'view_fisico.id IN (SELECT al.id_livro FROM autores_livros al '
            'INNER JOIN autores a ON al.id_autor=a.id ' 
            f'WHERE {likes})'
        )
        params.extend([f'%{autor}%' for autor in autores])

    where = '' if not conditions else 'WHERE ' + ' AND '.join(conditions)
    fetch = db_fetch_all(
        'SELECT * FROM view_fisico '
        f'{where}',
        params
    )

    if not fetch:
        raise HTTPException(
            HTTPStatus.NOT_FOUND,
            'Nenhum exemplar físico com esses critérios foi encontrado.'
        )
    
    for i in fetch:
        i['autores'] = i['autores'].split(', ')

    return fetch


@router.post('/', status_code=HTTPStatus.CREATED, response_model=int)
def criar_livro_fisico(livro_fisico: ExemplarFisicoSchema):
    try:
        autor_inexistente = buscar_autores_inexistentes(livro_fisico.autores)
        if autor_inexistente != -1:
            raise HTTPException(
                HTTPStatus.NOT_FOUND,
                f'Nenhum autor(a) com o ID {autor_inexistente} foi encontrado(a).'
            )
        

        id_estante = buscar_estante(livro_fisico.estante)
        if not id_estante:
            raise HTTPException(
                HTTPStatus.NOT_FOUND,
                'Nenhuma estante com esse identificador foi encontrada.'
            )

        id_estante = id_estante['id']

        espacos = db_fetch_one(
            'SELECT fn_calcular_espacos_disponiveis(%s) AS espacos',
            (id_estante,)
        )['espacos']

        if espacos == 0:
            raise HTTPException(
                HTTPStatus.CONFLICT,
                detail='Essa estante já está lotada.'
            )

        id = criar_livro(livro_fisico)
        db_insert(
            'INSERT INTO exemplar_fisico (id_fisico, id_estante_associada) VALUES (%s, %s)',
            (id, id_estante)
        )

        adicionar_autores_a_livro(id, livro_fisico.autores)

        return id
    except mysql_errors.IntegrityError:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT, detail="ISBN já cadastrado")
    except mysql_errors.Error as e:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e))


@router.put('/{id_livro_fisico}', response_model=int)
def atualizar_livro_fisico(
    id_livro_fisico: int,
    livro_fisico: AtualizarExemplarFisicoSchema,
    response: Response
):
    # Buscar livro e exemplar físico para ver se existe
    if db_fetch_one('SELECT id FROM livros WHERE id = %s', (id_livro_fisico,)) is None \
        or db_fetch_one(
            'SELECT id_fisico FROM exemplar_fisico WHERE id_fisico = %s',
            (id_livro_fisico,)
    ) is None:
        raise HTTPException(
            HTTPStatus.NOT_FOUND,
            'Nenhum livro com esse ID foi encontrado.'
        )

    fields = []
    params = []

    data = livro_fisico.model_dump(exclude_none=True)

    livros_fields = {'ISBN', 'titulo', 'data_publicacao', 'autores'}
    livros_data = {k: v for k, v in data.items() if k in livros_fields}

    rows = 0
    if 'autores' in livros_data:
        # Garantir que autores são existentes
        autor_inexistente = buscar_autores_inexistentes(livro_fisico.autores)
        if autor_inexistente != -1:
            raise HTTPException(
                HTTPStatus.NOT_FOUND,
                f'Nenhum autor(a) com o ID {autor_inexistente} foi encontrado(a).'
            )
        
        rows = db_modify(
            'DELETE FROM autores_livros WHERE id_livro = %s', 
            (id_livro_fisico,)
        )

        rows += adicionar_autores_a_livro(id_livro_fisico, livro_fisico.autores)

        del livros_data['autores']

    if livros_data:
        fields = [f'{k} = %s' for k in livros_data]
        params = list(livros_data.values()) + [id_livro_fisico]
        try:
            rows += db_modify(
                f'UPDATE livros SET {', '.join(fields)} WHERE id = %s', params)
        except mysql_errors.IntegrityError:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT, detail="ISBN já cadastrado")
        except mysql_errors.Error as e:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e))

    fisico_fields = {'status', 'estante'}
    fisico_data = {k: v for k, v in data.items() if k in fisico_fields}

    if 'estante' in fisico_data:
        id_estante = buscar_estante(fisico_data['estante'])
        if not id_estante:
            raise HTTPException(
                HTTPStatus.NOT_FOUND,
                'Nenhuma estante com esse identificador foi encontrada.'
            )

        id_estante = id_estante['id']

        del fisico_data['estante']
        fisico_data['id_estante_associada'] = id_estante

        espacos = db_fetch_one(
            'SELECT fn_calcular_espacos_disponiveis(%s) AS espacos',
            (id_estante,)
        )['espacos']

        if espacos == 0:
            raise HTTPException(
                HTTPStatus.CONFLICT,
                detail='Essa estante já está lotada.'
            )
        
    if 'status' in fisico_data:
        disponivel = fisico_data['status'] == 'disponível'
        del fisico_data['status']
        fisico_data['disponivel'] = disponivel

    if fisico_data:
        fields = [f'{k} = %s' for k in fisico_data]
        params = list(fisico_data.values()) + [id_livro_fisico]
        try:
            rows += db_modify(
                f'UPDATE exemplar_fisico SET {', '.join(fields)} WHERE id_fisico = %s', params)
        except mysql_errors.Error as e:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e))

    if rows == 0:
        response.status_code = HTTPStatus.NO_CONTENT

    return rows


@router.delete('/{id_livro_fisico}', response_model=int)
def deletar_livro_fisico(id_livro_fisico: int):
    # Buscar livro e exemplar físico para ver se existe
    if db_fetch_one('SELECT id FROM livros WHERE id = %s', (id_livro_fisico,)) is None \
        or db_fetch_one(
            'SELECT id_fisico FROM exemplar_fisico WHERE id_fisico = %s',
            (id_livro_fisico,)
    ) is None:
        raise HTTPException(
            HTTPStatus.NOT_FOUND,
            'Nenhum livro com esse ID foi encontrado.'
        )

    rows = db_modify(
        'DELETE FROM exemplar_fisico WHERE id_fisico = %s', (id_livro_fisico,)
    )

    rows += db_modify(
        'DELETE FROM autores_livros WHERE id_livro = %s', (id_livro_fisico,)
    )

    rows += db_modify(
        'DELETE FROM livros WHERE id = %s', (id_livro_fisico,)
    )

    return rows
