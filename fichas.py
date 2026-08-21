import discord

from database import cursor, db

from config import (
ATRIBUTOS,
PERICIAS,
ORDEM_PERICIAS
)

# ============================================================

# BUSCAR FICHA DO JOGADOR

# ============================================================

def buscar_ficha_jogador(channel_id, user_id):

```
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
```

# ============================================================

# BUSCAR FICHA PELO ID

# ============================================================

def buscar_ficha(ficha_id):

```
cursor.execute("""
    SELECT *
    FROM fichas
    WHERE id = ?
""", (ficha_id,))

return cursor.fetchone()
```

# ============================================================

# TRANSFORMAR FICHA

# ============================================================

def transformar_ficha(dados):

```
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
```

# ============================================================

# ATUALIZAR HP

# ============================================================

def atualizar_hp(ficha_id, novo_hp):

```
cursor.execute("""
    UPDATE fichas
    SET hp_atual = ?
    WHERE id = ?
""", (
    novo_hp,
    ficha_id
))

db.commit()
```

# ============================================================

# ATUALIZAR MANA

# ============================================================

def atualizar_mana(ficha_id, nova_mana):

```
cursor.execute("""
    UPDATE fichas
    SET mana_atual = ?
    WHERE id = ?
""", (
    nova_mana,
    ficha_id
))

db.commit()
```

# ============================================================

# ATUALIZAR XP

# ============================================================

def adicionar_xp(ficha_id, valor):

```
cursor.execute("""
    UPDATE fichas
    SET xp = xp + ?
    WHERE id = ?
""", (
    valor,
    ficha_id
))

db.commit()
```

# ============================================================

# DELETAR FICHA

# ============================================================

def deletar_ficha(ficha_id):

```
cursor.execute("""
    DELETE FROM fichas
    WHERE id = ?
""", (ficha_id,))

db.commit()
```

# ============================================================

# CALCULAR RC

# ============================================================

def calcular_rc(ficha):

```
return (
    ficha.get("esquiva", 0)
    + ficha.get("destreza", 0)
    \+ 5
)
```

# ============================================================

# ESTADO DE RECURSO

# ============================================================

def estado_recurso(atual, maximo):

```
if maximo <= 0:
    return "0/0"

return f"{atual}/{maximo}"
```

# ============================================================

# FORMATAR ATRIBUTOS

# ============================================================

def formatar_atributos(ficha):

```
linhas = []

for chave, dados in ATRIBUTOS.items():

    emoji, nome = dados

    valor = ficha.get(
        chave,
        0
    )

    linhas.append(
        f"{emoji} **{nome}: {valor}**"
    )

return linhas
```

# ============================================================

# FORMATAR PERÍCIAS

# ============================================================

def formatar_pericias(ficha):

```
linhas = []

for chave in ORDEM_PERICIAS:

    emoji, nome = PERICIAS[chave]

    valor = ficha.get(
        chave,
        0
    )

    linhas.append(
        f"{emoji} {nome}: **{valor}**"
    )

return linhas
```

# ============================================================

# CRIAR PÁGINA DE STATUS

# ============================================================

def criar_pagina_status(ficha, jogador=None):

```
nome = ficha.get(
    "nome",
    "Sem nome"
)

hp_atual = ficha.get(
    "hp_atual",
    0
)

hp_max = ficha.get(
    "hp_max",
    0
)

mana_atual = ficha.get(
    "mana_atual",
    0
)

mana_max = ficha.get(
    "mana_max",
    0
)

xp = ficha.get(
    "xp",
    0
)

rc = calcular_rc(
    ficha
)

embed = discord.Embed(
    title=f"📜 FICHA DE {nome.upper()}",
    color=discord.Color.dark_red()
)

# ========================================================
# STATUS
# ========================================================

embed.add_field(
    name="❤️ STATUS",
    value=(
        f"❤️ HP: **{hp_atual}/{hp_max}**\n"
        f"🔵 Mana: **{mana_atual}/{mana_max}**\n"
        f"✨ XP: **{xp}**\n"
        f"⚡ RC: **{rc}**"
    ),
    inline=False
)

# ========================================================
# ATRIBUTOS — DUAS COLUNAS
# ========================================================

atributos = []

for chave in ATRIBUTOS:

    emoji, nome_atributo = ATRIBUTOS[chave]

    valor = ficha.get(
        chave,
        0
    )

    atributos.append(
        f"{emoji} **{nome_atributo}: {valor}**"
    )

# Divide os 6 atributos em 2 colunas,
# mantendo a ordem original.
metade = len(atributos) // 2

coluna_1 = atributos[:metade]
coluna_2 = atributos[metade:]

embed.add_field(
    name="📊 ATRIBUTOS",
    value="\n".join(coluna_1),
    inline=True
)

embed.add_field(
    name=" ",
    value="\n".join(coluna_2),
    inline=True
)

# ========================================================
# RODAPÉ
# ========================================================

if jogador is not None:

    embed.set_footer(
        text=(
            f"Jogador: {jogador.display_name}"
            " • Página 1/2 • Status e Atributos"
        )
    )

else:

    embed.set_footer(
        text="Página 1/2 • Status e Atributos"
    )

return embed
```

