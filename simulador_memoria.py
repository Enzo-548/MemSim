"""
Simulador de memoria com comparacao entre os algoritmos FIFO e LRU.

Prof. Filipo - github.com/ProfessorFilipo/MemSim/
"""

import sys


class Frame:
    def __init__(self, id_frame):
        self.id_frame = id_frame
        self.pagina_alocada = None
        self.timestamp = 0


class TabelaPaginas:
    ALGORITMOS_VALIDOS = ("fifo", "lru")

    def __init__(self, num_frames, algoritmo):
        if not isinstance(num_frames, int) or num_frames < 1:
            raise ValueError("A quantidade de frames deve ser um inteiro maior que zero.")

        self.algoritmo = algoritmo.lower()
        if self.algoritmo not in self.ALGORITMOS_VALIDOS:
            raise ValueError(
                f"Algoritmo invalido: {algoritmo}. Use 'fifo' ou 'lru'."
            )

        self.frames = [Frame(i) for i in range(num_frames)]
        self.total_page_faults = 0
        self.total_acessos = 0
        self.ponteiro_fifo = 0

    @property
    def taxa_page_faults(self):
        if self.total_acessos == 0:
            return 0.0
        return (self.total_page_faults / self.total_acessos) * 100

    def acessar_pagina(self, numero_pagina):
        if not isinstance(numero_pagina, int) or numero_pagina < 0:
            raise ValueError("O numero da pagina deve ser um inteiro nao negativo.")

        self.total_acessos += 1

        for frame in self.frames:
            if frame.pagina_alocada == numero_pagina:
                frame.timestamp = self.total_acessos
                return True, frame.id_frame

        self.total_page_faults += 1

        for frame in self.frames:
            if frame.pagina_alocada is None:
                frame.pagina_alocada = numero_pagina
                frame.timestamp = self.total_acessos
                return False, frame.id_frame

        frame_vitima_id = self.substituir_pagina(numero_pagina)
        return False, frame_vitima_id

    def substituir_pagina(self, nova_pagina):
        """Substitui uma pagina conforme o algoritmo configurado."""
        if self.algoritmo == "fifo":
            frame_vitima = self.frames[self.ponteiro_fifo]
            self.ponteiro_fifo = (self.ponteiro_fifo + 1) % len(self.frames)
        else:
            frame_vitima = min(self.frames, key=lambda frame: frame.timestamp)

        frame_vitima.pagina_alocada = nova_pagina
        frame_vitima.timestamp = self.total_acessos
        return frame_vitima.id_frame

    def imprimir_mapa_memoria(
        self, passo, pagina_acessada, foi_hit, frame_alterado=None
    ):
        status = "Hit" if foi_hit else "Page Fault"
        print(
            f"\n--- Passo {passo}: Acesso a Pagina "
            f"{pagina_acessada} ({status}) ---"
        )

        for frame in self.frames:
            if frame.pagina_alocada is None:
                conteudo = "[Vazio]"
            else:
                conteudo = f"Pagina {frame.pagina_alocada}"

            marcador = ""
            if not foi_hit and frame.id_frame == frame_alterado:
                marcador = " <-- Alterado"

            print(f"[Frame {frame.id_frame}]: {conteudo}{marcador}")

        print("-" * 40)

    def obter_resultado(self):
        return {
            "algoritmo": self.algoritmo.upper(),
            "total_acessos": self.total_acessos,
            "total_page_faults": self.total_page_faults,
            "taxa_page_faults": self.taxa_page_faults,
            "frames": [frame.pagina_alocada for frame in self.frames],
        }


class ErroEntrada(ValueError):
    """Erro de validacao do arquivo de entrada."""


