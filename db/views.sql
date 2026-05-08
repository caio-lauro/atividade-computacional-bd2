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