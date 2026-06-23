# -*- coding: utf-8 -*-
"""Construção do PDF técnico com sumário, paginação, imagens e estatísticas."""

import os
import re
import unicodedata
from xml.sax.saxutils import escape

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image, KeepTogether, PageBreak, PageTemplate,
    Paragraph, Spacer, Table, TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

import pbix_parser


def _progresso(callback, mensagem, percentual):
    if not callback:
        return
    try:
        callback(mensagem, percentual)
    except TypeError:
        callback(mensagem)


class CanvasNumerado(canvas.Canvas):
    """Canvas que escreve Página X de Y após conhecer o total de páginas."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._paginas_salvas = []

    def showPage(self):
        self._paginas_salvas.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._paginas_salvas)
        for estado in self._paginas_salvas:
            self.__dict__.update(estado)
            self.setFont("Helvetica", 8)
            self.setFillColor(HexColor("#666666"))
            self.drawCentredString(A4[0] / 2, 0.8 * cm, f"Página {self._pageNumber} de {total}")
            super().showPage()
        super().save()


class DocumentoPDF(BaseDocTemplate):
    """Documento que registra automaticamente títulos no sumário."""

    def __init__(self, caminho, **kwargs):
        super().__init__(caminho, **kwargs)
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="conteudo")
        self.addPageTemplates(PageTemplate(id="padrao", frames=[frame]))
        self._indice_titulo = 0

    def beforeDocument(self):
        # multiBuild realiza mais de uma passagem; as chaves precisam ser idênticas em todas elas.
        self._indice_titulo = 0

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name == "Secao":
            self._indice_titulo += 1
            texto = flowable.getPlainText()
            chave = f"secao_{self._indice_titulo}"
            # bookmarkPage com fit='XYZ' e y=None ancora no topo atual da página,
            # garantindo que o sumário navegue para a posição correta.
            self.canv.bookmarkPage(chave, fit="XYZ", left=0, top=self.canv._y, zoom=0)
            self.canv.addOutlineEntry(texto, chave, level=0, closed=False)
            self.notify("TOCEntry", (0, texto, self.page, chave))


def _estilos(cor_primaria, cor_secundaria, cor_terciaria,
             tam_grande, tam_medio, tam_pequeno):
    primaria, secundaria, terciaria = map(HexColor, (cor_primaria, cor_secundaria, cor_terciaria))
    base = getSampleStyleSheet()
    return {
        "primaria": primaria, "secundaria": secundaria, "terciaria": terciaria,
        "titulo_capa": ParagraphStyle(
            "TituloCapa", parent=base["Title"], fontSize=tam_grande, leading=tam_grande * 1.15,
            textColor=primaria, spaceAfter=8, fontName="Helvetica-Bold", alignment=TA_CENTER),
        "subtitulo_capa": ParagraphStyle(
            "SubCapa", parent=base["Normal"], fontSize=tam_medio, leading=tam_medio * 1.2,
            textColor=secundaria, spaceAfter=4, alignment=TA_CENTER),
        "pequeno_capa": ParagraphStyle(
            "PequenoCapa", parent=base["Normal"], fontSize=tam_pequeno,
            textColor=colors.grey, alignment=TA_CENTER),
        "secao": ParagraphStyle(
            "Secao", parent=base["Heading1"], textColor=primaria, fontSize=18,
            leading=22, spaceBefore=8, spaceAfter=12, alignment=TA_CENTER),
        "titulo_sumario": ParagraphStyle(
            "TituloSumario", parent=base["Heading1"], textColor=primaria, fontSize=18,
            spaceAfter=14, alignment=TA_CENTER),
        "h2": ParagraphStyle(
            "H2", parent=base["Heading2"], textColor=secundaria, fontSize=13,
            spaceBefore=8, spaceAfter=6, alignment=TA_LEFT),
        "corpo": ParagraphStyle(
            "Corpo", parent=base["Normal"], fontSize=10, leading=14, alignment=TA_LEFT),
        "corpo_centro": ParagraphStyle(
            "CorpoCentro", parent=base["Normal"], fontSize=10, leading=14, alignment=TA_CENTER),
        "celula": ParagraphStyle(
            "Celula", parent=base["Normal"], fontSize=8.5, leading=11, alignment=TA_LEFT),
        "celula_id": ParagraphStyle(
            "CelulaId", parent=base["Normal"], fontSize=8.5, leading=11,
            alignment=TA_LEFT, textColor=secundaria, fontName="Helvetica-Bold"),
        "dax": ParagraphStyle(
            "DAX", parent=base["Code"], fontSize=8.5, leading=11,
            backColor=HexColor("#F5F0E6"), borderColor=terciaria,
            borderWidth=1, borderPadding=6, fontName="Courier"),
        "glossario_func": ParagraphStyle(
            "GlossarioFunc", parent=base["Normal"], fontSize=9, leading=12,
            fontName="Courier-Bold", textColor=terciaria),
        "glossario_desc": ParagraphStyle(
            "GlossarioDesc", parent=base["Normal"], fontSize=9, leading=12,
            leftIndent=12, textColor=HexColor("#444444")),
    }


def _tabela(dados, larguras, cor_cabecalho, cor_alternada="#F2F6F6"):
    tabela = Table(dados, colWidths=larguras, hAlign="CENTER", repeatRows=1)
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), cor_cabecalho),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, HexColor(cor_alternada)]),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#CCCCCC")),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("ALIGN", (0, 1), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
    ]))
    return tabela


def _imagem_ajustada(caminho, largura_max, altura_max):
    with PILImage.open(caminho) as imagem:
        largura, altura = imagem.size
    escala = min(largura_max / largura, altura_max / altura, 1.0)
    elemento = Image(caminho, width=largura * escala, height=altura * escala)
    elemento.hAlign = "CENTER"
    return elemento


def _normalizar_nome(texto):
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]", "", texto.lower())


_GLOSSARIO_DAX = {
    "CALCULATE": "Avalia uma expressão modificando o contexto de filtro.",
    "CALCULATETABLE": "Retorna uma tabela avaliada em um contexto de filtro modificado.",
    "SUMX": "Itera uma tabela e soma o resultado de uma expressão por linha.",
    "AVERAGEX": "Itera uma tabela e calcula a média de uma expressão por linha.",
    "COUNTX": "Itera uma tabela e conta linhas onde a expressão não é em branco.",
    "MAXX": "Retorna o valor máximo de uma expressão avaliada linha a linha.",
    "MINX": "Retorna o valor mínimo de uma expressão avaliada linha a linha.",
    "FILTER": "Retorna uma tabela filtrada com base em uma condição.",
    "ALL": "Remove filtros de uma tabela ou coluna, retornando todos os valores.",
    "ALLEXCEPT": "Remove todos os filtros exceto os das colunas especificadas.",
    "ALLSELECTED": "Remove filtros internos preservando os filtros externos do relatório.",
    "VALUES": "Retorna os valores distintos de uma coluna como tabela de uma coluna.",
    "DISTINCT": "Retorna os valores distintos de uma coluna ou tabela.",
    "RELATED": "Retorna um valor de uma tabela relacionada (lado 1 do relacionamento).",
    "RELATEDTABLE": "Retorna as linhas relacionadas de outra tabela.",
    "DIVIDE": "Realiza divisão segura, retornando um valor alternativo em caso de divisão por zero.",
    "IF": "Avalia uma condição e retorna um valor para verdadeiro e outro para falso.",
    "SWITCH": "Avalia uma expressão e retorna o resultado correspondente entre vários casos.",
    "COALESCE": "Retorna o primeiro argumento que não é BLANK.",
    "BLANK": "Retorna um valor em branco (equivalente ao nulo do DAX).",
    "ISBLANK": "Verifica se um valor é BLANK.",
    "SUM": "Soma todos os valores de uma coluna.",
    "AVERAGE": "Calcula a média de todos os valores de uma coluna.",
    "COUNT": "Conta o número de linhas com valores não vazios em uma coluna.",
    "COUNTA": "Conta o número de linhas não vazias em uma coluna.",
    "COUNTROWS": "Conta o número de linhas de uma tabela.",
    "COUNTBLANK": "Conta os valores em branco de uma coluna.",
    "DISTINCTCOUNT": "Conta o número de valores distintos em uma coluna.",
    "MAX": "Retorna o valor máximo de uma coluna.",
    "MIN": "Retorna o valor mínimo de uma coluna.",
    "TOTALYTD": "Calcula o valor acumulado no ano até a data atual do contexto.",
    "TOTALQTD": "Calcula o valor acumulado no trimestre até a data atual do contexto.",
    "TOTALMTD": "Calcula o valor acumulado no mês até a data atual do contexto.",
    "DATESYTD": "Retorna um conjunto de datas desde o início do ano até a data atual.",
    "DATESBETWEEN": "Retorna datas entre um intervalo especificado.",
    "DATEADD": "Desloca um conjunto de datas por um número de intervalos.",
    "SAMEPERIODLASTYEAR": "Retorna datas correspondentes ao mesmo período do ano anterior.",
    "PREVIOUSMONTH": "Retorna todas as datas do mês anterior.",
    "PREVIOUSYEAR": "Retorna todas as datas do ano anterior.",
    "USERELATIONSHIP": "Ativa um relacionamento inativo para uso dentro de CALCULATE.",
    "CROSSFILTER": "Define a direção de filtragem cruzada de um relacionamento.",
    "HASONEVALUE": "Retorna verdadeiro se uma coluna tiver exatamente um valor no contexto.",
    "HASONEFILTER": "Retorna verdadeiro se exatamente um filtro direto estiver ativo na coluna.",
    "SELECTEDVALUE": "Retorna o valor quando a coluna tem apenas um valor filtrado; caso contrário, retorna alternativo.",
    "CONCATENATE": "Concatena duas strings de texto.",
    "CONCATENATEX": "Concatena o resultado de uma expressão avaliada em cada linha de uma tabela.",
    "FORMAT": "Converte um valor em texto com um formato especificado.",
    "LEFT": "Retorna os N caracteres mais à esquerda de uma string.",
    "RIGHT": "Retorna os N caracteres mais à direita de uma string.",
    "MID": "Retorna uma substring a partir de uma posição com um comprimento definido.",
    "LEN": "Retorna o número de caracteres de uma string.",
    "UPPER": "Converte texto para maiúsculas.",
    "LOWER": "Converte texto para minúsculas.",
    "TRIM": "Remove espaços extras de uma string.",
    "SUBSTITUTE": "Substitui ocorrências de uma substring por outra.",
    "SEARCH": "Retorna a posição de uma substring (não diferencia maiúsculas/minúsculas).",
    "FIND": "Retorna a posição de uma substring (diferencia maiúsculas/minúsculas).",
    "RANKX": "Retorna o ranking de um valor em uma tabela.",
    "TOPN": "Retorna as N primeiras linhas de uma tabela com base em uma expressão.",
    "GENERATESERIES": "Retorna uma tabela com uma coluna de valores em série.",
    "ROW": "Retorna uma tabela de uma única linha com os valores especificados.",
    "DATATABLE": "Cria uma tabela inline com dados definidos manualmente.",
    "UNION": "Combina tabelas com as mesmas colunas empilhando as linhas.",
    "INTERSECT": "Retorna as linhas em comum entre duas tabelas.",
    "EXCEPT": "Retorna as linhas da primeira tabela que não existem na segunda.",
    "NATURALLEFTOUTERJOIN": "Realiza junção LEFT OUTER entre duas tabelas por colunas comuns.",
    "TREATAS": "Aplica os valores de uma tabela como filtro sobre colunas de outra tabela.",
    "VAR": "Declara uma variável para reutilizar em uma expressão DAX.",
    "RETURN": "Retorna o resultado final após declarações VAR.",
}


def _extrair_glossario(medidas):
    """Retorna lista de (função, descrição) das funções DAX usadas nas medidas, ordenada."""
    padrao = re.compile(r'\b([A-Z][A-Z0-9]+)\s*\(', re.MULTILINE)
    encontradas = set()
    for medida in medidas:
        for func in padrao.findall(medida.get("expressao", "").upper()):
            if func in _GLOSSARIO_DAX:
                encontradas.add(func)
    return sorted((f, _GLOSSARIO_DAX[f]) for f in encontradas)


def localizar_screenshots(paginas, pasta):
    """Associa imagens às páginas por nome do arquivo; usa ordem alfabética como fallback."""
    if not pasta or not os.path.isdir(pasta):
        return {}
    caminhos = sorted(
        os.path.join(pasta, nome) for nome in os.listdir(pasta)
        if os.path.splitext(nome)[1].lower() in {".png", ".jpg", ".jpeg"}
    )
    por_nome = {_normalizar_nome(os.path.splitext(os.path.basename(c))[0]): c for c in caminhos}
    usados, resultado = set(), {}
    for pagina in paginas:
        chave = _normalizar_nome(pagina["nome"])
        if chave in por_nome:
            resultado[pagina["nome"]] = por_nome[chave]
            usados.add(por_nome[chave])
    restantes = [c for c in caminhos if c not in usados]
    paginas_sem_imagem = [p for p in paginas if p["nome"] not in resultado]
    for pagina, caminho in zip(paginas_sem_imagem, restantes):
        resultado[pagina["nome"]] = caminho
    return resultado


_TRADUCAO_FILTRO = {
    "Single": "Único",
    "Both": "Ambos",
}


def _traduzir_filtro(valor):
    return _TRADUCAO_FILTRO.get(valor, valor)


def _eh_coluna_id(nome):
    return pbix_parser.eh_coluna_id(nome)


def gerar_pdf(dados, caminho_saida, nome_arquivo_pbix,
              cor_primaria="#1B3A5C", cor_secundaria="#2E8B8B",
              cor_terciaria="#E0A458", tam_titulo_grande=28,
              tam_titulo_medio=15, tam_titulo_pequeno=10,
              texto_grande=None, texto_medio=None, texto_pequeno=None,
              secoes=None, progresso=None, caminho_logo=None,
              pasta_screenshots=None, caminho_diagrama=None, aviso_diagrama=None):
    """Gera a documentação; os novos parâmetros são opcionais para preservar compatibilidade."""
    _progresso(progresso, "Montando PDF...", 84)
    texto_grande = texto_grande or "Documentação Técnica"
    texto_medio = texto_medio or nome_arquivo_pbix
    texto_pequeno = texto_pequeno or "Gerado automaticamente"
    secoes = list(secoes or (
        "resumo_geral", "visao_geral", "colunas", "relacionamentos", "medidas", "diagrama", "paginas"
    ))
    est = _estilos(cor_primaria, cor_secundaria, cor_terciaria,
                   tam_titulo_grande, tam_titulo_medio, tam_titulo_pequeno)
    story = [Spacer(1, 2.2 * cm)]
    if caminho_logo and os.path.isfile(caminho_logo):
        try:
            story.extend([_imagem_ajustada(caminho_logo, 7 * cm, 3.5 * cm), Spacer(1, 0.7 * cm)])
        except (OSError, ValueError):
            pass
    story.extend([
        Spacer(1, 1.5 * cm), Paragraph(escape(texto_grande), est["titulo_capa"]),
        Paragraph(escape(texto_medio), est["subtitulo_capa"]), Spacer(1, 0.3 * cm),
        Paragraph(escape(texto_pequeno), est["pequeno_capa"]), PageBreak(),
        Paragraph("Sumário", est["titulo_sumario"]),
    ])
    sumario = TableOfContents()
    sumario.levelStyles = [ParagraphStyle(
        "SumarioNivel1", fontName="Helvetica", fontSize=11, leading=18,
        leftIndent=0, firstLineIndent=0, textColor=est["primaria"],
    )]
    # Não adicionamos PageBreak aqui — nova_secao já cuida disso,
    # evitando a página em branco entre o sumário e a primeira seção.
    story.append(sumario)
    numero = 0

    def nova_secao(titulo):
        nonlocal numero
        numero += 1
        story.append(PageBreak())
        story.append(Paragraph(f"{numero}. {escape(titulo)}", est["secao"]))

    def kt(*elementos):
        """Agrupa elementos com KeepTogether para evitar órfãos (linha solitária no rodapé)."""
        return KeepTogether(list(elementos))

    if "resumo_geral" in secoes:
        _progresso(progresso, "Montando resumo geral...", 86)
        nova_secao("Resumo Geral")
        stats = dados.get("estatisticas", {})
        indicadores = [
            ["Indicador", "Quantidade"], ["Tabelas", stats.get("tabelas", 0)],
            ["Colunas", stats.get("colunas", 0)], ["Medidas", stats.get("medidas", 0)],
            ["Relacionamentos", stats.get("relacionamentos", 0)], ["Páginas", stats.get("paginas", 0)],
            ["Visuais", stats.get("visuais", 0)],
        ]
        story.append(kt(_tabela(indicadores, [10 * cm, 5 * cm], est["primaria"]), Spacer(1, 14)))
        categorias = [["Categoria", "Quantidade"]] + [
            [categoria, quantidade] for categoria, quantidade in stats.get("visuais_por_categoria", {}).items()
        ]
        story.append(kt(Paragraph("Visuais por categoria", est["h2"]),
                        _tabela(categorias, [10 * cm, 5 * cm], est["secundaria"])))
        tipos = stats.get("visuais_por_tipo", {})
        if tipos:
            story.append(kt(Spacer(1, 12), Paragraph("Visuais por tipo", est["h2"]),
                            _tabela([["Tipo", "Quantidade"]] + list(map(list, tipos.items())),
                                    [10 * cm, 5 * cm], est["terciaria"], "#FBF3E6")))

    if "visao_geral" in secoes or "colunas" in secoes:
        _progresso(progresso, "Montando modelo de dados...", 88)
        nova_secao("Modelo de Dados")
        if "visao_geral" in secoes:
            linhas = [["Tabela", "Qtde. de Colunas"]] + [
                [nome, len(colunas)] for nome, colunas in dados.get("tabelas", {}).items()
            ]
            story.append(kt(Paragraph("Visão geral das tabelas", est["h2"]),
                            _tabela(linhas, [10 * cm, 5 * cm], est["primaria"]), Spacer(1, 14)))
        if "colunas" in secoes:
            for nome, colunas in dados.get("tabelas", {}).items():
                linhas = [["Coluna", "Tipo de Dado"]]
                for nome_col, tipo in colunas:
                    estilo_col = est["celula_id"] if _eh_coluna_id(nome_col) else est["celula"]
                    linhas.append([
                        Paragraph(escape(nome_col), estilo_col),
                        Paragraph(escape(tipo), est["celula"]),
                    ])
                story.append(kt(Paragraph(escape(nome), est["h2"]),
                                _tabela(linhas, [9 * cm, 6 * cm], est["secundaria"]), Spacer(1, 10)))

    if "diagrama" in secoes:
        _progresso(progresso, "Inserindo diagrama do modelo...", 90)
        nova_secao("Diagrama do Modelo")
        if caminho_diagrama and os.path.isfile(caminho_diagrama):
            try:
                story.append(_imagem_ajustada(caminho_diagrama, 16.5 * cm, 21.5 * cm))
            except (OSError, ValueError) as erro:
                story.append(Paragraph(f"Não foi possível inserir o diagrama: {escape(str(erro))}", est["corpo"]))
        else:
            story.append(Paragraph(escape(aviso_diagrama or "Diagrama não disponível."), est["corpo"]))

    if "relacionamentos" in secoes:
        nova_secao("Relacionamentos")
        relacionamentos = dados.get("relacionamentos", [])
        if relacionamentos:
            linhas = [["Tabela Origem", "Tabela Destino", "Cardinalidade", "Direção do Filtro"]]
            for rel in relacionamentos:
                linhas.append([
                    Paragraph(escape(f"{rel['de_tabela']} ({rel['de_coluna']})"), est["celula"]),
                    Paragraph(escape(f"{rel['para_tabela']} ({rel['para_coluna']})"), est["celula"]),
                    rel["cardinalidade"], _traduzir_filtro(rel["filtro"]),
                ])
            story.append(_tabela(linhas, [5.3 * cm, 5.3 * cm, 2.3 * cm, 2.7 * cm], est["secundaria"]))
        else:
            story.append(Paragraph("Nenhum relacionamento encontrado no modelo.", est["corpo"]))

    if "medidas" in secoes:
        _progresso(progresso, "Montando medidas DAX...", 92)
        nova_secao("Medidas DAX")
        medidas = dados.get("medidas", [])
        if medidas:
            for medida in medidas:
                expressao = escape(medida["expressao"]).replace("\n", "<br/>")
                story.append(kt(
                    Paragraph(escape(f"{medida['nome']} ({medida['tabela']})"), est["h2"]),
                    Paragraph(expressao, est["dax"]),
                    Spacer(1, 8),
                ))
            # Glossário DAX automático em tabela
            glossario = _extrair_glossario(medidas)
            if glossario:
                story.append(Spacer(1, 16))
                linhas_gloss = [["Função", "Descrição"]]
                for func, desc in glossario:
                    linhas_gloss.append([
                        Paragraph(func, est["glossario_func"]),
                        Paragraph(desc, est["glossario_desc"]),
                    ])
                story.append(kt(
                    Paragraph("Glossário de Funções DAX Utilizadas", est["h2"]),
                    _tabela(linhas_gloss, [4 * cm, 11.6 * cm], est["terciaria"], "#FBF3E6"),
                ))
        else:
            story.append(Paragraph("Nenhuma medida DAX encontrada no modelo.", est["corpo"]))

    if "paginas" in secoes:
        _progresso(progresso, "Montando páginas do relatório...", 94)
        nova_secao("Páginas do Relatório")
        paginas = dados.get("paginas", [])
        screenshots = localizar_screenshots(paginas, pasta_screenshots)
        linhas = [["Página", "Qtde. de Visuais"]] + [[p["nome"], p["qtde_visuais"]] for p in paginas]
        story.append(kt(_tabela(linhas, [10 * cm, 5 * cm], est["terciaria"], "#FBF3E6"), Spacer(1, 14)))
        for pagina in paginas:
            # Mantém título e descrição juntos (evita órfão de título sozinho no rodapé)
            story.append(kt(
                Paragraph(escape(pagina["nome"]), est["h2"]),
                Paragraph(escape(pagina.get("descricao", "")), est["corpo"]),
                Spacer(1, 8),
            ))
            # Screenshot e tabela de visuais fluem livremente na sequência
            screenshot = screenshots.get(pagina["nome"])
            if screenshot:
                try:
                    story.extend([_imagem_ajustada(screenshot, 16 * cm, 10 * cm), Spacer(1, 10)])
                except (OSError, ValueError):
                    pass
            if pagina["visuais"]:
                linhas_visuais = [["Tipo de Visual", "Campos Utilizados"]]
                for visual in pagina["visuais"]:
                    campos = ", ".join(visual["campos"]) or "-"
                    linhas_visuais.append([
                        Paragraph(escape(visual["tipo"]), est["celula"]),
                        Paragraph(escape(campos), est["celula"]),
                    ])
                story.append(_tabela(linhas_visuais, [5.5 * cm, 9.5 * cm], est["terciaria"], "#FBF3E6"))
            else:
                story.append(Paragraph("Nenhum visual de dados nesta página.", est["corpo"]))
            story.append(Spacer(1, 16))
    _progresso(progresso, "Salvando...", 97)
    documento = DocumentoPDF(
        caminho_saida, pagesize=A4, topMargin=1.8 * cm, bottomMargin=1.5 * cm,
        leftMargin=2 * cm, rightMargin=2 * cm, title=f"Documentação - {nome_arquivo_pbix}",
        author="Documentador de PBIX 1.0",
    )
    documento.multiBuild(story, canvasmaker=CanvasNumerado)
    return caminho_saida
