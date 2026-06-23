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


-- View que contém todas as informações de um dado livro e seus autores
CREATE OR REPLACE VIEW view_livro AS
    SELECT l.id, l.ISBN, l.titulo, l.data_publicacao,
    GROUP_CONCAT(a.nome ORDER BY a.nome SEPARATOR ', ') AS autores
    FROM livros l 
    INNER JOIN autores_livros al
    ON l.id=al.id_livro
    INNER JOIN autores a
    ON a.id=al.id_autor
    GROUP BY l.id, l.ISBN, l.titulo, l.data_publicacao;


-- View que contém todas as informações de um dado livro físico

CREATE OR REPLACE VIEW view_fisico AS
    SELECT l.id, l.ISBN, l.titulo, l.data_publicacao, l.autores,
    f.disponivel, e.identificador_fisico Estante
    FROM view_livro l INNER JOIN exemplar_fisico f
    ON l.id=f.id_fisico 
    INNER JOIN estantes e
    ON f.id_estante_associada=e.id;


-- View que contém todas as informações de um dado livro digital

CREATE OR REPLACE VIEW view_digital AS
    SELECT l.id, l.ISBN, l.titulo, l.data_publicacao, l.autores,
    d.numero_acessos, d.URL
    FROM view_livro l INNER JOIN exemplar_digital d
    ON l.id=d.id_digital;
