# -*- coding: utf-8 -*-
"""Leitura do modelo e do layout de relatórios Power BI (.pbix)."""

from collections import Counter
import json
import re
import zipfile

from pbixray import PBIXRay


PREFIXOS_TABELAS_AUTOMATICAS = ("DateTableTemplate_", "LocalDateTable_")

ROTULOS_VISUAL = {
    "cardVisual": "Cartão", "card": "Cartão", "multiRowCard": "Cartão Múltiplo",
    "clusteredBarChart": "Gráfico de Barras Agrupadas",
    "clusteredColumnChart": "Gráfico de Colunas Agrupadas",
    "columnChart": "Gráfico de Colunas", "barChart": "Gráfico de Barras",
    "lineChart": "Gráfico de Linhas", "pieChart": "Gráfico de Pizza",
    "donutChart": "Gráfico de Rosca", "scatterChart": "Gráfico de Dispersão",
    "tableEx": "Tabela", "table": "Tabela", "pivotTable": "Matriz",
    "slicer": "Segmentação de Dados", "textbox": "Caixa de Texto",
    "map": "Mapa", "filledMap": "Mapa Coroplético", "gauge": "Medidor (Gauge)",
    "kpi": "Indicador (KPI)", "treemap": "Treemap",
    "waterfallChart": "Gráfico em Cascata", "funnel": "Funil",
    "ribbonChart": "Gráfico de Faixas", "shape": "Forma", "image": "Imagem",
}

ROTULOS_CARDINALIDADE = {"M:1": "N:1", "1:M": "1:N", "1:1": "1:1", "M:M": "N:N"}

TRADUCAO_TIPOS = {
    "Int64": "Inteiro", "Int32": "Inteiro", "int64": "Inteiro", "int32": "Inteiro",
    "Float64": "Decimal", "Float32": "Decimal", "float64": "Decimal",
    "decimal.Decimal": "Decimal", "string": "Texto", "str": "Texto", "object": "Texto",
    "datetime64[ns]": "Data/Hora", "datetime64": "Data/Hora", "date": "Data",
    "bool": "Verdadeiro/Falso", "boolean": "Verdadeiro/Falso",
}


def _progresso(callback, mensagem, percentual):
    """Aceita callbacks novos (mensagem, percentual) e antigos (mensagem)."""
    if not callback:
        return
    try:
        callback(mensagem, percentual)
    except TypeError:
        callback(mensagem)


def traduzir_tipo(tipo_interno):
    return TRADUCAO_TIPOS.get(tipo_interno, tipo_interno)


def rotulo_visual(tipo_interno):
    return ROTULOS_VISUAL.get(tipo_interno, tipo_interno)


def rotulo_cardinalidade(card_interna):
    return ROTULOS_CARDINALIDADE.get(card_interna, card_interna)


def eh_coluna_id(nome):
    texto = str(nome).strip()
    if not texto:
        return False

    texto_normalizado = re.sub(r"[\s\-]+", "_", texto)
    texto_lower = texto_normalizado.lower()
    if texto_lower.startswith("id_") or texto_lower == "id":
        return True
    if texto_lower.endswith("_id"):
        return True

    if re.match(r"(?i)^id(?=[A-Z0-9_])", texto_normalizado):
        return True
    if texto_lower.endswith("id") and (
        texto_normalizado.isupper()
        or "_" in texto_normalizado
        or sum(1 for caractere in texto_normalizado if caractere.isupper()) >= 2
    ):
        return True

    return False


def _categoria_visual(tipo):
    tipo = tipo.lower()
    if "cartão" in tipo or "indicador" in tipo or "medidor" in tipo:
        return "Cartões e indicadores"
    if "segmentação" in tipo:
        return "Segmentações"
    if "matriz" in tipo:
        return "Matrizes"
    if tipo == "tabela":
        return "Tabelas"
    if "mapa" in tipo:
        return "Mapas"
    if "gráfico" in tipo or tipo in {"treemap", "funil"}:
        return "Gráficos"
    return "Outros"


