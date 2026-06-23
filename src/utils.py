from difflib import get_close_matches
from fastapi import HTTPException

from schemas import PessoaSchema, LivroSchema
from db import db_insert, db_fetch_all, db_fetch_one
from auth import hash_senha


def criar_pessoa(pessoa: PessoaSchema) -> int:
    return db_insert(
        'INSERT INTO pessoas (nome, CPF, email, senha, telefone, data_nascimento) '
        'VALUES (%s, %s, %s, %s, %s, %s)',
        (pessoa.nome, pessoa.CPF.replace('-', '').replace('.', ''), pessoa.email,
         hash_senha(pessoa.senha), pessoa.telefone.replace('-', ''), pessoa.data_nascimento)
    )


def criar_livro(livro: LivroSchema) -> int:
    return db_insert(
        'INSERT INTO livros (ISBN, titulo, data_publicacao) '
        'VALUES (%s, %s, %s)',
        (livro.ISBN, livro.titulo, livro.data_publicacao)
    )


def buscar_autores_inexistentes(autores: list[int]) -> int:
    for id_autor in autores:
        if not db_fetch_one(
            'SELECT id FROM autores WHERE id = %s',
            (id_autor,)
        ):
            return id_autor
    return -1


def adicionar_autores_a_livro(id_livro: int, autores: list[int]) -> int:
    rows = 0
    for id_autor in autores:
        rows += db_insert(
            'INSERT INTO autores_livros (id_autor, id_livro) '
            'VALUES (%s, %s)',
            (id_autor, id_livro)
        )


def buscar_estante(identificador_fisico: str) -> dict:
    id = db_fetch_one(
        'SELECT id FROM estantes WHERE identificador_fisico = %s',
        (identificador_fisico,)
    )

    return id


def resolver_cargo(cargo: int | str) -> int:
    if isinstance(cargo, int):
        return cargo

    cargos = db_fetch_all("SELECT id, cargo FROM cargos")
    nomes = [c['cargo'] for c in cargos]
    matches = get_close_matches(cargo, nomes, n=1, cutoff=0.6)

    if matches:
        return next(c['id'] for c in cargos if c['cargo'] == matches[0])

    raise HTTPException(
        status_code=404, detail=f"Cargo '{cargo}' não encontrado")
