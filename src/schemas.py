from datetime import date
from enum import Enum
from pydantic import BaseModel, EmailStr


class PessoaSchema(BaseModel):
    nome: str
    CPF: str
    email: EmailStr
    senha: str
    telefone: str
    data_nascimento: date


class UsuarioSchema(PessoaSchema):
    ...


class StatusUsuario(str, Enum):
    ativo = 'ativo'
    inativo = 'inativo'


class FuncionarioSchema(PessoaSchema):
    cargo: int | str
    data_contratacao: date | None = None


def criar_enum_cargos() -> type:
    from db import db_fetch_all
    cargos = db_fetch_all('SELECT id, cargo FROM cargos ORDER BY id')
    return Enum('CargoFuncionario', {c['cargo']: c['cargo'] for c in cargos})

CargoFuncionario = criar_enum_cargos()
