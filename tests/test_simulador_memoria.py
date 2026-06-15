import io
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from simulador_memoria import ErroEntrada, Simulador, TabelaPaginas, main


SEQUENCIA_README = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3]
RAIZ_PROJETO = Path(__file__).resolve().parents[1]


class TabelaPaginasTests(unittest.TestCase):
    def test_carregamento_inicial_e_hit(self):
        tabela = TabelaPaginas(2, "fifo")

        self.assertEqual(tabela.acessar_pagina(5), (False, 0))
        self.assertEqual(tabela.acessar_pagina(5), (True, 0))
        self.assertEqual(tabela.total_acessos, 2)
        self.assertEqual(tabela.total_page_faults, 1)
        self.assertEqual([frame.pagina_alocada for frame in tabela.frames], [5, None])

    def test_fifo_substitui_frames_em_ordem_circular(self):
        tabela = TabelaPaginas(3, "fifo")
        resultados = [tabela.acessar_pagina(pagina) for pagina in [1, 2, 3, 4, 5]]

        self.assertEqual(resultados[-2], (False, 0))
        self.assertEqual(resultados[-1], (False, 1))
        self.assertEqual([frame.pagina_alocada for frame in tabela.frames], [4, 5, 3])
        self.assertEqual(tabela.ponteiro_fifo, 2)

    def test_lru_atualiza_timestamp_no_hit_e_escolhe_vitima(self):
        tabela = TabelaPaginas(3, "lru")
        for pagina in [1, 2, 3, 1]:
            tabela.acessar_pagina(pagina)

        self.assertEqual(tabela.frames[0].timestamp, 4)
        self.assertEqual(tabela.acessar_pagina(4), (False, 1))
        self.assertEqual([frame.pagina_alocada for frame in tabela.frames], [1, 4, 3])

    def test_pagina_invalida_na_api(self):
        tabela = TabelaPaginas(2, "fifo")
        with self.assertRaises(ValueError):
            tabela.acessar_pagina(-1)

    def test_numero_de_frames_invalido_na_api(self):
        with self.assertRaises(ValueError):
            TabelaPaginas(0, "fifo")


