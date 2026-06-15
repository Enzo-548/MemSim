# Simulador de Memoria - FIFO vs LRU

Simulador de substituicao de paginas que executa os algoritmos FIFO e LRU
sobre a mesma sequencia de acessos e compara seus resultados.

## Como executar

O projeto utiliza apenas a biblioteca padrao do Python 3.

```text
python simulador_memoria.py [arquivo_entrada]
```

O caminho do arquivo e opcional. Quando ele nao for informado, o simulador
utiliza `entrada.txt`.

Exemplo:

```text
python simulador_memoria.py entrada.txt
```

Cada execucao processa primeiro o FIFO e depois o LRU. Ao final, o programa
exibe uma tabela comparativa e indica o algoritmo com menos Page Faults. Se os
dois obtiverem o mesmo resultado, sera informado um empate.

## Formato da entrada

A primeira linha valida informa a quantidade de frames. As demais linhas
informam, uma por linha, as paginas acessadas.

```text
3
7
0
1
2
```

Linhas vazias e linhas iniciadas por `#` sao ignoradas. A quantidade de frames
deve ser maior que zero, e as paginas devem ser numeros inteiros nao negativos.
Um arquivo contendo somente a quantidade de frames e valido.

## Algoritmos

- **FIFO:** um ponteiro circular indica o frame que contem a pagina carregada
  ha mais tempo. A cada substituicao, o ponteiro avanca para o proximo frame.
- **LRU:** cada frame armazena o instante do ultimo acesso. Hits tambem
  atualizam esse valor, e a pagina com o menor timestamp e substituida.

## OUTPUT

Para cada algoritmo, o estado dos frames e exibido depois de cada acesso. Um
Page Fault destaca somente o frame preenchido ou substituido.

```text
================ ALGORITMO FIFO ================
Iniciando simulacao com 3 frames disponiveis.
========================================

--- Passo 1: Acesso a Pagina 7 (Page Fault) ---
[Frame 0]: Pagina 7 <-- Alterado
[Frame 1]: [Vazio]
[Frame 2]: [Vazio]
----------------------------------------

--- Passo 2: Acesso a Pagina 0 (Page Fault) ---
[Frame 0]: Pagina 7
[Frame 1]: Pagina 0 <-- Alterado
[Frame 2]: [Vazio]
----------------------------------------

--- Passo 3: Acesso a Pagina 7 (Hit) ---
[Frame 0]: Pagina 7
[Frame 1]: Pagina 0
[Frame 2]: [Vazio]
----------------------------------------

================ STATS FINAIS ================
Total de Acessos: 3
Total de Page Faults: 2
Taxa de Page Faults: 66.67%
==============================================
```

Depois das simulacoes FIFO e LRU, o resumo segue este formato:

```text
================ COMPARACAO FINAL ================
Algoritmo | Acessos | Page Faults | Taxa
-----------------------------------------------
FIFO      |      12 |          10 |  83.33%
LRU       |      12 |           9 |  75.00%
-----------------------------------------------
Vencedor: LRU
=================================================
```

## Testes

Execute toda a suite com:

```text
python -m unittest discover -s tests -v
```

Os testes cobrem os algoritmos, as estatisticas, a formatacao principal da
saida, a comparacao e os erros de entrada.
