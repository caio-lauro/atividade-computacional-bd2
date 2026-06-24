from datetime import date
from enum import Enum
from pydantic import BaseModel, EmailStr, Field, NonNegativeInt, HttpUrl


class PessoaSchema(BaseModel):
    nome: str
    CPF: str
    email: EmailStr
    senha: str
    telefone: str
    data_nascimento: date


class AtualizarPessoaSchema(BaseModel):
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


class AtualizarUsuarioSchema(AtualizarPessoaSchema):
    status: StatusUsuario | None = None
    limite_emprestimos: NonNegativeInt | None = None


class FuncionarioSchema(PessoaSchema):
    cargo: int | str
    data_contratacao: date | None = None


class AtualizarFuncionarioSchema(AtualizarPessoaSchema):
    cargo: int | str | None = None
    data_contratacao: date | None = None


def criar_enum_cargos() -> type:
    from db import db_fetch_all
    cargos = db_fetch_all('SELECT id, cargo FROM cargos ORDER BY id')
    return Enum('CargoFuncionario', {c['cargo']: c['cargo'] for c in cargos})


CargoFuncionario = criar_enum_cargos()


class EstanteSchema(BaseModel):
    identificador_fisico: str
    capacidade: NonNegativeInt
    funcionarios_responsaveis: list[int] = Field(min_length=1)


class AtualizarEstanteSchema(BaseModel):
    identificador_fisico: str | None = None
    capacidade: NonNegativeInt | None = None
    funcionarios_responsaveis: list[int] = []


class LivroSchema(BaseModel):
    ISBN: str
    data_publicacao: date
    titulo: str
    autores: list[int] = Field(min_length=1)


class ExemplarDigitalSchema(LivroSchema):
    numero_acessos: NonNegativeInt = 0
    URL: HttpUrl


class AtualizarLivroSchema(BaseModel):
    ISBN: str | None = None
    data_publicacao: date | None = None
    titulo: str | None = None
    autores: list[int] = []


class AtualizarExemplarDigitalSchema(AtualizarLivroSchema):
    numero_acessos: NonNegativeInt | None = None
    URL: HttpUrl | None = None


class ExemplarFisicoSchema(LivroSchema):
    estante: str


class StatusExemplarFisico(str, Enum):
    disponivel = 'disponível'
    indisponivel = 'indisponível'


class AtualizarExemplarFisicoSchema(AtualizarLivroSchema):
    status: StatusExemplarFisico | None = None
    estante: str | None = None


class AutorSchema(BaseModel):
    nome: str
    nacionalidade: str


class AtualizarAutorSchema(BaseModel):
    nome: str | None = None
    nacionalidade: str | None = None


class EmprestimoSchema(BaseModel):
    id_usuario: NonNegativeInt
    id_livro_fisico: NonNegativeInt


class AtualizarEmprestimoSchema(BaseModel):
    data_devolucao: date | None = None
    devolvido: bool | None = None
