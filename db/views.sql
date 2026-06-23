-- View que contém todas as informações de um dado usuário

CREATE OR REPLACE VIEW view_usuario AS
    SELECT p.id, p.nome, p.CPF, p.email, p.telefone, p.data_nascimento,
    u.status, u.limite_emprestimos
    FROM pessoas p INNER JOIN usuarios u
    ON p.id = u.id_usuario;


-- View que contém todas as informações de um dado funcionário

CREATE OR REPLACE VIEW view_funcionario AS
    SELECT p.id, p.nome, p.CPF, p.email, p.telefone, p.data_nascimento,
    c.cargo, f.data_contratacao
    FROM pessoas p INNER JOIN funcionarios f
    ON p.id = f.id_funcionario
    INNER JOIN cargos c
    ON f.id_cargo=c.id;


-- View que contém todas as informações de um dado livro físico

CREATE OR REPLACE VIEW view_fisico AS
    SELECT l.id, l.ISBN, l.titulo, l.data_publicacao, 
    f.disponivel, e.identificador_fisico Estante
    FROM livros l INNER JOIN exemplar_fisico f
    ON l.id=f.id_fisico 
    INNER JOIN estantes e
    ON f.id_estante_associada=e.id;


-- View que contém todas as informações de um dado livro digital

CREATE OR REPLACE VIEW view_digital AS
    SELECT l.id, l.ISBN, l.titulo, l.data_publicacao, 
    d.numero_acessos, d.URL
    FROM livros l INNER JOIN exemplar_digital d
    ON l.id=d.id_digital;
