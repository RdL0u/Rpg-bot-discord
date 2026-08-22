import asyncio
import discord

from discord.ext import (
    commands,
    tasks,
)

from config import TOKEN

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


# ============================================================
# CONFIGURAÇÃO DO BOT
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

registrar_comandos_backup(
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

        caminho = await asyncio.to_thread(
            criar_backup
        )

        print(
            "Backup automático criado: "
            f"{caminho.name}"
        )

    except Exception as erro:

        print(
            "Erro ao criar backup automático: "
            f"{erro}"
        )


# ============================================================
# AGUARDAR BOT FICAR PRONTO
# ============================================================

@backup_automatico.before_loop
async def antes_do_backup():

    await bot.wait_until_ready()


# ============================================================
# BOT ONLINE
# ============================================================

@bot.event
async def on_ready():

    print(
        f"Bot conectado como {bot.user}"
    )

    # ========================================================
    # INICIAR BACKUP AUTOMÁTICO
    # ========================================================

    if not backup_automatico.is_running():

        backup_automatico.start()

        print(
            "Sistema de backup automático iniciado."
        )

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
            "Erro ao sincronizar comandos: "
            f"{erro}"
        )


# ============================================================
# HELP
# ============================================================

@bot.tree.command(
    name="help",
    description="Mostra os principais comandos do bot."
)
async def help_command(
    interaction: discord.Interaction
):

    embed = discord.Embed(
        title="📖 AJUDA — BOT DE RPG",
        description=(
            "Principais comandos disponíveis "
            "para gerenciamento da mesa."
        ),
        color=discord.Color.dark_red()
    )

    embed.add_field(
        name="👤 JOGADORES",
        value=(
            "`/criarficha` — Criar ficha\n"
            "`/ficha` — Ver sua ficha\n"
            "`/verficha` — Ver outra ficha\n"
            "`/atributo` — Alterar atributo\n"
            "`/pericia` — Alterar perícia\n"
            "`/apagarficha` — Apagar sua ficha"
        ),
        inline=False
    )

    embed.add_field(
        name="❤️ RECURSOS",
        value=(
            "`/dano` — Aplicar dano\n"
            "`/cura` — Recuperar HP\n"
            "`/gastarmana` — Gastar Mana\n"
            "`/recuperarmana` — Recuperar Mana\n"
            "`/addxp` — Adicionar XP"
        ),
        inline=False
    )

    embed.add_field(
        name="👑 MESTRE E NPCs",
        value=(
            "`/mestre` — Ver Mestre da mesa\n"
            "`/definirmestre` — Definir Mestre\n"
            "`/passarmestre` — Passar Mestre\n"
            "`/criarnpc` — Criar NPC\n"
            "`/npcs` — Mostrar NPCs\n"
            "`/apagarnpc` — Apagar NPCs"
        ),
        inline=False
    )

    embed.add_field(
        name="📋 GERENCIAMENTO",
        value=(
            "`/painel` — Painel da mesa\n"
            "`/historico` — Histórico da mesa"
        ),
        inline=False
    )

    embed.add_field(
        name="💾 BACKUPS",
        value=(
            "`/backup` — Criar backup manual\n"
            "`/backups` — Listar backups\n\n"
            "🔒 Comandos de backup são "
            "restritos a administradores."
        ),
        inline=False
    )

    embed.set_footer(
        text=(
            "As fichas também possuem "
            "controles de visualização e edição."
        )
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
