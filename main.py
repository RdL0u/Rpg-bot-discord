import os
import sqlite3
import discord
from discord.ext import commands
from discord import app_commands

# ==================================================
# CONFIGURAÇÃO
# ==================================================

TOKEN = os.getenv("DISCORD_TOKEN")

# ==================================================
# BANCO DE DADOS
# ==================================================

db = sqlite3.connect("fichas.db")
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS fichas (
    user_id INTEGER PRIMARY KEY,
    nome_personagem TEXT NOT NULL DEFAULT 'Sem nome',
    hp_atual INTEGER NOT NULL DEFAULT 100,
    hp_max INTEGER NOT NULL DEFAULT 100,
    mana_atual INTEGER NOT NULL DEFAULT 100,
    mana_max INTEGER NOT NULL DEFAULT 100,
    xp INTEGER NOT NULL DEFAULT 0
)
""")

db.commit()

# ==================================================
# BOT
# ==================================================

intents = discord.Intents.default()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

# ==================================================
# VERIFICAR ADMINISTRADOR
# ==================================================

def eh_admin(interaction):

    return (
        interaction.guild is not None
        and interaction.user.guild_permissions.administrator
    )


# ==================================================
# VERIFICAR SE PODE ALTERAR A FICHA
# ==================================================

def pode_alterar(interaction, jogador_id):

    # Administrador pode alterar qualquer ficha
    if eh_admin(interaction):
        return True

    # Jogador comum só pode alterar a própria ficha
    if interaction.user.id == jogador_id:
        return True

    return False


# ==================================================
# BOT ONLINE
# ==================================================

@bot.event
async def on_ready():

    print(f"Bot conectado como {bot.user}")

    try:

        comandos = await bot.tree.sync()

        print(
            f"{len(comandos)} comandos sincronizados."
        )

    except Exception as erro:

        print(
            f"Erro ao sincronizar comandos: {erro}"
        )


# ==================================================
# CRIAR FICHA
# ==================================================

@bot.tree.command(
    name="criarficha",
    description="Cria sua ficha de personagem."
)
@app_commands.describe(
    nome="Nome do personagem",
    hp="HP inicial",
    mana="Mana inicial"
)
async def criarficha(
    interaction: discord.Interaction,
    nome: str,
    hp: int,
    mana: int
):

    user_id = interaction.user.id

    cursor.execute(
        "SELECT user_id FROM fichas WHERE user_id = ?",
        (user_id,)
    )

    if cursor.fetchone() is not None:

        await interaction.response.send_message(
            "⚠️ Você já possui uma ficha.",
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
            user_id,
            nome_personagem,
            hp_atual,
            hp_max,
            mana_atual,
            mana_max,
            xp
        )
        VALUES (?, ?, ?, ?, ?, ?, 0)
    """, (
        user_id,
        nome,
        hp,
        hp,
        mana,
        mana
    ))

    db.commit()

    embed = discord.Embed(
        title="📜 Nova ficha criada!",
        color=discord.Color.green()
    )

    embed.add_field(
        name="👤 Personagem",
        value=nome,
        inline=False
    )

    embed.add_field(
        name="❤️ HP",
        value=f"{hp}/{hp}",
        inline=True
    )

    embed.add_field(
        name="💧 Mana",
        value=f"{mana}/{mana}",
        inline=True
    )

    embed.add_field(
        name="⭐ XP",
        value="0",
        inline=True
    )

    await interaction.response.send_message(
        embed=embed
    )


# ==================================================
# MOSTRAR PRÓPRIA FICHA
# ==================================================

@bot.tree.command(
    name="ficha",
    description="Mostra sua ficha."
)
async def ficha(interaction: discord.Interaction):

    user_id = interaction.user.id

    cursor.execute("""
        SELECT
            nome_personagem,
            hp_atual,
            hp_max,
            mana_atual,
            mana_max,
            xp
        FROM fichas
        WHERE user_id = ?
    """, (user_id,))

    dados = cursor.fetchone()

    if dados is None:

        await interaction.response.send_message(
            "❌ Você ainda não possui uma ficha.\n"
            "Use `/criarficha` para criar uma.",
            ephemeral=True
        )

        return

    nome, hp, hp_max, mana, mana_max, xp = dados

    embed = discord.Embed(
        title=f"📜 Ficha de {nome}",
        description=f"Jogador: {interaction.user.mention}",
        color=discord.Color.dark_red()
    )

    embed.add_field(
        name="❤️ HP",
        value=f"{hp_max}/{hp}",
        inline=True
    )

    embed.add_field(
        name="💧 Mana",
        value=f"{mana_max}/{mana}",
        inline=True
    )

    embed.add_field(
        name="⭐ XP",
        value=str(xp),
        inline=True
    )

    await interaction.response.send_message(
        embed=embed
    )


