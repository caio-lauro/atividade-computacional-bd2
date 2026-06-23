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


class _AtualizarPessoaSchema(BaseModel):
    nome: str | None = None
    CPF: str | None = None
    email: EmailStr | None = None
    senha: str | None = None
    telefone: str | None = None
    data_nascimento: date | None = None


class UsuarioSchema(PessoaSchema):
    ...


class StatusUsuario(str, Enum):
    ativo = 'ativo'
    inativo = 'inativo'


class AtualizarUsuarioSchema(_AtualizarPessoaSchema):
    status: StatusUsuario | None = None
    limite_emprestimos: int | None = None


class FuncionarioSchema(PessoaSchema):
    cargo: int | str
    data_contratacao: date | None = None


class AtualizarFuncionarioSchema(_AtualizarPessoaSchema):
    cargo: int | str | None = None
    data_contratacao: date | None = None


def criar_enum_cargos() -> type:
    from db import db_fetch_all
    cargos = db_fetch_all('SELECT id, cargo FROM cargos ORDER BY id')
    return Enum('CargoFuncionario', {c['cargo']: c['cargo'] for c in cargos})


CargoFuncionario = criar_enum_cargos()


class EstanteSchema(BaseModel):
    identificador_fisico: str
    capacidade: int


class AtualizarEstanteSchema(BaseModel):
    identificador_fisico: str | None = None
    capacidade: int | None = None


class LivroSchema(BaseModel):
    ISBN: str
    data_publicacao: date
    titulo: str


class ExemplarDigitalSchema(LivroSchema):
    acessos: int
    URL: str


class AtualizarExemplarDigitalSchema(BaseModel):
    ISBN: str | None = None
    data_publicacao: date | None = None
    titulo: str | None = None
    acessos: int | None = None
    URL: str | None = None


class ExemplarFisicoSchema(LivroSchema):
    estante: str


class StatusExemplarFisico(str, Enum):
    disponivel = 'disponível'
    indisponivel = 'indisponível'


class AtualizarExemplarFisicoSchema(BaseModel):
    ISBN: str | None = None
    data_publicacao: date | None = None
    titulo: str | None = None
    status: StatusExemplarFisico | None = None
    estante: str | None = None
