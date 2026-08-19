import os
import sqlite3
import random
import discord

from discord.ext import commands
from discord import app_commands


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
    "forca": ("💪", "For"),
    "destreza": ("🏹", "Des"),
    "vigor": ("🛡️", "Vig"),
    "inteligencia": ("🧠", "Int"),
    "carisma": ("🎭", "Car"),
    "raciocinio": ("💡", "Rac")
}


ATRIBUTOS_NOMES = {
    "forca": "Força",
    "destreza": "Destreza",
    "vigor": "Vigor",
    "inteligencia": "Inteligência",
    "carisma": "Carisma",
    "raciocinio": "Raciocínio"
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
# NOMES ALEATÓRIOS DE NPC
# ============================================================

NOMES_NPC = [
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
    "Cavaleiro Sombrio",
    "Mercenário",
    "Caçador",
    "Demônio",
    "Criatura Sombria",
    "Soldado"
]


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


def calcular_rc(ficha):
    return (
        ficha["esquiva"]
        + ficha["destreza"]
        + 5
    )


def estado_recurso(atual, maximo):
    if atual <= 0 or maximo <= 0:
        return "ZERADO"

    percentual = (atual / maximo) * 100

    if percentual >= 70:
        return "BOM"

    if percentual >= 30:
        return "BAIXO"

    return "CRÍTICO"


def pode_alterar_ficha(interaction, ficha):

    if eh_admin(interaction):
        return True

    if ficha["tipo"] == "jogador":
        return (
            ficha["dono_id"] == interaction.user.id
            or eh_mestre(interaction)
        )

    if ficha["tipo"] == "npc":
        return (
            ficha["mestre_id"] == interaction.user.id
        )

    return False


# ============================================================
# PÁGINA 1
# STATUS + ATRIBUTOS
# ============================================================

def criar_pagina_status(f, jogador=None):

    embed = discord.Embed(
        title=f"📜 FICHA DE {f['nome'].upper()}",
        color=discord.Color.dark_red()
    )

    if jogador:
        identificacao = f"Jogador: {jogador.mention}"
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
# PERÍCIAS EM 2 COLUNAS
# ============================================================

def criar_pagina_pericias(f):

    embed = discord.Embed(
        title=f"📚 PERÍCIAS — {f['nome']}",
        color=discord.Color.dark_red()
    )

    metade = (len(ORDEM_PERICIAS) + 1) // 2

    coluna_esquerda = ORDEM_PERICIAS[:metade]
    coluna_direita = ORDEM_PERICIAS[metade:]

    texto_esquerda = []

    for chave in coluna_esquerda:
        emoji, nome = PERICIAS[chave]

        texto_esquerda.append(
            f"{emoji} {nome}: **{f[chave]}**"
        )

    texto_direita = []

    for chave in coluna_direita:
        emoji, nome = PERICIAS[chave]

        texto_direita.append(
            f"{emoji} {nome}: **{f[chave]}**"
        )

    embed.add_field(
        name="📚 Perícias",
        value="\n".join(texto_esquerda),
        inline=True
    )

    embed.add_field(
        name="📚 Perícias",
        value="\n".join(texto_direita),
        inline=True
    )

    embed.set_footer(
        text="Página 2/2 • Perícias"
    )

    return embed


# ============================================================
# PAGINAÇÃO
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
# MODAL — DADOS BÁSICOS DO NPC
# ============================================================

class NPCBasicoModal(discord.ui.Modal):

    def __init__(self, criacao):
        super().__init__(
            title="Dados básicos do NPC"
        )

        self.criacao = criacao

        self.nome = discord.ui.TextInput(
            label="Nome do NPC",
            placeholder="Ex: Goblin Guerreiro",
            required=True,
            max_length=50
        )

        self.hp = discord.ui.TextInput(
            label="HP",
            placeholder="Ex: 100",
            required=True,
            max_length=6
        )

        self.mana = discord.ui.TextInput(
            label="Mana",
            placeholder="Ex: 50",
            required=True,
            max_length=6
        )

        self.add_item(self.nome)
        self.add_item(self.hp)
        self.add_item(self.mana)

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

        try:
            hp = int(str(self.hp.value))
            mana = int(str(self.mana.value))
        except ValueError:

            await interaction.response.send_message(
                "❌ HP e Mana precisam ser números.",
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

        self.criacao.nome = str(self.nome.value)[:50]
        self.criacao.hp = hp
        self.criacao.mana = mana

        await interaction.response.edit_message(
            content=(
                "⚔️ **ETAPA 2/3 — ATRIBUTOS**\n\n"
                "Deseja gerar os atributos do NPC "
                "aleatoriamente?"
            ),
            embed=None,
            view=NPCAtributosView(self.criacao)
        )


# ============================================================
# VIEW — DADOS BÁSICOS
# ============================================================

class NPCBasicoView(discord.ui.View):

    def __init__(self, criacao):
        super().__init__(timeout=300)

        self.criacao = criacao

    @discord.ui.button(
        label="🎲 Aleatório",
        style=discord.ButtonStyle.primary
    )
    async def aleatorio(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        self.criacao.nome = random.choice(NOMES_NPC)
        self.criacao.hp = random.randint(20, 150)
        self.criacao.mana = random.randint(0, 100)

        await interaction.response.edit_message(
            content=(
                "⚔️ **ETAPA 2/3 — ATRIBUTOS**\n\n"
                "Deseja gerar os atributos do NPC "
                "aleatoriamente?"
            ),
            view=NPCAtributosView(self.criacao)
        )

    @discord.ui.button(
        label="✏️ Personalizado",
        style=discord.ButtonStyle.success
    )
    async def personalizado(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.send_modal(
            NPCBasicoModal(self.criacao)
        )


# ============================================================
# MODAL — ATRIBUTOS
# ============================================================

class NPCAtributosModal1(discord.ui.Modal):

    def __init__(self, criacao):
        super().__init__(
            title="Atributos — Parte 1/2"
        )

        self.criacao = criacao

        self.forca = discord.ui.TextInput(
            label="Força",
            placeholder="0",
            required=True,
            max_length=3
        )

        self.destreza = discord.ui.TextInput(
            label="Destreza",
            placeholder="0",
            required=True,
            max_length=3
        )

        self.vigor = discord.ui.TextInput(
            label="Vigor",
            placeholder="0",
            required=True,
            max_length=3
        )

        self.inteligencia = discord.ui.TextInput(
            label="Inteligência",
            placeholder="0",
            required=True,
            max_length=3
        )

        self.carisma = discord.ui.TextInput(
            label="Carisma",
            placeholder="0",
            required=True,
            max_length=3
        )

        self.add_item(self.forca)
        self.add_item(self.destreza)
        self.add_item(self.vigor)
        self.add_item(self.inteligencia)
        self.add_item(self.carisma)

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

        try:

            valores = {
                "forca": int(str(self.forca.value)),
                "destreza": int(str(self.destreza.value)),
                "vigor": int(str(self.vigor.value)),
                "inteligencia": int(str(self.inteligencia.value)),
                "carisma": int(str(self.carisma.value))
            }

            if any(valor < 0 for valor in valores.values()):
                raise ValueError

        except ValueError:

            await interaction.response.send_message(
                "❌ Os atributos precisam ser números iguais ou maiores que 0.",
                ephemeral=True
            )

            return

        self.criacao.atributos.update(valores)

        await interaction.response.send_modal(
            NPCAtributosModal2(self.criacao)
        )


class NPCAtributosModal2(discord.ui.Modal):

    def __init__(self, criacao):
        super().__init__(
            title="Atributos — Parte 2/2"
        )

        self.criacao = criacao

        self.raciocinio = discord.ui.TextInput(
            label="Raciocínio",
            placeholder="0",
            required=True,
            max_length=3
        )

        self.add_item(self.raciocinio)

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

        try:
            raciocinio = int(str(self.raciocinio.value))

            if raciocinio < 0:
                raise ValueError

        except ValueError:

            await interaction.response.send_message(
                "❌ O valor precisa ser um número igual ou maior que 0.",
                ephemeral=True
            )

            return

        self.criacao.atributos["raciocinio"] = raciocinio

        await interaction.response.edit_message(
            content=(
                "📚 **ETAPA 3/3 — PERÍCIAS**\n\n"
                "Deseja gerar as perícias do NPC "
                "aleatoriamente?"
            ),
            embed=None,
            view=NPCPericiasView(self.criacao)
        )


# ============================================================
# VIEW — ATRIBUTOS
# ============================================================

class NPCAtributosView(discord.ui.View):

    def __init__(self, criacao):
        super().__init__(timeout=300)

        self.criacao = criacao

    @discord.ui.button(
        label="🎲 Sim, aleatórios",
        style=discord.ButtonStyle.primary
    )
    async def aleatorios(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        for chave in ATRIBUTOS:
            self.criacao.atributos[chave] = random.randint(0, 5)

        await interaction.response.edit_message(
            content=(
                "📚 **ETAPA 3/3 — PERÍCIAS**\n\n"
                "Deseja gerar as perícias do NPC "
                "aleatoriamente?"
            ),
            view=NPCPericiasView(self.criacao)
        )

    @discord.ui.button(
        label="✏️ Não, personalizados",
        style=discord.ButtonStyle.success
    )
    async def personalizados(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.send_modal(
            NPCAtributosModal1(self.criacao)
        )


# ============================================================
# MODAL — PERÍCIAS
# ============================================================

class NPCPericiasModal(discord.ui.Modal):

    def __init__(
        self,
        criacao,
        chaves,
        numero,
        total
    ):

        super().__init__(
            title=f"Perícias {numero}/{total}"
        )

        self.criacao = criacao
        self.chaves = chaves

        for chave in chaves:

            _, nome = PERICIAS[chave]

            campo = discord.ui.TextInput(
                label=nome[:45],
                placeholder="0",
                required=True,
                max_length=3
            )

            setattr(
                self,
                f"campo_{chave}",
                campo
            )

            self.add_item(campo)

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

        try:

            for chave in self.chaves:

                campo = getattr(
                    self,
                    f"campo_{chave}"
                )

                valor = int(str(campo.value))

                if valor < 0:
                    raise ValueError

                self.criacao.pericias[chave] = valor

        except ValueError:

            await interaction.response.send_message(
                "❌ Todos os valores precisam ser números iguais ou maiores que 0.",
                ephemeral=True
            )

            return

        self.criacao.pericias_preenchidas.update(
            self.chaves
        )

        proxima = self.criacao.proxima_parte_pericias()

        if proxima:

            numero, chaves, total = proxima

            await interaction.response.send_modal(
                NPCPericiasModal(
                    self.criacao,
                    chaves,
                    numero,
                    total
                )
            )

            return

        await interaction.response.edit_message(
            content=(
                "✅ **Criação concluída!**\n\n"
                "Confira a ficha abaixo antes de criar o NPC."
            ),
            embed=self.criacao.criar_embed_previa(),
            view=NPCConfirmacaoView(self.criacao)
        )


# ============================================================
# VIEW — PERÍCIAS
# ============================================================

class NPCPericiasView(discord.ui.View):

    def __init__(self, criacao):
        super().__init__(timeout=300)

        self.criacao = criacao

    @discord.ui.button(
        label="🎲 Sim, aleatórias",
        style=discord.ButtonStyle.primary
    )
    async def aleatorias(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        for chave in PERICIAS:
            self.criacao.pericias[chave] = random.randint(0, 5)

        await interaction.response.edit_message(
            content=(
                "✅ **Criação concluída!**\n\n"
                "Confira a ficha abaixo antes de criar o NPC."
            ),
            embed=self.criacao.criar_embed_previa(),
            view=NPCConfirmacaoView(self.criacao)
        )

    @discord.ui.button(
        label="✏️ Não, personalizadas",
        style=discord.ButtonStyle.success
    )
    async def personalizadas(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        partes = []

        for i in range(0, len(ORDEM_PERICIAS), 5):

            partes.append(
                ORDEM_PERICIAS[i:i + 5]
            )

        self.criacao.pericias_partes = partes

        primeira = partes[0]

        await interaction.response.send_modal(
            NPCPericiasModal(
                self.criacao,
                primeira,
                1,
                len(partes)
            )
        )


# ============================================================
# ESTADO DA CRIAÇÃO DO NPC
# ============================================================

class CriacaoNPC:

    def __init__(
        self,
        interaction
    ):

        self.channel_id = interaction.channel.id
        self.mestre_id = interaction.user.id

        self.nome = ""
        self.hp = 0
        self.mana = 0

        self.atributos = {
            chave: 0
            for chave in ATRIBUTOS
        }

        self.pericias = {
            chave: 0
            for chave in PERICIAS
        }

        self.pericias_partes = []
        self.pericias_preenchidas = set()

    def proxima_parte_pericias(self):

        if not self.pericias_partes:
            return None

        for indice, parte in enumerate(
            self.pericias_partes
        ):

            if not all(
                chave in self.pericias_preenchidas
                for chave in parte
            ):

                return (
                    indice + 1,
                    parte,
                    len(self.pericias_partes)
                )

        return None

    def criar_embed_previa(self):

        rc = (
            self.pericias["esquiva"]
            + self.atributos["destreza"]
            + 5
        )

        embed = discord.Embed(
            title=f"👹 NPC — {self.nome.upper()}",
            color=discord.Color.dark_red()
        )

        status = (
            f"❤️ HP: **{self.hp}/{self.hp}**    "
            f"🔵 Mana: **{self.mana}/{self.mana}**\n"
            f"✨ XP: **0**    "
            f"⚡ RC: **{rc}**"
        )

        atributos = (
            f"💪 For: **{self.atributos['forca']}**    "
            f"🏹 Des: **{self.atributos['destreza']}**\n"
            f"🛡️ Vig: **{self.atributos['vigor']}**    "
            f"🧠 Int: **{self.atributos['inteligencia']}**\n"
            f"🎭 Car: **{self.atributos['carisma']}**    "
            f"💡 Rac: **{self.atributos['raciocinio']}**"
        )

        embed.description = (
            "👹 **NPC**\n\n"
            "❤️ **STATUS**\n"
            f"{status}\n\n"
            "⚔️ **ATRIBUTOS**\n"
            f"{atributos}"
        )

        metade = (
            len(ORDEM_PERICIAS) + 1
        ) // 2

        esquerda = ORDEM_PERICIAS[:metade]
        direita = ORDEM_PERICIAS[metade:]

        texto_esquerda = []

        for chave in esquerda:

            emoji, nome = PERICIAS[chave]

            texto_esquerda.append(
                f"{emoji} {nome}: **{self.pericias[chave]}**"
            )

        texto_direita = []

        for chave in direita:

            emoji, nome = PERICIAS[chave]

            texto_direita.append(
                f"{emoji} {nome}: **{self.pericias[chave]}**"
            )

        embed.add_field(
            name="📚 Perícias",
            value="\n".join(texto_esquerda),
            inline=True
        )

        embed.add_field(
            name="📚 Perícias",
            value="\n".join(texto_direita),
            inline=True
        )

        embed.set_footer(
            text="Prévia do NPC • Confira antes de criar"
        )

        return embed


# ============================================================
# CONFIRMAÇÃO DO NPC
# ============================================================

class NPCConfirmacaoView(discord.ui.View):

    def __init__(self, criacao):
        super().__init__(timeout=300)

        self.criacao = criacao

    @discord.ui.button(
        label="✅ Criar NPC",
        style=discord.ButtonStyle.success
    )
    async def criar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if (
            interaction.user.id
            != self.criacao.mestre_id
            and not eh_admin(interaction)
        ):

            await interaction.response.send_message(
                "❌ Somente o Mestre que iniciou a criação ou um administrador pode confirmar.",
                ephemeral=True
            )

            return

        garantir_mesa(
            self.criacao.channel_id
        )

        mestre_id = obter_mestre(
            self.criacao.channel_id
        )

        if mestre_id is None:
            mestre_id = self.criacao.mestre_id

            cursor.execute("""
                UPDATE mesas
                SET mestre_id = ?
                WHERE channel_id = ?
            """, (
                mestre_id,
                self.criacao.channel_id
            ))

        colunas = (
            list(ATRIBUTOS.keys())
            + ORDEM_PERICIAS
        )

        valores = (
            [
                self.criacao.atributos[chave]
                for chave in ATRIBUTOS
            ]
            +
            [
                self.criacao.pericias[chave]
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
                0
            )
            """,
            [
                self.criacao.channel_id,
                mestre_id,
                self.criacao.nome,
                self.criacao.hp,
                self.criacao.hp,
                self.criacao.mana,
                self.criacao.mana
            ]
            + valores
        )

        db.commit()

        dados = cursor.lastrowid

        ficha = buscar_ficha(dados)

        ficha = transformar_ficha(ficha)

        await interaction.response.edit_message(
            content="👹 **NPC criado com sucesso!**",
            embed=criar_pagina_status(ficha),
            view=FichaView(ficha)
        )

    @discord.ui.button(
        label="❌ Cancelar",
        style=discord.ButtonStyle.danger
    )
    async def cancelar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.edit_message(
            content="❌ Criação do NPC cancelada.",
            embed=None,
            view=None
        )


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
        f"👑 **{jogador.display_name}** agora é o Mestre deste canal!"
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
            f"👑 Mestre deste canal: **{membro.display_name}**"
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
            f"❌ **{jogador.display_name}** não possui uma ficha.",
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
# ALTERAR ATRIBUTO
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
        app_commands.Choice(name="Força", value="forca"),
        app_commands.Choice(name="Destreza", value="destreza"),
        app_commands.Choice(name="Vigor", value="vigor"),
        app_commands.Choice(name="Inteligência", value="inteligencia"),
        app_commands.Choice(name="Carisma", value="carisma"),
        app_commands.Choice(name="Raciocínio", value="raciocinio")
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

    f = transformar_ficha(dados)

    coluna = atributo.value

    if coluna not in ATRIBUTOS:
        await interaction.response.send_message(
            "❌ Atributo inválido.",
            ephemeral=True
        )
        return

    cursor.execute(
        f"""
        UPDATE fichas
        SET {coluna} = ?
        WHERE id = ?
        """,
        (
            valor,
            f["id"]
        )
    )

    db.commit()

    await interaction.response.send_message(
        f"⚔️ **{ATRIBUTOS[coluna][1]}** "
        f"alterado para **{valor}**!"
    )


# ============================================================
# ALTERAR PERÍCIA
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
        app_commands.Choice(name="Acadêmicos", value="academicos"),
        app_commands.Choice(name="Idiomas", value="idiomas"),
        app_commands.Choice(name="Ofícios", value="oficios"),
        app_commands.Choice(name="Armas Brancas", value="armas_brancas"),
        app_commands.Choice(name="Intimidação", value="intimidacao"),
        app_commands.Choice(name="Ocultismo", value="ocultismo"),
        app_commands.Choice(name="Briga", value="briga"),
        app_commands.Choice(name="Investigação", value="investigacao"),
        app_commands.Choice(name="Persuasão", value="persuasao"),
        app_commands.Choice(name="Ciências", value="ciencias"),
        app_commands.Choice(name="Lábia", value="labia"),
        app_commands.Choice(name="Prontidão", value="prontidao"),
        app_commands.Choice(name="Conhecimentos Gerais", value="conhecimentos_gerais"),
        app_commands.Choice(name="Liderança", value="lideranca"),
        app_commands.Choice(name="Sobrevivência", value="sobrevivencia"),
        app_commands.Choice(name="Condução", value="conducao"),
        app_commands.Choice(name="Manha", value="manha"),
        app_commands.Choice(name="Tecnologia", value="tecnologia"),
        app_commands.Choice(name="Esportes", value="esportes"),
        app_commands.Choice(name="Medicina", value="medicina"),
        app_commands.Choice(name="Mira", value="mira"),
        app_commands.Choice(name="Esquiva", value="esquiva"),
        app_commands.Choice(name="Furtividade", value="furtividade")
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

    f = transformar_ficha(dados)

    coluna = pericia.value

    if coluna not in PERICIAS:
        await interaction.response.send_message(
            "❌ Perícia inválida.",
            ephemeral=True
        )
        return

    cursor.execute(
        f"""
        UPDATE fichas
        SET {coluna} = ?
        WHERE id = ?
        """,
        (
            valor,
            f["id"]
        )
    )

    db.commit()

    await interaction.response.send_message(
        f"📚 **{PERICIAS[coluna][1]}** "
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

    f = transformar_ficha(dados)

    if not pode_alterar_ficha(
        interaction,
        f
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
        f["id"]
    ))

    db.commit()

    await interaction.response.send_message(
        f"⚙️ Ficha de **{f['nome']}** atualizada!\n\n"
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

    f = transformar_ficha(dados)

    cursor.execute(
        "DELETE FROM fichas WHERE id = ?",
        (f["id"],)
    )

    db.commit()

    await interaction.response.send_message(
        f"🗑️ A ficha **{f['nome']}** foi apagada."
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

    f = transformar_ficha(dados)

    novo_hp = max(
        0,
        f["hp_atual"] - valor
    )

    cursor.execute("""
        UPDATE fichas
        SET hp_atual = ?
        WHERE id = ?
    """, (
        novo_hp,
        f["id"]
    ))

    db.commit()

    await interaction.response.send_message(
        f"💥 **{f['nome']}** recebeu **{valor} de dano**!\n"
        f"❤️ HP: **{novo_hp}/{f['hp_max']}**"
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

    f = transformar_ficha(dados)

    novo_hp = min(
        f["hp_max"],
        f["hp_atual"] + valor
    )

    recuperado = novo_hp - f["hp_atual"]

    cursor.execute("""
        UPDATE fichas
        SET hp_atual = ?
        WHERE id = ?
    """, (
        novo_hp,
        f["id"]
    ))

    db.commit()

    await interaction.response.send_message(
        f"💚 **{f['nome']}** recuperou **{recuperado} de HP**!\n"
        f"❤️ HP: **{novo_hp}/{f['hp_max']}**"
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

    f = transformar_ficha(dados)

    if valor <= 0:

        await interaction.response.send_message(
            "❌ O valor precisa ser maior que 0.",
            ephemeral=True
        )

        return

    if valor > f["mana_atual"]:

        await interaction.response.send_message(
            "❌ Mana insuficiente.",
            ephemeral=True
        )

        return

    nova_mana = f["mana_atual"] - valor

    cursor.execute("""
        UPDATE fichas
        SET mana_atual = ?
        WHERE id = ?
    """, (
        nova_mana,
        f["id"]
    ))

    db.commit()

    await interaction.response.send_message(
        f"🔮 **{f['nome']}** gastou **{valor} de Mana**!\n"
        f"🔵 Mana: **{nova_mana}/{f['mana_max']}**"
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

    f = transformar_ficha(dados)

    nova_mana = min(
        f["mana_max"],
        f["mana_atual"] + valor
    )

    recuperado = nova_mana - f["mana_atual"]

    cursor.execute("""
        UPDATE fichas
        SET mana_atual = ?
        WHERE id = ?
    """, (
        nova_mana,
        f["id"]
    ))

    db.commit()

    await interaction.response.send_message(
        f"💧 **{f['nome']}** recuperou **{recuperado} de Mana**!\n"
        f"🔵 Mana: **{nova_mana}/{f['mana_max']}**"
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

    f = transformar_ficha(dados)

    if (
        f["dono_id"] != interaction.user.id
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
        f["id"]
    ))

    db.commit()

    cursor.execute(
        "SELECT xp FROM fichas WHERE id = ?",
        (f["id"],)
    )

    xp_atual = cursor.fetchone()[0]

    await interaction.response.send_message(
        f"✨ **{f['nome']}** recebeu **{valor} XP**!\n"
        f"✨ XP atual: **{xp_atual}**"
    )


# ============================================================
# NOVO /CRIARNPC
# ============================================================

@bot.tree.command(
    name="criarnpc",
    description="Inicia a criação guiada de um NPC."
)
async def criarnpc(
    interaction: discord.Interaction
):

    garantir_mesa(
        interaction.channel.id
    )

    if (
        not eh_mestre(interaction)
        and not eh_admin(interaction)
    ):

        await interaction.response.send_message(
            "❌ Somente o Mestre ou um administrador pode criar NPCs.",
            ephemeral=True
        )

        return

    criacao = CriacaoNPC(
        interaction
    )

    await interaction.response.send_message(
        content=(
            "👹 **CRIAÇÃO DE NPC — ETAPA 1/3**\n\n"
            "Como deseja definir **Nome, HP e Mana** do NPC?"
        ),
        view=NPCBasicoView(criacao),
        ephemeral=True
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
        f"👹 **NPCs da mesa — {len(resultados)} encontrados**"
    )

    for dados in resultados:

        f = transformar_ficha(dados)

        await interaction.followup.send(
            embed=criar_pagina_status(f),
            view=FichaView(f)
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
            "`/atributo` — Alterar atributo\n"
            "`/pericia` — Alterar perícia\n"
            "`/alterarficha` — Alterar HP/Mana\n"
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
        name="👹 Mestre",
        value=(
            "`/criarnpc` — Criar NPC guiado\n"
            "`/npcs` — Ver NPCs\n"
            "`/apagarnpc` — Apagar NPC\n"
            "`/passarmestre` — Passar Mestre\n"
            "`/mestre` — Ver Mestre"
        ),
        inline=False
    )

    embed.add_field(
        name="🛡️ Administrador",
        value=(
            "`/definirmestre` — Definir Mestre\n"
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
