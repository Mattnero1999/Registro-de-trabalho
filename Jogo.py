import pygame
import sys
import threading
import time
import random
import os

# --- Constantes do Jogo ---
LARGURA_TELA = 800
ALTURA_TELA = 600
FPS = 60
TEMPO_POR_FASE = 30 # --- NOVO --- Duração de cada corrida em segundos
NUM_ADVERSARIOS = 8 # --- NOVO ---

# --- Cores ---
PRETO = (0, 0, 0)
BRANCO = (255, 255, 255)
VERMELHO = (255, 0, 0)
VERDE = (0, 255, 0)
AZUL = (0, 0, 255)
AMARELO = (255, 255, 0)

# --- Classes (Esboço) ---

class ObjetoJogo(pygame.sprite.Sprite):
    def __init__(self, imagem_path, x, y, largura, altura):
        super().__init__()
        self.image = pygame.image.load(imagem_path).convert_alpha()
        self.image = pygame.transform.scale(self.image, (largura, altura))
        self.rect = self.image.get_rect(topleft=(x, y))

    def desenhar(self, tela):
        tela.blit(self.image, self.rect)

    def atualizar(self, *args, **kwargs):
        pass

class Pista(ObjetoJogo):
    def __init__(self):
        super().__init__("assets/pista.png", 0, 0, LARGURA_TELA, ALTURA_TELA * 2)
        self.y1 = 0
        self.y2 = -ALTURA_TELA

    def carregar_imagem(self):
        self.image = pygame.image.load("assets/pista.png").convert()
        self.image = pygame.transform.scale(self.image, (LARGURA_TELA, ALTURA_TELA * 2))

    # A pista agora rola na velocidade do JOGADOR
    def atualizar(self, velocidade_jogador):
        self.y1 += velocidade_jogador
        self.y2 += velocidade_jogador

        if self.y1 >= ALTURA_TELA:
            self.y1 = -ALTURA_TELA
        if self.y2 >= ALTURA_TELA:
            self.y2 = -ALTURA_TELA
        self.rect.y = self.y1

    def desenhar(self, tela):
        tela.blit(self.image, (0, self.y1))
        tela.blit(self.image, (0, self.y2))


class Jogador(ObjetoJogo):
    def __init__(self, x, y):
        super().__init__("assets/carro_jogador.png", x, y, 50, 80)
        self.velocidade_lateral = 0 # Movimento A/D
        self.velocidade_lateral_max = 7
        
        # --- NOVO --- Controle de aceleração
        self.velocidade_atual = 5 # Velocidade de "cruzeiro"
        self.velocidade_max = 15
        self.velocidade_min = 3
        self.aceleracao = 0.1
        self.freio = 0.2
        self.atrito = 0.05 # Desaceleração natural

    def carregar_imagem(self):
        self.image = pygame.image.load("assets/carro_jogador.png").convert_alpha()
        self.image = pygame.transform.scale(self.image, (50, 80))
        self.rect = self.image.get_rect(center=(self.rect.centerx, self.rect.centery))

    def mover_lateral(self, direcao):
        if direcao == "esquerda":
            self.velocidade_lateral = -self.velocidade_lateral_max
        elif direcao == "direita":
            self.velocidade_lateral = self.velocidade_lateral_max
        else:
            self.velocidade_lateral = 0

    # --- NOVO --- Controle de velocidade W/S
    def controlar_velocidade(self, acao):
        if acao == "acelerar":
            self.velocidade_atual = min(self.velocidade_atual + self.aceleracao, self.velocidade_max)
        elif acao == "frear":
            self.velocidade_atual = max(self.velocidade_atual - self.freio, self.velocidade_min)
        elif acao == "atrito":
            # Volta para a velocidade de cruzeiro (5)
            if self.velocidade_atual > 5:
                self.velocidade_atual -= self.atrito
            elif self.velocidade_atual < 5:
                self.velocidade_atual += self.atrito

    # --- NOVO --- Chamado na colisão
    def sofrer_batida(self):
        self.velocidade_atual = self.velocidade_min # Perde toda a velocidade
        self.rect.y += 10 # Salta para trás

    def atualizar(self, *args, **kwargs):
        # Movimento lateral
        self.rect.x += self.velocidade_lateral
        if self.rect.left < 50:
            self.rect.left = 50
        if self.rect.right > LARGURA_TELA - 50:
            self.rect.right = LARGURA_TELA - 50
        
        # O movimento Y do jogador é controlado pela câmera (Pista)
        # Mas mantemos ele fixo na parte de baixo da tela
        if self.rect.bottom > ALTURA_TELA - 20:
             self.rect.bottom = ALTURA_TELA - 20
        elif self.rect.bottom < ALTURA_TELA - 20:
             self.rect.y += (self.velocidade_atual - 5) # Efeito de "empurrar" para frente


