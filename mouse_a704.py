"""Daemon para el mouse generico Instant A704 (USB 30fa:1701) en Windows.

- Aplica botones limpios al chip (no guarda nada: hay que reaplicar al reconectar).
- Escucha el canal vendor 0xFF00 y convierte los botones en "Key Input" en acciones:
    pulgar (07)  -> clic izquierdo mantenido (disparar en Horizon con el derecho apuntando)
    chico  (09)  -> Win+Shift+S (recortar pantalla)
    rueda arriba (08) -> Ctrl+V (pegar)
Protocolo: github.com/AmberIsFrozen/Instant-A704F-Mouse-Utilities (SPECS.md), mas los
codigos 07 y 09 encontrados en un modelo de 10 botones (ver README).
"""
import ctypes
import logging
import logging.handlers
import os
import sys
import time

import hid

VID, PID = 0x30FA, 0x1701
CARPETA = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(CARPETA, "mouse_a704.log")

# Codigo fisico -> accion del chip. 0x00 = Key Input (solo avisa por 0xFF00).
BOTONES = {
    0x01: 0x01,  # izquierdo  -> clic izquierdo
    0x02: 0x02,  # rueda      -> clic central
    0x03: 0x03,  # derecho    -> clic derecho
    0x04: 0x04,  # lateral 2  -> Atras
    0x05: 0x05,  # lateral 1  -> Adelante
    0x06: 0x00,  # sin boton fisico conocido: neutralizado
    0x07: 0x00,  # pulgar     -> lo maneja este programa (venia con Win+D de fabrica)
    0x08: 0x00,  # encima de la rueda -> lo maneja este programa
    0x09: 0x00,  # chico debajo de los laterales -> lo maneja este programa
}

u32 = ctypes.windll.user32
k32 = ctypes.WinDLL("kernel32", use_last_error=True)
_mutex = None  # se guarda para que el mutex viva mientras corra el proceso

VK_LWIN, VK_SHIFT, VK_CONTROL = 0x5B, 0x10, 0x11
KEYUP = 0x0002
MOUSE_LEFTDOWN, MOUSE_LEFTUP = 0x0002, 0x0004


def combo(*teclas):
    for vk in teclas:
        u32.keybd_event(vk, 0, 0, 0)
    for vk in reversed(teclas):
        u32.keybd_event(vk, 0, KEYUP, 0)


class Estado:
    izquierdo_simulado = False


def soltar_izquierdo():
    if Estado.izquierdo_simulado:
        u32.mouse_event(MOUSE_LEFTUP, 0, 0, 0, 0)
        Estado.izquierdo_simulado = False


def manejar(boton, presionado):
    if boton == 0xF7:  # pulgar: clic izquierdo mientras se mantiene
        if presionado and not Estado.izquierdo_simulado:
            u32.mouse_event(MOUSE_LEFTDOWN, 0, 0, 0, 0)
            Estado.izquierdo_simulado = True
        elif not presionado:
            soltar_izquierdo()
    elif boton == 0xF9 and presionado:  # chico: recortar
        combo(VK_LWIN, VK_SHIFT, ord("S"))
    elif boton == 0xF8 and presionado:  # encima de la rueda: pegar
        combo(VK_CONTROL, ord("V"))


def ruta(usage_page):
    for d in hid.enumerate(VID, PID):
        if d["usage_page"] == usage_page:
            return d["path"]
    return None


def aplicar_botones():
    h = hid.device()
    h.open_path(ruta(0xFF01))
    try:
        for fisico, accion in BOTONES.items():
            h.send_feature_report([0x07, 0x10, fisico, accion, 0, 0, 0, 0])
            time.sleep(0.03)
    finally:
        h.close()


def sesion():
    """Aplica la configuracion y escucha hasta que el mouse se desconecte."""
    aplicar_botones()
    logging.info("configuracion aplicada")
    lector = hid.device()
    lector.open_path(ruta(0xFF00))
    try:
        while True:
            r = lector.read(16, 500)  # lanza excepcion si se desconecta
            if r and r[0] == 0x06 and len(r) >= 3:
                manejar(r[1], presionado=not (r[2] & 0x80))
    finally:
        soltar_izquierdo()
        lector.close()


def una_sola_instancia():
    global _mutex
    _mutex = k32.CreateMutexW(None, False, "Local\\mouse_a704_daemon")
    return ctypes.get_last_error() != 183  # ERROR_ALREADY_EXISTS


def main():
    if not una_sola_instancia():
        return
    manejador = logging.handlers.RotatingFileHandler(LOG, maxBytes=512_000, backupCount=1,
                                                     encoding="utf-8")
    logging.basicConfig(level=logging.INFO, handlers=[manejador],
                        format="%(asctime)s %(levelname)s %(message)s")
    logging.info("iniciado")
    avisado = False
    ultimo_error = None
    while True:
        if ruta(0xFF01) and ruta(0xFF00):
            avisado = False
            try:
                sesion()
            except Exception as e:  # desconexion u otro error de E/S
                if str(e) != ultimo_error:  # no repetir el mismo error cada 2 s
                    logging.info("sesion terminada: %s", e)
                    ultimo_error = str(e)
        elif not avisado:
            logging.info("mouse no conectado; esperando")
            avisado = True
        time.sleep(2)


if __name__ == "__main__":
    sys.exit(main())
