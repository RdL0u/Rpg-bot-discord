 import sqlite3


# ============================================================
# BANCO DE DADOS
# ============================================================

db = sqlite3.connect(
    "rpg_fichas.db"
)

cursor = db.cursor()


# ============================================================
# TABELA DE MESAS
# ============================================================

cursor.execute("""
    CREATE TABLE IF NOT EXISTS mesas (
        channel_id INTEGER PRIMARY KEY,
        mestre_id INTEGER
    )
""")


# ============================================================
# TABELA DE FICHAS
# ============================================================

cursor.execute("""
    CREATE TABLE IF NOT EXISTS fichas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        channel_id INTEGER NOT NULL,

        dono_id INTEGER,
        mestre_id INTEGER,

        tipo TEXT NOT NULL,
        nome TEXT NOT NULL,

        hp_atual INTEGER NOT NULL,
        hp_max INTEGER NOT NULL,

        mana_atual INTEGER NOT NULL,
        mana_max INTEGER NOT NULL,

        xp INTEGER NOT NULL DEFAULT 0,

        forca INTEGER DEFAULT 0,
        destreza INTEGER DEFAULT 0,
        vigor INTEGER DEFAULT 0,
        inteligencia INTEGER DEFAULT 0,
        carisma INTEGER DEFAULT 0,
        raciocinio INTEGER DEFAULT 0,

        academicos INTEGER DEFAULT 0,
        idiomas INTEGER DEFAULT 0,
        oficios INTEGER DEFAULT 0,
        armas_brancas INTEGER DEFAULT 0,
        intimidacao INTEGER DEFAULT 0,
        ocultismo INTEGER DEFAULT 0,
        briga INTEGER DEFAULT 0,
        investigacao INTEGER DEFAULT 0,
        persuasao INTEGER DEFAULT 0,
        ciencias INTEGER DEFAULT 0,
        labia INTEGER DEFAULT 0,
        prontidao INTEGER DEFAULT 0,
        conhecimentos_gerais INTEGER DEFAULT 0,
        lideranca INTEGER DEFAULT 0,
        sobrevivencia INTEGER DEFAULT 0,
        conducao INTEGER DEFAULT 0,
        manha INTEGER DEFAULT 0,
        tecnologia INTEGER DEFAULT 0,
        esportes INTEGER DEFAULT 0,
        medicina INTEGER DEFAULT 0,
        mira INTEGER DEFAULT 0,
        esquiva INTEGER DEFAULT 0,
        furtividade INTEGER DEFAULT 0,

        aleatorio INTEGER DEFAULT 0
    )
""")


# ============================================================
# TABELA DE HISTÓRICO
# ============================================================

cursor.execute("""
    CREATE TABLE IF NOT EXISTS historico (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        channel_id INTEGER NOT NULL,

        ficha_id INTEGER,

        ficha_nome TEXT NOT NULL,

        ficha_tipo TEXT NOT NULL,

        usuario_id INTEGER,

        acao TEXT NOT NULL,

        campo TEXT,

        valor_anterior TEXT,

        valor_novo TEXT,

        descricao TEXT,

        criado_em TIMESTAMP NOT NULL
            DEFAULT CURRENT_TIMESTAMP
    )
""")


# ============================================================
# ÍNDICES DO HISTÓRICO
# ============================================================

cursor.execute("""
    CREATE INDEX IF NOT EXISTS
    idx_historico_channel
    ON historico (
        channel_id
    )
""")


cursor.execute("""
    CREATE INDEX IF NOT EXISTS
    idx_historico_ficha
    ON historico (
        ficha_id
    )
""")


cursor.execute("""
    CREATE INDEX IF NOT EXISTS
    idx_historico_acao
    ON historico (
        acao
    )
""")


cursor.execute("""
    CREATE INDEX IF NOT EXISTS
    idx_historico_data
    ON historico (
        criado_em
    )
""")


db.commit()


# ============================================================
# MIGRAÇÃO DE COLUNAS DA TABELA FICHAS
# ============================================================

def adicionar_coluna_se_nao_existir(
    nome_coluna
):

    cursor.execute(
        "PRAGMA table_info(fichas)"
    )

    colunas = [
        coluna[1]
        for coluna in cursor.fetchall()
    ]

    if nome_coluna not in colunas:

        cursor.execute(
            f"""
            ALTER TABLE fichas
            ADD COLUMN {nome_coluna}
            INTEGER DEFAULT 0
            """
        )

        db.commit()


# ============================================================
# GARANTIR TODAS AS COLUNAS DA FICHA
# ============================================================

