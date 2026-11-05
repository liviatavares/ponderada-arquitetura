# Ponderada do pipeline ao deadlock

Nome: **Lívia Sabóia Tavares**

## Estrutura

```
.
├── README.md
├── .gitignore
└── ponderada/
    ├── ponderada-tato.md   # Parte A (técnica) e Parte B (decisão do CTO)
    ├── codigo/             # questão A4: produtor/consumidor com buffer circular
    │   ├── versao1.py      # sem sincronização
    │   ├── versao2.py      # com semáforos (vazio, cheio, mutex)
    │   └── versao3.py      # ordem dos semáforos trocada no produtor (deadlock)
    └── img/                # prints
```

## Como rodar a questão A4

Requisito: Python 3.8 ou superior. Não há dependências externas, só a biblioteca padrão (`threading`, `time`).

Cada versão roda com um único comando, a partir da pasta `ponderada/codigo`:

```bash
cd ponderada/codigo

python3 versao1.py   # sem sincronização: perde e duplica amostras
python3 versao2.py   # com semáforos: entrega as 20.000 amostras
python3 versao3.py   # ordem trocada: deadlock, encerra pelo watchdog de 1 s
```

Para repetir as três execuções de cada versão, como na tabela da A4.1:

```bash
cd ponderada/codigo
for v in 1 2 3; do for r in 1 2 3; do echo "### versao$v execucao$r"; python3 versao$v.py; done; done
```

Parâmetros no topo de cada arquivo: `N = 6` (tamanho do buffer), `TOTAL = 20000` (amostras) e `TIMEOUT_OCIOSO = 1.0` (segundos sem receber nada até registrar travamento).

Cada execução imprime amostras consumidas, perdidas, duplicadas e se travou. As três terminam sozinhas: nenhuma precisa de `Ctrl+C`, inclusive a versão 3, que detecta o deadlock por timeout nos semáforos e usa threads daemon.

Tempos aproximados: versão 1 cerca de 2,5 s, versão 2 cerca de 2,7 s, versão 3 exatamente 1,0 s (o tempo do watchdog).