class SimuladorTests(unittest.TestCase):
    @staticmethod
    def remover_arquivo(caminho):
        if os.path.exists(caminho):
            os.unlink(caminho)

    def criar_entrada(self, conteudo):
        arquivo = tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", delete=False
        )
        self.addCleanup(self.remover_arquivo, arquivo.name)
        arquivo.write(conteudo)
        arquivo.close()
        return arquivo.name

    def executar_sem_saida(self, caminho):
        saida = io.StringIO()
        with redirect_stdout(saida):
            resultado = Simulador(caminho).executar()
        return resultado, saida.getvalue()

    def test_estatisticas_da_sequencia_do_readme(self):
        conteudo = "3\n" + "\n".join(map(str, SEQUENCIA_README))
        resultado, _ = self.executar_sem_saida(self.criar_entrada(conteudo))

        self.assertEqual(resultado["fifo"]["total_page_faults"], 10)
        self.assertAlmostEqual(
            resultado["fifo"]["taxa_page_faults"], 83.3333, places=3
        )
        self.assertEqual(resultado["fifo"]["frames"], [0, 2, 3])
        self.assertEqual(resultado["lru"]["total_page_faults"], 9)
        self.assertAlmostEqual(resultado["lru"]["taxa_page_faults"], 75.0)
        self.assertEqual(resultado["lru"]["frames"], [0, 3, 2])
        self.assertEqual(resultado["vencedor"], "LRU")

    def test_comparacao_reconhece_fifo_lru_e_empate(self):
        def resultado(nome, faults):
            return {
                "algoritmo": nome,
                "total_acessos": 5,
                "total_page_faults": faults,
                "taxa_page_faults": faults / 5 * 100,
                "frames": [],
            }

        with redirect_stdout(io.StringIO()):
            self.assertEqual(
                Simulador.comparar_resultados(
                    resultado("FIFO", 2), resultado("LRU", 3)
                ),
                "FIFO",
            )
            self.assertEqual(
                Simulador.comparar_resultados(
                    resultado("FIFO", 4), resultado("LRU", 3)
                ),
                "LRU",
            )
            self.assertEqual(
                Simulador.comparar_resultados(
                    resultado("FIFO", 3), resultado("LRU", 3)
                ),
                "Empate",
            )

    def test_hit_nao_marca_frame_como_alterado(self):
        tabela = TabelaPaginas(2, "fifo")
        tabela.acessar_pagina(7)

        saida = io.StringIO()
        with redirect_stdout(saida):
            tabela.imprimir_mapa_memoria(2, 7, True, 0)

        self.assertNotIn("<-- Alterado", saida.getvalue())

    def test_page_fault_marca_somente_um_frame(self):
        tabela = TabelaPaginas(2, "fifo")
        _, frame_id = tabela.acessar_pagina(7)

        saida = io.StringIO()
        with redirect_stdout(saida):
            tabela.imprimir_mapa_memoria(1, 7, False, frame_id)

        self.assertEqual(saida.getvalue().count("<-- Alterado"), 1)

    def test_comentarios_e_linhas_vazias_sao_ignorados(self):
        caminho = self.criar_entrada("# comentario\n\n2\n1\n\n# outro\n1\n")
        simulador = Simulador(caminho)

        self.assertEqual(simulador.ler_entrada(), (2, [1, 1]))

    def test_arquivo_apenas_com_frames_e_valido_e_empata(self):
        resultado, _ = self.executar_sem_saida(self.criar_entrada("4\n"))

        self.assertEqual(resultado["fifo"]["total_acessos"], 0)
        self.assertEqual(resultado["lru"]["taxa_page_faults"], 0.0)
        self.assertEqual(resultado["vencedor"], "Empate")

    def test_erros_de_entrada(self):
        casos = [
            ("", "Arquivo de entrada vazio"),
            ("0\n1\n", "Linha 1: a quantidade de frames deve ser maior que zero"),
            ("-2\n1\n", "Linha 1: a quantidade de frames deve ser maior que zero"),
            ("dois\n1\n", "Linha 1: a quantidade de frames deve ser um inteiro"),
            ("2\nabc\n", "Linha 2: a pagina deve ser um inteiro"),
            ("2\n-1\n", "Linha 2: a pagina deve ser um inteiro nao negativo"),
        ]

        for conteudo, mensagem in casos:
            with self.subTest(conteudo=conteudo):
                with self.assertRaisesRegex(ErroEntrada, mensagem):
                    Simulador(self.criar_entrada(conteudo)).ler_entrada()

    def test_arquivo_inexistente_nao_gera_traceback(self):
        caminho = str(RAIZ_PROJETO / "arquivo-que-nao-existe.txt")
        resultado, saida = self.executar_sem_saida(caminho)

        self.assertIsNone(resultado)
        self.assertIn("nao foi encontrado", saida)
        self.assertNotIn("Traceback", saida)

    def test_main_rejeita_argumentos_extras(self):
        saida = io.StringIO()
        with redirect_stdout(saida):
            codigo = main(["entrada.txt", "fifo"])

        self.assertEqual(codigo, 1)
        self.assertIn("Uso:", saida.getvalue())

    def test_main_sem_argumentos_usa_entrada_padrao(self):
        with tempfile.TemporaryDirectory() as diretorio:
            Path(diretorio, "entrada.txt").write_text("2\n1\n1\n", encoding="utf-8")
            saida = io.StringIO()
            diretorio_anterior = os.getcwd()
            try:
                os.chdir(diretorio)
                with redirect_stdout(saida):
                    codigo = main([])
            finally:
                os.chdir(diretorio_anterior)

        self.assertEqual(codigo, 0)
        self.assertIn("COMPARACAO FINAL", saida.getvalue())

    def test_execucao_com_python_3(self):
        processo = subprocess.run(
            [sys.executable, "simulador_memoria.py", "entrada.txt"],
            cwd=RAIZ_PROJETO,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

        self.assertEqual(processo.returncode, 0, processo.stderr)
        self.assertIn("ALGORITMO FIFO", processo.stdout)
        self.assertIn("ALGORITMO LRU", processo.stdout)
        self.assertIn("COMPARACAO FINAL", processo.stdout)
        self.assertNotIn("Traceback", processo.stderr)


if __name__ == "__main__":
    unittest.main()
