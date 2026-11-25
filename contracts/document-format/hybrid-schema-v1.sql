-- hybrid-schema-v1.sql  |  schema_version 1.0.0
-- DONA: SPEC-002 (formato .hybrid). Nenhuma outra spec define DDL.
-- Conexão: PRAGMA journal_mode = WAL; PRAGMA foreign_keys = ON; PRAGMA synchronous = NORMAL (WAL) - a validar no spike (c).

CREATE TABLE file_meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
) WITHOUT ROWID;
-- Chaves obrigatórias: schema_version, created_at, last_modified, app_version, doc_id

CREATE TABLE document_meta (
    doc_id        BLOB PRIMARY KEY,                 -- node_id do nó Document
    width         INTEGER NOT NULL CHECK (width  BETWEEN 1 AND 65536),
    height        INTEGER NOT NULL CHECK (height BETWEEN 1 AND 65536),
    dpi           INTEGER NOT NULL CHECK (dpi > 0),
    color_profile BLOB    NOT NULL,                 -- perfil ICC embutido
    bit_depth     INTEGER NOT NULL CHECK (bit_depth IN (8, 16)),
    blend_space   TEXT    NOT NULL CHECK (blend_space IN ('perceptual', 'linear'))
);

CREATE TABLE nodes (
    node_id    BLOB PRIMARY KEY,                    -- UUID v7 (16 bytes)
    parent_id  BLOB REFERENCES nodes(node_id),
    kind       TEXT NOT NULL CHECK (kind IN ('Document','Artboard','Group','RasterLayer','VectorLayer','EmbeddedImage')),
    ord        TEXT NOT NULL,                       -- índice fracionário
    name       TEXT NOT NULL DEFAULT '',
    visible    INTEGER NOT NULL DEFAULT 1,
    locked     INTEGER NOT NULL DEFAULT 0,
    opacity    REAL    NOT NULL DEFAULT 1.0 CHECK (opacity BETWEEN 0.0 AND 1.0),
    blend_mode TEXT    NOT NULL DEFAULT 'Normal',
    transform  BLOB    NOT NULL,                    -- 6 x f32 (24 bytes)
    clip_path  BLOB,
    mask       BLOB,
    extra      BLOB                                 -- dados específicos do kind (JSON)
);
CREATE INDEX idx_nodes_parent ON nodes(parent_id, ord);

CREATE TABLE tiles (
    hash    BLOB PRIMARY KEY,                       -- blake3 (32 bytes), imutável
    codec   TEXT    NOT NULL DEFAULT 'zstd',
    raw_len INTEGER NOT NULL,
    data    BLOB    NOT NULL
) WITHOUT ROWID;

CREATE TABLE tile_refs (
    layer_id  BLOB    NOT NULL REFERENCES nodes(node_id),
    mip       INTEGER NOT NULL DEFAULT 0,           -- nível 0 no R1; reservado para mipmaps
    col       INTEGER NOT NULL,
    row       INTEGER NOT NULL,
    tile_hash BLOB    NOT NULL REFERENCES tiles(hash),
    PRIMARY KEY (layer_id, mip, col, row)
) WITHOUT ROWID;
CREATE INDEX idx_tile_refs_hash ON tile_refs(tile_hash);

CREATE TABLE assets (
    hash   BLOB PRIMARY KEY,                        -- blake3 do conteúdo
    kind   TEXT NOT NULL,                           -- 'image'
    mime   TEXT NOT NULL,
    width  INTEGER,
    height INTEGER,
    data   BLOB NOT NULL
) WITHOUT ROWID;

CREATE TABLE oplog (
    seq            INTEGER PRIMARY KEY AUTOINCREMENT,
    op_id          BLOB    NOT NULL UNIQUE,
    author_id      BLOB    NOT NULL,
    device_id      BLOB    NOT NULL,
    hlc_ts         INTEGER NOT NULL,                -- HLC: milissegundos
    hlc_counter    INTEGER NOT NULL,                -- HLC: contador lógico
    base_seq       INTEGER NOT NULL,
    schema_version TEXT    NOT NULL,
    op_type        TEXT    NOT NULL,
    targets        BLOB    NOT NULL,                -- JSON: lista de node_id
    payload        BLOB    NOT NULL,                -- JSON comprimido (zstd)
    inverse        BLOB    NOT NULL,                -- JSON comprimido (zstd)
    created_at     TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_oplog_device_hlc ON oplog(device_id, hlc_ts, hlc_counter);

-- Regras de integridade (verificadas por testes, não por DDL):
-- 1. Tiles e assets são imutáveis e nunca removidos por esta versão (coleta de lixo é spec futura);
--    hashes citados em oplog.inverse precisam permanecer em `tiles`.
-- 2. nodes e tile_refs são o ESTADO MATERIALIZADO; são atualizados na mesma transação que insere em oplog.
-- 3. snapshots versionados e thumbnails entram com ADR-011 (R2); não existem no schema 1.0.0.
