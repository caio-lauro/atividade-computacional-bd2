from datetime import date
from pydantic import BaseModel
from schemas import PessoaSchema, UsuarioSchema, FuncionarioSchema


class PessoaDBSchema(PessoaSchema):
    id: int


class UsuarioDBSchema(UsuarioSchema):
    id_usuario: int
    status: bool
    limite_emprestimos: int


class FuncionarioDBSchema(FuncionarioSchema):
    id_funcionario: int
    data_contratacao: date


class PessoaLista(BaseModel):
    pessoas: list[PessoaDBSchema]


class UsuarioLista(BaseModel):
    usuarios: list[UsuarioDBSchema]


class FuncionarioLista(BaseModel):
    funcionarios: list[FuncionarioDBSchema]
