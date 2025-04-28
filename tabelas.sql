-- ================================================
-- Tabelas do Banco de Dados
-- ================================================

-- 1. Tabela de Grupo
CREATE TABLE grupo (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL UNIQUE
);

-- 2. Tabela de Usuário
CREATE TABLE usuario (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    senha VARCHAR(200) NOT NULL,
    grupo_id INT,
    grupo_original_id INT,
    avatar VARCHAR(200),
    bio TEXT,
    rede_social VARCHAR(255),
    FOREIGN KEY (grupo_id) REFERENCES grupo(id),
    FOREIGN KEY (grupo_original_id) REFERENCES grupo(id)
);


-- 4. Tabela de Conexão entre Usuários
CREATE TABLE conexao (
    id INT AUTO_INCREMENT PRIMARY KEY,
    seguidor_id INT NOT NULL,
    seguido_id INT NOT NULL,
    visto BOOLEAN DEFAULT FALSE,
    data_visto DATETIME,
    FOREIGN KEY (seguidor_id) REFERENCES usuario(id),
    FOREIGN KEY (seguido_id) REFERENCES usuario(id),
    UNIQUE (seguidor_id, seguido_id)
);

-- 5. Tabela de Pedido de Seguir
CREATE TABLE pedido_seguir (
    id INT AUTO_INCREMENT PRIMARY KEY,
    remetente_id INT NOT NULL,
    destinatario_id INT NOT NULL,
    status VARCHAR(20) DEFAULT 'pendente',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    visto BOOLEAN DEFAULT FALSE,
    data_visto DATETIME,
    FOREIGN KEY (remetente_id) REFERENCES usuario(id),
    FOREIGN KEY (destinatario_id) REFERENCES usuario(id)
);

-- 6. Tabela de Convite de Grupo
CREATE TABLE convite_grupo (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email_convidado VARCHAR(120) NOT NULL,
    grupo_id INT NOT NULL,
    token VARCHAR(64) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'pendente',
    data_envio DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (grupo_id) REFERENCES grupo(id)
);

-- 7. Tabela de Solicitação de Grupo
CREATE TABLE solicitacao_grupo (
    id INT AUTO_INCREMENT PRIMARY KEY,
    solicitante_id INT NOT NULL,
    grupo_id INT NOT NULL,
    status VARCHAR(20) DEFAULT 'pendente',
    visto BOOLEAN DEFAULT FALSE,
    data_visto DATETIME,
    FOREIGN KEY (solicitante_id) REFERENCES usuario(id),
    FOREIGN KEY (grupo_id) REFERENCES grupo(id)
);

-- 8. Tabela de Histórico de Ranking
CREATE TABLE historico_ranking (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    grupo_id INT NOT NULL,
    tarefas_concluidas INT NOT NULL,
    semana VARCHAR(10) NOT NULL,  -- Ex: '2025-W15'
    data_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuario(id),
    FOREIGN KEY (grupo_id) REFERENCES grupo(id)
);

-- 9. Tabela de Tarefa Padrão
CREATE TABLE tarefa_padrao (
    id INT AUTO_INCREMENT PRIMARY KEY,
    descricao VARCHAR(200) NOT NULL,
    imagem VARCHAR(200)
);

-- 10. Tabela de Tarefa (criada por um usuário para o grupo)
CREATE TABLE tarefa (
    id INT AUTO_INCREMENT PRIMARY KEY,
    descricao VARCHAR(120) NOT NULL,
    imagem VARCHAR(120),
    grupo_id INT,
    usuario_id INT,  -- Criador
    concluida_por INT,  -- Concluidor
    data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
    data_conclusao DATETIME,
    concluida BOOLEAN DEFAULT FALSE,
    ativa BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (grupo_id) REFERENCES grupo(id),
    FOREIGN KEY (usuario_id) REFERENCES usuario(id),
    FOREIGN KEY (concluida_por) REFERENCES usuario(id)
);