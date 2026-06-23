-- 
-- ESSE ARQUIVO UTILIZA UMA SEQUÊNCIA DE TRÊS '-' 
-- COMO SEPARADOR PARA CRIAR CADA TRIGGER.
--

-- Procedure para criar cargos automaticamente
---
CREATE PROCEDURE IF NOT EXISTS sp_criar_cargos ()
BEGIN
    INSERT IGNORE INTO cargos (cargo) VALUES
    ('Diretor'),
    ('Gerente'),
    ('Assistente Administrativo'),
    ('Bibliotecário'),
    ('Analista Técnico'),
    ('Documentalista'),
    ('Recepcionista'),
    ('Auxiliar');
END
---
CALL sp_criar_cargos()
---

-- Procedure que mostra autor e livro
---
CREATE PROCEDURE IF NOT EXISTS sp_lista_autores_livros()
BEGIN
    SELECT a.nome, a.nacionalidade, l.titulo, l.ISBN,
    CASE 
        WHEN ef.id_fisico IS NOT NULL AND ed.id_digital IS NOT NULL THEN 'Físico e Digital'
        WHEN ef.id_fisico IS NOT NULL THEN 'Físico'
        WHEN ed.id_digital IS NOT NULL THEN 'Digital'
        ELSE 'Não especificado'
    END AS formato_disponivel,
    ef.id_estante_associada AS codigo_estante,
    ed.URL AS link_download
    FROM autores a
    INNER JOIN autores_livros al ON a.id = al.id_autor
    INNER JOIN livros l ON l.id = al.id_livro
    LEFT JOIN exemplar_digital ed ON l.id = ed.id_digital
    LEFT JOIN exemplar_fisico ef ON l.id = ef.id_fisico;
END 
---

-- Procedure que mostra os funcionários responsáveis pelas estantes
---
CREATE PROCEDURE IF NOT EXISTS sp_funcionario_estante()
BEGIN
    SELECT p.nome, e.identificador_fisico
    FROM pessoa p
    INNER JOIN organizadores_estantes oe ON p.id = oe.id_funcionario
    INNER JOIN funcionarios f ON p.id = f.id_funcionario
    INNER JOIN estantes e ON oe.id_estante = e.id;
END
---

-- Procedure que mostra a capacidade de estantes e quantos livros estão nelas
---
CREATE PROCEDURE IF NOT EXISTS sp_lotacao_estantes()
BEGIN
    SELECT 
        e.identificador_fisico AS "Identificador da estante", 
        COUNT(ef.id_fisico) AS "Quantidade na estante", 
        e.capacidade AS "Capacidade da estante",
        CONCAT(ROUND((COUNT(ef.id_fisico) / e.capacidade) * 100, 2), "%") AS "Porcentagem"
    FROM estantes e
    LEFT JOIN exemplar_fisico ef ON e.id = ef.id_estante_associada
    LEFT JOIN livros l ON ef.id_fisico = l.id
    GROUP BY e.identificador_fisico, e.capacidade;
END
---

-- Procedure que mostra o nome dos usuários que têm empréstimos atrasados
---
CREATE PROCEDURE IF NOT EXISTS sp_emprestimo_atrasado()
BEGIN
    SELECT
        vu.nome as "Nome usuário",
        e.data_emprestimo as "Data empréstimo",
        e.data_devolucao as "Data devolução esperada",
        DATEDIFF(CURDATE(), e.data_devolucao) as "Tempo de atraso"
    FROM view_usuario vu
    INNER JOIN emprestimos e ON u.id_usuario = e.id_usuario;
END 
---