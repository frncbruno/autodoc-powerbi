# Documentador de PBIX 1.0 — Instruções de uso

## Baixando o programa

1. Acesse o link do Drive [clicando aqui](https://drive.google.com/file/d/1MYiRkUvUYx9yP7Bu23SBWDcnl82clc-u/view?usp=sharing)
2. Baixe o arquivo `DocumentadorPBIX.exe`
3. Salve em qualquer pasta do seu computador (ex: `Documentos`)

> Não é necessário instalar nada. Basta baixar e abrir o `.exe`.

---

## Usando o programa

### 1. Selecionar o arquivo .pbix

Clique em **"Selecionar arquivo..."** e escolha o arquivo `.pbix` que deseja documentar.

### 2. Identidade visual (opcional)

- **Logotipo da capa:** adicione a logo da empresa em formato `.png` ou `.jpg`
- **Pasta de screenshots:** se quiser incluir prints das páginas do relatório no PDF, selecione a pasta onde eles estão salvos

### 3. Cores do documento (opcional)

Personalize as cores do PDF digitando os códigos hexadecimais (ex: `#1B3A5C`).
As cores padrão já seguem a identidade visual da empresa.

### 4. Textos da capa (opcional)

Preencha os campos de texto grande, médio e pequeno para personalizar a capa do PDF.
Se deixar em branco, o programa usa valores padrão automaticamente.

### 5. Seções incluídas no PDF

Marque ou desmarque as seções que deseja incluir na documentação:

- **Resumo geral e estatísticas** — visão macro do modelo
- **Visão geral das tabelas** — lista de tabelas e quantidade de colunas
- **Colunas por tabela** — detalhamento de cada coluna e seu tipo de dado
- **Relacionamentos** — como as tabelas se conectam entre si
- **Medidas DAX** — todas as medidas criadas no modelo
- **Diagrama do modelo** — diagrama visual de relacionamentos
- **Páginas, visuais e screenshots** — lista de páginas e visuais do relatório

### 6. Gerar a documentação

Clique em **"Gerar Documentação (PDF)"**, escolha onde salvar e aguarde.
O PDF abre automaticamente ao finalizar.

---

## Dicas

- As configurações de cores e tamanhos são salvas automaticamente entre sessões
- O botão **"Abrir Pasta"** abre a pasta onde o PDF foi salvo
- Para documentar vários relatórios, basta trocar o arquivo `.pbix` e gerar novamente

---

## Diagrama de relacionamentos

O diagrama é gerado automaticamente. Para uma qualidade visual melhor, instale o **Graphviz**:

1. Acesse https://graphviz.org/download/ e baixe o instalador para Windows
2. Durante a instalação, marque ✅ **"Add Graphviz to the system PATH for all users"**
3. Reinicie o programa após instalar

Sem o Graphviz, o diagrama ainda é gerado normalmente, só com um layout mais simples.

---

## Problemas comuns

**O antivírus bloqueou o .exe**
Falso positivo comum com programas gerados em Python. Clique em "Mais informações" → "Executar assim mesmo", ou adicione uma exceção no antivírus.

**O programa demorou para abrir**
Normal na primeira execução. A partir da segunda abre mais rápido.

**Erro ao processar o .pbix**
Certifique-se de que o arquivo não está aberto no Power BI Desktop durante a geração.