# --- MUDANÇA --- Classe Obstaculo renomeada para Adversario
class Adversario(ObjetoJogo):
    def __init__(self, x, y, fase):
        super().__init__("assets/carro_inimigo.png", x, y, 50, 80)
        
        # --- NOVO --- Velocidade própria baseada na fase
        # Fase 1: vel entre 4.0 e 6.0
        # Fase 2: vel entre 4.5 e 6.5
        vel_min = 4.0 + (fase - 1) * 0.5
        vel_max = 6.0 + (fase - 1) * 0.5
        self.velocidade_propria = random.uniform(vel_min, vel_max)

        # --- NOVO --- IA Simples de movimento lateral
        self.velocidade_x = random.uniform(1, 3)
        self.direcao_x = random.choice([-1, 1])
        self.timer_mudanca_direcao = 0 # Temporizador para mudar de direção

    def carregar_imagem(self):
        self.image = pygame.image.load("assets/carro_inimigo.png").convert_alpha()
        self.image = pygame.transform.scale(self.image, (50, 80))
        self.rect = self.image.get_rect(center=(self.rect.centerx, self.rect.centery))

    # --- NOVO --- Atualização baseada na velocidade relativa
    def atualizar(self, velocidade_jogador):
        # Movimento Y (Relativo ao Jogador)
        delta_velocidade = velocidade_jogador - self.velocidade_propria
        self.rect.y += delta_velocidade
        
        # Movimento X (IA)
        self.rect.x += self.velocidade_x * self.direcao_x
        if self.rect.left < 50 or self.rect.right > LARGURA_TELA - 50:
            self.direcao_x *= -1 # Inverte a direção se bater na borda da pista
        
        # Chance de mudar de direção aleatoriamente
        self.timer_mudanca_direcao -= 1
        if self.timer_mudanca_direcao <= 0:
            self.direcao_x = random.choice([-1, 0, 1]) # Pode parar ou inverter
            self.timer_mudanca_direcao = random.randint(60, 180) # Muda a cada 1-3 seg
            
        # Remove se ficar muito para trás (saiu da tela)
        if self.rect.top > ALTURA_TELA + 100:
            self.kill()

class Cronometro:
    """Cronômetro da CORRIDA (controla a duração da fase)."""
    def __init__(self):
        self.tempo_inicio = 0
        self.tempo_decorrido = 0
        self.duracao_total = 0
        self.rodando = False
        self.lock = threading.Lock()

    def iniciar(self, duracao):
        self.duracao_total = duracao
        self.tempo_inicio = time.time()
        self.rodando = True

    def parar(self):
        self.rodando = False

    def resetar(self):
        self.tempo_inicio = 0
        self.tempo_decorrido = 0
        self.duracao_total = 0
        self.rodando = False

    def _atualizar_tempo(self):
        while self.rodando:
            with self.lock:
                if self.rodando:
                    self.tempo_decorrido = time.time() - self.tempo_inicio
            time.sleep(0.1)
            # Para a thread se o tempo acabar
            if self.get_tempo_restante() <= 0:
                self.rodando = False

    # --- NOVO --- Retorna o tempo que falta
    def get_tempo_restante(self):
        with self.lock:
            tempo_restante = self.duracao_total - self.tempo_decorrido
            return max(0, tempo_restante)

    def iniciar_thread(self, duracao):
        if not self.rodando:
            self.iniciar(duracao)
            cronometro_thread = threading.Thread(target=self._atualizar_tempo)
            cronometro_thread.daemon = True
            cronometro_thread.start()


