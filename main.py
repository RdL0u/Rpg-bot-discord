import os
import random
import discord

from discord.ext import commands
from discord import app_commands

from database import db, cursor


# ============================================================
# CONFIGURAÇÃO
# ============================================================

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN não foi configurado.")


# ============================================================
# BANCO DE DADOS
# ============================================================

db = sqlite3.connect("rpg_fichas.db")
cursor = db.cursor()


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
    colunas = [coluna[1] for coluna in cursor.fetchall()]

    if nome_coluna not in colunas:

        cursor.execute(
            f"""
            ALTER TABLE fichas
            ADD COLUMN {nome_coluna} INTEGER NOT NULL DEFAULT 0
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
# BOT
# ============================================================

intents = discord.Intents.default()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# ============================================================
# ATRIBUTOS
# ============================================================

ATRIBUTOS = {
    "forca": ("💪", "Força", "For"),
    "destreza": ("🏹", "Destreza", "Des"),
    "vigor": ("🛡️", "Vigor", "Vig"),
    "inteligencia": ("🧠", "Inteligência", "Int"),
    "carisma": ("🎭", "Carisma", "Car"),
    "raciocinio": ("💡", "Raciocínio", "Rac")
}


# ============================================================
# PERÍCIAS
# ============================================================

PERICIAS = {
    "academicos": ("📚", "Acadêmicos"),
    "idiomas": ("🗣️", "Idiomas"),
    "oficios": ("🔧", "Ofícios"),
    "armas_brancas": ("⚔️", "Armas Brancas"),
    "intimidacao": ("😠", "Intimidação"),
    "ocultismo": ("🔮", "Ocultismo"),
    "briga": ("👊", "Briga"),
    "investigacao": ("🔎", "Investigação"),
    "persuasao": ("🤝", "Persuasão"),
    "ciencias": ("🧪", "Ciências"),
    "labia": ("💬", "Lábia"),
    "prontidao": ("👁️", "Prontidão"),
    "conhecimentos_gerais": ("🌎", "Conhecimentos Gerais"),
    "lideranca": ("👑", "Liderança"),
    "sobrevivencia": ("🏕️", "Sobrevivência"),
    "conducao": ("🚗", "Condução"),
    "manha": ("🕵️", "Manha"),
    "tecnologia": ("💻", "Tecnologia"),
    "esportes": ("🏃", "Esportes"),
    "medicina": ("⚕️", "Medicina"),
    "mira": ("🎯", "Mira"),
    "esquiva": ("💨", "Esquiva"),
    "furtividade": ("🥷", "Furtividade")
}


ORDEM_PERICIAS = list(PERICIAS.keys())


# ============================================================
# FUNÇÕES AUXILIARES
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


def eh_admin(interaction):

    if interaction.guild is None:
        return False

    return interaction.user.guild_permissions.administrator


def eh_mestre(interaction):

    return (
        obter_mestre(interaction.channel.id)
        == interaction.user.id
    )


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


def transformar_ficha(dados):

    if dados is None:
        return None

    colunas = [
        "id",
        "channel_id",
        "dono_id",
        "mestre_id",
        "tipo",
        "nome",

        "hp_atual",
        "hp_max",

        "mana_atual",
        "mana_max",

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

        "aleatorio"
    ]

    ficha = {}

    for indice, coluna in enumerate(colunas):

        if indice < len(dados):
            ficha[coluna] = dados[indice]

    return ficha


# ============================================================
# REFLEXO DE COMBATE
# ============================================================

def calcular_rc(ficha):

    return (
        ficha["esquiva"]
        + ficha["destreza"]
        + 5
    )


# ============================================================
# PÁGINA 1
# ============================================================

def criar_pagina_status(f, jogador=None):

    embed = discord.Embed(
        title=f"📜 FICHA DE {f['nome'].upper()}",
        color=discord.Color.dark_red()
    )

    if jogador:

        identificacao = (
            f"Jogador: {jogador.mention}"
        )

    else:

        identificacao = "👹 NPC"

    status = (
        f"❤️ HP: **{f['hp_atual']}/{f['hp_max']}**    "
        f"🔵 Mana: **{f['mana_atual']}/{f['mana_max']}**\n"
        f"✨ XP: **{f['xp']}**    "
        f"⚡ RC: **{calcular_rc(f)}**"
    )

    atributos = (
        f"💪 For: **{f['forca']}**    "
        f"🏹 Des: **{f['destreza']}**\n"
        f"🛡️ Vig: **{f['vigor']}**    "
        f"🧠 Int: **{f['inteligencia']}**\n"
        f"🎭 Car: **{f['carisma']}**    "
        f"💡 Rac: **{f['raciocinio']}**"
    )

    embed.description = (
        f"{identificacao}\n\n"
        f"❤️ **STATUS**\n"
        f"{status}\n\n"
        f"⚔️ **ATRIBUTOS**\n"
        f"{atributos}"
    )

    embed.set_footer(
        text="Página 1/2 • Status e Atributos"
    )

    return embed


# ============================================================
# PÁGINA 2
# ============================================================

def criar_pagina_pericias(f):

    embed = discord.Embed(
        title=f"📚 PERÍCIAS — {f['nome']}",
        color=discord.Color.dark_red()
    )

    linhas = []

    for chave, (emoji, nome) in PERICIAS.items():

        linhas.append(
            f"{emoji} {nome}: **{f[chave]}**"
        )

    texto = "\n".join(linhas)

    embed.description = (
        "📚 **PERÍCIAS**\n\n"
        f"{texto}"
    )

    embed.set_footer(
        text="Página 2/2 • Perícias"
    )

    return embed


# ============================================================
# PAGINAÇÃO DA FICHA
# ============================================================

class FichaView(discord.ui.View):

    def __init__(self, ficha, jogador=None):

        super().__init__(timeout=120)

        self.ficha = ficha
        self.jogador = jogador

    @discord.ui.button(
        label="◀ Status",
        style=discord.ButtonStyle.primary
    )
    async def status(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.edit_message(
            embed=criar_pagina_status(
                self.ficha,
                self.jogador
            ),
            view=self
        )

    @discord.ui.button(
        label="Perícias ▶",
        style=discord.ButtonStyle.primary
    )
    async def pericias(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.edit_message(
            embed=criar_pagina_pericias(
                self.ficha
            ),
            view=self
        )


# ============================================================
# PERMISSÕES
# ============================================================

def pode_alterar_ficha(interaction, ficha):

    if eh_admin(interaction):
        return True

    if ficha["tipo"] == "jogador":

        return (
            ficha["dono_id"]
            == interaction.user.id
            or eh_mestre(interaction)
        )

    if ficha["tipo"] == "npc":

        return (
            eh_mestre(interaction)
            or ficha["mestre_id"]
            == interaction.user.id
        )

    return False


def pode_alterar_status(interaction, ficha):

    if eh_admin(interaction):
        return True

    if eh_mestre(interaction):
        return True

    return False


# ============================================================
# BOT ONLINE
# ============================================================

@bot.event
async def on_ready():

    print(
        f"Bot conectado como {bot.user}"
    )

    try:

        comandos = await bot.tree.sync()

        print(
            f"{len(comandos)} comandos sincronizados."
        )

    except Exception as erro:

        print(
            f"Erro ao sincronizar comandos: {erro}"
        )


# ============================================================
# DEFINIR MESTRE
# ============================================================

@bot.tree.command(
    name="definirmestre",
    description="Define o Mestre deste canal."
)
@app_commands.describe(
    jogador="Jogador que será o Mestre"
)
async def definirmestre(
    interaction: discord.Interaction,
    jogador: discord.Member
):

    if not eh_admin(interaction):

        await interaction.response.send_message(
            "❌ Somente administradores podem definir o Mestre.",
            ephemeral=True
        )

        return

    garantir_mesa(
        interaction.channel.id
    )

    cursor.execute("""
        UPDATE mesas
        SET mestre_id = ?
        WHERE channel_id = ?
    """, (
        jogador.id,
        interaction.channel.id
    ))

    cursor.execute("""
        UPDATE fichas
        SET mestre_id = ?
        WHERE channel_id = ?
        AND tipo = 'npc'
    """, (
        jogador.id,
        interaction.channel.id
    ))

    db.commit()

    await interaction.response.send_message(
        f"👑 **{jogador.display_name}** "
        f"agora é o Mestre deste canal!"
    )


# ============================================================
# PASSAR MESTRE
# ============================================================

@bot.tree.command(
    name="passarmestre",
    description="Passa o cargo de Mestre para outro jogador."
)
@app_commands.describe(
    jogador="Jogador que será o novo Mestre"
)
async def passarmestre(
    interaction: discord.Interaction,
    jogador: discord.Member
):

    mestre_id = obter_mestre(
        interaction.channel.id
    )

    if (
        interaction.user.id != mestre_id
        and not eh_admin(interaction)
    ):

        await interaction.response.send_message(
            "❌ Somente o Mestre atual ou um administrador pode fazer isso.",
            ephemeral=True
        )

        return

    garantir_mesa(
        interaction.channel.id
    )

    cursor.execute("""
        UPDATE mesas
        SET mestre_id = ?
        WHERE channel_id = ?
    """, (
        jogador.id,
        interaction.channel.id
    ))

    cursor.execute("""
        UPDATE fichas
        SET mestre_id = ?
        WHERE channel_id = ?
        AND tipo = 'npc'
    """, (
        jogador.id,
        interaction.channel.id
    ))

    db.commit()

    await interaction.response.send_message(
        f"👑 Novo Mestre: {jogador.mention}\n"
        f"👹 Os NPCs foram transferidos para ele."
    )


# ============================================================
# MOSTRAR MESTRE
# ============================================================

@bot.tree.command(
    name="mestre",
    description="Mostra o Mestre deste canal."
)
async def mestre(
    interaction: discord.Interaction
):

    mestre_id = obter_mestre(
        interaction.channel.id
    )

    if mestre_id is None:

        await interaction.response.send_message(
            "👑 Este canal ainda não possui um Mestre."
        )

        return

    membro = interaction.guild.get_member(
        mestre_id
    )

    if membro:

        await interaction.response.send_message(
            f"👑 Mestre deste canal: "
            f"**{membro.display_name}**"
        )

    else:

        await interaction.response.send_message(
            f"👑 Mestre: <@{mestre_id}>"
        )


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

    cursor.execute("""
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
            forca,
            destreza,
            vigor,
            inteligencia,
            carisma,
            raciocinio,
            aleatorio
        )
        VALUES (
            ?, ?, NULL, 'jogador', ?,
            ?, ?, ?, ?, 0,
            0, 0, 0, 0, 0, 0, 0
        )
    """, (
        interaction.channel.id,
        interaction.user.id,
        nome,
        hp,
        hp,
        mana,
        mana
    ))

    db.commit()

    await interaction.response.send_message(
        f"📜 Ficha de **{nome}** criada!\n\n"
        f"❤️ HP: **{hp}/{hp}**\n"
        f"🔵 Mana: **{mana}/{mana}**\n"
        f"✨ XP: **0**\n"
        f"⚡ RC: **5**"
    )


# ============================================================
# MOSTRAR PRÓPRIA FICHA
# ============================================================

@bot.tree.command(
    name="ficha",
    description="Mostra sua ficha neste canal."
)
async def ficha(
    interaction: discord.Interaction
):

    dados = buscar_ficha_jogador(
        interaction.channel.id,
        interaction.user.id
    )

    if dados is None:

        await interaction.response.send_message(
            "❌ Você não possui uma ficha neste canal.",
            ephemeral=True
        )

        return

    f = transformar_ficha(dados)

    await interaction.response.send_message(
        embed=criar_pagina_status(
            f,
            interaction.user
        ),
        view=FichaView(
            f,
            interaction.user
        ),
        ephemeral=True
    )


# ============================================================
# VER FICHA DE OUTRO JOGADOR
# ============================================================

@bot.tree.command(
    name="verficha",
    description="Visualiza a ficha de outro jogador."
)
@app_commands.describe(
    jogador="Jogador cuja ficha você deseja visualizar"
)
async def verficha(
    interaction: discord.Interaction,
    jogador: discord.Member
):

    dados = buscar_ficha_jogador(
        interaction.channel.id,
        jogador.id
    )

    if dados is None:

        await interaction.response.send_message(
            f"❌ **{jogador.display_name}** "
            f"não possui uma ficha.",
            ephemeral=True
        )

        return

    f = transformar_ficha(dados)

    await interaction.response.send_message(
        embed=criar_pagina_status(
            f,
            jogador
        ),
        view=FichaView(
            f,
            jogador
        )
    )


# ============================================================
# PAINEL DE ALTERAÇÃO
# ============================================================

class AlterarCampoModal(discord.ui.Modal):

    def __init__(
        self,
        ficha,
        campo,
        nome_campo,
        somente_jogador=False
    ):

        super().__init__(
            title=f"Alterar {nome_campo}"[:45]
        )

        self.ficha = ficha
        self.campo = campo
        self.nome_campo = nome_campo
        self.somente_jogador = somente_jogador

        valor_atual = ficha.get(
            campo,
            0
        )

        self.valor = discord.ui.TextInput(
            label=f"Novo valor para {nome_campo}"[:45],
            placeholder=f"Valor atual: {valor_atual}",
            required=True,
            max_length=10
        )

        self.add_item(
            self.valor
        )

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

        try:

            novo_valor = int(
                self.valor.value
            )

        except ValueError:

            await interaction.response.send_message(
                "❌ Informe apenas um número inteiro.",
                ephemeral=True
            )

            return

        if novo_valor < 0:

            await interaction.response.send_message(
                "❌ O valor não pode ser negativo.",
                ephemeral=True
            )

            return

        ficha_atual = buscar_ficha(
            self.ficha["id"]
        )

        if ficha_atual is None:

            await interaction.response.send_message(
                "❌ Essa ficha não existe mais.",
                ephemeral=True
            )

            return

        ficha = transformar_ficha(
            ficha_atual
        )

        if not pode_alterar_ficha(
            interaction,
            ficha
        ):

            await interaction.response.send_message(
                "❌ Você não pode alterar essa ficha.",
                ephemeral=True
            )

            return

        # ----------------------------------------------------
        # JOGADOR NÃO ALTERA STATUS
        # ----------------------------------------------------

        campos_status = {
            "hp_atual",
            "hp_max",
            "mana_atual",
            "mana_max",
            "xp"
        }

        if (
            self.somente_jogador
            and self.campo in campos_status
        ):

            await interaction.response.send_message(
                "❌ Jogadores não podem alterar "
                "HP, Mana ou XP pelo painel.",
                ephemeral=True
            )

            return

        # ----------------------------------------------------
        # HP MÁXIMO
        # ----------------------------------------------------

        if self.campo == "hp_max":

            if novo_valor <= 0:

                await interaction.response.send_message(
                    "❌ O HP máximo precisa ser maior que 0.",
                    ephemeral=True
                )

                return

            hp_atual = min(
                ficha["hp_atual"],
                novo_valor
            )

            cursor.execute("""
                UPDATE fichas
                SET hp_max = ?,
                    hp_atual = ?
                WHERE id = ?
            """, (
                novo_valor,
                hp_atual,
                ficha["id"]
            ))

        # ----------------------------------------------------
        # HP ATUAL
        # ----------------------------------------------------

        elif self.campo == "hp_atual":

            novo_valor = min(
                novo_valor,
                ficha["hp_max"]
            )

            cursor.execute("""
                UPDATE fichas
                SET hp_atual = ?
                WHERE id = ?
            """, (
                novo_valor,
                ficha["id"]
            ))

        # ----------------------------------------------------
        # MANA MÁXIMA
        # ----------------------------------------------------

        elif self.campo == "mana_max":

            novo_valor = max(
                0,
                novo_valor
            )

            mana_atual = min(
                ficha["mana_atual"],
                novo_valor
            )

            cursor.execute("""
                UPDATE fichas
                SET mana_max = ?,
                    mana_atual = ?
                WHERE id = ?
            """, (
                novo_valor,
                mana_atual,
                ficha["id"]
            ))

        # ----------------------------------------------------
        # MANA ATUAL
        # ----------------------------------------------------

        elif self.campo == "mana_atual":

            novo_valor = min(
                novo_valor,
                ficha["mana_max"]
            )

            cursor.execute("""
                UPDATE fichas
                SET mana_atual = ?
                WHERE id = ?
            """, (
                novo_valor,
                ficha["id"]
            ))

        # ----------------------------------------------------
        # XP
        # ----------------------------------------------------

        elif self.campo == "xp":

            cursor.execute("""
                UPDATE fichas
                SET xp = ?
                WHERE id = ?
            """, (
                novo_valor,
                ficha["id"]
            ))

        # ----------------------------------------------------
        # ATRIBUTOS
        # ----------------------------------------------------

        elif self.campo in ATRIBUTOS:

            cursor.execute(
                f"""
                UPDATE fichas
                SET {self.campo} = ?
                WHERE id = ?
                """,
                (
                    novo_valor,
                    ficha["id"]
                )
            )

        # ----------------------------------------------------
        # PERÍCIAS
        # ----------------------------------------------------

        elif self.campo in PERICIAS:

            cursor.execute(
                f"""
                UPDATE fichas
                SET {self.campo} = ?
                WHERE id = ?
                """,
                (
                    novo_valor,
                    ficha["id"]
                )
            )

        else:

            await interaction.response.send_message(
                "❌ Campo inválido.",
                ephemeral=True
            )

            return

        db.commit()

        await interaction.response.send_message(
            f"✅ **{self.nome_campo}** de "
            f"**{ficha['nome']}** foi alterado para "
            f"**{novo_valor}**.",
            ephemeral=True
        )


# ============================================================
# SELECT DE CAMPOS
# ============================================================

class AlterarCampoSelect(discord.ui.Select):

    def __init__(
        self,
        ficha,
        categoria,
        somente_jogador=False
    ):

        self.ficha = ficha
        self.categoria = categoria
        self.somente_jogador = somente_jogador

        opcoes = []

        if categoria == "status":

            opcoes = [
                discord.SelectOption(
                    label="HP Atual",
                    value="hp_atual",
                    emoji="❤️",
                    description=f"Atual: {ficha['hp_atual']}"
                ),
                discord.SelectOption(
                    label="HP Máximo",
                    value="hp_max",
                    emoji="❤️",
                    description=f"Atual: {ficha['hp_max']}"
                ),
                discord.SelectOption(
                    label="Mana Atual",
                    value="mana_atual",
                    emoji="🔵",
                    description=f"Atual: {ficha['mana_atual']}"
                ),
                discord.SelectOption(
                    label="Mana Máxima",
                    value="mana_max",
                    emoji="🔵",
                    description=f"Atual: {ficha['mana_max']}"
                ),
                discord.SelectOption(
                    label="XP",
                    value="xp",
                    emoji="✨",
                    description=f"Atual: {ficha['xp']}"
                )
            ]

        elif categoria == "atributos":

            for chave, dados in ATRIBUTOS.items():

                emoji = dados[0]
                nome = dados[1]

                opcoes.append(
                    discord.SelectOption(
                        label=nome,
                        value=chave,
                        emoji=emoji,
                        description=f"Atual: {ficha[chave]}"
                    )
                )

        elif categoria == "pericias":

            for chave, dados in PERICIAS.items():

                emoji = dados[0]
                nome = dados[1]

                opcoes.append(
                    discord.SelectOption(
                        label=nome,
                        value=chave,
                        emoji=emoji,
                        description=f"Atual: {ficha[chave]}"
                    )
                )

        super().__init__(
            placeholder="Selecione o que deseja alterar...",
            options=opcoes,
            min_values=1,
            max_values=1
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        campo = self.values[0]

        if campo in ATRIBUTOS:

            nome_campo = ATRIBUTOS[campo][1]

        elif campo in PERICIAS:

            nome_campo = PERICIAS[campo][1]

        else:

            nomes = {
                "hp_atual": "HP Atual",
                "hp_max": "HP Máximo",
                "mana_atual": "Mana Atual",
                "mana_max": "Mana Máxima",
                "xp": "XP"
            }

            nome_campo = nomes[campo]

        await interaction.response.send_modal(
            AlterarCampoModal(
                self.ficha,
                campo,
                nome_campo,
                self.somente_jogador
            )
        )


# ============================================================
# CATEGORIAS DE ALTERAÇÃO
# ============================================================

class CategoriaAlteracaoView(discord.ui.View):

    def __init__(
        self,
        ficha,
        somente_jogador=False
    ):

        super().__init__(
            timeout=120
        )

        self.ficha = ficha
        self.somente_jogador = somente_jogador

        if somente_jogador:

            # Jogador não altera status pelo painel.
            pass

    @discord.ui.button(
        label="❤️ Status",
        style=discord.ButtonStyle.primary
    )
    async def status(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if self.somente_jogador:

            await interaction.response.send_message(
                "❌ Jogadores não podem alterar "
                "HP, Mana ou XP por este painel.",
                ephemeral=True
            )

            return

        view = discord.ui.View(
            timeout=120
        )

        view.add_item(
            AlterarCampoSelect(
                self.ficha,
                "status",
                self.somente_jogador
            )
        )

        await interaction.response.edit_message(
            content=(
                f"⚙️ **ALTERANDO FICHA**\n\n"
                f"📜 Personagem: **{self.ficha['nome']}**\n\n"
                f"❤️ Selecione o campo de Status:"
            ),
            view=view
        )

    @discord.ui.button(
        label="⚔️ Atributos",
        style=discord.ButtonStyle.primary
    )
    async def atributos(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        view = discord.ui.View(
            timeout=120
        )

        view.add_item(
            AlterarCampoSelect(
                self.ficha,
                "atributos",
                self.somente_jogador
            )
        )

        await interaction.response.edit_message(
            content=(
                f"⚙️ **ALTERANDO FICHA**\n\n"
                f"📜 Personagem: **{self.ficha['nome']}**\n\n"
                f"⚔️ Selecione o atributo:"
            ),
            view=view
        )

    @discord.ui.button(
        label="📚 Perícias",
        style=discord.ButtonStyle.primary
    )
    async def pericias(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        view = discord.ui.View(
            timeout=120
        )

        view.add_item(
            AlterarCampoSelect(
                self.ficha,
                "pericias",
                self.somente_jogador
            )
        )

        await interaction.response.edit_message(
            content=(
                f"⚙️ **ALTERANDO FICHA**\n\n"
                f"📜 Personagem: **{self.ficha['nome']}**\n\n"
                f"📚 Selecione a perícia:"
            ),
            view=view
        )


# ============================================================
# SELEÇÃO DE NPC
# ============================================================

class EscolherNPCSelect(discord.ui.Select):

    def __init__(self, fichas):

        self.fichas = fichas

        opcoes = []

        for ficha in fichas[:25]:

            opcoes.append(
                discord.SelectOption(
                    label=ficha["nome"][:100],
                    value=str(ficha["id"]),
                    emoji="👹"
                )
            )

        super().__init__(
            placeholder="Selecione o NPC...",
            options=opcoes,
            min_values=1,
            max_values=1
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        ficha_id = int(
            self.values[0]
        )

        dados = buscar_ficha(
            ficha_id
        )

        if dados is None:

            await interaction.response.send_message(
                "❌ Essa ficha não existe mais.",
                ephemeral=True
            )

            return

        ficha = transformar_ficha(
            dados
        )

        if not pode_alterar_ficha(
            interaction,
            ficha
        ):

            await interaction.response.send_message(
                "❌ Você não pode alterar esse NPC.",
                ephemeral=True
            )

            return

        await interaction.response.edit_message(
            content=(
                f"⚙️ **ALTERAR FICHA**\n\n"
                f"👹 NPC: **{ficha['nome']}**\n\n"
                f"Escolha o que deseja alterar:"
            ),
            view=CategoriaAlteracaoView(
                ficha,
                False
            )
        )


# ============================================================
# SELEÇÃO DE JOGADOR — MESTRE / ADM
# ============================================================

class EscolherJogadorSelect(discord.ui.UserSelect):

    def __init__(self):

        super().__init__(
            placeholder="Selecione o jogador...",
            min_values=1,
            max_values=1
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        jogador = self.values[0]

        dados = buscar_ficha_jogador(
            interaction.channel.id,
            jogador.id
        )

        if dados is None:

            await interaction.response.send_message(
                "❌ Esse jogador não possui uma ficha.",
                ephemeral=True
            )

            return

        ficha = transformar_ficha(
            dados
        )

        if not pode_alterar_ficha(
            interaction,
            ficha
        ):

            await interaction.response.send_message(
                "❌ Você não pode alterar essa ficha.",
                ephemeral=True
            )

            return

        await interaction.response.edit_message(
            content=(
                f"⚙️ **ALTERAR FICHA**\n\n"
                f"👤 Jogador: **{ficha['nome']}**\n\n"
                f"Escolha o que deseja alterar:"
            ),
            view=CategoriaAlteracaoView(
                ficha,
                False
            )
        )


class EscolherJogadorView(discord.ui.View):

    def __init__(self):

        super().__init__(
            timeout=120
        )

        self.add_item(
            EscolherJogadorSelect()
        )


# ============================================================
# TIPO DE FICHA — MESTRE / ADM
# ============================================================

class TipoFichaAlteracaoView(discord.ui.View):

    def __init__(self, interaction):

        super().__init__(
            timeout=120
        )

        self.channel_id = interaction.channel.id

    @discord.ui.button(
        label="👤 Jogador",
        style=discord.ButtonStyle.primary
    )
    async def jogador(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.edit_message(
            content=(
                "⚙️ **ALTERAR FICHA**\n\n"
                "👤 Selecione o jogador:"
            ),
            view=EscolherJogadorView()
        )

    @discord.ui.button(
        label="👹 NPC",
        style=discord.ButtonStyle.danger
    )
    async def npc(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        cursor.execute("""
            SELECT *
            FROM fichas
            WHERE channel_id = ?
            AND tipo = 'npc'
            ORDER BY nome
        """, (
            self.channel_id,
        ))

        resultados = cursor.fetchall()

        if not resultados:

            await interaction.response.edit_message(
                content=(
                    "❌ Não existem NPCs nesta mesa."
                ),
                view=None
            )

            return

        fichas = [
            transformar_ficha(dados)
            for dados in resultados
        ]

        view = discord.ui.View(
            timeout=120
        )

        view.add_item(
            EscolherNPCSelect(
                fichas
            )
        )

        await interaction.response.edit_message(
            content=(
                "⚙️ **ALTERAR FICHA**\n\n"
                "👹 Selecione o NPC:"
            ),
            view=view
        )


# ============================================================
# /ALTERAR
# ============================================================

@bot.tree.command(
    name="alterar",
    description="Altera sua ficha ou uma ficha sob sua responsabilidade."
)
async def alterar(
    interaction: discord.Interaction
):

    # --------------------------------------------------------
    # MESTRE / ADM
    # --------------------------------------------------------

    if eh_admin(interaction) or eh_mestre(interaction):

        await interaction.response.send_message(
            "⚙️ **PAINEL DE ALTERAÇÃO DE FICHA**\n\n"
            "Escolha o tipo de ficha que deseja alterar:",
            view=TipoFichaAlteracaoView(
                interaction
            ),
            ephemeral=True
        )

        return

    # --------------------------------------------------------
    # JOGADOR
    # --------------------------------------------------------

    dados = buscar_ficha_jogador(
        interaction.channel.id,
        interaction.user.id
    )

    if dados is None:

        await interaction.response.send_message(
            "❌ Você não possui uma ficha neste canal.",
            ephemeral=True
        )

        return

    ficha = transformar_ficha(
        dados
    )

    await interaction.response.send_message(
        (
            "⚙️ **ALTERAR MINHA FICHA**\n\n"
            f"👤 Personagem: **{ficha['nome']}**\n\n"
            "Escolha o que deseja alterar:"
        ),
        view=CategoriaAlteracaoView(
            ficha,
            True
        ),
        ephemeral=True
    )


# ============================================================
# ALTERAR ATRIBUTO — COMPATIBILIDADE
# ============================================================

@bot.tree.command(
    name="atributo",
    description="Define ou altera um atributo da sua ficha."
)
@app_commands.describe(
    atributo="Atributo",
    valor="Novo valor"
)
@app_commands.choices(
    atributo=[
        app_commands.Choice(
            name="Força",
            value="forca"
        ),
        app_commands.Choice(
            name="Destreza",
            value="destreza"
        ),
        app_commands.Choice(
            name="Vigor",
            value="vigor"
        ),
        app_commands.Choice(
            name="Inteligência",
            value="inteligencia"
        ),
        app_commands.Choice(
            name="Carisma",
            value="carisma"
        ),
        app_commands.Choice(
            name="Raciocínio",
            value="raciocinio"
        )
    ]
)
async def atributo(
    interaction: discord.Interaction,
    atributo: app_commands.Choice[str],
    valor: int
):

    dados = buscar_ficha_jogador(
        interaction.channel.id,
        interaction.user.id
    )

    if dados is None:

        await interaction.response.send_message(
            "❌ Você não possui uma ficha.",
            ephemeral=True
        )

        return

    if valor < 0:

        await interaction.response.send_message(
            "❌ O valor não pode ser negativo.",
            ephemeral=True
        )

        return

    ficha = transformar_ficha(
        dados
    )

    cursor.execute(
        f"""
        UPDATE fichas
        SET {atributo.value} = ?
        WHERE id = ?
        """,
        (
            valor,
            ficha["id"]
        )
    )

    db.commit()

    await interaction.response.send_message(
        f"⚔️ **{ATRIBUTOS[atributo.value][1]}** "
        f"alterado para **{valor}**!"
    )


# ============================================================
# ALTERAR PERÍCIA — COMPATIBILIDADE
# ============================================================

@bot.tree.command(
    name="pericia",
    description="Define ou altera uma perícia da sua ficha."
)
@app_commands.describe(
    pericia="Perícia",
    valor="Novo valor"
)
@app_commands.choices(
    pericia=[
        app_commands.Choice(
            name="Acadêmicos",
            value="academicos"
        ),
        app_commands.Choice(
            name="Idiomas",
            value="idiomas"
        ),
        app_commands.Choice(
            name="Ofícios",
            value="oficios"
        ),
        app_commands.Choice(
            name="Armas Brancas",
            value="armas_brancas"
        ),
        app_commands.Choice(
            name="Intimidação",
            value="intimidacao"
        ),
        app_commands.Choice(
            name="Ocultismo",
            value="ocultismo"
        ),
        app_commands.Choice(
            name="Briga",
            value="briga"
        ),
        app_commands.Choice(
            name="Investigação",
            value="investigacao"
        ),
        app_commands.Choice(
            name="Persuasão",
            value="persuasao"
        ),
        app_commands.Choice(
            name="Ciências",
            value="ciencias"
        ),
        app_commands.Choice(
            name="Lábia",
            value="labia"
        ),
        app_commands.Choice(
            name="Prontidão",
            value="prontidao"
        ),
        app_commands.Choice(
            name="Conhecimentos Gerais",
            value="conhecimentos_gerais"
        ),
        app_commands.Choice(
            name="Liderança",
            value="lideranca"
        ),
        app_commands.Choice(
            name="Sobrevivência",
            value="sobrevivencia"
        ),
        app_commands.Choice(
            name="Condução",
            value="conducao"
        ),
        app_commands.Choice(
            name="Manha",
            value="manha"
        ),
        app_commands.Choice(
            name="Tecnologia",
            value="tecnologia"
        ),
        app_commands.Choice(
            name="Esportes",
            value="esportes"
        ),
        app_commands.Choice(
            name="Medicina",
            value="medicina"
        ),
        app_commands.Choice(
            name="Mira",
            value="mira"
        ),
        app_commands.Choice(
            name="Esquiva",
            value="esquiva"
        ),
        app_commands.Choice(
            name="Furtividade",
            value="furtividade"
        )
    ]
)
async def pericia(
    interaction: discord.Interaction,
    pericia: app_commands.Choice[str],
    valor: int
):

    dados = buscar_ficha_jogador(
        interaction.channel.id,
        interaction.user.id
    )

    if dados is None:

        await interaction.response.send_message(
            "❌ Você não possui uma ficha.",
            ephemeral=True
        )

        return

    if valor < 0:

        await interaction.response.send_message(
            "❌ O valor não pode ser negativo.",
            ephemeral=True
        )

        return

    ficha = transformar_ficha(
        dados
    )

    cursor.execute(
        f"""
        UPDATE fichas
        SET {pericia.value} = ?
        WHERE id = ?
        """,
        (
            valor,
            ficha["id"]
        )
    )

    db.commit()

    await interaction.response.send_message(
        f"📚 **{PERICIAS[pericia.value][1]}** "
        f"alterada para **{valor}**!"
    )


# ============================================================
# ALTERAR HP E MANA
# ============================================================

@bot.tree.command(
    name="alterarficha",
    description="Altera HP e Mana máximos de um jogador."
)
@app_commands.describe(
    jogador="Jogador",
    hp="Novo HP máximo",
    mana="Nova Mana máxima"
)
async def alterarficha(
    interaction: discord.Interaction,
    jogador: discord.Member,
    hp: int,
    mana: int
):

    dados = buscar_ficha_jogador(
        interaction.channel.id,
        jogador.id
    )

    if dados is None:

        await interaction.response.send_message(
            "❌ Esse jogador não possui uma ficha.",
            ephemeral=True
        )

        return

    ficha = transformar_ficha(
        dados
    )

    if not pode_alterar_ficha(
        interaction,
        ficha
    ):

        await interaction.response.send_message(
            "❌ Você não pode alterar essa ficha.",
            ephemeral=True
        )

        return

    if hp <= 0 or mana < 0:

        await interaction.response.send_message(
            "❌ Valores inválidos.",
            ephemeral=True
        )

        return

    cursor.execute("""
        UPDATE fichas
        SET hp_atual = ?,
            hp_max = ?,
            mana_atual = ?,
            mana_max = ?
        WHERE id = ?
    """, (
        hp,
        hp,
        mana,
        mana,
        ficha["id"]
    ))

    db.commit()

    await interaction.response.send_message(
        f"⚙️ Ficha de **{ficha['nome']}** atualizada!\n\n"
        f"❤️ HP: **{hp}/{hp}**\n"
        f"🔵 Mana: **{mana}/{mana}**"
    )


# ============================================================
# APAGAR FICHA
# ============================================================

@bot.tree.command(
    name="apagarficha",
    description="Apaga sua ficha."
)
async def apagarficha(
    interaction: discord.Interaction
):

    dados = buscar_ficha_jogador(
        interaction.channel.id,
        interaction.user.id
    )

    if dados is None:

        await interaction.response.send_message(
            "❌ Você não possui uma ficha.",
            ephemeral=True
        )

        return

    ficha = transformar_ficha(
        dados
    )

    cursor.execute(
        "DELETE FROM fichas WHERE id = ?",
        (ficha["id"],)
    )

    db.commit()

    await interaction.response.send_message(
        f"🗑️ A ficha **{ficha['nome']}** foi apagada."
    )


# ============================================================
# DANO
# ============================================================

@bot.tree.command(
    name="dano",
    description="Aplica dano a um jogador."
)
@app_commands.describe(
    jogador="Jogador que receberá o dano",
    valor="Quantidade de dano"
)
async def dano(
    interaction: discord.Interaction,
    jogador: discord.Member,
    valor: int
):

    dados = buscar_ficha_jogador(
        interaction.channel.id,
        jogador.id
    )

    if dados is None:

        await interaction.response.send_message(
            "❌ Ficha não encontrada.",
            ephemeral=True
        )

        return

    if valor <= 0:

        await interaction.response.send_message(
            "❌ O dano precisa ser maior que 0.",
            ephemeral=True
        )

        return

    ficha = transformar_ficha(
        dados
    )

    novo_hp = max(
        0,
        ficha["hp_atual"] - valor
    )

    cursor.execute("""
        UPDATE fichas
        SET hp_atual = ?
        WHERE id = ?
    """, (
        novo_hp,
        ficha["id"]
    ))

    db.commit()

    await interaction.response.send_message(
        f"💥 **{ficha['nome']}** recebeu "
        f"**{valor} de dano**!\n"
        f"❤️ HP: **{novo_hp}/{ficha['hp_max']}**"
    )


# ============================================================
# CURA
# ============================================================

@bot.tree.command(
    name="cura",
    description="Cura um jogador."
)
@app_commands.describe(
    jogador="Jogador que receberá a cura",
    valor="Quantidade de cura"
)
async def cura(
    interaction: discord.Interaction,
    jogador: discord.Member,
    valor: int
):

    dados = buscar_ficha_jogador(
        interaction.channel.id,
        jogador.id
    )

    if dados is None:

        await interaction.response.send_message(
            "❌ Ficha não encontrada.",
            ephemeral=True
        )

        return

    if valor <= 0:

        await interaction.response.send_message(
            "❌ A cura precisa ser maior que 0.",
            ephemeral=True
        )

        return

    ficha = transformar_ficha(
        dados
    )

    novo_hp = min(
        ficha["hp_max"],
        ficha["hp_atual"] + valor
    )

    recuperado = (
        novo_hp - ficha["hp_atual"]
    )

    cursor.execute("""
        UPDATE fichas
        SET hp_atual = ?
        WHERE id = ?
    """, (
        novo_hp,
        ficha["id"]
    ))

    db.commit()

    await interaction.response.send_message(
        f"💚 **{ficha['nome']}** recuperou "
        f"**{recuperado} de HP**!\n"
        f"❤️ HP: **{novo_hp}/{ficha['hp_max']}**"
    )


# ============================================================
# GASTAR MANA
# ============================================================

@bot.tree.command(
    name="gastarmana",
    description="Gasta Mana da sua própria ficha."
)
@app_commands.describe(
    valor="Quantidade de Mana"
)
async def gastarmana(
    interaction: discord.Interaction,
    valor: int
):

    dados = buscar_ficha_jogador(
        interaction.channel.id,
        interaction.user.id
    )

    if dados is None:

        await interaction.response.send_message(
            "❌ Você não possui uma ficha.",
            ephemeral=True
        )

        return

    ficha = transformar_ficha(
        dados
    )

    if valor <= 0:

        await interaction.response.send_message(
            "❌ O valor precisa ser maior que 0.",
            ephemeral=True
        )

        return

    if valor > ficha["mana_atual"]:

        await interaction.response.send_message(
            "❌ Mana insuficiente.",
            ephemeral=True
        )

        return

    nova_mana = (
        ficha["mana_atual"] - valor
    )

    cursor.execute("""
        UPDATE fichas
        SET mana_atual = ?
        WHERE id = ?
    """, (
        nova_mana,
        ficha["id"]
    ))

    db.commit()

    await interaction.response.send_message(
        f"🔮 **{ficha['nome']}** gastou "
        f"**{valor} de Mana**!\n"
        f"🔵 Mana: **{nova_mana}/{ficha['mana_max']}**"
    )


# ============================================================
# RECUPERAR MANA
# ============================================================

@bot.tree.command(
    name="recuperarmana",
    description="Recupera Mana de um jogador."
)
@app_commands.describe(
    jogador="Jogador que recuperará Mana",
    valor="Quantidade de Mana"
)
async def recuperarmana(
    interaction: discord.Interaction,
    jogador: discord.Member,
    valor: int
):

    dados = buscar_ficha_jogador(
        interaction.channel.id,
        jogador.id
    )

    if dados is None:

        await interaction.response.send_message(
            "❌ Ficha não encontrada.",
            ephemeral=True
        )

        return

    if valor <= 0:

        await interaction.response.send_message(
            "❌ O valor precisa ser maior que 0.",
            ephemeral=True
        )

        return

    ficha = transformar_ficha(
        dados
    )

    nova_mana = min(
        ficha["mana_max"],
        ficha["mana_atual"] + valor
    )

    recuperado = (
        nova_mana - ficha["mana_atual"]
    )

    cursor.execute("""
        UPDATE fichas
        SET mana_atual = ?
        WHERE id = ?
    """, (
        nova_mana,
        ficha["id"]
    ))

    db.commit()

    await interaction.response.send_message(
        f"💧 **{ficha['nome']}** recuperou "
        f"**{recuperado} de Mana**!\n"
        f"🔵 Mana: **{nova_mana}/{ficha['mana_max']}**"
    )


# ============================================================
# XP
# ============================================================

@bot.tree.command(
    name="addxp",
    description="Adiciona XP a uma ficha."
)
@app_commands.describe(
    jogador="Jogador que receberá XP",
    valor="Quantidade de XP"
)
async def addxp(
    interaction: discord.Interaction,
    jogador: discord.Member,
    valor: int
):

    dados = buscar_ficha_jogador(
        interaction.channel.id,
        jogador.id
    )

    if dados is None:

        await interaction.response.send_message(
            "❌ Ficha não encontrada.",
            ephemeral=True
        )

        return

    ficha = transformar_ficha(
        dados
    )

    if (
        ficha["dono_id"] != interaction.user.id
        and not eh_admin(interaction)
        and not eh_mestre(interaction)
    ):

        await interaction.response.send_message(
            "❌ Você não pode alterar o XP dessa ficha.",
            ephemeral=True
        )

        return

    if valor <= 0:

        await interaction.response.send_message(
            "❌ O XP precisa ser maior que 0.",
            ephemeral=True
        )

        return

    cursor.execute("""
        UPDATE fichas
        SET xp = xp + ?
        WHERE id = ?
    """, (
        valor,
        ficha["id"]
    ))

    db.commit()

    cursor.execute(
        "SELECT xp FROM fichas WHERE id = ?",
        (ficha["id"],)
    )

    xp_atual = cursor.fetchone()[0]

    await interaction.response.send_message(
        f"✨ **{ficha['nome']}** recebeu "
        f"**{valor} XP**!\n"
        f"✨ XP atual: **{xp_atual}**"
    )


# ============================================================
# CRIAR NPC
# ============================================================

@bot.tree.command(
    name="criarnpc",
    description="Cria um NPC."
)
@app_commands.describe(
    aleatorio="NPC aleatório ou personalizado",
    nome="Nome do NPC",
    hp="HP do NPC",
    mana="Mana do NPC"
)
@app_commands.choices(
    aleatorio=[
        app_commands.Choice(
            name="Sim",
            value="sim"
        ),
        app_commands.Choice(
            name="Não",
            value="nao"
        )
    ]
)
async def criarnpc(
    interaction: discord.Interaction,
    aleatorio: app_commands.Choice[str],
    nome: str = None,
    hp: int = None,
    mana: int = None
):

    garantir_mesa(
        interaction.channel.id
    )

    if (
        not eh_mestre(interaction)
        and not eh_admin(interaction)
    ):

        await interaction.response.send_message(
            "❌ Somente o Mestre pode criar NPCs.",
            ephemeral=True
        )

        return

    if aleatorio.value == "sim":

        nomes = [
            "Goblin",
            "Orc",
            "Esqueleto",
            "Bandido",
            "Lobo",
            "Zumbi",
            "Slime",
            "Aranha Gigante",
            "Cultista",
            "Guardião",
            "Golem",
            "Morcego Gigante",
            "Troll",
            "Ladrão",
            "Cavaleiro Sombrio"
        ]

        nome = random.choice(nomes)

        hp = random.randint(
            20,
            150
        )

        mana = random.randint(
            0,
            100
        )

        atributos = {}

        for chave in ATRIBUTOS:

            atributos[chave] = random.randint(
                0,
                5
            )

        pericias = {}

        for chave in PERICIAS:

            pericias[chave] = random.randint(
                0,
                5
            )

        aleatorio_valor = 1

    else:

        if not nome:

            await interaction.response.send_message(
                "❌ Informe o nome do NPC.",
                ephemeral=True
            )

            return

        if hp is None:

            await interaction.response.send_message(
                "❌ Informe o HP do NPC.",
                ephemeral=True
            )

            return

        if mana is None:

            await interaction.response.send_message(
                "❌ Informe a Mana do NPC.",
                ephemeral=True
            )

            return

        if hp <= 0 or mana < 0:

            await interaction.response.send_message(
                "❌ Valores inválidos.",
                ephemeral=True
            )

            return

        atributos = {
            chave: 0
            for chave in ATRIBUTOS
        }

        pericias = {
            chave: 0
            for chave in PERICIAS
        }

        aleatorio_valor = 0

    nome = nome[:50]

    mestre_id = obter_mestre(
        interaction.channel.id
    )

    if mestre_id is None:

        mestre_id = interaction.user.id

        cursor.execute("""
            UPDATE mesas
            SET mestre_id = ?
            WHERE channel_id = ?
        """, (
            mestre_id,
            interaction.channel.id
        ))

    colunas = (
        list(ATRIBUTOS.keys())
        + ORDEM_PERICIAS
    )

    valores = (
        [
            atributos[chave]
            for chave in ATRIBUTOS
        ]
        +
        [
            pericias[chave]
            for chave in ORDEM_PERICIAS
        ]
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
            interaction.channel.id,
            mestre_id,
            nome,
            hp,
            hp,
            mana,
            mana
        ]
        +
        valores
        +
        [
            aleatorio_valor
        ]
    )

    db.commit()

    rc = (
        pericias["esquiva"]
        + atributos["destreza"]
        + 5
    )

    await interaction.response.send_message(
        f"👹 NPC **{nome}** criado!\n\n"
        f"❤️ HP: **{hp}/{hp}**\n"
        f"🔵 Mana: **{mana}/{mana}**\n"
        f"⚡ RC: **{rc}**\n\n"
        f"🎲 Atributos e perícias "
        f"{'foram gerados aleatoriamente' if aleatorio_valor else 'começaram em 0'}."
    )


# ============================================================
# LISTAR NPCS
# ============================================================

@bot.tree.command(
    name="npcs",
    description="Mostra os NPCs da mesa."
)
async def npcs(
    interaction: discord.Interaction
):

    if (
        not eh_mestre(interaction)
        and not eh_admin(interaction)
    ):

        await interaction.response.send_message(
            "❌ Somente o Mestre pode visualizar os NPCs.",
            ephemeral=True
        )

        return

    cursor.execute("""
        SELECT *
        FROM fichas
        WHERE channel_id = ?
        AND tipo = 'npc'
        ORDER BY nome
    """, (
        interaction.channel.id,
    ))

    resultados = cursor.fetchall()

    if not resultados:

        await interaction.response.send_message(
            "👹 Não existem NPCs neste canal.",
            ephemeral=True
        )

        return

    await interaction.response.send_message(
        f"👹 **NPCs da mesa — "
        f"{len(resultados)} encontrados**"
    )

    for dados in resultados:

        ficha_npc = transformar_ficha(
            dados
        )

        await interaction.followup.send(
            embed=criar_pagina_status(
                ficha_npc
            ),
            view=FichaView(
                ficha_npc
            )
        )


# ============================================================
# APAGAR NPC
# ============================================================

@bot.tree.command(
    name="apagarnpc",
    description="Apaga um NPC."
)
@app_commands.describe(
    nome="Nome exato do NPC"
)
async def apagarnpc(
    interaction: discord.Interaction,
    nome: str
):

    if (
        not eh_mestre(interaction)
        and not eh_admin(interaction)
    ):

        await interaction.response.send_message(
            "❌ Somente o Mestre pode apagar NPCs.",
            ephemeral=True
        )

        return

    cursor.execute("""
        SELECT id
        FROM fichas
        WHERE channel_id = ?
        AND tipo = 'npc'
        AND nome = ?
        LIMIT 1
    """, (
        interaction.channel.id,
        nome
    ))

    resultado = cursor.fetchone()

    if resultado is None:

        await interaction.response.send_message(
            "❌ NPC não encontrado.",
            ephemeral=True
        )

        return

    cursor.execute(
        "DELETE FROM fichas WHERE id = ?",
        (resultado[0],)
    )

    db.commit()

    await interaction.response.send_message(
        f"🗑️ NPC **{nome}** apagado."
    )


# ============================================================
# HELP
# ============================================================

@bot.tree.command(
    name="help",
    description="Mostra os comandos do bot."
)
async def help(
    interaction: discord.Interaction
):

    embed = discord.Embed(
        title="📖 BotRPG",
        description="Comandos disponíveis:",
        color=discord.Color.dark_red()
    )

    embed.add_field(
        name="👤 Jogador",
        value=(
            "`/criarficha` — Criar ficha\n"
            "`/ficha` — Ver ficha\n"
            "`/verficha` — Ver ficha de outro jogador\n"
            "`/alterar` — Alterar sua ficha\n"
            "`/atributo` — Alterar atributo\n"
            "`/pericia` — Alterar perícia\n"
            "`/apagarficha` — Apagar ficha\n"
            "`/gastarmana` — Gastar Mana\n"
            "`/cura` — Curar outro jogador\n"
            "`/dano` — Aplicar dano\n"
            "`/recuperarmana` — Recuperar Mana\n"
            "`/addxp` — Adicionar XP"
        ),
        inline=False
    )

    embed.add_field(
        name="👑 Mestre",
        value=(
            "`/alterar` — Alterar qualquer ficha\n"
            "`/criarnpc` — Criar NPC\n"
            "`/npcs` — Ver NPCs\n"
            "`/apagarnpc` — Apagar NPC\n"
            "`/passarmestre` — Passar Mestre\n"
            "`/mestre` — Ver Mestre\n"
            "`/alterarficha` — Alterar HP/Mana"
        ),
        inline=False
    )

    embed.add_field(
        name="🛡️ Administrador",
        value=(
            "`/definirmestre` — Definir Mestre\n"
            "`/alterar` — Alterar qualquer ficha\n"
            "Permissões administrativas também "
            "permitem alterar fichas."
        ),
        inline=False
    )

    embed.set_footer(
        text="BotRPG • Sistema de fichas"
    )

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )


# ============================================================
# INICIAR BOT
# ============================================================

bot.run(TOKEN)