# ============================================================

# CRIAR PÁGINA DE PERÍCIAS

# ============================================================

def criar_pagina_pericias(ficha, jogador=None):

```
nome = ficha.get(
    "nome",
    "Sem nome"
)

embed = discord.Embed(
    title=f"📜 FICHA DE {nome.upper()}",
    color=discord.Color.dark_red()
)

linhas = formatar_pericias(
    ficha
)

# ========================================================
# DUAS COLUNAS
# ========================================================

metade = (
    len(linhas) + 1
) // 2

coluna_1 = linhas[:metade]
coluna_2 = linhas[metade:]

embed.add_field(
    name="📚 PERÍCIAS",
    value="\n".join(
        coluna_1
    ) if coluna_1 else "Nenhuma",
    inline=True
)

embed.add_field(
    name=" ",
    value="\n".join(
        coluna_2
    ) if coluna_2 else "Nenhuma",
    inline=True
)

# ========================================================
# RODAPÉ
# ========================================================

if jogador is not None:

    embed.set_footer(
        text=(
            f"Jogador: {jogador.display_name}"
            " • Página 2/2 • Perícias"
        )
    )

else:

    embed.set_footer(
        text="Página 2/2 • Perícias"
    )

return embed
```

# ============================================================

# VIEW DA FICHA

# ============================================================

class FichaView(discord.ui.View):

```
def __init__(
    self,
    ficha,
    jogador=None
):

    super().__init__(
        timeout=300
    )

    self.ficha = ficha
    self.jogador = jogador
    self.pagina = 1

    self.atualizar_botoes()


# ========================================================
# ATUALIZAR BOTÕES
# ========================================================

def atualizar_botoes(self):

    self.status_button.disabled = (
        self.pagina == 1
    )

    self.pericias_button.disabled = (
        self.pagina == 2
    )


# ========================================================
# BOTÃO STATUS
# ========================================================

@discord.ui.button(
    label="◀ Status",
    style=discord.ButtonStyle.secondary
)
async def status_button(
    self,
    interaction: discord.Interaction,
    button: discord.ui.Button
):

    self.pagina = 1

    self.atualizar_botoes()

    await interaction.response.edit_message(
        embed=criar_pagina_status(
            self.ficha,
            self.jogador
        ),
        view=self
    )


# ========================================================
# BOTÃO PERÍCIAS
# ========================================================

@discord.ui.button(
    label="Perícias ▶",
    style=discord.ButtonStyle.secondary
)
async def pericias_button(
    self,
    interaction: discord.Interaction,
    button: discord.ui.Button
):

    self.pagina = 2

    self.atualizar_botoes()

    await interaction.response.edit_message(
        embed=criar_pagina_pericias(
            self.ficha,
            self.jogador
        ),
        view=self
    )
```

# ============================================================

# VERIFICAR SE PODE ALTERAR FICHA

# ============================================================

def pode_alterar_ficha(
interaction,
ficha
):

```
if ficha is None:
    return False

# ========================================================
# ADMIN
# ========================================================

if (
    interaction.guild
    and interaction.user.guild_permissions.administrator
):
    return True

# ========================================================
# DONO DA FICHA
# ========================================================

if (
    ficha.get("dono_id")
    == interaction.user.id
):
    return True

# ========================================================
# MESTRE
# ========================================================

mestre_id = ficha.get(
    "mestre_id"
)

if (
    mestre_id is not None
    and mestre_id
    == interaction.user.id
):
    return True

return False
