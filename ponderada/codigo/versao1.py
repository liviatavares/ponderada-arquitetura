#!/usr/bin/env python3
"""
versao1.py - Questao A4, versao 1: produtor/consumidor SEM sincronizacao.

Contexto: pulseira sensorial da Tato. A thread do sensor (produtora) gera
amostras numeradas de 0 a 19.999 e a thread do motor (consumidora) as retira
de um buffer circular de N = 6 posicoes.

Nesta versao nao existe nenhum semaforo: o controle de ocupacao e feito por um
contador compartilhado (`ocupadas`) com espera ocupada (busy wait). Entre a
LEITURA e a ESCRITA desse contador ha um time.sleep(0), que entrega a CPU para
a outra thread exatamente no pior momento possivel e faz a condicao de corrida
aparecer de forma reproduzivel.

Metricas registradas: amostras consumidas, perdidas, duplicadas e travamento.

Uso:
    python3 versao1.py
Autora: Livia Saboia Tavares
"""

import threading
import time

N = 6                      # posicoes do buffer circular (3 + (D2 mod 5), D2 = 8)
TOTAL = 20_000             # amostras produzidas, numeradas de 0 a 19.999
TIMEOUT_OCIOSO = 1.0       # segundos sem receber nada => registra travamento


class EstadoCompartilhado:
    """Estado que as duas threads acessam sem nenhuma protecao.

    Atributos:
        buffer: lista de N posicoes que guarda as amostras.
        ocupadas: contador de posicoes ocupadas (a variavel disputada).
        pos_escrita / pos_leitura: indices circulares do produtor e do consumidor.
        produtor_terminou: sinaliza que o produtor acabou seu laco.
        leituras: valores retirados pelo consumidor, na ordem em que sairam.
        travou: True se o consumidor ficou TIMEOUT_OCIOSO sem receber nada.
    """

    def __init__(self):
        self.buffer = [None] * N
        self.ocupadas = 0
        self.pos_escrita = 0
        self.pos_leitura = 0
        self.produtor_terminou = False
        self.leituras = []
        self.travou = False


def produtor(estado):
    """Gera as TOTAL amostras e grava no buffer circular.

    Espera ocupada enquanto o buffer parece cheio. Depois de gravar, incrementa
    o contador em duas etapas (ler -> ceder a CPU -> escrever), o que permite
    que o incremento do consumidor seja perdido e vice-versa.

    Parametros:
        estado (EstadoCompartilhado): estado compartilhado com o consumidor.
    Retorno:
        None. O efeito e a escrita no buffer e a atualizacao do contador.
    """
    for amostra in range(TOTAL):
        while estado.ocupadas >= N and not estado.travou:
            time.sleep(0)                      # espera ocupada
        if estado.travou:
            break
        estado.buffer[estado.pos_escrita] = amostra
        estado.pos_escrita = (estado.pos_escrita + 1) % N
        lido = estado.ocupadas                 # 1) le o contador
        time.sleep(0)                          # 2) interrompida no pior momento
        estado.ocupadas = lido + 1             # 3) escreve de volta
    estado.produtor_terminou = True


def consumidor(estado):
    """Retira amostras do buffer circular e registra o que recebeu.

    Encerra quando ja fez TOTAL leituras ou quando fica TIMEOUT_OCIOSO segundos
    sem nada para consumir (registrado como travamento).

    Parametros:
        estado (EstadoCompartilhado): estado compartilhado com o produtor.
    Retorno:
        None. O efeito e preencher estado.leituras e estado.travou.
    """
    while len(estado.leituras) < TOTAL:
        inicio = time.monotonic()
        while estado.ocupadas <= 0:
            if time.monotonic() - inicio > TIMEOUT_OCIOSO:
                estado.travou = True
                return
            time.sleep(0)
        valor = estado.buffer[estado.pos_leitura]
        estado.pos_leitura = (estado.pos_leitura + 1) % N
        lido = estado.ocupadas                 # 1) le o contador
        time.sleep(0)                          # 2) interrompida no pior momento
        estado.ocupadas = lido - 1             # 3) escreve de volta
        estado.leituras.append(valor)


def apurar(leituras):
    """Calcula as metricas da execucao a partir da lista de leituras.

    Parametros:
        leituras (list): valores retirados do buffer, podendo conter None
            (posicao lida sem nunca ter sido escrita) e repeticoes.
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
    """Roda uma execucao completa da versao 1 e imprime o relatorio."""
    estado = EstadoCompartilhado()
    t_sensor = threading.Thread(target=produtor, args=(estado,), name="sensor")
    t_motor = threading.Thread(target=consumidor, args=(estado,), name="motor")

    inicio = time.monotonic()
    t_motor.start()
    t_sensor.start()
    t_sensor.join()
    t_motor.join()
    duracao = time.monotonic() - inicio

    m = apurar(estado.leituras)
    print("=" * 58)
    print(f"VERSAO 1 - sem sincronizacao | N = {N} | amostras = {TOTAL}")
    print("=" * 58)
    print(f"consumidas .......... {m['consumidas']}")
    print(f"perdidas ............ {m['perdidas']}")
    print(f"duplicadas .......... {m['duplicadas']}")
    print(f"posicoes vazias lidas {m['vazias']}")
    print(f"travou .............. {'SIM' if estado.travou else 'nao'}")
    print(f"contador final ...... {estado.ocupadas} (deveria ser 0)")
    print(f"tempo ............... {duracao:.2f} s")


if __name__ == "__main__":
    main()