# ==================================================
# MOSTRAR TODAS AS FICHAS
# ==================================================

@bot.tree.command(
    name="fichas",
    description="Mostra todas as fichas dos jogadores."
)
async def fichas(interaction: discord.Interaction):

    cursor.execute("""
        SELECT
            nome_personagem,
            hp_atual,
            hp_max,
            mana_atual,
            mana_max,
            xp,
            user_id
        FROM fichas
        ORDER BY nome_personagem
    """)

    dados = cursor.fetchall()

    if not dados:

        await interaction.response.send_message(
            "📜 Ainda não existem fichas."
        )

        return

    embed = discord.Embed(
        title="📜 Fichas dos jogadores",
        color=discord.Color.dark_red()
    )

    for (
        nome,
        hp,
        hp_max,
        mana,
        mana_max,
        xp,
        user_id
    ) in dados:

        membro = interaction.guild.get_member(user_id)

        if membro:
            jogador = membro.mention
        else:
            jogador = f"<@{user_id}>"

        embed.add_field(
            name=f"👤 {nome}",
            value=(
                f"Jogador: {jogador}\n"
                f"❤️ HP: **{hp_max}/{hp}**\n"
                f"💧 Mana: **{mana_max}/{mana}**\n"
                f"⭐ XP: **{xp}**"
            ),
            inline=False
        )

    await interaction.response.send_message(
        embed=embed
    )


# ==================================================
# APAGAR FICHA
# ==================================================

@bot.tree.command(
    name="apagarficha",
    description="Apaga sua própria ficha."
)
async def apagarficha(interaction: discord.Interaction):

    user_id = interaction.user.id

    cursor.execute(
        "SELECT nome_personagem FROM fichas WHERE user_id = ?",
        (user_id,)
    )

    ficha = cursor.fetchone()

    if ficha is None:

        await interaction.response.send_message(
            "❌ Você não possui uma ficha.",
            ephemeral=True
        )

        return

    nome = ficha[0]

    cursor.execute(
        "DELETE FROM fichas WHERE user_id = ?",
        (user_id,)
    )

    db.commit()

    await interaction.response.send_message(
        f"🗑️ A ficha **{nome}** foi apagada.\n"
        "Você pode criar uma nova usando `/criarficha`."
    )


# ==================================================
# ALTERAR FICHA
# ==================================================