class Pontuacao:
    """Gerencia a pontuação TOTAL do jogador."""
    def __init__(self):
        self.pontos = 0
        self.lock = threading.Lock()

    def adicionar_pontos_totais(self, quantidade):
        with self.lock:
            self.pontos += quantidade

    def get_pontos_totais(self):
        with self.lock:
            return self.pontos

    def resetar(self):
        self.pontos = 0

class Jogo:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
        pygame.display.set_caption("Jogo de Corrida (Avaliação 2)")
        self.clock = pygame.time.Clock()
        self.fonte = pygame.font.Font(None, 36)
        self.fonte_grande = pygame.font.Font(None, 72)

        self.estado_jogo = "MENU" # MENU, JOGANDO, FIM_DE_CORRIDA, FIM_DE_JOGO
        
        # --- NOVO --- Atributos de Jogo
        self.fase = 1
        self.pontuacao_total = Pontuacao()
        self.posicao_final_corrida = 0 # Posição (1-9) da última corrida
        self.pontos_ultima_corrida = 0

        # Objetos do jogo
        self.pista = Pista()
        self.jogador = Jogador(LARGURA_TELA // 2, ALTURA_TELA - 100)
        self.adversarios = pygame.sprite.Group()
        self.cronometro_corrida = Cronometro()

        # Sons
        self.som_fundo = pygame.mixer.Sound("assets/musica_fundo.ogg")
        self.som_colisao = pygame.mixer.Sound("assets/som_batida.ogg")

        # Imagem de "Fim de Jogo"
        self.imagem_fim_jogo = pygame.image.load("assets/sair_botao.png").convert_alpha()
        self.imagem_fim_jogo = pygame.transform.scale(self.imagem_fim_jogo, (150, 75))
        self.rect_fim_jogo = self.imagem_fim_jogo.get_rect(center=(LARGURA_TELA // 2, ALTURA_TELA // 2 + 150))


    # (carregar_recursos, _criar_placeholder_image, _criar_placeholder_sound, 
    #  iniciar_musica_fundo, parar_musica_fundo, tela_menu)
    # ... (Essas funções permanecem iguais ao código anterior) ...
    def carregar_recursos(self):
        if not os.path.exists("assets"):
            os.makedirs("assets")
        self._criar_placeholder_image("assets/pista.png", (LARGURA_TELA, ALTURA_TELA * 2), (50, 50, 50), "Pista")
        self._criar_placeholder_image("assets/carro_jogador.png", (50, 80), AZUL, "Jogador")
        self._criar_placeholder_image("assets/cone.png", (40, 40), VERMELHO, "Obstáculo Cone")
        self._criar_placeholder_image("assets/carro_inimigo.png", (50, 80), PRETO, "Adversário")
        self._criar_placeholder_image("assets/sair_botao.png", (150, 75), (100,100,100), "Sair")
        self._criar_placeholder_sound("assets/musica_fundo.ogg")
        self._criar_placeholder_sound("assets/som_batida.ogg")
    def _criar_placeholder_image(self, path, size, color, text=""):
        if not os.path.exists(path):
            print(f"Criando imagem placeholder: {path}")
            surface = pygame.Surface(size)
            surface.fill(color)
            if text:
                font = pygame.font.Font(None, 24)
                text_surface = font.render(text, True, BRANCO if color != BRANCO else PRETO)
                text_rect = text_surface.get_rect(center=(size[0]//2, size[1]//2))
                surface.blit(text_surface, text_rect)
            pygame.image.save(surface, path)
    def _criar_placeholder_sound(self, path):
        if not os.path.exists(path):
            print(f"Criando placeholder para som: {path} (silencioso)")
            with open(path, 'w') as f: f.write("")
    def iniciar_musica_fundo(self):
        try: self.som_fundo.play(-1)
        except pygame.error: print("Não foi possível tocar a música de fundo.")
    def parar_musica_fundo(self):
        self.som_fundo.stop()
    def tela_menu(self):
        self.tela.fill(PRETO)
        titulo = self.fonte.render("Jogo de Corrida POO II", True, BRANCO)
        instrucoes = self.fonte.render("Pressione ESPAÇO para Iniciar", True, BRANCO)
        self.tela.blit(titulo, (LARGURA_TELA // 2 - titulo.get_width() // 2, ALTURA_TELA // 2 - 50))
        self.tela.blit(instrucoes, (LARGURA_TELA // 2 - instrucoes.get_width() // 2, ALTURA_TELA // 2 + 10))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.sair_jogo()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.estado_jogo = "JOGANDO"
                    self.iniciar_nova_corrida(self.fase) # Inicia a Fase 1
                    self.iniciar_musica_fundo()

    # --- NOVO --- Renomeado e modificado
    def iniciar_nova_corrida(self, fase):
        self.fase = fase
        self.jogador = Jogador(LARGURA_TELA // 2, ALTURA_TELA - 100) # Reseta posição
        self.adversarios.empty()
        
        # Cria os 8 adversários da fase
        for _ in range(NUM_ADVERSARIOS):
            self._gerar_novo_adversario(fase)
            
        self.cronometro_corrida.resetar()
        self.cronometro_corrida.iniciar_thread(TEMPO_POR_FASE) # Inicia timer de 30s
        self.estado_jogo = "JOGANDO"

    # --- NOVO --- Lógica de teclado (estado)
    def _processar_teclado(self):
        teclas = pygame.key.get_pressed()

        # Aceleração e Freio
        if teclas[pygame.K_w] or teclas[pygame.K_UP]:
            self.jogador.controlar_velocidade("acelerar")
        elif teclas[pygame.K_s] or teclas[pygame.K_DOWN]:
            self.jogador.controlar_velocidade("frear")
        else:
            self.jogador.controlar_velocidade("atrito")

        # Movimento Lateral
        if teclas[pygame.K_a] or teclas[pygame.K_LEFT]:
            self.jogador.mover_lateral("esquerda")
        elif teclas[pygame.K_d] or teclas[pygame.K_RIGHT]:
            self.jogador.mover_lateral("direita")
        else:
            self.jogador.mover_lateral("parar")
            
    # --- NOVO --- Gerador de adversários
    def _gerar_novo_adversario(self, fase):
        # Posição X aleatória na pista
        pos_x = random.randint(70, LARGURA_TELA - 70) 
        # Posição Y aleatória À FRENTE do jogador ("começa em último")
        pos_y = random.randint(-1500, ALTURA_TELA - 200) 
        
        novo_adversario = Adversario(pos_x, pos_y, fase)
        
        # Evita que nasçam um em cima do outro
        tentativas = 0
        while pygame.sprite.spritecollideany(novo_adversario, self.adversarios) and tentativas < 10:
            pos_x = random.randint(70, LARGURA_TELA - 70)
            pos_y = random.randint(-1500, ALTURA_TELA - 200)
            novo_adversario.rect.topleft = (pos_x, pos_y)
            tentativas += 1
            
        if tentativas < 10:
            self.adversarios.add(novo_adversario)

    def loop_jogo(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                # Clique do mouse
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.estado_jogo == "FIM_DE_JOGO":
                        if self.rect_fim_jogo.collidepoint(event.pos):
                            self.sair_jogo()
                    # --- NOVO --- Clique para avançar de fase
                    if self.estado_jogo == "FIM_DE_CORRIDA":
                         self.iniciar_nova_corrida(self.fase + 1)
                         self.iniciar_musica_fundo()


            # --- Gerenciamento de Estado do Jogo ---
            if self.estado_jogo == "MENU":
                self.tela_menu()
            elif self.estado_jogo == "JOGANDO":
                self._processar_teclado()
                self.atualizar_jogo()
                self.desenhar_jogo()
            # --- NOVO --- Tela de resultado da corrida
            elif self.estado_jogo == "FIM_DE_CORRIDA":
                self.tela_fim_de_corrida()
            elif self.estado_jogo == "FIM_DE_JOGO":
                self.parar_musica_fundo()
                self.tela_fim_de_jogo()

            self.clock.tick(FPS)

        self.sair_jogo()

    def atualizar_jogo(self):
        # --- NOVO --- Verifica se o tempo da corrida acabou
        if self.cronometro_corrida.get_tempo_restante() <= 0:
            self.estado_jogo = "FIM_DE_CORRIDA"
            self.finalizar_corrida()
            return

        # Atualiza Pista e Jogador
        self.pista.atualizar(self.jogador.velocidade_atual)
        self.jogador.atualizar()
        # Atualiza Adversários (passando a velocidade do jogador)
        self.adversarios.update(self.jogador.velocidade_atual)

        # --- NOVO --- Lógica de Colisão (Penalidade, não Game Over)
        colisao = pygame.sprite.spritecollideany(self.jogador, self.adversarios)
        if colisao:
            try: self.som_colisao.play()
            except pygame.error: print("Erro som colisão.")
            
            self.jogador.sofrer_batida()
            # Empurra o adversário para frente
            colisao.rect.y -= 20
            colisao.velocidade_propria *= 0.9 # Reduz a vel do adversário
            

    def desenhar_jogo(self):
        self.pista.desenhar(self.tela)
        self.jogador.desenhar(self.tela)
        self.adversarios.draw(self.tela) # Desenha todos os adversários

        # --- NOVO --- UI (Interface do Usuário) da corrida
        # Fase Atual
        texto_fase = self.fonte.render(f"Fase: {self.fase}", True, BRANCO)
        self.tela.blit(texto_fase, (10, 10))

        # Pontuação Total
        pontos_str = f"Pontos: {self.pontuacao_total.get_pontos_totais()}"
        texto_pontos = self.fonte.render(pontos_str, True, BRANCO)
        self.tela.blit(texto_pontos, (10, 50))
        
        # Velocidade (km/h)
        velocidade_kmh = int(self.jogador.velocidade_atual * 15)
        velocidade_str = f"{velocidade_kmh} km/h"
        texto_velocidade = self.fonte.render(velocidade_str, True, BRANCO)
        self.tela.blit(texto_velocidade, (LARGURA_TELA - texto_velocidade.get_width() - 10, 10))

        # Tempo Restante (Cronômetro)
        tempo_restante = int(self.cronometro_corrida.get_tempo_restante())
        tempo_str = f"Tempo: {tempo_restante}s"
        cor_tempo = BRANCO if tempo_restante > 10 else VERMELHO
        texto_tempo = self.fonte.render(tempo_str, True, cor_tempo)
        self.tela.blit(texto_tempo, (LARGURA_TELA // 2 - texto_tempo.get_width() // 2, 10))
        
        # --- NOVO --- Posição Atual (calculada em tempo real)
        posicao_atual = self.calcular_posicao_atual()
        posicao_str = f"Posição: {posicao_atual} / 9"
        texto_posicao = self.fonte.render(posicao_str, True, AMARELO)
        self.tela.blit(texto_posicao, (LARGURA_TELA - texto_posicao.get_width() - 10, 50))


        pygame.display.flip()

    # --- NOVO --- Calcula a posição do jogador em tempo real
    def calcular_posicao_atual(self):
        # Posição é baseada em quem tem o menor Y (está mais "acima" na pista)
        # Lista com todos os corredores
        corredores = self.adversarios.sprites() + [self.jogador]
        # Ordena: quem tem o menor 'y' vem primeiro (1º lugar)
        corredores.sort(key=lambda c: c.rect.y)
        
        try:
            posicao = corredores.index(self.jogador) + 1
            return posicao
        except ValueError:
            return 9 # Se o jogador não for encontrado (raro)

    # --- NOVO --- Chamado quando o tempo acaba
    def finalizar_corrida(self):
        self.parar_musica_fundo()
        self.cronometro_corrida.parar()
        
        # 1. Calcular Posição Final
        self.posicao_final_corrida = self.calcular_posicao_atual()
        
        # 2. Calcular Pontos
        # 1º = 10000, 2º = 9000, ... 9º = 2000
        pontos_base = 11000 
        self.pontos_ultima_corrida = max(0, pontos_base - (self.posicao_final_corrida * 1000))
        self.pontuacao_total.adicionar_pontos_totais(self.pontos_ultima_corrida)
        
        # 3. Verificar se é Game Over
        if self.posicao_final_corrida >= 5:
            self.estado_jogo = "FIM_DE_JOGO"
        else:
            self.estado_jogo = "FIM_DE_CORRIDA"
            self.fase += 1 # Prepara para a próxima fase

    # --- NOVO --- Tela entre as fases
    def tela_fim_de_corrida(self):
        self.tela.fill(PRETO)
        msg_fase = self.fonte_grande.render(f"Fase {self.fase - 1} Concluída!", True, VERDE)
        msg_pos = self.fonte.render(f"Posição Final: {self.posicao_final_corrida}º lugar", True, BRANCO)
        msg_pts = self.fonte.render(f"Pontos Ganhos: {self.pontos_ultima_corrida}", True, AMARELO)
        msg_total = self.fonte.render(f"Pontuação Total: {self.pontuacao_total.get_pontos_totais()}", True, BRANCO)
        msg_prox = self.fonte.render(f"Clique para iniciar a Fase {self.fase}", True, BRANCO)

        self.tela.blit(msg_fase, (LARGURA_TELA // 2 - msg_fase.get_width() // 2, 100))
        self.tela.blit(msg_pos, (LARGURA_TELA // 2 - msg_pos.get_width() // 2, 200))
        self.tela.blit(msg_pts, (LARGURA_TELA // 2 - msg_pts.get_width() // 2, 250))
        self.tela.blit(msg_total, (LARGURA_TELA // 2 - msg_total.get_width() // 2, 300))
        self.tela.blit(msg_prox, (LARGURA_TELA // 2 - msg_prox.get_width() // 2, 400))
        
        pygame.display.flip()

    # --- MUDANÇA --- Tela de Fim de Jogo agora mostra mais dados
    def tela_fim_de_jogo(self):
        self.tela.fill(PRETO)
        msg_fim = self.fonte_grande.render("GAME OVER", True, VERMELHO)
        
        motivo = f"Você terminou em {self.posicao_final_corrida}º lugar."
        msg_motivo = self.fonte.render(motivo, True, BRANCO)
        
        msg_pontos = self.fonte.render(f"Pontuação Total: {self.pontuacao_total.get_pontos_totais()}", True, AMARELO)
        msg_fase = self.fonte.render(f"Você chegou até a Fase {self.fase}", True, BRANCO)

        self.tela.blit(msg_fim, (LARGURA_TELA // 2 - msg_fim.get_width() // 2, 100))
        self.tela.blit(msg_motivo, (LARGURA_TELA // 2 - msg_motivo.get_width() // 2, 200))
        self.tela.blit(msg_fase, (LARGURA_TELA // 2 - msg_fase.get_width() // 2, 250))
        self.tela.blit(msg_pontos, (LARGURA_TELA // 2 - msg_pontos.get_width() // 2, 300))

        self.tela.blit(self.imagem_fim_jogo, self.rect_fim_jogo)
        pygame.display.flip()


    def sair_jogo(self):
        self.cronometro_corrida.parar()
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Jogo()
    game.carregar_recursos()
    game.loop_jogo()
