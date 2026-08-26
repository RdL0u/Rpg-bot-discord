import discord

from discord.ext import (
    commands,
    tasks,
)

from config import (
    TOKEN,
)

from backup import (
    criar_backup,
)

from comando.jogador import (
    registrar_comandos_jogador,
)

from comando.mestre import (
    registrar_comandos_mestre,
)

from comando.painel import (
    registrar_comandos_painel,
)

from comando.historico import (
    registrar_comandos_historico,
)

from comando.backup import (
    registrar_comandos_backup,
)

from comando.rolagem import (
    registrar_comandos_rolagem,
)


# ============================================================
# INTENTS
# ============================================================

intents = discord.Intents.default()


# ============================================================
# BOT
# ============================================================

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# ============================================================
# REGISTRAR MÓDULOS
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

registrar_comandos_backup(
    bot
)

registrar_comandos_rolagem(
    bot
)


# ============================================================
# BACKUP AUTOMÁTICO
# ============================================================

@tasks.loop(
    hours=6
)
async def backup_automatico():

    try:

        caminho = criar_backup()

        print(
            "Backup automático criado:",
            caminho
        )

    except Exception as erro:

        print(
            "Erro no backup automático:",
            erro
        )


# ============================================================
# BOT PRONTO
# ============================================================

@bot.event
async def on_ready():

    print(
        f"Bot conectado como {bot.user}"
    )

    # ========================================================
    # BACKUP AUTOMÁTICO
    # ========================================================

    if not backup_automatico.is_running():

        backup_automatico.start()

    # ========================================================
    # SINCRONIZAR COMANDOS
    # ========================================================

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
    description="Mostra os comandos do BotRPG."
)
async def help(
    interaction: discord.Interaction
):

    embed = discord.Embed(
        title="📖 BotRPG",
        description=(
            "Comandos disponíveis para a mesa."
        ),
        color=discord.Color.dark_red()
    )

    # ========================================================
    # JOGADORES
    # ========================================================

    embed.add_field(
        name="👤 Jogador",
        value=(
            "`/criarficha` — Criar ficha\n"
            "`/ficha` — Ver sua ficha\n"
            "`/verficha` — Ver ficha de jogador\n"
            "`/atributo` — Alterar atributo\n"
            "`/pericia` — Alterar perícia\n"
            "`/alterarficha` — Alterar HP/Mana\n"
            "`/apagarficha` — Apagar ficha\n"
            "`/gastarmana` — Gastar Mana\n"
            "`/dano` — Aplicar dano\n"
            "`/cura` — Aplicar cura\n"
            "`/recuperarmana` — Recuperar Mana\n"
            "`/addxp` — Adicionar XP"
        ),
        inline=False
    )

    # ========================================================
    # ROLAGENS
    # ========================================================

    embed.add_field(
        name="🎲 Rolagens",
        value=(
            "`/rolar` — Realiza uma rolagem "
            "de **2d10 + Atributo + Perícia**"
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
            "`/npcs` — Ver NPCs\n"
            "`/apagarnpc` — Apagar NPC\n"
            "`/passarmestre` — Passar Mestre\n"
            "`/mestre` — Ver Mestre"
        ),
        inline=False
    )

    # ========================================================
    # MESA
    # ========================================================

    embed.add_field(
        name="📋 Mesa",
        value=(
            "`/painel` — Painel da mesa\n"
            "`/historico` — Histórico da mesa"
        ),
        inline=False
    )

    # ========================================================
    # ADMIN
    # ========================================================

    embed.add_field(
        name="🛡️ Administrador",
        value=(
            "`/definirmestre` — Definir Mestre\n"
            "`/backup` — Criar backup\n"
            "`/backups` — Ver backups"
        ),
        inline=False
    )

    embed.set_footer(
        text="BotRPG • Sistema de RPG"
    )

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )


# ============================================================
# INICIAR BOT
# ============================================================

bot.run(
    TOKEN
)