class Simulador:
    def __init__(self, caminho_arquivo):
        self.caminho_arquivo = caminho_arquivo

    def ler_entrada(self):
        try:
            with open(self.caminho_arquivo, "r", encoding="utf-8") as arquivo:
                linhas_validas = [
                    (numero_linha, texto.strip())
                    for numero_linha, texto in enumerate(arquivo, start=1)
                    if texto.strip() and not texto.strip().startswith("#")
                ]
        except (OSError, UnicodeError) as erro:
            if isinstance(erro, FileNotFoundError):
                raise ErroEntrada(
                    f"O arquivo '{self.caminho_arquivo}' nao foi encontrado."
                ) from erro
            raise ErroEntrada(
                f"Nao foi possivel ler o arquivo '{self.caminho_arquivo}': {erro}."
            ) from erro

        if not linhas_validas:
            raise ErroEntrada("Arquivo de entrada vazio.")

        linha_frames, texto_frames = linhas_validas[0]
        try:
            num_frames = int(texto_frames)
        except ValueError as erro:
            raise ErroEntrada(
                f"Linha {linha_frames}: a quantidade de frames deve ser um inteiro."
            ) from erro

        if num_frames < 1:
            raise ErroEntrada(
                f"Linha {linha_frames}: a quantidade de frames deve ser maior que zero."
            )

        paginas = []
        for numero_linha, texto_pagina in linhas_validas[1:]:
            try:
                pagina = int(texto_pagina)
            except ValueError as erro:
                raise ErroEntrada(
                    f"Linha {numero_linha}: a pagina deve ser um inteiro."
                ) from erro

            if pagina < 0:
                raise ErroEntrada(
                    f"Linha {numero_linha}: a pagina deve ser um inteiro nao negativo."
                )
            paginas.append(pagina)

        return num_frames, paginas

    @staticmethod
    def imprimir_estatisticas(resultado):
        print("\n================ STATS FINAIS ================")
        print(f"Total de Acessos: {resultado['total_acessos']}")
        print(f"Total de Page Faults: {resultado['total_page_faults']}")
        print(f"Taxa de Page Faults: {resultado['taxa_page_faults']:.2f}%")
        print("=" * 46)

    @staticmethod
    def executar_algoritmo(num_frames, paginas, algoritmo):
        tabela_paginas = TabelaPaginas(num_frames, algoritmo)

        print(f"\n================ ALGORITMO {algoritmo.upper()} ================")
        print(f"Iniciando simulacao com {num_frames} frames disponiveis.")
        print("=" * 40)

        for passo, numero_pagina in enumerate(paginas, start=1):
            foi_hit, frame_id = tabela_paginas.acessar_pagina(numero_pagina)
            tabela_paginas.imprimir_mapa_memoria(
                passo, numero_pagina, foi_hit, frame_id
            )

        resultado = tabela_paginas.obter_resultado()
        Simulador.imprimir_estatisticas(resultado)
        return resultado

    @staticmethod
    def comparar_resultados(resultado_fifo, resultado_lru):
        faults_fifo = resultado_fifo["total_page_faults"]
        faults_lru = resultado_lru["total_page_faults"]

        if faults_fifo < faults_lru:
            vencedor = "FIFO"
        elif faults_lru < faults_fifo:
            vencedor = "LRU"
        else:
            vencedor = "Empate"

        print("\n================ COMPARACAO FINAL ================")
        print("Algoritmo | Acessos | Page Faults | Taxa")
        print("-" * 47)
        for resultado in (resultado_fifo, resultado_lru):
            print(
                f"{resultado['algoritmo']:<9} | "
                f"{resultado['total_acessos']:>7} | "
                f"{resultado['total_page_faults']:>11} | "
                f"{resultado['taxa_page_faults']:>6.2f}%"
            )
        print("-" * 47)
        print(f"Vencedor: {vencedor}")
        print("=" * 49)
        return vencedor

    def executar(self):
        try:
            num_frames, paginas = self.ler_entrada()
        except ErroEntrada as erro:
            print(f"Erro: {erro}")
            return None

        resultado_fifo = self.executar_algoritmo(num_frames, paginas, "fifo")
        resultado_lru = self.executar_algoritmo(num_frames, paginas, "lru")
        vencedor = self.comparar_resultados(resultado_fifo, resultado_lru)

        return {
            "fifo": resultado_fifo,
            "lru": resultado_lru,
            "vencedor": vencedor,
        }


def main(argumentos=None):
    if argumentos is None:
        argumentos = sys.argv[1:]

    if len(argumentos) > 1:
        print("Uso: python simulador_memoria.py [arquivo_entrada]")
        return 1

    caminho_arquivo = argumentos[0] if argumentos else "entrada.txt"
    resultado = Simulador(caminho_arquivo).executar()
    return 0 if resultado is not None else 1


if __name__ == "__main__":
    sys.exit(main())
