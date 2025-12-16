import argparse
from cryptography.hazmat.primitives import hashes


def md5Hex(texto):
    h = hashes.Hash(hashes.MD5())
    h.update(texto.encode("utf-8"))
    b = h.finalize()
    return b.hex()


def sha256Hex(texto):
    h = hashes.Hash(hashes.SHA256())
    h.update(texto.encode("utf-8"))
    b = h.finalize()
    return b.hex()


def numeroDesdeTexto(texto, minimo, maximo):
    resumen = sha256Hex(texto)
    parte = resumen[0:8]
    numero = int(parte, 16)
    rango = maximo - minimo + 1
    numero = numero % rango
    numero = numero + minimo
    return numero


class Juego:
    def __init__(self, nombre, tipo):
        self.JUEGO_NOMBRE = nombre
        self.JUEGO_TIPO = tipo
        self.JUEGO_ID = self.GenerarID()

    def GenerarID(self):
        texto = self.JUEGO_NOMBRE + self.JUEGO_TIPO
        return md5Hex(texto)

    def Imprimir(self):
        print(self.JUEGO_NOMBRE, "-", self.JUEGO_TIPO, "-", self.JUEGO_ID)


class Jugador:
    def __init__(self, nombre, correo):
        self.JUGADOR_NAME = nombre
        self.JUGADOR_MAIL = correo
        self.JUGADOR_ID = numeroDesdeTexto(nombre + correo, 1000, 9999)
        self.JUGADOR_KEY = self.CrearKey()
        self.JUEGOS = {}

    def CrearKey(self):
        nombre = self.JUGADOR_NAME.strip()

        letra = ""
        if len(nombre) > 0:
            letra = nombre[0].upper()

        ultimas = ""
        if len(nombre) >= 2:
            ultimas = nombre[-2:].lower()

        texto = letra + ultimas + "ufv."
        return sha256Hex(texto)

    def ListaJuegos(self, ficheroRegistros, juegosDisponibles):
        juegosId = {}
        for item in juegosDisponibles:
            partes = item.split("-", 1)
            if len(partes) == 2:
                j = Juego(partes[0], partes[1])
                juegosId[j.JUEGO_ID] = j

        f = open(ficheroRegistros, "r", encoding="utf-8")
        lineas = f.readlines()
        f.close()

        for linea in lineas:
            linea = linea.strip()
            if linea == "":
                continue

            partes = linea.split("||")
            if len(partes) != 4:
                continue

            idJuego = partes[0]
            clave = partes[1]
            puntosTexto = partes[3]

            if clave != self.JUGADOR_KEY:
                continue

            if idJuego in juegosId:
                puntos = 0
                if puntosTexto.isdigit():
                    puntos = int(puntosTexto)

                juegoObj = juegosId[idJuego]
                nombreJuego = juegoObj.JUEGO_NOMBRE

                if nombreJuego not in self.JUEGOS:
                    self.JUEGOS[nombreJuego] = {"JUEGO": juegoObj, "PUNTOS": 0}

                total = self.JUEGOS[nombreJuego]["PUNTOS"]
                total = total + puntos
                self.JUEGOS[nombreJuego]["PUNTOS"] = total

    def Puntuacion(self, nombreJuego=None):
        if nombreJuego is None:
            for n in self.JUEGOS:
                print(n + ":", self.JUEGOS[n]["PUNTOS"])
            return

        if nombreJuego in self.JUEGOS:
            print(nombreJuego + ":", self.JUEGOS[nombreJuego]["PUNTOS"])
            return

        print(nombreJuego + ":", 0)

    def Imprimir(self):
        print("Jugador:", self.JUGADOR_NAME, "-", self.JUGADOR_MAIL)
        print("ID:", self.JUGADOR_ID)
        print("KEY:", self.JUGADOR_KEY)


class ListaJugadores:
    def __init__(self, ruta):
        self.FICHERO = ruta
        self.JUGADORES = []
        self.leer()

    def leer(self):
        f = open(self.FICHERO, "r", encoding="utf-8")
        lineas = f.readlines()
        f.close()

        for linea in lineas:
            linea = linea.strip()
            if linea == "":
                continue

            partes = linea.split("@@")
            if len(partes) != 2:
                continue

            nombre = partes[0].strip()
            correo = partes[1].strip()

            self.JUGADORES.append(Jugador(nombre, correo))

    def Imprimir(self):
        for j in self.JUGADORES:
            j.Imprimir()


