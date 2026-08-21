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

        forca INTEGER NOT NULL DEFAULT 0,
        destreza INTEGER NOT NULL DEFAULT 0,
        vigor INTEGER NOT NULL DEFAULT 0,
        inteligencia INTEGER NOT NULL DEFAULT 0,
        carisma INTEGER NOT NULL DEFAULT 0,
        raciocinio INTEGER NOT NULL DEFAULT 0,

        academicos INTEGER NOT NULL DEFAULT 0,
        idiomas INTEGER NOT NULL DEFAULT 0,
        oficios INTEGER NOT NULL DEFAULT 0,
        armas_brancas INTEGER NOT NULL DEFAULT 0,
        intimidacao INTEGER NOT NULL DEFAULT 0,
        ocultismo INTEGER NOT NULL DEFAULT 0,
        briga INTEGER NOT NULL DEFAULT 0,
        investigacao INTEGER NOT NULL DEFAULT 0,
        persuasao INTEGER NOT NULL DEFAULT 0,
        ciencias INTEGER NOT NULL DEFAULT 0,
        labia INTEGER NOT NULL DEFAULT 0,
        prontidao INTEGER NOT NULL DEFAULT 0,
        conhecimentos_gerais INTEGER NOT NULL DEFAULT 0,
        lideranca INTEGER NOT NULL DEFAULT 0,
        sobrevivencia INTEGER NOT NULL DEFAULT 0,
        conducao INTEGER NOT NULL DEFAULT 0,
        manha INTEGER NOT NULL DEFAULT 0,
        tecnologia INTEGER NOT NULL DEFAULT 0,
        esportes INTEGER NOT NULL DEFAULT 0,
        medicina INTEGER NOT NULL DEFAULT 0,
        mira INTEGER NOT NULL DEFAULT 0,
        esquiva INTEGER NOT NULL DEFAULT 0,
        furtividade INTEGER NOT NULL DEFAULT 0,

        aleatorio INTEGER NOT NULL DEFAULT 0
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
    idx_historico_data
    ON historico (
        criado_em
    )
""")


db.commit()


# ============================================================
# MIGRAÇÃO DE COLUNAS
# ============================================================

def adicionar_coluna_se_nao_existir(
    tabela,
    coluna,
    definicao
):

    cursor.execute(
        f"PRAGMA table_info({tabela})"
    )

    colunas = [
        linha[1]
        for linha in cursor.fetchall()
    ]

    if coluna not in colunas:

        cursor.execute(
            f"""
            ALTER TABLE {tabela}
            ADD COLUMN {coluna} {definicao}
            """
        )

        db.commit()


# ============================================================
# GARANTIR COLUNAS DA TABELA FICHAS
# ============================================================

COLUNAS_FICHAS = [
    (
        "xp",
        "INTEGER NOT NULL DEFAULT 0"
    ),

    (
        "forca",
        "INTEGER NOT NULL DEFAULT 0"
    ),

    (
        "destreza",
        "INTEGER NOT NULL DEFAULT 0"
    ),

    (
        "vigor",
        "INTEGER NOT NULL DEFAULT 0"
    ),

    (
        "inteligencia",
        "INTEGER NOT NULL DEFAULT 0"
    ),

    (
        "carisma",
        "INTEGER NOT NULL DEFAULT 0"
    ),

    (
        "raciocinio",
        "INTEGER NOT NULL DEFAULT 0"
    ),

    (
        "academicos",
        "INTEGER NOT NULL DEFAULT 0"
    ),

    (
        "idiomas",
        "INTEGER NOT NULL DEFAULT 0"
    ),

    (
        "oficios",
        "INTEGER NOT NULL DEFAULT 0"
    ),

    (
        "armas_brancas",
        "INTEGER NOT NULL DEFAULT 0"
    ),

    (
        "intimidacao",
        "INTEGER NOT NULL DEFAULT 0"
    ),

    (
        "ocultismo",
        "INTEGER NOT NULL DEFAULT 0"
    ),

    (
        "briga",
        "INTEGER NOT NULL DEFAULT 0"
    ),

    (
        "investigacao",
        "INTEGER NOT NULL DEFAULT 0"
    ),

    (
        "persuasao",
        "INTEGER NOT NULL DEFAULT 0"
    ),

    (
        "ciencias",
        "INTEGER NOT NULL DEFAULT 0"
    ),

    (
        "labia",
        "INTEGER NOT NULL DEFAULT 0"
    ),

    (
        "prontidao",
        "INTEGER NOT NULL DEFAULT 0"
    ),

    (
        "conhecimentos_gerais",
        "INTEGER NOT NULL DEFAULT 0"
    ),

    (
        "lideranca",
        "INTEGER NOT NULL DEFAULT 0"
    ),

    (
        "sobrevivencia",
        "INTEGER NOT NULL DEFAULT 0"
    ),

    (
        "conducao",
        "INTEGER NOT NULL DEFAULT 0"
    ),

    (
        "manha",
        "INTEGER NOT NULL DEFAULT 0"
    ),

    (
        "tecnologia",
        "INTEGER NOT NULL DEFAULT 0"
    ),

    (
        "esportes",
        "INTEGER NOT NULL DEFAULT 0"
    ),

    (
        "medicina",
        "INTEGER NOT NULL DEFAULT 0"
    ),

    (
        "mira",
        "INTEGER NOT NULL DEFAULT 0"
    ),

    (
        "esquiva",
        "INTEGER NOT NULL DEFAULT 0"
    ),

    (
        "furtividade",
        "INTEGER NOT NULL DEFAULT 0"
    ),

    (
        "aleatorio",
        "INTEGER NOT NULL DEFAULT 0"
    )
]


for (
    nome_coluna,
    definicao_coluna
) in COLUNAS_FICHAS:

    adicionar_coluna_se_nao_existir(
        "fichas",
        nome_coluna,
        definicao_coluna
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
    """, (
        channel_id,
    ))

    resultado = cursor.fetchone()

    if resultado:

        return resultado[0]

    return None


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
        (
            None
            if valor_anterior is None
            else str(valor_anterior)
        ),
        (
            None
            if valor_novo is None
            else str(valor_novo)
        ),
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
