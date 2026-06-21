-- Função que mostra quantos livros um usuário já pegou emprestado
---
CREATE FUNCTION IF NOT EXISTS fn_conta_emprestimos(f_id_usuario INT) RETURNS INT
DETERMINISTIC
BEGIN
    DECLARE cont INT;
    SELECT COUNT(*) INTO cont FROM emprestimos WHERE f_id_usuario = id_usuario;
    RETURN cont;
END #
---