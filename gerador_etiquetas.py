import sys
import os
from tkinter import *
from tkinter import filedialog, messagebox
# Tenta importar o TkinterDnD, se não tiver avisa o usuário
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError:
    print("Erro: A biblioteca 'tkinterdnd2' não está instalada.")
    print("Instale usando: pip install tkinterdnd2")
    sys.exit(1)

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from PIL import Image

class AppEtiquetas:
    def __init__(self, root):
        self.root = root
        self.root.title("Gerador de Etiquetas (3x3 cm)")
        self.root.geometry("600x500")
        
        # Lista de arquivos selecionados
        self.arquivos = []

        # --- Interface Gráfica ---
        
        # Título / Instruções
        lbl_titulo = Label(root, text="Gerador de Etiquetas Compactas", font=("Arial", 14, "bold"))
        lbl_titulo.pack(pady=(15, 5))

        lbl_instrucoes = Label(root, text="Arraste as imagens aqui (Tamanho final: 3cm x 3cm)", font=("Arial", 10))
        lbl_instrucoes.pack(pady=5)

        # Listbox (Área onde os arquivos ficam listados)
        # Scrollbar para caso tenha muitos arquivos
        frame_lista = Frame(root)
        frame_lista.pack(padx=20, pady=5)
        
        scrollbar = Scrollbar(frame_lista)
        scrollbar.pack(side=RIGHT, fill=Y)

        self.listbox = Listbox(frame_lista, selectmode=EXTENDED, width=70, height=15, yscrollcommand=scrollbar.set)
        self.listbox.pack(side=LEFT, fill=BOTH)
        scrollbar.config(command=self.listbox.yview)
        
        # Habilitar Drag & Drop na Listbox
        self.listbox.drop_target_register(DND_FILES)
        self.listbox.dnd_bind('<<Drop>>', self.soltar_arquivos)

        # Botões
        frame_botoes = Frame(root)
        frame_botoes.pack(pady=20)

        btn_add = Button(frame_botoes, text="Adicionar Arquivos", command=self.selecionar_arquivos, width=18)
        btn_add.pack(side=LEFT, padx=5)

        btn_limpar = Button(frame_botoes, text="Limpar Lista", command=self.limpar_lista, width=12)
        btn_limpar.pack(side=LEFT, padx=5)

        btn_gerar = Button(frame_botoes, text="GERAR PDF", command=self.gerar_pdf, bg="#008CBA", fg="white", font=("Arial", 10, "bold"), width=18)
        btn_gerar.pack(side=LEFT, padx=20)

        # Barra de status
        self.status = Label(root, text="0 arquivos na fila", bd=1, relief=SUNKEN, anchor=W)
        self.status.pack(side=BOTTOM, fill=X)

    def atualizar_status(self):
        qtd = len(self.arquivos)
        self.status.config(text=f"{qtd} arquivos na fila")

    def soltar_arquivos(self, event):
        # Limpa formatação que o Windows/TkinterDnD pode colocar (chaves {})
        raw_files = self.root.tk.splitlist(event.data)
        for f in raw_files:
            if f and f not in self.arquivos:
                self.arquivos.append(f)
                self.listbox.insert(END, os.path.basename(f))
        self.atualizar_status()

    def selecionar_arquivos(self):
        files = filedialog.askopenfilenames(title="Selecione as imagens", filetypes=[("Imagens", "*.png;*.jpg;*.jpeg;*.bmp")])
        for f in files:
            if f not in self.arquivos:
                self.arquivos.append(f)
                self.listbox.insert(END, os.path.basename(f))
        self.atualizar_status()

    def limpar_lista(self):
        self.arquivos = []
        self.listbox.delete(0, END)
        self.atualizar_status()

    def gerar_pdf(self):
        if not self.arquivos:
            messagebox.showwarning("Aviso", "Nenhum arquivo selecionado!")
            return

        caminho_salvar = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")], title="Salvar PDF como")
        
        if not caminho_salvar:
            return

        try:
            self.criar_pdf(caminho_salvar)
            messagebox.showinfo("Sucesso", f"PDF gerado com sucesso!\nSalvo em: {caminho_salvar}")
            os.startfile(caminho_salvar)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar PDF: {str(e)}")

    def criar_pdf(self, output_path):
        c = canvas.Canvas(output_path, pagesize=A4)
        largura_pag, altura_pag = A4
        
        # --- CONFIGURAÇÕES DE MEDIDA (MODIFICADO PARA 3CM) ---
        tamanho_max = 3.0 * cm   # Tamanho da etiqueta
        margem_esq = 1.0 * cm    # Margem esquerda da página
        margem_sup = 1.0 * cm    # Margem superior da página
        espacamento = 0.2 * cm   # Espaço entre etiquetas (reduzido para caber mais)
        
        # Posição inicial
        x = margem_esq
        y = altura_pag - margem_sup - tamanho_max
        
        count = 0
        for img_path in self.arquivos:
            try:
                pil_img = Image.open(img_path)
                w_orig, h_orig = pil_img.size
                
                # Calcula proporção
                ratio = min(tamanho_max/w_orig, tamanho_max/h_orig)
                w_final = w_orig * ratio
                h_final = h_orig * ratio
                
                # Centraliza a imagem no espaço de 3x3 se ela não for quadrada
                offset_x = (tamanho_max - w_final) / 2
                offset_y = (tamanho_max - h_final) / 2
                
                # Desenha imagem
                c.drawImage(img_path, x + offset_x, y + offset_y, width=w_final, height=h_final, mask='auto')
                
                # Opcional: Desenha uma borda fina cinza ao redor da área de 3x3 para facilitar o corte
                c.setLineWidth(0.5)
                c.setStrokeColorRGB(0.8, 0.8, 0.8) # Cinza claro
                c.rect(x, y, tamanho_max, tamanho_max)
                
                count += 1
                
                # Lógica de posicionamento (Avança para a direita)
                x += tamanho_max + espacamento
                
                # Se passar da largura (quebra de linha)
                if x + tamanho_max > largura_pag - margem_esq:
                    x = margem_esq
                    y -= (tamanho_max + espacamento)
                
                # Se acabar a página (quebra de página)
                if y < 1 * cm:
                    c.showPage()
                    y = altura_pag - margem_sup - tamanho_max
                    x = margem_esq
                    
            except Exception as e:
                print(f"Erro ao processar imagem {img_path}: {e}")
                
        c.save()

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = AppEtiquetas(root)
    root.mainloop()