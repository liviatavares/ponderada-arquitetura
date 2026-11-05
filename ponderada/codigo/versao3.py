#!/usr/bin/env python3
"""
versao3.py - Questao A4, versao 3: ordem dos semaforos trocada (deadlock).

Identica a versao 2, com UMA diferenca: o produtor faz
    P(mutex) antes de P(vazio)
em vez de P(vazio) antes de P(mutex).

Consequencia: quando o buffer enche, o produtor ja esta com o mutex na mao e
dorme em `vazio`. O consumidor consegue passar por P(cheio), mas trava em
P(mutex), que o produtor nunca vai liberar. Nenhum dos dois avanca: deadlock
classico de posse e espera com espera circular.

Para o programa nao ficar preso, o consumidor tem um watchdog: se esperar mais
de 1 s por um semaforo, marca travamento e desiste. As threads sao daemon, para
que o processo encerre sozinho sem Ctrl+C mesmo com o produtor dormindo.

Uso:
    python3 versao3.py
Autora: Livia Saboia Tavares
"""

import threading
import time

N = 6                      # posicoes do buffer circular (3 + (D2 mod 5), D2 = 8)
TOTAL = 20_000             # amostras produzidas, numeradas de 0 a 19.999
TIMEOUT_OCIOSO = 1.0       # segundos esperando um semaforo => registra travamento


class Buffer:
    """Buffer circular de N posicoes com os mesmos tres semaforos da versao 2.

    Atributos:
        dados: lista de N posicoes.
        pos_escrita / pos_leitura: indices circulares.
        vazio / cheio / mutex: semaforos (N, 0, 1).
        leituras: valores retirados pelo consumidor.
        travou: True se o watchdog disparou.
        diagnostico: texto curto dizendo onde cada thread parou.
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
        self.diagnostico = ""
        self.produzidas = 0


def produtor(buf):
    """Produz as amostras na ORDEM ERRADA: P(mutex) -> P(vazio) -> grava.

    Parametros:
        buf (Buffer): buffer compartilhado.
    Retorno:
        None. Fica bloqueada para sempre em P(vazio) quando o buffer enche,
        ainda segurando o mutex.
    """
    for amostra in range(TOTAL):
        buf.mutex.acquire()                                 # P(mutex)  <-- trocado
        buf.vazio.acquire()                                 # P(vazio)  <-- trocado
        buf.dados[buf.pos_escrita] = amostra                # regiao critica
        buf.pos_escrita = (buf.pos_escrita + 1) % N
        buf.produzidas += 1
        time.sleep(0)
        buf.mutex.release()                                 # V(mutex)
        buf.cheio.release()                                 # V(cheio)


def consumidor(buf):
    """Consome as amostras na ordem correta, com watchdog de TIMEOUT_OCIOSO.

    Parametros:
        buf (Buffer): buffer compartilhado.
    Retorno:
        None. Se o watchdog disparar, preenche buf.travou e buf.diagnostico.
    """
    for _ in range(TOTAL):
        if not buf.cheio.acquire(timeout=TIMEOUT_OCIOSO):   # P(cheio)
            buf.travou = True
            buf.diagnostico = "consumidor bloqueado em P(cheio): buffer vazio"
            return
        if not buf.mutex.acquire(timeout=TIMEOUT_OCIOSO):   # P(mutex)
            buf.travou = True
            buf.diagnostico = ("consumidor bloqueado em P(mutex); o mutex esta "
                               "com o produtor, que dorme em P(vazio)")
            return
        valor = buf.dados[buf.pos_leitura]
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
    """Roda uma execucao da versao 3, detecta o deadlock e imprime o relatorio."""
    buf = Buffer()
    # daemon=True: o processo encerra mesmo com o produtor preso em P(vazio).
    t_sensor = threading.Thread(target=produtor, args=(buf,), name="sensor", daemon=True)
    t_motor = threading.Thread(target=consumidor, args=(buf,), name="motor", daemon=True)

    inicio = time.monotonic()
    t_motor.start()
    t_sensor.start()
    t_motor.join()                       # o watchdog esta no consumidor
    duracao = time.monotonic() - inicio

    m = apurar(buf.leituras)
    print("=" * 58)
    print(f"VERSAO 3 - ordem trocada no produtor | N = {N} | amostras = {TOTAL}")
    print("=" * 58)
    print(f"consumidas .......... {m['consumidas']}")
    print(f"perdidas ............ {m['perdidas']}")
    print(f"duplicadas .......... {m['duplicadas']}")
    print(f"posicoes vazias lidas {m['vazias']}")
    print(f"travou .............. {'SIM (deadlock)' if buf.travou else 'nao'}")
    print(f"produzidas ate travar {buf.produzidas}")
    print(f"diagnostico ......... {buf.diagnostico}")
    print(f"sensor ainda viva ... {t_sensor.is_alive()} (presa em P(vazio) com o mutex)")
    print(f"tempo ............... {duracao:.2f} s")
    print("encerrado pelo watchdog de 1 s, sem Ctrl+C (threads daemon)")


if __name__ == "__main__":
    main()
