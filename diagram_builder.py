# -*- coding: utf-8 -*-
"""Geração do diagrama de relacionamentos com Graphviz ou fallback em Python puro."""

import os
import re
import math
import shutil
from PIL import Image as PILImage
from PIL import ImageDraw, ImageFont

import pbix_parser

try:
    from graphviz import Digraph
    from graphviz.backend import ExecutableNotFound
except ImportError:  # pragma: no cover - depende do ambiente local
    Digraph = None

    class ExecutableNotFound(Exception):
        pass


def _id_seguro(nome, indice):
    return f"t{indice}_{re.sub(r'[^a-zA-Z0-9_]', '_', nome)}"


def _localizar_graphviz():
    """Atualiza o PATH do processo quando o Graphviz foi instalado após o app ser aberto."""
    encontrado = shutil.which("dot")
    if encontrado:
        return encontrado

    candidatos = [
        os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "Graphviz", "bin"),
        os.path.join(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"), "Graphviz", "bin"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Graphviz", "bin"),
    ]
    for pasta in candidatos:
        executavel = os.path.join(pasta, "dot.exe")
        if os.path.isfile(executavel):
            os.environ["PATH"] = pasta + os.pathsep + os.environ.get("PATH", "")
            return executavel
    return None


def _fonte(tamanho, negrito=False):
    candidatos = []
    if os.name == "nt":
        candidatos.extend([
            r"C:\Windows\Fonts\segoeuib.ttf" if negrito else r"C:\Windows\Fonts\segoeui.ttf",
            r"C:\Windows\Fonts\arialbd.ttf" if negrito else r"C:\Windows\Fonts\arial.ttf",
        ])
    candidatos.extend([
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if negrito else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if negrito else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ])
    for caminho in candidatos:
        if caminho and os.path.isfile(caminho):
            try:
                return ImageFont.truetype(caminho, tamanho)
            except OSError:
                pass
    return ImageFont.load_default()


def _medir_texto(desenho, texto, fonte):
    caixa = desenho.textbbox((0, 0), texto, font=fonte)
    return caixa[2] - caixa[0], caixa[3] - caixa[1]


def _quebrar_linhas(desenho, texto, fonte, largura_maxima):
    palavras = str(texto).split()
    if not palavras:
        return [""]
    linhas, atual = [], ""
    for palavra in palavras:
        candidato = palavra if not atual else f"{atual} {palavra}"
        if _medir_texto(desenho, candidato, fonte)[0] <= largura_maxima:
            atual = candidato
        else:
            if atual:
                linhas.append(atual)
            atual = palavra
    if atual:
        linhas.append(atual)
    return linhas or [str(texto)]


def _desenhar_seta(desenho, origem, destino, cor, largura=2, tamanho_ponta=10,
                   rotulo="", fonte_rotulo=None):
    desenho.line([origem, destino], fill=cor, width=largura)
    dx = destino[0] - origem[0]
    dy = destino[1] - origem[1]
    angulo = math.atan2(dy, dx)
    a1 = angulo + math.pi / 7
    a2 = angulo - math.pi / 7
    p1 = (destino[0] - tamanho_ponta * math.cos(a1), destino[1] - tamanho_ponta * math.sin(a1))
    p2 = (destino[0] - tamanho_ponta * math.cos(a2), destino[1] - tamanho_ponta * math.sin(a2))
    desenho.polygon([destino, p1, p2], fill=cor)
    if rotulo and fonte_rotulo:
        mx = (origem[0] + destino[0]) / 2
        my = (origem[1] + destino[1]) / 2
        lw, lh = _medir_texto(desenho, rotulo, fonte_rotulo)
        px, py = mx - lw / 2, my - lh - 3
        desenho.rectangle([px - 3, py - 1, px + lw + 3, py + lh + 1], fill="white")
        desenho.text((px, py), rotulo, fill=cor, font=fonte_rotulo)