@bot.tree.command(
    name="alterarficha",
    description="Altera o HP e a Mana máximos de uma ficha."
)
@app_commands.describe(
    jogador="Jogador da ficha",
    hp="Novo HP máximo",
    mana="Nova Mana máxima"
)
async def alterarficha(
    interaction: discord.Interaction,
    jogador: discord.Member,
    hp: int,
    mana: int
):

    user_id = jogador.id

    if not pode_alterar(
        interaction,
        user_id
    ):

        await interaction.response.send_message(
            "❌ Você só pode alterar sua própria ficha.",
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

    cursor.execute(
        "SELECT nome_personagem FROM fichas WHERE user_id = ?",
        (user_id,)
    )

    ficha = cursor.fetchone()

    if ficha is None:

        await interaction.response.send_message(
            "❌ Esse jogador não possui uma ficha.",
            ephemeral=True
        )

        return

    cursor.execute("""
        UPDATE fichas
        SET
            hp_atual = ?,
            hp_max = ?,
            mana_atual = ?,
            mana_max = ?
        WHERE user_id = ?
    """, (
        hp,
        hp,
        mana,
        mana,
        user_id
    ))

    db.commit()

    await interaction.response.send_message(
        f"⚙️ Ficha de **{ficha[0]}** alterada!\n"
        f"❤️ HP: **{hp}/{hp}**\n"
        f"💧 Mana: **{mana}/{mana}**"
    )


# ==================================================
# DANO
# QUALQUER JOGADOR PODE CAUSAR DANO
# ==================================================

@bot.tree.command(
    name="dano",
    description="Causa dano a qualquer jogador."
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

    user_id = jogador.id

    if valor <= 0:

        await interaction.response.send_message(
            "❌ O dano precisa ser maior que 0.",
            ephemeral=True
        )

        return

    cursor.execute("""
        SELECT
            nome_personagem,
            hp_atual,
            hp_max
        FROM fichas
        WHERE user_id = ?
    """, (user_id,))

    dados = cursor.fetchone()

    if dados is None:

        await interaction.response.send_message(
            "❌ Esse jogador não possui uma ficha.",
            ephemeral=True
        )

        return

    nome, hp_atual, hp_max = dados

    novo_hp = max(
        0,
        hp_atual - valor
    )

    cursor.execute("""
        UPDATE fichas
        SET hp_atual = ?
        WHERE user_id = ?
    """, (
        novo_hp,
        user_id
    ))

    db.commit()

    await interaction.response.send_message(
        f"💥 **{interaction.user.display_name}** "
        f"causou **{valor} de dano** em **{nome}**!\n"
        f"❤️ HP: **{hp_max}/{novo_hp}**"
    )


# ==================================================
# CURA
# QUALQUER JOGADOR PODE CURAR QUALQUER FICHA
# ==================================================

@bot.tree.command(
    name="cura",
    description="Cura qualquer jogador."
)
@app_commands.describe(
    jogador="Jogador que será curado",
    valor="Quantidade de HP recuperado"
)
async def cura(
    interaction: discord.Interaction,
    jogador: discord.Member,
    valor: int
):

    user_id = jogador.id

    if valor <= 0:

        await interaction.response.send_message(
            "❌ A cura precisa ser maior que 0.",
            ephemeral=True
        )

        return

    cursor.execute("""
        SELECT
            nome_personagem,
            hp_atual,
            hp_max
        FROM fichas
        WHERE user_id = ?
    """, (user_id,))

    dados = cursor.fetchone()

    if dados is None:

        await interaction.response.send_message(
            "❌ Esse jogador não possui uma ficha.",
            ephemeral=True
        )

        return

    nome, hp_atual, hp_max = dados

    novo_hp = min(
        hp_max,
        hp_atual + valor
    )

    recuperado = novo_hp - hp_atual

    cursor.execute("""
        UPDATE fichas
        SET hp_atual = ?
        WHERE user_id = ?
    """, (
        novo_hp,
        user_id
    ))

    db.commit()

    await interaction.response.send_message(
        f"💚 **{interaction.user.display_name}** "
        f"curou **{nome}** em **{recuperado} de HP**!\n"
        f"❤️ HP: **{hp_max}/{novo_hp}**"
    )


# ==================================================
# GASTAR MANA
# PRÓPRIO JOGADOR OU ADMINISTRADOR
# ==================================================

@bot.tree.command(
    name="gastarmana",
    description="Gasta Mana de um jogador."
)
@app_commands.describe(
    jogador="Jogador que gastará Mana",
    valor="Quantidade de Mana gasta"
)
async def gastarmana(
    interaction: discord.Interaction,
    jogador: discord.Member,
    valor: int
):

    user_id = jogador.id

    if not pode_alterar(
        interaction,
        user_id
    ):

        await interaction.response.send_message(
            "❌ Você só pode alterar sua própria Mana. "
            "Somente administradores podem alterar a Mana de outros jogadores.",
            ephemeral=True
        )

        return

    if valor <= 0:

        await interaction.response.send_message(
            "❌ O gasto precisa ser maior que 0.",
            ephemeral=True
        )

        return

    cursor.execute("""
        SELECT
            nome_personagem,
            mana_atual,
            mana_max
        FROM fichas
        WHERE user_id = ?
    """, (user_id,))

    dados = cursor.fetchone()

    if dados is None:

        await interaction.response.send_message(
            "❌ Esse jogador não possui uma ficha.",
            ephemeral=True
        )

        return

    nome, mana_atual, mana_max = dados

    if valor > mana_atual:

        await interaction.response.send_message(
            f"❌ **{nome}** não possui Mana suficiente!\n"
            f"💧 Mana: **{mana_max}/{mana_atual}**",
            ephemeral=True
        )

        return

    nova_mana = mana_atual - valor

    cursor.execute("""
        UPDATE fichas
        SET mana_atual = ?
        WHERE user_id = ?
    """, (
        nova_mana,
        user_id
    ))

    db.commit()

    await interaction.response.send_message(
        f"🔮 **{nome}** gastou **{valor} de Mana**!\n"
        f"💧 Mana: **{mana_max}/{nova_mana}**"
    )


# ==================================================
# RECUPERAR MANA
# PRÓPRIO JOGADOR OU ADMINISTRADOR
# ==================================================

@bot.tree.command(
    name="recuperarmana",
    description="Recupera Mana de um jogador."
)
@app_commands.describe(
    jogador="Jogador que recuperará Mana",
    valor="Quantidade de Mana recuperada"
)
async def recuperarmana(
    interaction: discord.Interaction,
    jogador: discord.Member,
    valor: int
):

    user_id = jogador.id

    if not pode_alterar(
        interaction,
        user_id
    ):

        await interaction.response.send_message(
            "❌ Você só pode alterar sua própria Mana. "
            "Somente administradores podem alterar a Mana de outros jogadores.",
            ephemeral=True
        )

        return

    if valor <= 0:

        await interaction.response.send_message(
            "❌ A recuperação precisa ser maior que 0.",
            ephemeral=True
        )

        return

    cursor.execute("""
        SELECT
            nome_personagem,
            mana_atual,
            mana_max
        FROM fichas
        WHERE user_id = ?
    """, (user_id,))

    dados = cursor.fetchone()

    if dados is None:

        await interaction.response.send_message(
            "❌ Esse jogador não possui uma ficha.",
            ephemeral=True
        )

        return

    nome, mana_atual, mana_max = dados

    nova_mana = min(
        mana_max,
        mana_atual + valor
    )

    recuperado = nova_mana - mana_atual

    cursor.execute("""
        UPDATE fichas
        SET mana_atual = ?
        WHERE user_id = ?
    """, (
        nova_mana,
        user_id
    ))

    db.commit()

    await interaction.response.send_message(
        f"💧 **{nome}** recuperou **{recuperado} de Mana**!\n"
        f"💧 Mana: **{mana_max}/{nova_mana}**"
    )


# ==================================================
# ADICIONAR XP
# PRÓPRIO JOGADOR OU ADMINISTRADOR
# ==================================================

@bot.tree.command(
    name="addxp",
    description="Adiciona XP a um jogador."
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

    user_id = jogador.id

    if not pode_alterar(
        interaction,
        user_id
    ):

        await interaction.response.send_message(
            "❌ Você só pode alterar o XP da sua própria ficha. "
            "Somente administradores podem alterar o XP de outros jogadores.",
            ephemeral=True
        )

        return

    if valor <= 0:

        await interaction.response.send_message(
            "❌ O XP precisa ser maior que 0.",
            ephemeral=True
        )

        return

    cursor.execute(
        "SELECT nome_personagem FROM fichas WHERE user_id = ?",
        (user_id,)
    )

    ficha = cursor.fetchone()

    if ficha is None:

        await interaction.response.send_message(
            "❌ Esse jogador não possui uma ficha.",
            ephemeral=True
        )

        return

    cursor.execute("""
        UPDATE fichas
        SET xp = xp + ?
        WHERE user_id = ?
    """, (
        valor,
        user_id
    ))

    db.commit()

    cursor.execute(
        "SELECT xp FROM fichas WHERE user_id = ?",
        (user_id,)
    )

    xp_atual = cursor.fetchone()[0]

    await interaction.response.send_message(
        f"⭐ **{ficha[0]}** recebeu **{valor} XP**!\n"
        f"⭐ XP atual: **{xp_atual}**"
    )


# ==================================================
# INICIAR BOT
# ==================================================

if not TOKEN:

    raise RuntimeError(
        "DISCORD_TOKEN não foi configurado."
    )

bot.run(TOKEN)
