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