def _descricao_pagina(nome, visuais):
    if not visuais:
        return f"{nome}: não contém visuais de dados identificados."

    tipos = [v["tipo"] for v in visuais]
    campos = " ".join(c for v in visuais for c in v.get("campos", [])).lower()
    elementos = []
    if any(_categoria_visual(t) == "Cartões e indicadores" for t in tipos):
        elementos.append("indicadores de destaque")
    if any(_categoria_visual(t) == "Gráficos" for t in tipos):
        elementos.append("gráficos analíticos")
    if any(_categoria_visual(t) in {"Tabelas", "Matrizes"} for t in tipos):
        elementos.append("detalhamento tabular")
    if any(_categoria_visual(t) == "Mapas" for t in tipos):
        elementos.append("análises geográficas")
    if any(_categoria_visual(t) == "Segmentações" for t in tipos):
        elementos.append("filtros interativos")

    temas = []
    grupos = (
        (("fatur", "receita", "venda", "valor", "finance"), "resultados financeiros"),
        (("data", "ano", "mês", "mes", "período", "periodo"), "evolução temporal"),
        (("região", "regiao", "estado", "cidade", "país", "pais"), "desempenho por região"),
        (("cliente", "segmento"), "perfil de clientes"),
        (("produto", "categoria"), "desempenho de produtos"),
    )
    for palavras, rotulo in grupos:
        if any(palavra in campos for palavra in palavras):
            temas.append(rotulo)

    lista_elementos = ", ".join(elementos[:-1]) + (" e " + elementos[-1] if len(elementos) > 1 else elementos[0])
    finalidade = ", ".join(temas[:3]) if temas else "os principais dados e indicadores do relatório"
    return f"{nome}: contém {lista_elementos}, permitindo analisar {finalidade}."


def extrair_modelo(caminho_pbix, progresso=None):
    """Extrai tabelas, colunas, relacionamentos e medidas DAX."""
    _progresso(progresso, "Extraindo modelo...", 10)
    model = PBIXRay(caminho_pbix)
    schema = model.schema
    relacionamentos_df = model.relationships
    medidas_df = model.dax_measures

    tabelas_reais = [
        t for t in schema["TableName"].unique()
        if not str(t).startswith(PREFIXOS_TABELAS_AUTOMATICAS)
    ]
    tabelas = {}
    total = len(tabelas_reais)
    for indice, nome_tabela in enumerate(tabelas_reais, 1):
        percentual = 18 + int((indice / max(total, 1)) * 27)
        _progresso(progresso, f"Lendo tabela {indice} de {total}: {nome_tabela}", percentual)
        linhas = schema[schema["TableName"] == nome_tabela]
        tabelas[str(nome_tabela)] = [
            (str(row.ColumnName), traduzir_tipo(str(row.PandasDataType)))
            for row in linhas.itertuples(index=False)
        ]

    _progresso(progresso, "Lendo relacionamentos...", 48)
    relacionamentos = []
    if relacionamentos_df is not None and len(relacionamentos_df) > 0:
        for row in relacionamentos_df.itertuples(index=False):
            relacionamentos.append({
                "de_tabela": str(row.FromTableName), "de_coluna": str(row.FromColumnName),
                "para_tabela": str(row.ToTableName), "para_coluna": str(row.ToColumnName),
                "cardinalidade": rotulo_cardinalidade(str(row.Cardinality)),
                "filtro": str(row.CrossFilteringBehavior),
            })

    _progresso(progresso, "Lendo medidas...", 53)
    medidas = []
    if medidas_df is not None and len(medidas_df) > 0:
        for row in medidas_df.itertuples(index=False):
            expressao = str(row.Expression).strip() if row.Expression else ""
            medidas.append({"tabela": str(row.TableName), "nome": str(row.Name), "expressao": expressao})

    return {"tabelas": tabelas, "relacionamentos": relacionamentos, "medidas": medidas}


