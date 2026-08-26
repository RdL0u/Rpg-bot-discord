import random


# ============================================================
# ROLAR 1D10
# ============================================================

def rolar_d10():

    return random.randint(
        1,
        10
    )


# ============================================================
# ROLAR 2D10
# ============================================================

def rolar_2d10():

    dado_1 = rolar_d10()
    dado_2 = rolar_d10()

    return (
        dado_1,
        dado_2
    )


# ============================================================
# CALCULAR MODIFICADOR
# ATRIBUTO + PERÍCIA
# ============================================================

def calcular_modificador(
    valor_atributo,
    valor_pericia
):

    return (
        valor_atributo
        + valor_pericia
    )


# ============================================================
# REALIZAR ROLAGEM COMPLETA
#
# 2D10 + ATRIBUTO + PERÍCIA
# ============================================================

def realizar_rolagem(
    valor_atributo,
    valor_pericia
):

    # ========================================================
    # GARANTIR VALORES INTEIROS
    # ========================================================

    valor_atributo = int(
        valor_atributo
        or 0
    )

    valor_pericia = int(
        valor_pericia
        or 0
    )

    # ========================================================
    # ROLAR DADOS
    # ========================================================

    dado_1, dado_2 = rolar_2d10()

    # ========================================================
    # MODIFICADOR
    # ========================================================

    modificador = calcular_modificador(
        valor_atributo,
        valor_pericia
    )

    # ========================================================
    # RESULTADO FINAL
    # ========================================================

    resultado = (
        dado_1
        + dado_2
        + modificador
    )

    # ========================================================
    # RETORNO
    # ========================================================

    return {
        "dado_1": dado_1,
        "dado_2": dado_2,
        "valor_atributo": valor_atributo,
        "valor_pericia": valor_pericia,
        "modificador": modificador,
        "resultado": resultado,
    }


# ============================================================
# FORMATAR ROLAGEM
# ============================================================

def formatar_rolagem(
    nome_jogador,
    nome_atributo,
    emoji_atributo,
    nome_pericia,
    emoji_pericia,
    dados_rolagem
):

    # ========================================================
    # DADOS
    # ========================================================

    dado_1 = dados_rolagem[
        "dado_1"
    ]

    dado_2 = dados_rolagem[
        "dado_2"
    ]

    valor_atributo = dados_rolagem[
        "valor_atributo"
    ]

    valor_pericia = dados_rolagem[
        "valor_pericia"
    ]

    modificador = dados_rolagem[
        "modificador"
    ]

    resultado = dados_rolagem[
        "resultado"
    ]

    # ========================================================
    # TEXTO FINAL
    # ========================================================

    return (
        f"🎲 **ROLAGEM — {nome_jogador}**\n\n"
        f"{emoji_atributo} {nome_atributo}: "
        f"**{valor_atributo}**\n"
        f"{emoji_pericia} {nome_pericia}: "
        f"**{valor_pericia}**\n\n"
        f"🎲 **{dado_1}** + "
        f"🎲 **{dado_2}** + "
        f"**{modificador}**\n\n"
        f"🏁 Resultado: **{resultado}**"
    )
