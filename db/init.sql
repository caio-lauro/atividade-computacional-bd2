-- ===========================
-- Tabelas de Entidades Fortes
-- ===========================

-- Tabela de pessoas (para usuários e funcionários)
CREATE TABLE IF NOT EXISTS pessoas (
    id INT AUTO_INCREMENT NOT NULL,
    nome VARCHAR(50) NOT NULL,
    CPF VARCHAR(11) NOT NULL UNIQUE,
    email VARCHAR(50) NOT NULL UNIQUE,
    senha VARCHAR(100) NOT NULL,
    telefone VARCHAR(11),
    data_nascimento DATE NOT NULL,
    PRIMARY KEY (id)
);

-- Tabela de autores
CREATE TABLE IF NOT EXISTS autores (
    id INT AUTO_INCREMENT NOT NULL,
    nome VARCHAR(100) NOT NULL,
    nacionalidade VARCHAR(50) NOT NULL,
    PRIMARY KEY (id)
);

-- Tabela de Livros
CREATE TABLE IF NOT EXISTS livros (
    id INT AUTO_INCREMENT NOT NULL,
    ISBN VARCHAR(13) UNIQUE,
    titulo VARCHAR(100) NOT NULL,
    data_publicacao DATE NOT NULL,
    PRIMARY KEY (id)
);

-- Tabela de cargos para Funcionário
CREATE TABLE IF NOT EXISTS cargos (
    id INT AUTO_INCREMENT NOT NULL,
    cargo VARCHAR(50) NOT NULL UNIQUE,
    PRIMARY KEY (id)
);

-- Tabela de Estantes da Biblioteca
CREATE TABLE IF NOT EXISTS estantes (
    id INT AUTO_INCREMENT NOT NULL,
    identificador_fisico VARCHAR(10) UNIQUE NOT NULL,
    capacidade INT NOT NULL,
    PRIMARY KEY (id)
);

-- ===========================
-- Tabelas de Especializações
-- ===========================

-- Especialização de Pessoa: Usuário
CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario INT NOT NULL,
    status BOOLEAN NOT NULL,
    limite_emprestimos INT NOT NULL,
    PRIMARY KEY (id_usuario),
    FOREIGN KEY (id_usuario) REFERENCES pessoas(id)
);

-- Especialização de Pessoa: Funcionário
CREATE TABLE IF NOT EXISTS funcionarios (
    id_funcionario INT NOT NULL,
    id_cargo INT NOT NULL,
    data_contratacao DATE NOT NULL,
    PRIMARY KEY (id_funcionario),
    FOREIGN KEY (id_funcionario) REFERENCES pessoas(id),
    FOREIGN KEY (id_cargo) REFERENCES cargos(id)
);

-- Especialização de Livro: Exemplar Digital
CREATE TABLE IF NOT EXISTS exemplar_digital (
    id_digital INT NOT NULL,
    numero_acessos INT NOT NULL,
    URL VARCHAR(200) NOT NULL UNIQUE,
    PRIMARY KEY (id_digital),
    FOREIGN KEY (id_digital) REFERENCES livros(id)
);

-- Especialização de Livro: Exemplar Físico
CREATE TABLE IF NOT EXISTS exemplar_fisico (
    id_fisico INT NOT NULL,
    disponivel BOOLEAN NOT NULL,
    id_estante_associada INT NOT NULL,
    PRIMARY KEY (id_fisico),
    FOREIGN KEY (id_fisico) REFERENCES livros(id),
    FOREIGN KEY (id_estante_associada) REFERENCES estantes(id)
);

-- ===========================
-- Tabelas de Entidades Fracas
-- ===========================

-- Relação Escrever
CREATE TABLE IF NOT EXISTS autores_livros (
    id_autor INT NOT NULL,
    id_livro INT NOT NULL,
    FOREIGN KEY (id_autor) REFERENCES autores(id),
    FOREIGN KEY (id_livro) REFERENCES livros(id)
);

-- Relação Emprestar
CREATE TABLE IF NOT EXISTS emprestimos (
    id_usuario INT NOT NULL,
    id_fisico INT NOT NULL,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario),
    FOREIGN KEY (id_fisico) REFERENCES exemplar_fisico(id_fisico)
);

-- Relação Possuir já feita:
-- exemplar_fisico possui id_estante como campo

-- Relação Organizar
CREATE TABLE IF NOT EXISTS organizadores_estantes (
    id_funcionario INT NOT NULL,
    id_estante INT NOT NULL,
    FOREIGN KEY (id_funcionario) REFERENCES funcionarios(id_funcionario),
    FOREIGN KEY (id_estante) REFERENCES estantes(id)
);

-- Relação Exercer já feita:
-- funcionarios tem id_cargo como campo
