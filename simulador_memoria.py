###
###     S I M U L A D O R    D E    M E M Ó R I A
###
### Prof. Filipo - github.com/ProfessorFilipo/MemSim/
###

import sys


class Frame:
    def __init__(self, id_frame):
        self.id_frame = id_frame
        self.pagina_alocada = None  # Armazena o número da página ou None se estiver vazio
        self.timestamp = 0  # Timestamp de acesso usado pelo LRU
        # Dica para os alunos: vocês podem adicionar atributos aqui para ajudar no algoritmo (ex: timestamp, contador)


class TabelaPaginas:
    def __init__(self, num_frames, algoritmo="fifo"):
        # Inicializa a memória física com a quantidade de frames especificada
        self.frames = [Frame(i) for i in range(num_frames)]
        self.total_page_faults = 0
        self.total_acessos = 0
        self.ponteiro_fifo = 0  # Controla a ordem de chegada para o FIFO
        self.algoritmo = algoritmo.lower()

        if self.algoritmo not in ("fifo", "lru"):
            raise ValueError(f"Algoritmo invalido: {algoritmo}. Use 'fifo' ou 'lru'.")

    def acessar_pagina(self, numero_pagina):
        self.total_acessos += 1

        # 1. Verificar se a página já está em algum frame (Hit)
        for frame in self.frames:
            if frame.pagina_alocada == numero_pagina:
                frame.timestamp = self.total_acessos
                return True, frame.id_frame  # Retorna (Hit=True, frame_id)

        # 2. Se não encontrou, ocorreu um Page Fault!
        self.total_page_faults += 1

        # 3. Verificar se existe algum frame vazio disponível
        for frame in self.frames:
            if frame.pagina_alocada is None:
                frame.pagina_alocada = numero_pagina
                frame.timestamp = self.total_acessos
                return False, frame.id_frame  # Retorna (Hit=False, frame_id)

        # 4. Memória cheia: Aplicar algoritmo de substituição de página
        frame_vitima_id = self.substituir_pagina(numero_pagina)
        return False, frame_vitima_id

    def substituir_pagina(self, nova_pagina):
        """
        Substitui uma página usando o algoritmo configurado (FIFO ou LRU).
        """
        if self.algoritmo == "fifo":
            # O frame escolhido é o mais antigo (apontado pelo ponteiro FIFO)
            frame_escolhido_id = self.ponteiro_fifo

            # Atualiza a página no frame
            self.frames[frame_escolhido_id].pagina_alocada = nova_pagina
            self.frames[frame_escolhido_id].timestamp = self.total_acessos

            # Avança o ponteiro de forma circular (módulo número de frames)
            self.ponteiro_fifo = (self.ponteiro_fifo + 1) % len(self.frames)
            return frame_escolhido_id

        # LRU: escolhe o frame com menor timestamp de último acesso.
        frame_vitima = min(self.frames, key=lambda frame: frame.timestamp)
        frame_vitima.pagina_alocada = nova_pagina
        frame_vitima.timestamp = self.total_acessos

        return frame_vitima.id_frame

    def imprimir_mapa_memoria(self, passo, pagina_acessada, foi_hit, frame_alterado=None):
        """
        TODO: IMPLEMENTAR PELO GRUPO
        Esta função deve imprimir o estado atual da memória física (frames) no terminal,
        conforme o padrão visual exigido no enunciado do trabalho.
        """
        status = "Hit" if foi_hit else "Page Fault"
        print(f"\n--- Passo {passo}: Acesso a Pagina {pagina_acessada} ({status}) ---")

        # Exemplo de iteração sobre os frames para os alunos completarem o print:
        for frame in self.frames:
            conteudo = f"Pagina {frame.pagina_alocada}" if frame.pagina_alocada is not None else "[Vazio]"
            marcador = " <-- Alterado" if frame.id_frame == frame_alterado and not foi_hit else ""
            print(f"[Frame {frame.id_frame}]: {conteudo}{marcador}")

        print("-" * 40)

    def imprimir_configuracao_final(self):
        print("\n================ CONFIGURACAO FINAL ================")
        for frame in self.frames:
            conteudo = f"Pagina {frame.pagina_alocada}" if frame.pagina_alocada is not None else "[Vazio]"
            print(f"[Frame {frame.id_frame}]: {conteudo}")


class Simulador:
    def __init__(self, caminho_arquivo, algoritmo="fifo"):
        self.caminho_arquivo = caminho_arquivo
        self.algoritmo = algoritmo.lower()

    def executar(self):
        try:
            with open(self.caminho_arquivo, 'r') as arquivo:
                linhas = arquivo.readlines()
        except FileNotFoundError:
            print(f"Erro: O arquivo '{self.caminho_arquivo}' nao foi encontrado.")
            return

        # Limpa linhas vazias ou comentários se houver
        linhas = [l.strip() for l in linhas if l.strip() and not l.strip().startswith('#')]

        if not linhas:
            print("Erro: Arquivo de entrada vazio.")
            return

        # A primeira linha válida define o número de frames na memória RAM simulada
        num_frames = int(linhas[0])
        tabela_paginas = TabelaPaginas(num_frames, self.algoritmo)

        print(f"Iniciando simulacao com {num_frames} frames disponiveis.")
        print(f"Algoritmo selecionado: {self.algoritmo.upper()}")
        print("=" * 40)

        # As linhas seguintes são a sequência de acessos às páginas
        passo = 1
        for linha in linhas[1:]:
            numero_pagina = int(linha)

            # Processa o acesso na tabela de páginas
            foi_hit, frame_id = tabela_paginas.acessar_pagina(numero_pagina)

            # Renderiza o mapa de memória para o aluno ver o passo a passo
            tabela_paginas.imprimir_mapa_memoria(passo, numero_pagina, foi_hit, frame_id)
            passo += 1

        # Exibição das estatísticas finais da simulação
        print("\n================ ESTATISTICAS FINAIS ================")
        print(f"Total de Acessos: {tabela_paginas.total_acessos}")
        print(f"Total de Page Faults: {tabela_paginas.total_page_faults}")
        if tabela_paginas.total_acessos > 0:
            taxa_faults = (tabela_paginas.total_page_faults / tabela_paginas.total_acessos) * 100
            print(f"Taxa de Page Faults: {taxa_faults:.2f}%")

        tabela_paginas.imprimir_configuracao_final()

        print("==============================================")


if __name__ == "__main__":
    # Permite passar o arquivo de entrada por argumento de linha de comando ou usa um padrão
    arquivo_entrada = sys.argv[1] if len(sys.argv) > 1 else "entrada.txt"
    algoritmo = sys.argv[2] if len(sys.argv) > 2 else "fifo"
    simulador = Simulador(arquivo_entrada, algoritmo)
    simulador.executar()
