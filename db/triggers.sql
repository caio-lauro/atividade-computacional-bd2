-- 
-- ESSE ARQUIVO UTILIZA UMA SEQUÊNCIA DE TRÊS '-' 
-- COMO SEPARADOR PARA CRIAR CADA TRIGGER.
--

-- Triggers para valores default

-- Trigger para definir o status do usuário como ativo
---
CREATE TRIGGER IF NOT EXISTS tg_default_usuario_ativo
BEFORE INSERT ON usuarios
FOR EACH ROW
BEGIN
    IF NEW.status IS NULL THEN
        SET NEW.status = TRUE;
    END IF;
END
---

-- Trigger para definir o limite de empréstimo padrão como 5
---
CREATE TRIGGER IF NOT EXISTS tg_default_usuario_limite
BEFORE INSERT ON usuarios
FOR EACH ROW
BEGIN
    IF NEW.limite_emprestimos IS NULL THEN
        SET NEW.limite_emprestimos = 5;
    END IF;
END
---

-- Trigger para definir a data de contratação padrão como a data atual
---
CREATE TRIGGER IF NOT EXISTS tg_default_funcionario_data_contratacao
BEFORE INSERT ON funcionarios
FOR EACH ROW
BEGIN
    IF NEW.data_contratacao IS NULL THEN
        SET NEW.data_contratacao = CURRENT_DATE();
    END IF;
END
---

-- Trigger para definir o número de acessos padrão como 0
---
CREATE TRIGGER IF NOT EXISTS tg_default_fisico_acessos
BEFORE INSERT ON exemplar_digital
FOR EACH ROW
BEGIN
    IF NEW.numero_acessos IS NULL THEN
        SET NEW.numero_acessos = 0;
    END IF;
END
---