from difflib import get_close_matches
from fastapi import HTTPException

from schemas import PessoaSchema, LivroSchema, AtualizarLivroSchema, AtualizarPessoaSchema
from db import db_fetch_all, db_fetch_one
from auth import hash_senha


def cursor_criar_pessoa(cursor, pessoa: PessoaSchema):
    cursor.execute(
        'INSERT INTO pessoas (nome, CPF, email, senha, telefone, data_nascimento) '
        'VALUES (%s, %s, %s, %s, %s, %s)',
        (pessoa.nome, pessoa.CPF.replace('-', '').replace('.', ''), pessoa.email,
         hash_senha(pessoa.senha), pessoa.telefone.replace('-', ''), pessoa.data_nascimento)
    )


def cursor_criar_livro(cursor, livro: LivroSchema):
    cursor.execute(
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


def stmts_adicionar_autores_a_livro(id_livro: int, autores: list[int]) -> list[tuple[str, tuple]]:
    stmts = []
    for id_autor in autores:
        stmts.append((
            'INSERT INTO autores_livros (id_autor, id_livro) '
            'VALUES (%s, %s)',
            (id_autor, id_livro)
        ))
    return stmts


def stmt_atualizar_pessoa(id_pessoa: int, pessoa: AtualizarPessoaSchema) -> tuple[str, tuple]:
    fields = []
    params = []

    if pessoa.nome:
        fields.append('nome = %s')
        params.append(pessoa.nome)

    if pessoa.CPF:
        fields.append('CPF = %s')
        params.append(pessoa.CPF)

    if pessoa.email:
        fields.append('email = %s')
        params.append(pessoa.email)

    if pessoa.senha:
        fields.append('senha = %s')
        params.append(hash_senha(pessoa.senha))

    if pessoa.telefone:
        fields.append('telefone = %s')
        params.append(pessoa.telefone)

    if pessoa.data_nascimento:
        fields.append('data_nascimento = %s')
        params.append(pessoa.data_nascimento)

    if not fields:
        return []
    
    params.append(id_pessoa)
    return (
        f'UPDATE pessoas SET {','.join(fields)} WHERE id = %s',
        params
    )


def stmts_atualizar_livro(id_livro: int, livro: AtualizarLivroSchema) -> list[tuple[str, tuple]]:
    fields = []
    params = []

    if livro.ISBN:
        fields.append('ISBN = %s')
        params.append(livro.ISBN)
    
    if livro.data_publicacao:
        fields.append('data_publicacao = %s')
        params.append(livro.data_publicacao)

    if livro.titulo:
        fields.append('titulo = %s')
        params.append(livro.titulo)

    if not fields:
        return []

    params.append(id_livro)
    stmts = [(f'UPDATE livros SET {','.join(fields)} WHERE id = %s', params)]

    if livro.autores:
        stmts.append((
            'DELETE FROM autores_livros WHERE id_livro = %s',
            (id_livro,)
        ))
        
        stmts.extend(stmts_adicionar_autores_a_livro(id_livro, livro.autores))

    return stmts


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
