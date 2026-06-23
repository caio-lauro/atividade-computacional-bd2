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

-- Trigger de emprestimo
---
CREATE TRIGGER IF NOT EXISTS tg_emprestimo
BEFORE INSERT ON emprestimos
FOR EACH ROW
BEGIN
    DECLARE empresitmos_ativos INT;
    DECLARE t_limite_emprestimos INT;
    DECLARE disponibilidade_livro BOOLEAN;

    SELECT fn_conta_emprestimos_ativos(NEW.id_usuario) INTO empresitmos_ativos;
    SELECT limite_emprestimos INTO t_limite_emprestimos FROM usuarios WHERE id_usuario = NEW.id_usuario;
    SELECT disponivel INTO disponibilidade_livro FROM exemplar_fisico WHERE id_fisico = NEW.id_fisico;

    -- Vefifica se o livro não está disponível
    IF disponibilidade_livro = FALSE THEN
        SIGNAL SQLSTATE '40000'
            SET MESSAGE_TEXT='Livro indisponível para empréstimo.';
    END IF;

    -- verificar se o usuario pode fazer o emprestimo
    IF empresitmos_ativos >= t_limite_emprestimos THEN
        SIGNAL SQLSTATE '40000' 
            SET MESSAGE_TEXT='Não é possível realizar mais empréstimos para esse usuário.';
    END IF;

    -- colocar disponivel no exemplar fisico como false
    UPDATE exemplar_fisico SET disponivel = FALSE WHERE id_fisico = NEW.id_fisico;

    SET NEW.data_emprestimo = CURDATE();
    SET NEW.data_devolucao = DATE_ADD(CURDATE(), INTERVAL 20 DAY);
END
---