def _gerar_diagrama_fallback(dados, caminho_png, cor_primaria, cor_secundaria):
    tabelas = list(dados.get("tabelas", {}).items())
    if not tabelas:
        return None

    tabela_largura = 340
    tabela_altura = 220
    margem = 30
    espacamento_x = 40
    espacamento_y = 40
    quantidade = len(tabelas)
    colunas = min(4, max(1, math.ceil(math.sqrt(quantidade))))
    linhas = math.ceil(quantidade / colunas)
    largura = margem * 2 + colunas * tabela_largura + (colunas - 1) * espacamento_x
    altura = margem * 2 + linhas * tabela_altura + (linhas - 1) * espacamento_y

    imagem = PILImage.new("RGB", (largura, altura), "white")
    desenho = ImageDraw.Draw(imagem)

    fonte_titulo = _fonte(16, negrito=True)
    fonte_coluna = _fonte(12, negrito=False)
    fonte_rotulo = _fonte(11, negrito=True)

    posicoes = {}
    for indice, (nome, _colunas_tabela) in enumerate(tabelas):
        linha = indice // colunas
        coluna = indice % colunas
        x = margem + coluna * (tabela_largura + espacamento_x)
        y = margem + linha * (tabela_altura + espacamento_y)
        posicoes[nome] = (x, y)

    cor_borda = "#AAB7C4"
    cor_fundo_cabecalho = cor_primaria
    cor_texto_cabecalho = "white"
    cor_linhas = cor_secundaria

    for rel in dados.get("relacionamentos", []):
        pos_o = posicoes.get(rel.get("de_tabela"))
        pos_d = posicoes.get(rel.get("para_tabela"))
        if not pos_o or not pos_d:
            continue
        # Centros de cada tabela
        cx_o = pos_o[0] + tabela_largura / 2
        cy_o = pos_o[1] + tabela_altura / 2
        cx_d = pos_d[0] + tabela_largura / 2
        cy_d = pos_d[1] + tabela_altura / 2
        dx_c = cx_d - cx_o
        dy_c = cy_d - cy_o
        # Escolhe o lado de saída e entrada com base na direção entre os centros
        if abs(dx_c) >= abs(dy_c):
            # Predominantemente horizontal
            if dx_c >= 0:
                ox, oy = pos_o[0] + tabela_largura, cy_o
                ex, ey = pos_d[0], cy_d
            else:
                ox, oy = pos_o[0], cy_o
                ex, ey = pos_d[0] + tabela_largura, cy_d
        else:
            # Predominantemente vertical
            if dy_c >= 0:
                ox, oy = cx_o, pos_o[1] + tabela_altura
                ex, ey = cx_d, pos_d[1]
            else:
                ox, oy = cx_o, pos_o[1]
                ex, ey = cx_d, pos_d[1] + tabela_altura
        cardinalidade = rel.get("cardinalidade", "")
        _desenhar_seta(desenho, (ox, oy), (ex, ey), cor_linhas, largura=2,
                       tamanho_ponta=9, rotulo=cardinalidade, fonte_rotulo=fonte_rotulo)

    for nome, colunas_tabela in tabelas:
        x, y = posicoes[nome]
        desenho.rounded_rectangle(
            [x, y, x + tabela_largura, y + tabela_altura],
            radius=12,
            outline=cor_borda,
            width=2,
            fill="white",
        )
        desenho.rounded_rectangle(
            [x, y, x + tabela_largura, y + 34],
            radius=12,
            outline=cor_fundo_cabecalho,
            width=1,
            fill=cor_fundo_cabecalho,
        )
        desenho.rectangle([x, y + 16, x + tabela_largura, y + 34], fill=cor_fundo_cabecalho)

        titulo = _quebrar_linhas(desenho, nome, fonte_titulo, tabela_largura - 24)
        altura_titulo = sum(_medir_texto(desenho, linha, fonte_titulo)[1] + 1 for linha in titulo)
        inicio_y = y + max(7, (34 - altura_titulo) // 2)
        for linha in titulo:
            largura_texto, altura_texto = _medir_texto(desenho, linha, fonte_titulo)
            desenho.text((x + (tabela_largura - largura_texto) / 2, inicio_y), linha, fill=cor_texto_cabecalho, font=fonte_titulo)
            inicio_y += altura_texto + 1

        linhas = []
        limite = 10
        for nome_coluna, tipo in colunas_tabela[:limite]:
            linhas.append(f"{nome_coluna} ({tipo})")
        if len(colunas_tabela) > limite:
            linhas.append(f"+ {len(colunas_tabela) - limite} colunas")

        conteudo_y = y + 46
        conteudo_x = x + 12
        largura_conteudo = tabela_largura - 24
        altura_linha = 16
        for linha in linhas:
            nome_col = linha.split(" (")[0]
            eh_id = pbix_parser.eh_coluna_id(nome_col)
            cor_texto = cor_secundaria if eh_id else "#333333"
            pedaços = _quebrar_linhas(desenho, linha, fonte_coluna, largura_conteudo)
            for pedaço in pedaços:
                if conteudo_y + altura_linha > y + tabela_altura - 12:
                    break
                desenho.text((conteudo_x, conteudo_y), pedaço, fill=cor_texto, font=fonte_coluna)
                conteudo_y += altura_linha
            if conteudo_y + altura_linha > y + tabela_altura - 12:
                break

        desenho.line([x, y + 34, x + tabela_largura, y + 34], fill=cor_borda, width=1)

    imagem.save(caminho_png)
    return caminho_png


def gerar_diagrama(dados, diretorio_saida, cor_primaria="#1B3A5C",
                   cor_secundaria="#2E8B8B", progresso=None):
    """Retorna ``(caminho_png, aviso)``. O aviso é preenchido se o Graphviz não estiver disponível."""
    if progresso:
        progresso("Gerando diagrama do modelo...", 81)
    tabelas = dados.get("tabelas", {})
    if not tabelas:
        return None, "Não há tabelas para montar o diagrama."

    os.makedirs(diretorio_saida, exist_ok=True)
    base = os.path.join(diretorio_saida, "diagrama_modelo")
    if Digraph is not None:
        _localizar_graphviz()
        grafo = Digraph("modelo", format="png")
        grafo.attr(rankdir="LR", bgcolor="white", pad="0.25", nodesep="0.45", ranksep="0.8")
        grafo.attr("node", shape="plain", fontname="Helvetica")
        grafo.attr("edge", fontname="Helvetica", fontsize="9", color=cor_secundaria)

        ids = {}
        for indice, (tabela, colunas) in enumerate(tabelas.items(), 1):
            identificador = _id_seguro(tabela, indice)
            ids[tabela] = identificador
            linhas = [
                f'<TR><TD BGCOLOR="{cor_primaria}"><FONT COLOR="white"><B>{_html(tabela)}</B></FONT></TD></TR>'
            ]
            for nome, tipo in colunas[:12]:
                if pbix_parser.eh_coluna_id(nome):
                    nome_html = f'<FONT COLOR="{cor_secundaria}"><B>{_html(nome)}</B></FONT>'
                else:
                    nome_html = _html(nome)
                linhas.append(f'<TR><TD ALIGN="LEFT">{nome_html} <FONT COLOR="#777777">({_html(tipo)})</FONT></TD></TR>')
            if len(colunas) > 12:
                linhas.append(f'<TR><TD ALIGN="LEFT"><I>+ {len(colunas) - 12} colunas</I></TD></TR>')
            label = f'<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="5">{"".join(linhas)}</TABLE>>'
            grafo.node(identificador, label=label)

        for rel in dados.get("relacionamentos", []):
            origem = ids.get(rel["de_tabela"])
            destino = ids.get(rel["para_tabela"])
            if origem and destino:
                rotulo = f'{rel["de_coluna"]}  {rel["cardinalidade"]}  {rel["para_coluna"]}'
                grafo.edge(origem, destino, label=rotulo)

        try:
            return grafo.render(filename=base, cleanup=True), None
        except (ExecutableNotFound, OSError):
            pass

    caminho_png = base + ".png"
    resultado = _gerar_diagrama_fallback(dados, caminho_png, cor_primaria, cor_secundaria)
    if resultado:
        return resultado, "Graphviz não estava disponível; o diagrama foi gerado em modo alternativo."
    return None, "Não há dados suficientes para montar o diagrama."


def _html(texto):
    return str(texto).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