COLUNAS_FICHAS = [
    "xp",

    "forca",
    "destreza",
    "vigor",
    "inteligencia",
    "carisma",
    "raciocinio",

    "academicos",
    "idiomas",
    "oficios",
    "armas_brancas",
    "intimidacao",
    "ocultismo",
    "briga",
    "investigacao",
    "persuasao",
    "ciencias",
    "labia",
    "prontidao",
    "conhecimentos_gerais",
    "lideranca",
    "sobrevivencia",
    "conducao",
    "manha",
    "tecnologia",
    "esportes",
    "medicina",
    "mira",
    "esquiva",
    "furtividade",

    "aleatorio",
]


for coluna in COLUNAS_FICHAS:

    adicionar_coluna_se_nao_existir(
        coluna
    )


# ============================================================
# GARANTIR MESA
# ============================================================

def garantir_mesa(
    channel_id
):

    cursor.execute("""
        INSERT OR IGNORE INTO mesas (
            channel_id,
            mestre_id
        )
        VALUES (?, NULL)
    """, (
        channel_id,
    ))

    db.commit()


# ============================================================
# OBTER MESTRE
# ============================================================

def obter_mestre(
    channel_id
):

    cursor.execute("""
        SELECT mestre_id
        FROM mesas
        WHERE channel_id = ?
        LIMIT 1
    """, (
        channel_id,
    ))

    resultado = cursor.fetchone()

    if resultado is None:

        return None

    return resultado[0]


# ============================================================
# BUSCAR FICHA DE JOGADOR
# ============================================================

def buscar_ficha_jogador(
    channel_id,
    user_id
):

    cursor.execute("""
        SELECT *
        FROM fichas
        WHERE channel_id = ?
        AND dono_id = ?
        AND tipo = 'jogador'
        LIMIT 1
    """, (
        channel_id,
        user_id
    ))

    return cursor.fetchone()


# ============================================================
# BUSCAR FICHA POR ID
# ============================================================

def buscar_ficha(
    ficha_id
):

    cursor.execute("""
        SELECT *
        FROM fichas
        WHERE id = ?
        LIMIT 1
    """, (
        ficha_id,
    ))

    return cursor.fetchone()


# ============================================================
# REGISTRAR HISTÓRICO
# ============================================================

def registrar_historico(
    channel_id,
    ficha_id,
    ficha_nome,
    ficha_tipo,
    usuario_id,
    acao,
    campo=None,
    valor_anterior=None,
    valor_novo=None,
    descricao=None
):

    if valor_anterior is not None:

        valor_anterior = str(
            valor_anterior
        )

    if valor_novo is not None:

        valor_novo = str(
            valor_novo
        )

    cursor.execute("""
        INSERT INTO historico (
            channel_id,
            ficha_id,
            ficha_nome,
            ficha_tipo,
            usuario_id,
            acao,
            campo,
            valor_anterior,
            valor_novo,
            descricao
        )
        VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
    """, (
        channel_id,
        ficha_id,
        ficha_nome,
        ficha_tipo,
        usuario_id,
        acao,
        campo,
        valor_anterior,
        valor_novo,
        descricao
    ))

    db.commit()


# ============================================================
# BUSCAR HISTÓRICO DA MESA
# ============================================================

def buscar_historico(
    channel_id,
    limite=100
):

    cursor.execute("""
        SELECT *
        FROM historico
        WHERE channel_id = ?
        ORDER BY id DESC
        LIMIT ?
    """, (
        channel_id,
        limite
    ))

    return cursor.fetchall()


# ============================================================
# BUSCAR HISTÓRICO DE UMA FICHA
# ============================================================

def buscar_historico_ficha(
    channel_id,
    ficha_id,
    limite=100
):

    cursor.execute("""
        SELECT *
        FROM historico
        WHERE channel_id = ?
        AND ficha_id = ?
        ORDER BY id DESC
        LIMIT ?
    """, (
        channel_id,
        ficha_id,
        limite
    ))

    return cursor.fetchall()


# ============================================================
# ATUALIZAR HP
# ============================================================

def atualizar_hp(
    ficha_id,
    novo_hp
):

    cursor.execute("""
        UPDATE fichas
        SET hp_atual = ?
        WHERE id = ?
    """, (
        novo_hp,
        ficha_id
    ))

    db.commit()


# ============================================================
# ATUALIZAR MANA
# ============================================================

def atualizar_mana(
    ficha_id,
    nova_mana
):

    cursor.execute("""
        UPDATE fichas
        SET mana_atual = ?
        WHERE id = ?
    """, (
        nova_mana,
        ficha_id
    ))

    db.commit()


# ============================================================
# ADICIONAR XP
# ============================================================

def adicionar_xp(
    ficha_id,
    valor
):

    cursor.execute("""
        UPDATE fichas
        SET xp = xp + ?
        WHERE id = ?
    """, (
        valor,
        ficha_id
    ))

    db.commit()


# ============================================================
# DELETAR FICHA
# ============================================================

def deletar_ficha(
    ficha_id
):

    cursor.execute("""
        DELETE FROM fichas
        WHERE id = ?
    """, (
        ficha_id,
    ))

    db.commit()