class Diagnostico:
    def __init__(self, ficheroRegistro, jugadores, juegos):
        self.FICHERO_REGISTRO = ficheroRegistro
        self.JUGADORES = jugadores
        self.JUEGOS = juegos

        self.claves = set()
        for j in self.JUGADORES:
            self.claves.add(j.JUGADOR_KEY)

        self.juegosValidos = set()
        for item in self.JUEGOS:
            partes = item.split("-", 1)
            if len(partes) == 2:
                juego = Juego(partes[0], partes[1])
                self.juegosValidos.add(juego.JUEGO_ID)

    def GenFraudulentos(self):
        f = open(self.FICHERO_REGISTRO, "r", encoding="utf-8")
        lineas = f.readlines()
        f.close()

        salida = []
        unicos = set()

        cntP = 0
        cntJ = 0
        dias = {}

        for linea in lineas:
            linea = linea.strip()
            if linea == "":
                continue

            partes = linea.split("||")
            if len(partes) != 4:
                continue

            idJuego = partes[0]
            clave = partes[1]
            fecha = partes[2]

            if clave not in self.claves:
                texto = "PLAYER##" + clave + "##" + fecha
                if texto not in unicos:
                    unicos.add(texto)
                    salida.append(texto)
                cntP = cntP + 1
                if fecha not in dias:
                    dias[fecha] = []
                if "PLAYER" not in dias[fecha]:
                    dias[fecha].append("PLAYER")

            if idJuego not in self.juegosValidos:
                texto = "GAME##" + idJuego + "##" + fecha
                if texto not in unicos:
                    unicos.add(texto)
                    salida.append(texto)
                cntJ = cntJ + 1
                if fecha not in dias:
                    dias[fecha] = []
                if "GAME" not in dias[fecha]:
                    dias[fecha].append("GAME")

        out = open("BAD_REGISTERS.log", "w+", encoding="utf-8")
        for linea in salida:
            out.write(linea + "\n")
        out.close()

        return cntP, cntJ, dias

    def Informe(self, dias):
        lista = sorted(dias.keys(), key=self.claveFecha)
        for fecha in lista:
            tipos = dias[fecha]
            texto = ", ".join(tipos)
            print(fecha + ":", texto)

    def claveFecha(self, fecha):
        partes = fecha.split("/")
        if len(partes) != 3:
            return fecha
        return partes[2] + partes[1] + partes[0]


def crearParser():
    p = argparse.ArgumentParser()
    p.add_argument("-p", "--players", default="PLAYERS-1.txt")
    p.add_argument("-r", "--registros", default="REGISTROS-2.log")
    return p


if __name__ == "__main__":
    listaJuegos = [
        "Mus-Cartas",
        "Laberinto-Tablero",
        "Poker-Cartas",
        "Basket-Deporte",
        "LOL-Videojuego",
        "Fornite-Videojuego",
        "Pocha-Cartas",
        "Catan-Tablero",
        "Monopoly-Tablero",
        "Virus-Cartas",
        "Heroquest-Tablero",
        "Futbol-Deporte",
        "Damas-Tablero",
        "Ajedrez-Tablero",
    ]

    parser = crearParser()
    args = parser.parse_args()

    jugadores = ListaJugadores(args.players)

    d = Diagnostico(args.registros, jugadores.JUGADORES, listaJuegos)
    falsosPlayer, falsosGame, dias = d.GenFraudulentos()

    print("Registros falsos de jugadores:", falsosPlayer)
    print("Registros falsos de juegos:", falsosGame)
    print("Dias con registros falsos (y tipo):")
    d.Informe(dias)

    if len(jugadores.JUGADORES) > 0:
        j = jugadores.JUGADORES[0]
        j.ListaJuegos(args.registros, listaJuegos)
        print("Puntuaciones del primer jugador:")
        j.Puntuacion()