def extrair_paginas(caminho_pbix, progresso=None):
    """Extrai páginas, visuais, campos e descrições heurísticas do relatório."""
    _progresso(progresso, "Lendo layout do relatório...", 57)
    with zipfile.ZipFile(caminho_pbix) as arquivo_pbix:
        bruto = arquivo_pbix.read("Report/Layout")
    try:
        dados = json.loads(bruto.decode("utf-16"))
    except UnicodeDecodeError:
        dados = json.loads(bruto.decode("utf-8"))

    paginas = []
    secoes = dados.get("sections", [])
    total = len(secoes)
    for indice, secao in enumerate(secoes, 1):
        nome = secao.get("displayName") or secao.get("name", "Sem nome")
        percentual = 59 + int((indice / max(total, 1)) * 16)
        _progresso(progresso, f"Lendo página {indice} de {total}: {nome}", percentual)
        visuais = []
        for container in secao.get("visualContainers", []):
            try:
                config = json.loads(container.get("config", "{}"))
            except (json.JSONDecodeError, TypeError):
                continue
            visual = config.get("singleVisual", {})
            tipo_interno = visual.get("visualType", "desconhecido")
            if tipo_interno in {"textbox", "shape", "image"}:
                continue
            campos = []
            for itens in visual.get("projections", {}).values():
                for item in itens:
                    referencia = item.get("queryRef", "")
                    campo = referencia.split(".")[-1].rstrip(")")
                    if campo and campo not in campos:
                        campos.append(campo)
            visuais.append({
                "tipo": rotulo_visual(tipo_interno), "tipo_interno": tipo_interno, "campos": campos,
            })
        paginas.append({
            "nome": nome, "qtde_visuais": len(visuais), "visuais": visuais,
            "descricao": _descricao_pagina(nome, visuais),
        })
    return paginas


def calcular_estatisticas(tabelas, relacionamentos, medidas, paginas):
    """Consolida os indicadores gerais do modelo e do relatório."""
    tipos = Counter(v["tipo"] for p in paginas for v in p.get("visuais", []))
    categorias = Counter(_categoria_visual(tipo) for tipo, quantidade in tipos.items() for _ in range(quantidade))
    return {
        "tabelas": len(tabelas),
        "colunas": sum(len(colunas) for colunas in tabelas.values()),
        "medidas": len(medidas),
        "relacionamentos": len(relacionamentos),
        "paginas": len(paginas),
        "visuais": sum(p.get("qtde_visuais", 0) for p in paginas),
        "visuais_por_tipo": dict(sorted(tipos.items())),
        "visuais_por_categoria": dict(sorted(categorias.items())),
    }


def extrair_tudo(caminho_pbix, secoes=None, progresso=None):
    """Extrai todos os dados mantendo compatibilidade com as versões anteriores."""
    _progresso(progresso, "Abrindo PBIX...", 2)
    secoes = set(secoes or (
        "resumo_geral", "visao_geral", "colunas", "relacionamentos", "medidas", "diagrama", "paginas"
    ))
    precisa_modelo = bool(secoes & {
        "resumo_geral", "visao_geral", "colunas", "relacionamentos", "medidas", "diagrama"
    })
    precisa_paginas = bool(secoes & {"resumo_geral", "paginas"})
    modelo = extrair_modelo(caminho_pbix, progresso) if precisa_modelo else {
        "tabelas": {}, "relacionamentos": [], "medidas": []
    }
    paginas = extrair_paginas(caminho_pbix, progresso) if precisa_paginas else []
    _progresso(progresso, "Calculando estatísticas...", 77)
    estatisticas = calcular_estatisticas(
        modelo["tabelas"], modelo["relacionamentos"], modelo["medidas"], paginas
    )
    return {**modelo, "paginas": paginas, "estatisticas": estatisticas}
