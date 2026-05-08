from datetime import date
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


class FuncionarioSchema(PessoaSchema):
    cargo: int | str
    data_contratacao: date | None = None
