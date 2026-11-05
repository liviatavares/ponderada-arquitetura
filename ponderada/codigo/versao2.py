#!/usr/bin/env python3
"""
versao2.py - Questao A4, versao 2: produtor/consumidor COM semaforos.

Contexto: pulseira sensorial da Tato. A thread do sensor (produtora) gera
amostras numeradas de 0 a 19.999 e a thread do motor (consumidora) as retira
de um buffer circular de N = 6 posicoes.

Tres semaforos, na ordem classica:
    vazio (inicia em N) - conta posicoes livres; controle de fluxo do produtor.
    cheio (inicia em 0) - conta posicoes ocupadas; controle de fluxo do consumidor.
    mutex (inicia em 1) - exclusao mutua da regiao critica (buffer + indices).

O time.sleep(0) que quebrava a versao 1 continua aqui, dentro da regiao
critica. Como o mutex a protege, a troca de thread nesse ponto nao causa
mais perda nem duplicacao: e essa a comparacao com a versao 1.

Uso:
    python3 versao2.py
Autora: Livia Saboia Tavares
"""

import threading
import time

N = 6                      # posicoes do buffer circular (3 + (D2 mod 5), D2 = 8)
TOTAL = 20_000             # amostras produzidas, numeradas de 0 a 19.999
TIMEOUT_OCIOSO = 1.0       # segundos esperando um semaforo => registra travamento


class Buffer:
    """Buffer circular de N posicoes protegido por tres semaforos.

    Atributos:
        dados: lista de N posicoes.
        pos_escrita / pos_leitura: indices circulares.
        vazio / cheio / mutex: os tres semaforos descritos no cabecalho.
        leituras: valores retirados pelo consumidor, na ordem de saida.
        travou: True se alguma thread esperou mais de TIMEOUT_OCIOSO.
    """

    def __init__(self):
        self.dados = [None] * N
        self.pos_escrita = 0
        self.pos_leitura = 0
        self.vazio = threading.Semaphore(N)
        self.cheio = threading.Semaphore(0)
        self.mutex = threading.Semaphore(1)
        self.leituras = []
        self.travou = False


def produtor(buf):
    """Produz TOTAL amostras: P(vazio) -> P(mutex) -> grava -> V(mutex) -> V(cheio).

    Parametros:
        buf (Buffer): buffer compartilhado.
    Retorno:
        None. O efeito e gravar as amostras no buffer.
    """
    for amostra in range(TOTAL):
        if not buf.vazio.acquire(timeout=TIMEOUT_OCIOSO):   # P(vazio)
            buf.travou = True
            return
        if not buf.mutex.acquire(timeout=TIMEOUT_OCIOSO):   # P(mutex)
            buf.travou = True
            return
        buf.dados[buf.pos_escrita] = amostra                # regiao critica
        buf.pos_escrita = (buf.pos_escrita + 1) % N
        time.sleep(0)                                       # mesma janela da v1
        buf.mutex.release()                                 # V(mutex)
        buf.cheio.release()                                 # V(cheio)


def consumidor(buf):
    """Consome TOTAL amostras: P(cheio) -> P(mutex) -> le -> V(mutex) -> V(vazio).

    Parametros:
        buf (Buffer): buffer compartilhado.
    Retorno:
        None. O efeito e preencher buf.leituras.
    """
    for _ in range(TOTAL):
        if not buf.cheio.acquire(timeout=TIMEOUT_OCIOSO):   # P(cheio)
            buf.travou = True
            return
        if not buf.mutex.acquire(timeout=TIMEOUT_OCIOSO):   # P(mutex)
            buf.travou = True
            return
        valor = buf.dados[buf.pos_leitura]                  # regiao critica
        buf.pos_leitura = (buf.pos_leitura + 1) % N
        time.sleep(0)
        buf.mutex.release()                                 # V(mutex)
        buf.vazio.release()                                 # V(vazio)
        buf.leituras.append(valor)


def apurar(leituras):
    """Calcula consumidas, perdidas, duplicadas e posicoes vazias lidas.

    Parametros:
        leituras (list): valores retirados do buffer.
    Retorno:
        dict com as chaves consumidas, perdidas, duplicadas e vazias.
    """
    contagem = {}
    vazias = 0
    for valor in leituras:
        if valor is None:
            vazias += 1
            continue
        contagem[valor] = contagem.get(valor, 0) + 1
    return {
        "consumidas": sum(contagem.values()),
        "perdidas": TOTAL - len(contagem),
        "duplicadas": sum(c - 1 for c in contagem.values() if c > 1),
        "vazias": vazias,
    }


def main():
    """Roda uma execucao completa da versao 2 e imprime o relatorio."""
    buf = Buffer()
    t_sensor = threading.Thread(target=produtor, args=(buf,), name="sensor")
    t_motor = threading.Thread(target=consumidor, args=(buf,), name="motor")

    inicio = time.monotonic()
    t_motor.start()
    t_sensor.start()
    t_sensor.join()
    t_motor.join()
    duracao = time.monotonic() - inicio

    m = apurar(buf.leituras)
    print("=" * 58)
    print(f"VERSAO 2 - com semaforos | N = {N} | amostras = {TOTAL}")
    print("=" * 58)
    print(f"consumidas .......... {m['consumidas']}")
    print(f"perdidas ............ {m['perdidas']}")
    print(f"duplicadas .......... {m['duplicadas']}")
    print(f"posicoes vazias lidas {m['vazias']}")
    print(f"travou .............. {'SIM' if buf.travou else 'nao'}")
    print(f"ordem preservada .... {'sim' if buf.leituras == list(range(TOTAL)) else 'nao'}")
    print(f"tempo ............... {duracao:.2f} s")


if __name__ == "__main__":
    main()
