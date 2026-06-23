from http import HTTPStatus
from fastapi import APIRouter, HTTPException, Response, Query
from mysql.connector import errors as mysql_errors

from db import db_fetch_one, db_fetch_all, db_insert, db_modify, db_transaction
from schemas import ExemplarDigitalSchema, AtualizarExemplarDigitalSchema
from db_schemas import ExemplarDigitalDBSchema
from utils import criar_livro, buscar_autores_inexistentes, adicionar_autores_a_livro


router = APIRouter(prefix='/livros/digital', tags=['Livro Digital'])


@router.get('/', response_model=list[ExemplarDigitalDBSchema])
def ler_livro_digital(
    id_livro_digital: int | None = None,
    ISBN: str | None = None,
    titulo: str | None = None,
    estante: str | None = None,
    autores: list[str] | None = Query(default=None)
):
    conditions = []
    params = []

    if id_livro_digital:
        conditions.append('id = %s')
        params.append(id_livro_digital)

    if ISBN:
        conditions.append('ISBN = %s')
        params.append(ISBN)

    if titulo:
        conditions.append('titulo LIKE %s')
        params.append(f'%{titulo}%')

    if estante:
        conditions.append('Estante = %s')
        params.append(estante)

    if autores:
        likes = ' OR '.join(['a.nome LIKE %s'] * len(autores))
        conditions.append(
            'view_digital.id IN (SELECT al.id_livro FROM autores_livros al '
            'INNER JOIN autores a ON al.id_autor=a.id ' 
            f'WHERE {likes})'
        )
        params.extend([f'%{autor}%' for autor in autores])

    where = '' if not conditions else 'WHERE ' + ' AND '.join(conditions)
    fetch = db_fetch_all(
        'SELECT * FROM view_digital '
        f'{where}',
        params
    )

    if not fetch:
        raise HTTPException(
            HTTPStatus.NOT_FOUND,
            'Nenhum exemplar digital com esses critérios foi encontrado.'
        )
    
    for i in fetch:
        i['autores'] = i['autores'].split(', ')

    return fetch


@router.post('/', status_code=HTTPStatus.CREATED, response_model=int)
def criar_livro_digital(livro_digital: ExemplarDigitalSchema):
    try:
        autor_inexistente = buscar_autores_inexistentes(livro_digital.autores)
        if autor_inexistente != -1:
            raise HTTPException(
                HTTPStatus.NOT_FOUND,
                f'Nenhum autor(a) com o ID {autor_inexistente} foi encontrado(a).'
            )

        id = criar_livro(livro_digital)
        db_insert(
            'INSERT INTO exemplar_digital (id_digital, numero_acessos, URL) VALUES (%s, %s, %s)',
            (id, livro_digital.numero_acessos, str(livro_digital.URL))
        )

        adicionar_autores_a_livro(id, livro_digital.autores)

        return id
    except mysql_errors.IntegrityError:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT, detail="ISBN ou URL já cadastrado(s)")
    except mysql_errors.Error as e:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e))


@router.put('/{id_livro_digital}', response_model=int)
def atualizar_livro_digital(
    id_livro_digital: int,
    livro_fisico: AtualizarExemplarDigitalSchema,
    response: Response
):
    # Buscar livro e exemplar digital para ver se existe
    if db_fetch_one('SELECT id FROM livros WHERE id = %s', (id_livro_digital,)) is None \
        or db_fetch_one(
            'SELECT id_digital FROM exemplar_digital WHERE id_digital = %s',
            (id_livro_digital,)
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
            (id_livro_digital,)
        )

        rows += adicionar_autores_a_livro(id_livro_digital, livro_fisico.autores)

        del livros_data['autores']

    if livros_data:
        fields = [f'{k} = %s' for k in livros_data]
        params = list(livros_data.values()) + [id_livro_digital]
        try:
            rows += db_modify(
                f'UPDATE livros SET {', '.join(fields)} WHERE id = %s', params)
        except mysql_errors.IntegrityError:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT, detail="ISBN já cadastrado")
        except mysql_errors.Error as e:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e))

    digital_fields = {'numero_acessos', 'URL'}
    digital_data = {k: v for k, v in data.items() if k in digital_fields}

    if digital_data:
        fields = [f'{k} = %s' for k in digital_data]
        params = list(digital_data.values()) + [id_livro_digital]
        try:
            rows += db_modify(
                f'UPDATE exemplar_digital SET {', '.join(fields)} WHERE id_fisico = %s', params)
        except mysql_errors.IntegrityError:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT, detail="URL já cadastrada")
        except mysql_errors.Error as e:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e))

    if rows == 0:
        response.status_code = HTTPStatus.NO_CONTENT

    return rows


@router.delete('/{id_livro_digital}', response_model=int)
def deletar_livro_fisico(id_livro_digital: int):
    # Buscar livro e exemplar físico para ver se existe
    if db_fetch_one('SELECT id FROM livros WHERE id = %s', (id_livro_digital,)) is None \
        or db_fetch_one(
            'SELECT id_digital FROM exemplar_digital WHERE id_digital = %s',
            (id_livro_digital,)
    ) is None:
        raise HTTPException(
            HTTPStatus.NOT_FOUND,
            'Nenhum livro com esse ID foi encontrado.'
        )
    
    return sum(db_transaction([
        ('DELETE FROM exemplar_digital WHERE id_digital = %s', (id_livro_digital,)),
        ('DELETE FROM autores_livros WHERE id_livro = %s', (id_livro_digital,)),
        ('DELETE FROM livros WHERE id = %s', (id_livro_digital,))
    ]))
