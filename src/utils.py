from difflib import get_close_matches
from fastapi import HTTPException

from schemas import PessoaSchema
from db import db_insert, db_fetch_all
from auth import hash_senha


def criar_pessoa(pessoa: PessoaSchema) -> int:
    return db_insert(
        'INSERT INTO pessoas (nome, CPF, email, senha, telefone, data_nascimento) '
        'VALUES (%s, %s, %s, %s, %s, %s)',
        (pessoa.nome, pessoa.CPF.replace('-', ''), pessoa.email,
         hash_senha(pessoa.senha), pessoa.telefone.replace('-', ''), pessoa.data_nascimento)
    )


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
