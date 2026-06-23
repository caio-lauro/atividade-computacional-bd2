from datetime import date
from pydantic import BaseModel, EmailStr
from schemas import AutorSchema


class _PessoaDBSchema(BaseModel):
    id: int
    nome: str
    CPF: str
    email: EmailStr
    telefone: str
    data_nascimento: date


class UsuarioDBSchema(_PessoaDBSchema):
    status: bool
    limite_emprestimos: int


class FuncionarioDBSchema(_PessoaDBSchema):
    cargo: str
    data_contratacao: date


class EstanteDBSchema(BaseModel):
    id: int
    identificador_fisico: str
    capacidade: int
    responsaveis: list[str]


class _LivroDBSchema(BaseModel):
    id: int
    ISBN: str
    titulo: str
    data_publicacao: date
    autores: list[str]


class ExemplarDigitalDBSchema(_LivroDBSchema):
    acessos: int
    URL: str


class ExemplarFisicoDBSchema(_LivroDBSchema):
    disponivel: bool
    Estante: str


class AutorDBSchema(AutorSchema):
    id: int
