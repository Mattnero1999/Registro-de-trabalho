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
        self.title("Pneus Planalto - Asset Manager Pro v3.0")
        self.geometry("800x750")
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

        # 1. Seleção de Loja (Atualizada com Avenida Brasil)
        ctk.CTkLabel(self.inputs_frame, text="Selecione a Loja:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=15, pady=10, sticky="w")
        self.loja_var = ctk.StringVar(value="Araguari")
        # LISTA DE LOJAS ATUALIZADA
        lojas_disponiveis = [
            "Araguari", 
            "Floriano Peixoto", 
            "Afonso Pena", 
            "João Naves", 
            "Avenida Brasil", 
            "Outras"
        ]
        self.combo_loja = ctk.CTkComboBox(self.inputs_frame, variable=self.loja_var, width=250, values=lojas_disponiveis)
        self.combo_loja.grid(row=0, column=1, padx=15, pady=10)

        # 2. Tipo de Equipamento (Define qual planilha usar)
        ctk.CTkLabel(self.inputs_frame, text="Tipo de Item:", font=ctk.CTkFont(weight="bold")).grid(row=1, column=0, padx=15, pady=10, sticky="w")
        self.tipo_var = ctk.StringVar(value="Patrimônio TI (Geral)")
        self.combo_tipo = ctk.CTkComboBox(self.inputs_frame, variable=self.tipo_var, width=250,
                                          values=["Patrimônio TI (Geral)", "Celulares Corporativos", "Mobiliário", "Outros"])
        self.combo_tipo.grid(row=1, column=1, padx=15, pady=10)

        # 3. Código do Bem
        ctk.CTkLabel(self.inputs_frame, text="Código / Identificação:", font=ctk.CTkFont(weight="bold")).grid(row=2, column=0, padx=15, pady=10, sticky="w")
        self.code_entry = ctk.CTkEntry(self.inputs_frame, width=250, placeholder_text="Ex: CEL-ARG-01 ou IMEI")
        self.code_entry.grid(row=2, column=1, padx=15, pady=10)
        self.code_entry.bind("<Return>", lambda event: self.processar_ativo())

        # 4. Descrição Rápida (Para a planilha)
        ctk.CTkLabel(self.inputs_frame, text="Descrição (Opcional):", font=ctk.CTkFont(weight="bold")).grid(row=3, column=0, padx=15, pady=10, sticky="w")
        self.desc_entry = ctk.CTkEntry(self.inputs_frame, width=250, placeholder_text="Ex: iPhone 11 Preto - Vendas")
        self.desc_entry.grid(row=3, column=1, padx=15, pady=10)

        # --- OPÇÕES DE GERAÇÃO ---
        self.opts_frame = ctk.CTkFrame(self.main_container)
        self.opts_frame.pack(fill="x", pady=10)
        
        self.chk_barcode = ctk.CTkCheckBox(self.opts_frame, text="Gerar Código de Barras (Code 128)")
        self.chk_barcode.select()
        self.chk_barcode.pack(side="left", padx=20, pady=10)
        
        self.chk_qrcode = ctk.CTkCheckBox(self.opts_frame, text="Gerar QR Code")
        self.chk_qrcode.select()
        self.chk_qrcode.pack(side="left", padx=20, pady=10)

        self.chk_planilha = ctk.CTkCheckBox(self.opts_frame, text="Salvar na Planilha automaticamente")
        self.chk_planilha.select()
        self.chk_planilha.pack(side="left", padx=20, pady=10)

        # BOTÃO PRINCIPAL
        self.btn_gerar = ctk.CTkButton(self, text="CADASTRAR E GERAR ETIQUETA", height=50, 
                                       font=ctk.CTkFont(size=16, weight="bold"), 
                                       fg_color="#006400", hover_color="#004d00", # Verde escuro
                                       command=self.processar_ativo)
        self.btn_gerar.pack(fill="x", padx=40, pady=5)

        # PREVIEW
        self.preview_label = ctk.CTkLabel(self, text="Pré-visualização da Etiqueta:", text_color="gray")
        self.preview_label.pack(pady=(15, 5))
        
        self.img_preview = ctk.CTkLabel(self, text="")
        self.img_preview.pack(pady=5)
        
        self.status_bar = ctk.CTkLabel(self, text="Sistema Pronto.", text_color="gray")
        self.status_bar.pack(side="bottom", pady=10)

    # --- LÓGICA DO SISTEMA ---

    def processar_ativo(self):
        codigo = self.code_entry.get().strip().upper()
        loja = self.loja_var.get()
        tipo = self.tipo_var.get()
        descricao = self.desc_entry.get().strip()

        if not codigo:
            self.status_bar.configure(text="Erro: Digite um código válido.", text_color="#FF5555")
            return

        try:
            # 1. Define pastas baseadas na Loja
            pasta_destino = os.path.join(self.imgs_dir, loja)
            if not os.path.exists(pasta_destino):
                os.makedirs(pasta_destino)

            imagens_geradas = []

            # 2. Gera Barcode
            if self.chk_barcode.get():
                path_bar = self.gerar_barcode(codigo, pasta_destino)
                imagens_geradas.append(path_bar)
                self.mostrar_preview(path_bar, (250, 100))

            # 3. Gera QR Code
            if self.chk_qrcode.get():
                path_qr = self.gerar_qrcode(codigo, pasta_destino)
                imagens_geradas.append(path_qr)
                if not self.chk_barcode.get(): # Se só gerou QR, mostra ele no preview
                    self.mostrar_preview(path_qr, (150, 150))

            # 4. Salva na Planilha (O "Pulo do Gato")
            msg_planilha = ""
            if self.chk_planilha.get():
                arquivo_csv = self.definir_nome_planilha(tipo)
                self.salvar_na_planilha(arquivo_csv, loja, codigo, tipo, descricao)
                msg_planilha = f" + Salvo em '{arquivo_csv}'"

            # Sucesso
            self.status_bar.configure(text=f"Sucesso! Etiquetas salvas em '{loja}'{msg_planilha}", text_color="green")
            self.code_entry.delete(0, "end")
            self.desc_entry.delete(0, "end")
            self.code_entry.focus()

        except Exception as e:
            self.status_bar.configure(text=f"Erro crítico: {str(e)}", text_color="red")
            messagebox.showerror("Erro", str(e))

    def definir_nome_planilha(self, tipo):
        """Define em qual arquivo CSV salvar com base na categoria escolhida"""
        if "Celular" in tipo:
            return "Inventario_Celulares.csv"
        elif "Mobiliário" in tipo:
            return "Inventario_Mobiliario.csv"
        else:
            return "Inventario_Geral_TI.csv"

    def salvar_na_planilha(self, nome_arquivo, loja, codigo, tipo, descricao):
        caminho_csv = os.path.join(self.data_dir, nome_arquivo)
        arquivo_existe = os.path.exists(caminho_csv)
        
        with open(caminho_csv, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=';') # Ponto e vírgula para Excel PT-BR
            
            # Cabeçalho se for arquivo novo
            if not arquivo_existe:
                writer.writerow(["Data Registro", "Loja", "Tipo", "Código", "Descrição"])
            
            # Dados
            data_hoje = datetime.now().strftime("%d/%m/%Y %H:%M")
            writer.writerow([data_hoje, loja, tipo, codigo, descricao])

    def gerar_barcode(self, codigo, pasta):
        CODIGO_CLASSE = barcode.get_barcode_class('code128')
        writer = ImageWriter()
        filename = os.path.join(pasta, f"{codigo}_BAR")
        full_path = CODIGO_CLASSE(codigo, writer=writer).save(filename)
        return full_path

    def gerar_qrcode(self, codigo, pasta):
        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(codigo)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        filename = os.path.join(pasta, f"{codigo}_QR.png")
        img.save(filename)
        return filename

    def mostrar_preview(self, image_path, size):
        pil_img = Image.open(image_path)
        ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
        self.img_preview.configure(image=ctk_img)
        self.img_preview.image = ctk_img

# Inicialização
if __name__ == "__main__":
    app = AssetManagerPro()
    app.mainloop()