 import sqlite3


# ============================================================
# CONEXÃO COM O BANCO
# ============================================================

db = sqlite3.connect("rpg_fichas.db")
cursor = db.cursor()


# ============================================================
# CRIAÇÃO DAS TABELAS
# ============================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS mesas (
    channel_id INTEGER PRIMARY KEY,
    mestre_id INTEGER
)
""")


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

db.commit()


# ============================================================
# MIGRAÇÃO
# ============================================================

def adicionar_coluna_se_nao_existir(nome_coluna):

    cursor.execute("PRAGMA table_info(fichas)")

    colunas = [
        coluna[1]
        for coluna in cursor.fetchall()
    ]

    if nome_coluna not in colunas:

        cursor.execute(
            f"""
            ALTER TABLE fichas
            ADD COLUMN {nome_coluna}
            INTEGER NOT NULL DEFAULT 0
            """
        )

        db.commit()


COLUNAS_NOVAS = [
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
    "furtividade"
]


for coluna in COLUNAS_NOVAS:
    adicionar_coluna_se_nao_existir(coluna)


# ============================================================
# MESAS
# ============================================================

def garantir_mesa(channel_id):

    cursor.execute("""
        INSERT OR IGNORE INTO mesas (
            channel_id,
            mestre_id
        )
        VALUES (?, NULL)
    """, (channel_id,))

    db.commit()


def obter_mestre(channel_id):

    cursor.execute("""
        SELECT mestre_id
        FROM mesas
        WHERE channel_id = ?
    """, (channel_id,))

    resultado = cursor.fetchone()

    if resultado:
        return resultado[0]

    return None


def definir_mestre(channel_id, mestre_id):

    garantir_mesa(channel_id)

    cursor.execute("""
        UPDATE mesas
        SET mestre_id = ?
        WHERE channel_id = ?
    """, (
        mestre_id,
        channel_id
    ))

    db.commit()


# ============================================================
# BUSCAR FICHAS
# ============================================================

def buscar_ficha_jogador(channel_id, user_id):

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


def buscar_ficha(ficha_id):

    cursor.execute("""
        SELECT *
        FROM fichas
        WHERE id = ?
    """, (ficha_id,))

    return cursor.fetchone()


def buscar_npcs(channel_id):

    cursor.execute("""
        SELECT *
        FROM fichas
        WHERE channel_id = ?
        AND tipo = 'npc'
        ORDER BY nome
    """, (channel_id,))

    return cursor.fetchall()


def buscar_npc_por_nome(channel_id, nome):

    cursor.execute("""
        SELECT *
        FROM fichas
        WHERE channel_id = ?
        AND tipo = 'npc'
        AND nome = ?
        LIMIT 1
    """, (
        channel_id,
        nome
    ))

    return cursor.fetchone()


# ============================================================
# CRIAR FICHA DE JOGADOR
# ============================================================

@bot.tree.command(
    name="criarficha",
    description="Cria sua ficha neste canal."
)
@app_commands.describe(
    nome="Nome do personagem",
    hp="HP inicial e máximo",
    mana="Mana inicial e máxima"
)
async def criarficha(
    interaction: discord.Interaction,
    nome: str,
    hp: int,
    mana: int
):

    garantir_mesa(
        interaction.channel.id
    )

    existente = buscar_ficha_jogador(
        interaction.channel.id,
        interaction.user.id
    )

    if existente:

        await interaction.response.send_message(
            "⚠️ Você já possui uma ficha neste canal.",
            ephemeral=True
        )

        return

    if hp <= 0:

        await interaction.response.send_message(
            "❌ O HP precisa ser maior que 0.",
            ephemeral=True
        )

        return

    if mana < 0:

        await interaction.response.send_message(
            "❌ A Mana não pode ser negativa.",
            ephemeral=True
        )

        return

    nome = nome[:50]

    criar_ficha_jogador(
        channel_id=interaction.channel.id,
        dono_id=interaction.user.id,
        nome=nome,
        hp=hp,
        mana=mana
    )

    await interaction.response.send_message(
        f"📜 Ficha de **{nome}** criada!\n\n"
        f"❤️ HP: **{hp}/{hp}**\n"
        f"🔵 Mana: **{mana}/{mana}**\n"
        f"✨ XP: **0**\n"
        f"⚡ RC: **5**"
    )

# ============================================================
# CRIAR NPC
# ============================================================

def criar_npc(
    channel_id,
    mestre_id,
    nome,
    hp,
    mana,
    atributos,
    pericias,
    aleatorio
):

    colunas_atributos = [
        "forca",
        "destreza",
        "vigor",
        "inteligencia",
        "carisma",
        "raciocinio"
    ]

    colunas_pericias = [
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
        "furtividade"
    ]

    colunas = (
        colunas_atributos
        + colunas_pericias
    )

    valores = (
        [atributos[chave] for chave in colunas_atributos]
        + [pericias[chave] for chave in colunas_pericias]
    )

    placeholders = ", ".join(
        ["?"] * len(valores)
    )

    cursor.execute(
        f"""
        INSERT INTO fichas (
            channel_id,
            dono_id,
            mestre_id,
            tipo,
            nome,
            hp_atual,
            hp_max,
            mana_atual,
            mana_max,
            xp,
            {", ".join(colunas)},
            aleatorio
        )
        VALUES (
            ?, NULL, ?, 'npc', ?,
            ?, ?, ?, ?, 0,
            {placeholders},
            ?
        )
        """,
        [
            channel_id,
            mestre_id,
            nome,
            hp,
            hp,
            mana,
            mana
        ]
        + valores
        + [aleatorio]
    )

    db.commit()

    return cursor.lastrowid


# ============================================================
# HP
# ============================================================

def alterar_hp(ficha_id, novo_hp):

    cursor.execute("""
        UPDATE fichas
        SET hp_atual = ?
        WHERE id = ?
    """, (
        novo_hp,
        ficha_id
    ))

    db.commit()

    return novo_hp


def alterar_hp_e_maximo(
    ficha_id,
    hp_atual,
    hp_max
):

    cursor.execute("""
        UPDATE fichas
        SET hp_atual = ?,
            hp_max = ?
        WHERE id = ?
    """, (
        hp_atual,
        hp_max,
        ficha_id
    ))

    db.commit()


# ============================================================
# MANA
# ============================================================

def alterar_mana(ficha_id, nova_mana):

    cursor.execute("""
        UPDATE fichas
        SET mana_atual = ?
        WHERE id = ?
    """, (
        nova_mana,
        ficha_id
    ))

    db.commit()

    return nova_mana


def alterar_mana_e_maximo(
    ficha_id,
    mana_atual,
    mana_max
):

    cursor.execute("""
        UPDATE fichas
        SET mana_atual = ?,
            mana_max = ?
        WHERE id = ?
    """, (
        mana_atual,
        mana_max,
        ficha_id
    ))

    db.commit()


# ============================================================
# XP
# ============================================================

def adicionar_xp(ficha_id, valor):

    cursor.execute("""
        UPDATE fichas
        SET xp = xp + ?
        WHERE id = ?
    """, (
        valor,
        ficha_id
    ))

    db.commit()

    cursor.execute("""
        SELECT xp
        FROM fichas
        WHERE id = ?
    """, (ficha_id,))

    resultado = cursor.fetchone()

    if resultado:
        return resultado[0]

    return None


def definir_xp(ficha_id, valor):

    cursor.execute("""
        UPDATE fichas
        SET xp = ?
        WHERE id = ?
    """, (
        valor,
        ficha_id
    ))

    db.commit()


# ============================================================
# ATRIBUTOS
# ============================================================

ATRIBUTOS_BANCO = [
    "forca",
    "destreza",
    "vigor",
    "inteligencia",
    "carisma",
    "raciocinio"
]


def alterar_atributo(
    ficha_id,
    atributo,
    valor
):

    if atributo not in ATRIBUTOS_BANCO:
        raise ValueError(
            f"Atributo inválido: {atributo}"
        )

    cursor.execute(
        f"""
        UPDATE fichas
        SET {atributo} = ?
        WHERE id = ?
        """,
        (
            valor,
            ficha_id
        )
    )

    db.commit()


# ============================================================
# PERÍCIAS
# ============================================================

PERICIAS_BANCO = [
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
    "furtividade"
]


def alterar_pericia(
    ficha_id,
    pericia,
    valor
):

    if pericia not in PERICIAS_BANCO:
        raise ValueError(
            f"Perícia inválida: {pericia}"
        )

    cursor.execute(
        f"""
        UPDATE fichas
        SET {pericia} = ?
        WHERE id = ?
        """,
        (
            valor,
            ficha_id
        )
    )

    db.commit()


# ============================================================
# ALTERAR MESTRE DOS NPCS
# ============================================================

def transferir_npcs(
    channel_id,
    mestre_id
):

    cursor.execute("""
        UPDATE fichas
        SET mestre_id = ?
        WHERE channel_id = ?
        AND tipo = 'npc'
    """, (
        mestre_id,
        channel_id
    ))

    db.commit()


# ============================================================
# ALTERAR NOME
# ============================================================

def alterar_nome(
    ficha_id,
    nome
):

    cursor.execute("""
        UPDATE fichas
        SET nome = ?
        WHERE id = ?
    """, (
        nome,
        ficha_id
    ))

    db.commit()


# ============================================================
# APAGAR FICHA
# ============================================================

def apagar_ficha(ficha_id):

    cursor.execute("""
        DELETE FROM fichas
        WHERE id = ?
    """, (ficha_id,))

    db.commit()


# ============================================================
# APAGAR NPC POR NOME
# ============================================================

def apagar_npc_por_nome(
    channel_id,
    nome
):

    cursor.execute("""
        DELETE FROM fichas
        WHERE channel_id = ?
        AND tipo = 'npc'
        AND nome = ?
    """, (
        channel_id,
        nome
    ))

    db.commit()

    return cursor.rowcount


# ============================================================
# FECHAR BANCO
# ============================================================

def fechar_banco():

    db.commit()
    db.close()
