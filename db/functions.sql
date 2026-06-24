-- Função que mostra quantos livros um usuário já pegou emprestado
---
CREATE FUNCTION IF NOT EXISTS fn_conta_emprestimos(f_id_usuario INT) RETURNS INT
DETERMINISTIC
BEGIN
    DECLARE cont INT;
    SELECT COUNT(*) INTO cont FROM emprestimos WHERE f_id_usuario = id_usuario;
    RETURN cont;
END 
---

-- Função que retorna a quantidade de emprestimos ativos de um usuário
---
CREATE FUNCTION IF NOT EXISTS fn_conta_emprestimos_ativos(f_id_usuario INT) RETURNS INT
DETERMINISTIC
BEGIN
    DECLARE cont_ativos INT;
    SELECT COUNT(*) INTO cont_ativos FROM emprestimos WHERE f_id_usuario = id_usuario AND devolvido = FALSE;
    RETURN cont_ativos;
END 
---

-- Função que retorna a quantidade de espaços disponíveis em uma estante
---
CREATE FUNCTION IF NOT EXISTS fn_calcular_espacos_disponiveis(f_id_estante INT) RETURNS INT
DETERMINISTIC
BEGIN
    DECLARE disponivel INT;
    SELECT e.capacidade - COUNT(ef.id_fisico) INTO disponivel
    FROM estantes e
    LEFT JOIN exemplar_fisico ef ON e.id = ef.id_estante_associada
    LEFT JOIN livros l ON ef.id_fisico = l.id
    WHERE e.id=f_id_estante
    GROUP BY e.id, e.identificador_fisico, e.capacidade;
    RETURN disponivel;
END
---