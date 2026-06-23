# -*- coding: utf-8 -*-
"""Interface gráfica do Documentador de PBIX 1.0."""

import json
import os
import re
import tempfile
import threading
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, ttk

import diagram_builder
import pbix_parser
import pdf_builder


HEX_COR_REGEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
CONFIG_DIR = os.path.join(os.getenv("APPDATA") or os.path.expanduser("~"), "DocumentadorPBIX")
CONFIG_PATH = os.path.join(CONFIG_DIR, "perfil.json")

SECOES = {
    "resumo_geral": "Resumo geral e estatísticas",
    "visao_geral": "Visão geral das tabelas",
    "colunas": "Colunas por tabela",
    "relacionamentos": "Relacionamentos",
    "medidas": "Medidas DAX",
    "diagrama": "Diagrama do modelo",
    "paginas": "Páginas, visuais e screenshots",
}


class DocumentadorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Documentador de PBIX 1.0")
        self.geometry("720x900")
        self.minsize(650, 650)

        self.caminho_pbix = None
        self.caminho_logo = ""
        self.pasta_screenshots = ""
        self.ultimo_diretorio = ""
        self._ultima_pasta_saida = ""
        self.cores = {
            "primaria": tk.StringVar(value="#1B3A5C"),
            "secundaria": tk.StringVar(value="#2E8B8B"),
            "terciaria": tk.StringVar(value="#E0A458"),
        }
        self.tam_grande = tk.IntVar(value=28)
        self.tam_medio = tk.IntVar(value=15)
        self.tam_pequeno = tk.IntVar(value=10)
        self.texto_grande = tk.StringVar(value="")
        self.texto_medio = tk.StringVar(value="")
        self.texto_pequeno = tk.StringVar(value="")
        self.secoes = {chave: tk.BooleanVar(value=True) for chave in SECOES}

        self._carregar_perfil()
        # Seções 2 (identidade visual) e 5 (textos de capa) sempre começam zeradas
        self.caminho_logo = ""
        self.pasta_screenshots = ""
        self.texto_grande.set("")
        self.texto_medio.set("")
        self.texto_pequeno.set("")
        self._montar_interface()
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)

    def _montar_interface(self):
        cabecalho = tk.Frame(self)
        cabecalho.pack(fill="x")
        tk.Label(cabecalho, text="Documentador de PBIX 1.0",
                 font=("Segoe UI", 17, "bold")).pack(pady=(16, 3))
        tk.Label(cabecalho, text="Documentação técnica, estatísticas, diagrama e páginas do Power BI",
                 font=("Segoe UI", 9), fg="#555").pack(pady=(0, 8))

        area = tk.Frame(self)
        area.pack(fill="both", expand=True)
        canvas = tk.Canvas(area, highlightthickness=0)
        barra = ttk.Scrollbar(area, orient="vertical", command=canvas.yview)
        self.conteudo = tk.Frame(canvas)
        janela = canvas.create_window((0, 0), window=self.conteudo, anchor="nw")
        canvas.configure(yscrollcommand=barra.set)
        self.conteudo.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(janela, width=e.width))
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-e.delta / 120), "units"))
        canvas.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")

        pad = {"padx": 18, "pady": 7}
        arquivo = tk.LabelFrame(self.conteudo, text="1. Arquivo .pbix", padx=10, pady=10)
        arquivo.pack(fill="x", **pad)
        self.lbl_arquivo = tk.Label(arquivo, text="Nenhum arquivo selecionado", fg="#777", anchor="w")
        self.lbl_arquivo.pack(side="left", fill="x", expand=True)
        tk.Button(arquivo, text="Selecionar arquivo...", command=self._selecionar_arquivo).pack(side="right")

        imagens = tk.LabelFrame(self.conteudo, text="2. Identidade visual e screenshots", padx=10, pady=8)
        imagens.pack(fill="x", **pad)
        self.lbl_logo = self._linha_seletor(imagens, "Logotipo da capa", self._selecionar_logo, self._limpar_logo)
        self.lbl_screenshots = self._linha_seletor(
            imagens, "Pasta de screenshots", self._selecionar_screenshots, self._limpar_screenshots)
        self._atualizar_rotulos_imagens()

        cores = tk.LabelFrame(self.conteudo, text="3. Cores do documento", padx=10, pady=8)
        cores.pack(fill="x", **pad)
        self._linha_cor(cores, "Primária (títulos)", "primaria")
        self._linha_cor(cores, "Secundária (subtítulos)", "secundaria")
        self._linha_cor(cores, "Terciária (acentos/DAX)", "terciaria")

        tamanhos = tk.LabelFrame(self.conteudo, text="4. Tamanhos do texto da capa", padx=10, pady=8)
        tamanhos.pack(fill="x", **pad)
        self._linha_tamanho(tamanhos, "Título grande", self.tam_grande)
        self._linha_tamanho(tamanhos, "Título médio", self.tam_medio)
        self._linha_tamanho(tamanhos, "Título pequeno", self.tam_pequeno)

        textos = tk.LabelFrame(self.conteudo, text="5. Textos da capa (opcional)", padx=10, pady=8)
        textos.pack(fill="x", **pad)
        self._linha_texto(textos, "Texto grande", self.texto_grande, "padrão: Documentação Técnica")
        self._linha_texto(textos, "Texto médio", self.texto_medio, "padrão: nome do .pbix")
        self._linha_texto(textos, "Texto pequeno", self.texto_pequeno, "padrão: Gerado automaticamente")

        secoes = tk.LabelFrame(self.conteudo, text="6. Seções incluídas no PDF", padx=10, pady=8)
        secoes.pack(fill="x", **pad)
        for indice, (chave, rotulo) in enumerate(SECOES.items()):
            tk.Checkbutton(secoes, text=rotulo, variable=self.secoes[chave]).grid(
                row=indice // 2, column=indice % 2, sticky="w", padx=(0, 28), pady=3)

        rodape = tk.Frame(self, bd=1, relief="groove")
        rodape.pack(fill="x", side="bottom")
        self.lbl_status = tk.Label(rodape, text="Aguardando...", fg="#1B3A5C", font=("Segoe UI", 9))
        self.lbl_status.pack(pady=(8, 3))
        self.barra_progresso = ttk.Progressbar(rodape, mode="determinate", maximum=100, length=560)
        self.barra_progresso.pack(pady=(0, 7), padx=20, fill="x")
        botoes_rodape = tk.Frame(rodape)
        botoes_rodape.pack(pady=(0, 10))
        self.btn_gerar = tk.Button(
            botoes_rodape, text="Gerar Documentação (PDF)", font=("Segoe UI", 11, "bold"),
            bg="#1B3A5C", fg="white", padx=12, pady=9, command=self._gerar_documentacao)
        self.btn_gerar.pack(side="left", padx=(0, 8))
        self.btn_abrir_pasta = tk.Button(
            botoes_rodape, text="Abrir Pasta", font=("Segoe UI", 10),
            bg="#2E8B8B", fg="white", padx=10, pady=9,
            command=self._abrir_pasta_saida, state="disabled")
        self.btn_abrir_pasta.pack(side="left")

    def _linha_seletor(self, parent, rotulo, comando, limpar):
        linha = tk.Frame(parent)
        linha.pack(fill="x", pady=3)
        tk.Label(linha, text=rotulo, width=21, anchor="w").pack(side="left")
        etiqueta = tk.Label(linha, text="Não selecionado", fg="#777", anchor="w")
        etiqueta.pack(side="left", fill="x", expand=True, padx=5)
        tk.Button(linha, text="Selecionar...", command=comando).pack(side="left", padx=3)
        tk.Button(linha, text="Limpar", command=limpar).pack(side="left", padx=3)
        return etiqueta

    def _linha_cor(self, parent, rotulo, chave):
        linha = tk.Frame(parent)
        linha.pack(fill="x", pady=3)
        tk.Label(linha, text=rotulo, width=22, anchor="w").pack(side="left")
        amostra = tk.Label(linha, text="    ", bg=self.cores[chave].get(), relief="solid", borderwidth=1)
        amostra.pack(side="left", padx=6)
        entrada = tk.Entry(linha, textvariable=self.cores[chave], width=10)
        entrada.pack(side="left", padx=4)

        def atualizar(*_args):
            valor = self.cores[chave].get().strip()
            if valor and not valor.startswith("#"):
                valor = "#" + valor
            if HEX_COR_REGEX.match(valor):
                amostra.config(bg=valor)
                entrada.config(fg="#000000")
            else:
                entrada.config(fg="#CC0000")

        def escolher():
            atual = self.cores[chave].get().strip()
            resultado = colorchooser.askcolor(color=atual if HEX_COR_REGEX.match(atual) else None,
                                               title=f"Escolher cor {rotulo}")
            if resultado and resultado[1]:
                self.cores[chave].set(resultado[1])

        self.cores[chave].trace_add("write", atualizar)
        tk.Button(linha, text="Escolher cor...", command=escolher).pack(side="left", padx=6)

    @staticmethod
    def _linha_tamanho(parent, rotulo, variavel):
        linha = tk.Frame(parent)
        linha.pack(fill="x", pady=3)
        tk.Label(linha, text=rotulo, width=22, anchor="w").pack(side="left")
        tk.Spinbox(linha, from_=6, to=60, textvariable=variavel, width=6).pack(side="left")

    @staticmethod
    def _linha_texto(parent, rotulo, variavel, dica):
        linha = tk.Frame(parent)
        linha.pack(fill="x", pady=3)
        tk.Label(linha, text=rotulo, width=22, anchor="w").pack(side="left")
        tk.Entry(linha, textvariable=variavel, width=30).pack(side="left", padx=(0, 8))
        tk.Label(linha, text=dica, fg="#888", font=("Segoe UI", 8)).pack(side="left")

    def _selecionar_arquivo(self):
        caminho = filedialog.askopenfilename(
            title="Selecione o arquivo .pbix", filetypes=[("Arquivos Power BI", "*.pbix")],
            initialdir=self.ultimo_diretorio or None)
        if caminho:
            self.caminho_pbix = caminho
            self.ultimo_diretorio = os.path.dirname(caminho)
            self.lbl_arquivo.config(text=os.path.basename(caminho), fg="#000")

    def _selecionar_logo(self):
        caminho = filedialog.askopenfilename(
            title="Selecione o logotipo", filetypes=[("Imagens", "*.png *.jpg *.jpeg")],
            initialdir=self.ultimo_diretorio or None)
        if caminho:
            self.caminho_logo = caminho
            self._atualizar_rotulos_imagens()

    def _selecionar_screenshots(self):
        pasta = filedialog.askdirectory(title="Selecione a pasta de screenshots",
                                        initialdir=self.ultimo_diretorio or None)
        if pasta:
            self.pasta_screenshots = pasta
            self._atualizar_rotulos_imagens()

    def _limpar_logo(self):
        self.caminho_logo = ""
        self._atualizar_rotulos_imagens()

    def _limpar_screenshots(self):
        self.pasta_screenshots = ""
        self._atualizar_rotulos_imagens()

    def _atualizar_rotulos_imagens(self):
        self.lbl_logo.config(text=os.path.basename(self.caminho_logo) if self.caminho_logo else "Não selecionado",
                             fg="#000" if self.caminho_logo else "#777")
        self.lbl_screenshots.config(
            text=self.pasta_screenshots if self.pasta_screenshots else "Não selecionada",
            fg="#000" if self.pasta_screenshots else "#777")

    def _dados_perfil(self):
        return {
            "cores": {chave: var.get().strip() for chave, var in self.cores.items()},
            "tamanhos": {"grande": self.tam_grande.get(), "medio": self.tam_medio.get(),
                         "pequeno": self.tam_pequeno.get()},
            "textos": {"grande": self.texto_grande.get(), "medio": self.texto_medio.get(),
                       "pequeno": self.texto_pequeno.get()},
            "secoes": {chave: var.get() for chave, var in self.secoes.items()},
            "caminho_logo": self.caminho_logo,
            "pasta_screenshots": self.pasta_screenshots,
            "ultimo_diretorio": self.ultimo_diretorio,
        }

    def _salvar_perfil(self):
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(CONFIG_PATH, "w", encoding="utf-8") as arquivo:
                json.dump(self._dados_perfil(), arquivo, ensure_ascii=False, indent=2)
        except (OSError, tk.TclError):
            pass

    def _carregar_perfil(self):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as arquivo:
                perfil = json.load(arquivo)
            for chave, valor in perfil.get("cores", {}).items():
                if chave in self.cores and HEX_COR_REGEX.match(str(valor)):
                    self.cores[chave].set(valor)
            tamanhos = perfil.get("tamanhos", {})
            self.tam_grande.set(tamanhos.get("grande", self.tam_grande.get()))
            self.tam_medio.set(tamanhos.get("medio", self.tam_medio.get()))
            self.tam_pequeno.set(tamanhos.get("pequeno", self.tam_pequeno.get()))
            textos = perfil.get("textos", {})
            self.texto_grande.set(textos.get("grande", ""))
            self.texto_medio.set(textos.get("medio", ""))
            self.texto_pequeno.set(textos.get("pequeno", ""))
            for chave, valor in perfil.get("secoes", {}).items():
                if chave in self.secoes:
                    self.secoes[chave].set(bool(valor))
            self.caminho_logo = perfil.get("caminho_logo", "")
            self.pasta_screenshots = perfil.get("pasta_screenshots", "")
            self.ultimo_diretorio = perfil.get("ultimo_diretorio", "")
        except (OSError, ValueError, TypeError, tk.TclError):
            pass

    def _ao_fechar(self):
        self._salvar_perfil()
        self.destroy()

    def _validar(self):
        if not self.caminho_pbix:
            messagebox.showwarning("Atenção", "Selecione um arquivo .pbix primeiro.")
            return False
        for chave, nome in {"primaria": "Primária", "secundaria": "Secundária", "terciaria": "Terciária"}.items():
            if not HEX_COR_REGEX.match(self.cores[chave].get().strip()):
                messagebox.showwarning("Cor inválida", f"A cor {nome} deve usar o formato #RRGGBB.")
                return False
        if not any(var.get() for var in self.secoes.values()):
            messagebox.showwarning("Atenção", "Selecione pelo menos uma seção para o PDF.")
            return False
        return True

    def _gerar_documentacao(self):
        if not self._validar():
            return
        nome = os.path.splitext(os.path.basename(self.caminho_pbix))[0]
        caminho_saida = filedialog.asksaveasfilename(
            title="Salvar documentação como...", defaultextension=".pdf",
            initialfile=f"Documentacao_{nome}.pdf", filetypes=[("Arquivo PDF", "*.pdf")],
            initialdir=self.ultimo_diretorio or None)
        if not caminho_saida:
            return

        self.ultimo_diretorio = os.path.dirname(caminho_saida)
        opcoes = self._dados_perfil()
        opcoes["secoes_escolhidas"] = [chave for chave, var in self.secoes.items() if var.get()]
        caminho_pbix = self.caminho_pbix
        self._salvar_perfil()
        self.btn_gerar.config(state="disabled")
        self.barra_progresso["value"] = 0
        self._atualizar_status("Abrindo PBIX...", 1)
        threading.Thread(target=self._processar, args=(caminho_pbix, caminho_saida, opcoes), daemon=True).start()

    def _atualizar_status(self, mensagem, percentual=None):
        def atualizar():
            self.lbl_status.config(text=mensagem)
            if percentual is not None:
                self.barra_progresso["value"] = max(0, min(100, percentual))
        self.after(0, atualizar)

    def _processar(self, caminho_pbix, caminho_saida, opcoes):
        try:
            secoes = opcoes["secoes_escolhidas"]
            dados = pbix_parser.extrair_tudo(caminho_pbix, secoes=secoes, progresso=self._atualizar_status)
            with tempfile.TemporaryDirectory(prefix="pbix_doc_") as pasta_temporaria:
                diagrama, aviso = (None, None)
                if "diagrama" in secoes:
                    diagrama, aviso = diagram_builder.gerar_diagrama(
                        dados, pasta_temporaria, opcoes["cores"]["primaria"],
                        opcoes["cores"]["secundaria"], self._atualizar_status)
                pdf_builder.gerar_pdf(
                    dados, caminho_saida=caminho_saida, nome_arquivo_pbix=os.path.basename(caminho_pbix),
                    cor_primaria=opcoes["cores"]["primaria"],
                    cor_secundaria=opcoes["cores"]["secundaria"],
                    cor_terciaria=opcoes["cores"]["terciaria"],
                    tam_titulo_grande=opcoes["tamanhos"]["grande"],
                    tam_titulo_medio=opcoes["tamanhos"]["medio"],
                    tam_titulo_pequeno=opcoes["tamanhos"]["pequeno"],
                    texto_grande=opcoes["textos"]["grande"].strip(),
                    texto_medio=opcoes["textos"]["medio"].strip(),
                    texto_pequeno=opcoes["textos"]["pequeno"].strip(),
                    secoes=secoes, progresso=self._atualizar_status,
                    caminho_logo=opcoes.get("caminho_logo"),
                    pasta_screenshots=opcoes.get("pasta_screenshots"),
                    caminho_diagrama=diagrama, aviso_diagrama=aviso)
            self.after(0, lambda: self._concluido(caminho_saida))
        except Exception as erro:
            self.after(0, lambda e=erro: self._erro(e))

    def _abrir_pasta_saida(self):
        if self._ultima_pasta_saida and os.path.isdir(self._ultima_pasta_saida):
            os.startfile(self._ultima_pasta_saida)

    def _concluido(self, caminho_saida):
        self._ultima_pasta_saida = os.path.dirname(caminho_saida)
        self._atualizar_status(f"Concluído → {os.path.basename(caminho_saida)}", 99)
        self.btn_abrir_pasta.config(state="normal")
        try:
            os.startfile(caminho_saida)
            self._atualizar_status(f"Concluído → {os.path.basename(caminho_saida)}", 100)
        except OSError as erro:
            self._atualizar_status(f"Concluído → {os.path.basename(caminho_saida)}", 100)
            messagebox.showwarning("PDF gerado", f"O PDF foi salvo, mas não pôde ser aberto:\n{erro}\n\n{caminho_saida}")
        self.btn_gerar.config(state="normal")

    def _erro(self, excecao):
        self.lbl_status.config(text="Ocorreu um erro.")
        self.btn_gerar.config(state="normal")
        messagebox.showerror("Erro", f"Não foi possível gerar a documentação:\n{excecao}")


if __name__ == "__main__":
    DocumentadorApp().mainloop()
