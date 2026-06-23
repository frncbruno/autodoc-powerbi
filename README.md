# 📄 Documentador de PBIX

Automatize a documentação técnica dos seus projetos Power BI em poucos segundos.

O **Documentador de PBIX** é uma aplicação desenvolvida em Python que lê arquivos `.pbix` e gera automaticamente um documento PDF completo contendo informações do modelo de dados, medidas DAX, relacionamentos, estatísticas, páginas do relatório e diagramas do modelo.

---

## ✨ Funcionalidades

- ✅ Extração automática do modelo de dados
- ✅ Geração de documentação em PDF
- ✅ Estatísticas gerais do relatório
- ✅ Listagem de tabelas e colunas
- ✅ Relacionamentos e cardinalidades
- ✅ Extração das medidas DAX
- ✅ Glossário automático das funções DAX utilizadas
- ✅ Diagrama do modelo
- ✅ Identificação das páginas e visuais do relatório
- ✅ Inclusão de screenshots das páginas
- ✅ Personalização de cores e identidade visual
- ✅ Configurações persistentes
- ✅ Interface gráfica simples e intuitiva
- ✅ Geração da documentação em menos de 1 minuto

---

## 📸 O que é documentado?

### 📊 Resumo Geral

- Quantidade de tabelas
- Quantidade de colunas
- Quantidade de medidas
- Quantidade de relacionamentos
- Quantidade de páginas
- Quantidade e categorias dos visuais

### 🗂 Modelo de Dados

- Visão geral das tabelas
- Colunas e tipos de dados

### 🔗 Relacionamentos

- Tabela origem e destino
- Cardinalidade
- Direção do filtro

### 🧮 Medidas DAX

- Nome da medida
- Expressão DAX
- Glossário das funções utilizadas

### 📈 Diagrama do Modelo

- Representação visual dos relacionamentos entre tabelas

### 📑 Páginas do Relatório

- Quantidade de visuais por página
- Descrição automática das páginas
- Capturas de tela do relatório

---

## 🖥 Interface

O aplicativo permite:

- Selecionar um arquivo `.pbix`
- Escolher um logotipo para a capa
- Adicionar screenshots das páginas
- Personalizar as cores do documento
- Alterar tamanhos dos títulos
- Definir textos personalizados para a capa
- Selecionar quais seções serão incluídas no PDF

---

## 🚀 Tecnologias Utilizadas

- Python
- Tkinter
- PBIXRay
- ReportLab
- Graphviz
- Pillow

---

## 📦 Instalação

Clone o repositório:

```bash
git clone https://github.com/seu-usuario/documentador-pbix.git
cd documentador-pbix
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

Execute o programa:

```bash
python app.py
```

---

## ⚡ Ganho de Produtividade

| Processo | Tempo Médio |
|------------|-----------|
| Documentação manual | 30 min a 1 hora |
| Documentação automática | < 1 minuto |

### 🚀 Mais de 95% de redução no tempo gasto com documentação.

---

## 📄 Exemplo de Estrutura do PDF

```
1. Resumo Geral
2. Modelo de Dados
3. Diagrama do Modelo
4. Relacionamentos
5. Medidas DAX
6. Páginas do Relatório
```

O documento é gerado com:

- Sumário automático
- Paginação
- Cores personalizadas
- Logo na capa
- Tabelas formatadas
- Diagramas do modelo
- Screenshots das páginas

---

## 🎯 Objetivo

Eliminar o trabalho manual de documentação de projetos Power BI, tornando a criação de documentação técnica rápida, padronizada e automatizada, permitindo que analistas e desenvolvedores foquem no que realmente importa: gerar valor através dos dados.

---

## 📷 Exemplo

<p align="center">
  <img src="images/interface.png" width="700">
</p>

---

## 📜 Licença

Este projeto é distribuído sob a licença MIT.

---

⭐ Se este projeto foi útil para você, considere deixar uma estrela no repositório!