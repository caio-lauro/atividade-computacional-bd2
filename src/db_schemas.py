from datetime import date
from pydantic import BaseModel, EmailStr
from schemas import EstanteSchema


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


class EstanteDBSchema(EstanteSchema):
    id: int
