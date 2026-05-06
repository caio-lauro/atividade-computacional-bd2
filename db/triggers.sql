-- 
-- ESSE ARQUIVO UTILIZA UMA SEQUÊNCIA DE TRÊS '-' 
-- COMO SEPARADOR PARA CRIAR CADA TRIGGER.
--

-- Triggers para valores default
---
CREATE TRIGGER tg_default_usuario_ativo
BEFORE INSERT ON usuarios
FOR EACH ROW
BEGIN
    IF NEW.status is NULL THEN
        SET NEW.status = TRUE;
    END IF;
END
---