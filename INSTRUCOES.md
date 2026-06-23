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

## Graphviz (opcional — melhora o diagrama de relacionamentos)

O app funciona sem o Graphviz, mas o diagrama gerado fica mais bonito e organizado com ele instalado.

### Instalando o Graphviz no Windows

1. Acesse https://graphviz.org/download/
2. Em **Windows**, baixe o instalador `.exe` (ex: `windows_10_cmake_Release_graphviz-install-x.xx.x-win64.exe`)
3. Execute o instalador
4. Na tela **"Select Additional Tasks"**, marque a opção:
   - ✅ **Add Graphviz to the system PATH for all users**
   - (ou "for current user", qualquer uma serve)
5. Conclua a instalação

### Verificando se funcionou

Abra o Prompt de Comando (`Win + R` → digite `cmd` → Enter) e execute:

```
dot -version
```

Se aparecer a versão do Graphviz, está tudo certo. O app vai detectá-lo automaticamente.

> **Sem o Graphviz:** o diagrama é gerado em modo alternativo (Pillow puro), funcionando, mas com layout mais simples.

---

## Observações

- O EXE foi compilado para Windows 64-bit. Computadores com Windows 32-bit
  precisarão de build separado (raro atualmente).

- Se o antivírus bloquear o `.exe`, é falso positivo comum com PyInstaller.
  Adicione uma exceção ou use a opção "Executar assim mesmo".
