import customtkinter as ctk
from tkinter import messagebox
import barcode
from barcode.writer import ImageWriter
import qrcode
from PIL import Image
import os
import csv
from datetime import datetime

# --- Configurações Visuais ---
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class AssetManagerPro(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configuração da Janela
        self.title("Pneus Planalto - Asset Manager Pro v6.0")
        self.geometry("1000x800") # Largura ajustada para campos extras
        self.resizable(False, False)

        # Pastas de Saída
        self.base_dir = "Sistema_Patrimonio"
        self.imgs_dir = os.path.join(self.base_dir, "Etiquetas_Geradas")
        self.data_dir = os.path.join(self.base_dir, "Planilhas_Controle")

        for d in [self.imgs_dir, self.data_dir]:
            if not os.path.exists(d):
                os.makedirs(d)

        self.setup_ui()

    def setup_ui(self):
        # Cabeçalho
        self.header_frame = ctk.CTkFrame(self, corner_radius=0)
        self.header_frame.pack(fill="x")
        self.title_label = ctk.CTkLabel(self.header_frame, text="Central de Patrimônio & Etiquetas", font=ctk.CTkFont(size=22, weight="bold"))
        self.title_label.pack(pady=15)

        # --- ÁREA DE DADOS (Esquerda) ---
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=10)

        # Campos de Entrada
        self.inputs_frame = ctk.CTkFrame(self.main_container)
        self.inputs_frame.pack(fill="x", pady=5)

        # 1. Seleção de Loja
        ctk.CTkLabel(self.inputs_frame, text="Selecione a Loja:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=15, pady=10, sticky="w")
        self.loja_var = ctk.StringVar(value="Araguari")
        
        lojas_disponiveis = [
            "Araguari", "Floriano Peixoto", "Afonso Pena", 
            "João Naves", "Avenida Brasil", "Uberaba", 
            "Cadastrar Nova..."
        ]
        
        self.combo_loja = ctk.CTkComboBox(self.inputs_frame, variable=self.loja_var, width=350, 
                                          values=lojas_disponiveis, command=self.verificar_opcao_loja)
        self.combo_loja.grid(row=0, column=1, padx=15, pady=10)

        self.nova_loja_entry = ctk.CTkEntry(self.inputs_frame, width=200, placeholder_text="Nome da Nova Loja", fg_color=["#F9F9FA", "#343638"])

        # 2. Tipo de Equipamento (Atualizado com Maquinário)
        ctk.CTkLabel(self.inputs_frame, text="Tipo de Item:", font=ctk.CTkFont(weight="bold")).grid(row=1, column=0, padx=15, pady=10, sticky="w")
        self.tipo_var = ctk.StringVar(value="Patrimônio TI (Geral)")
        
        tipos_disponiveis = [
            "Patrimônio TI (Geral)",
            "Celulares Corporativos",
            "Mobiliário",
            "Maquinário Pesado",
            "Montadora de Pneus",
            "Balanceadora",
            "Ferramentas de Oficina",
            "Outros",
            "Cadastrar Novo Tipo..."
        ]

        self.combo_tipo = ctk.CTkComboBox(self.inputs_frame, variable=self.tipo_var, width=350,
                                          values=tipos_disponiveis, command=self.verificar_opcao_tipo)
        self.combo_tipo.grid(row=1, column=1, padx=15, pady=10)

        self.novo_tipo_entry = ctk.CTkEntry(self.inputs_frame, width=200, placeholder_text="Nome do Novo Tipo", fg_color=["#F9F9FA", "#343638"])

        # 3. Código do Bem
        ctk.CTkLabel(self.inputs_frame, text="Código / Identificação:", font=ctk.CTkFont(weight="bold")).grid(row=2, column=0, padx=15, pady=10, sticky="w")
        self.code_entry = ctk.CTkEntry(self.inputs_frame, width=350, placeholder_text="Ex: MAQ-ARA-01 ou Nº Série")
        self.code_entry.grid(row=2, column=1, padx=15, pady=10)
        self.code_entry.bind("<Return>", lambda event: self.processar_ativo())

        # 4. Descrição Rápida
        ctk.CTkLabel(self.inputs_frame, text="Descrição (Opcional):", font=ctk.CTkFont(weight="bold")).grid(row=3, column=0, padx=15, pady=10, sticky="w")
        self.desc_entry = ctk.CTkEntry(self.inputs_frame, width=350, placeholder_text="Ex: Balanceadora 3D Vermelha")
        self.desc_entry.grid(row=3, column=1, padx=15, pady=10)

        # --- NOVA SEÇÃO: INTEGRAÇÃO WEB ---
        self.web_frame = ctk.CTkFrame(self.main_container, border_color="gray", border_width=1)
        self.web_frame.pack(fill="x", pady=15)
        
        ctk.CTkLabel(self.web_frame, text="Integração Google Sheets / Web (Avançado)", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=5)
        
        self.chk_web_link = ctk.CTkCheckBox(self.web_frame, text="Vincular QR Code a um Link Online", command=self.toggle_web_input)
        self.chk_web_link.pack(pady=5)

        self.url_entry = ctk.CTkEntry(self.web_frame, width=500, placeholder_text="Link do Google Sheets (Ex: https://docs.google.com/spreadsheets/d/...)")
        self.url_entry.configure(state="disabled", fg_color=["#E0E0E0", "#2B2B2B"]) 
        self.url_entry.pack(pady=(0, 10), padx=20)

        # --- OPÇÕES DE GERAÇÃO ---
        self.opts_frame = ctk.CTkFrame(self.main_container)
        self.opts_frame.pack(fill="x", pady=5)
        
        self.chk_barcode = ctk.CTkCheckBox(self.opts_frame, text="Gerar Código de Barras")
        self.chk_barcode.select()
        self.chk_barcode.pack(side="left", padx=20, pady=10)
        
        self.chk_qrcode = ctk.CTkCheckBox(self.opts_frame, text="Gerar QR Code")
        self.chk_qrcode.select()
        self.chk_qrcode.pack(side="left", padx=20, pady=10)

        self.chk_planilha = ctk.CTkCheckBox(self.opts_frame, text="Salvar na Planilha Local")
        self.chk_planilha.select()
        self.chk_planilha.pack(side="left", padx=20, pady=10)

        # BOTÃO PRINCIPAL
        self.btn_gerar = ctk.CTkButton(self, text="CADASTRAR E GERAR ETIQUETA", height=50, 
                                       font=ctk.CTkFont(size=16, weight="bold"), 
                                       fg_color="#006400", hover_color="#004d00",
                                       command=self.processar_ativo)
        self.btn_gerar.pack(fill="x", padx=40, pady=5)

        # PREVIEW
        self.preview_label = ctk.CTkLabel(self, text="Pré-visualização:", text_color="gray")
        self.preview_label.pack(pady=(10, 0))
        
        self.img_preview = ctk.CTkLabel(self, text="")
        self.img_preview.pack(pady=5)
        
        self.status_bar = ctk.CTkLabel(self, text="Sistema Pronto.", text_color="gray")
        self.status_bar.pack(side="bottom", pady=10)

    # --- LÓGICA DO SISTEMA ---

    def verificar_opcao_loja(self, choice):
        """Gerencia campo de nova loja"""
        if choice == "Cadastrar Nova...":
            self.nova_loja_entry.grid(row=0, column=2, padx=10, pady=10)
            self.nova_loja_entry.focus()
        else:
            self.nova_loja_entry.grid_forget()

    def verificar_opcao_tipo(self, choice):
        """Gerencia campo de novo tipo"""
        if choice == "Cadastrar Novo Tipo...":
            self.novo_tipo_entry.grid(row=1, column=2, padx=10, pady=10)
            self.novo_tipo_entry.focus()
        else:
            self.novo_tipo_entry.grid_forget()

    def toggle_web_input(self):
        if self.chk_web_link.get():
            self.url_entry.configure(state="normal", fg_color=["#F9F9FA", "#343638"]) 
            self.status_bar.configure(text="Dica: O QR Code conterá o Link + Código.", text_color="#1E90FF")
        else:
            self.url_entry.configure(state="disabled", fg_color=["#E0E0E0", "#2B2B2B"])
            self.status_bar.configure(text="Modo Offline: O QR Code conterá apenas o código.", text_color="gray")

    def processar_ativo(self):
        codigo = self.code_entry.get().strip().upper()
        descricao = self.desc_entry.get().strip()
        
        # 1. Resolver Loja
        loja_selecao = self.loja_var.get()
        if loja_selecao == "Cadastrar Nova...":
            loja_real = self.nova_loja_entry.get().strip()
            if not loja_real:
                self.status_bar.configure(text="Erro: Digite o nome da Nova Loja.", text_color="#FF5555")
                self.nova_loja_entry.focus()
                return
        else:
            loja_real = loja_selecao

        # 2. Resolver Tipo
        tipo_selecao = self.tipo_var.get()
        if tipo_selecao == "Cadastrar Novo Tipo...":
            tipo_real = self.novo_tipo_entry.get().strip()
            if not tipo_real:
                self.status_bar.configure(text="Erro: Digite o nome do Novo Tipo.", text_color="#FF5555")
                self.novo_tipo_entry.focus()
                return
        else:
            tipo_real = tipo_selecao

        if not codigo:
            self.status_bar.configure(text="Erro: Digite um código válido.", text_color="#FF5555")
            return

        try:
            # Pasta destino usa o nome real da loja
            pasta_destino = os.path.join(self.imgs_dir, loja_real)
            if not os.path.exists(pasta_destino):
                os.makedirs(pasta_destino)

            imagens_geradas = []

            # Conteúdo QR
            conteudo_qrcode = codigo
            if self.chk_web_link.get():
                url_base = self.url_entry.get().strip()
                if url_base:
                    if url_base.endswith("=") or url_base.endswith("?"):
                        conteudo_qrcode = f"{url_base}{codigo}"
                    elif "?" in url_base:
                        conteudo_qrcode = f"{url_base}&q={codigo}"
                    else:
                        if not url_base.endswith("/"):
                            url_base += "/"
                        conteudo_qrcode = f"{url_base}{codigo}"

            # Gerar Barcode
            if self.chk_barcode.get():
                path_bar = self.gerar_barcode(codigo, pasta_destino)
                imagens_geradas.append(path_bar)
                self.mostrar_preview(path_bar, (250, 100))

            # Gerar QR Code
            if self.chk_qrcode.get():
                path_qr = self.gerar_qrcode(conteudo_qrcode, codigo, pasta_destino)
                imagens_geradas.append(path_qr)
                if not self.chk_barcode.get():
                    self.mostrar_preview(path_qr, (150, 150))

            # Salvar na Planilha
            msg_planilha = ""
            if self.chk_planilha.get():
                # Passa o tipo_real para definir o arquivo
                arquivo_csv = self.definir_nome_planilha(tipo_real)
                self.salvar_na_planilha(arquivo_csv, loja_real, codigo, tipo_real, descricao)
                msg_planilha = f" + Planilha OK"

            self.status_bar.configure(text=f"Sucesso! Gerado para '{tipo_real}' em '{loja_real}'.", text_color="green")
            self.code_entry.delete(0, "end")
            self.desc_entry.delete(0, "end")
            self.code_entry.focus()

        except Exception as e:
            self.status_bar.configure(text=f"Erro crítico: {str(e)}", text_color="red")
            messagebox.showerror("Erro", str(e))

    def definir_nome_planilha(self, tipo):
        """Roteia o tipo de equipamento para a planilha correta"""
        # Normaliza para minúsculo para facilitar comparação
        t = tipo.lower()
        
        if "celular" in t or "smartphone" in t:
            return "Inventario_Celulares.csv"
        elif "mobiliário" in t or "mesa" in t or "cadeira" in t:
            return "Inventario_Mobiliario.csv"
        elif any(x in t for x in ["maquinário", "pesado", "montadora", "balanceadora", "oficina", "elevador"]):
            return "Inventario_Oficina_Maquinario.csv"
        elif "ti" in t or "computador" in t or "notebook" in t:
            return "Inventario_Geral_TI.csv"
        else:
            # Se for um tipo muito diferente, salva num arquivo genérico ou personalizado
            return "Inventario_Outros_Diversos.csv"

    def salvar_na_planilha(self, nome_arquivo, loja, codigo, tipo, descricao):
        caminho_csv = os.path.join(self.data_dir, nome_arquivo)
        arquivo_existe = os.path.exists(caminho_csv)
        with open(caminho_csv, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=';')
            if not arquivo_existe:
                writer.writerow(["Data Registro", "Loja", "Tipo", "Código", "Descrição"])
            data_hoje = datetime.now().strftime("%d/%m/%Y %H:%M")
            writer.writerow([data_hoje, loja, tipo, codigo, descricao])

    def gerar_barcode(self, codigo, pasta):
        CODIGO_CLASSE = barcode.get_barcode_class('code128')
        writer = ImageWriter()
        filename = os.path.join(pasta, f"{codigo}_BAR")
        full_path = CODIGO_CLASSE(codigo, writer=writer).save(filename)
        return full_path

    def gerar_qrcode(self, conteudo, nome_arquivo_base, pasta):
        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(conteudo)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        safe_filename = "".join([c for c in nome_arquivo_base if c.isalnum() or c in ('-','_')]).strip()
        filename = os.path.join(pasta, f"{safe_filename}_QR.png")
        img.save(filename)
        return filename

    def mostrar_preview(self, image_path, size):
        pil_img = Image.open(image_path)
        ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
        self.img_preview.configure(image=ctk_img)
        self.img_preview.image = ctk_img

if __name__ == "__main__":
    app = AssetManagerPro()
    app.mainloop()