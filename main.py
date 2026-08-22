import discord

from discord.ext import commands

from config import TOKEN

from comando.jogador import (
    registrar_comandos_jogador
)

from comando.mestre import (
    registrar_comandos_mestre
)

from comando.painel import (
    registrar_comandos_painel
)

from comando.historico import (
    registrar_comandos_historico
)


# ============================================================
# BOT
# ============================================================

intents = discord.Intents.default()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# ============================================================
# REGISTRAR COMANDOS
# ============================================================

registrar_comandos_jogador(
    bot
)

registrar_comandos_mestre(
    bot
)

registrar_comandos_painel(
    bot
)

registrar_comandos_historico(
    bot
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
# HELP
# ============================================================

@bot.tree.command(
    name="help",
    description="Mostra os comandos disponíveis do bot."
)
async def help(
    interaction: discord.Interaction
):

    embed = discord.Embed(
        title="📖 COMANDOS DO BOT",
        description=(
            "Lista dos principais comandos disponíveis "
            "para a mesa de RPG."
        ),
        color=discord.Color.dark_red()
    )

    # ========================================================
    # JOGADOR
    # ========================================================

    embed.add_field(
        name="👤 Jogador",
        value=(
            "`/criarficha` — Criar sua ficha\n"
            "`/ficha` — Visualizar sua própria ficha\n"
            "`/verficha` — Visualizar ficha de outro jogador\n"
            "`/atributo` — Alterar um atributo\n"
            "`/pericia` — Alterar uma perícia\n"
            "`/alterarficha` — Alterar HP e Mana máximos\n"
            "`/apagarficha` — Apagar sua ficha\n"
            "`/dano` — Aplicar dano\n"
            "`/cura` — Recuperar HP\n"
            "`/gastarmana` — Gastar Mana\n"
            "`/recuperarmana` — Recuperar Mana\n"
            "`/addxp` — Adicionar XP"
        ),
        inline=False
    )

    # ========================================================
    # MESA
    # ========================================================

    embed.add_field(
        name="📋 Mesa",
        value=(
            "`/painel` — Ver fichas ativas da mesa\n"
            "`/historico` — Ver histórico de alterações"
        ),
        inline=False
    )

    # ========================================================
    # MESTRE
    # ========================================================

    embed.add_field(
        name="👑 Mestre",
        value=(
            "`/criarnpc` — Criar NPC\n"
            "`/npcs` — Ver NPCs da mesa\n"
            "`/apagarnpc` — Apagar NPC\n"
            "`/passarmestre` — Passar o cargo de Mestre\n"
            "`/mestre` — Ver quem é o Mestre"
        ),
        inline=False
    )

    # ========================================================
    # ADMINISTRAÇÃO
    # ========================================================

    embed.add_field(
        name="🛡️ Administração",
        value=(
            "`/definirmestre` — Definir o Mestre do canal"
        ),
        inline=False
    )

    embed.set_footer(
        text=(
            "Use / seguido do nome do comando "
            "para visualizar suas opções."
        )
    )

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )


# ============================================================
# INICIAR BOT
# ============================================================

if __name__ == "__main__":

    bot.run(
        TOKEN
    )
