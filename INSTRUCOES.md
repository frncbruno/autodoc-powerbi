# Como gerar o DocumentadorPBIX.exe

## Pré-requisito único: Python 3.10 ou superior

1. Acesse https://www.python.org/downloads/
2. Baixe e instale o Python 3.10+ para Windows
3. **Marque a opção "Add Python to PATH"** durante a instalação

---

## Gerando o EXE (uma única vez)

1. Coloque todos os arquivos desta pasta em um local de sua preferência
2. Clique duas vezes em **`BUILD_EXE.bat`**
3. O script vai:
   - Instalar todas as dependências automaticamente
   - Gerar o `DocumentadorPBIX.exe` dentro da pasta `dist\`
4. A pasta `dist\` abrirá automaticamente ao final

**O processo leva entre 2 e 5 minutos** na primeira vez (baixa dependências e compila).

---

## Distribuindo para os colegas

Após o build, basta enviar o arquivo:

```
dist\DocumentadorPBIX.exe
```

Os colegas **não precisam ter Python instalado**. Basta baixar e executar o `.exe`.

---

## Observações

- O Graphviz é opcional. Se não estiver instalado no computador do usuário,
  o diagrama de relacionamentos será gerado em modo alternativo (Pillow puro),
  que funciona bem na maioria dos casos.

- O EXE foi compilado para Windows 64-bit. Computadores com Windows 32-bit
  precisarão de build separado (raro atualmente).

- Se o antivírus bloquear o `.exe`, é falso positivo comum com PyInstaller.
  Adicione uma exceção ou use a opção "Executar assim mesmo".
