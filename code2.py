import argparse
from cryptography.hazmat.primitives import hashes


def hashHexMd5(textoPlano):
    digeridor = hashes.Hash(hashes.MD5())
    digeridor.update(textoPlano.encode("utf-8"))
    resultadoBytes = digeridor.finalize()
    return resultadoBytes.hex()


def hashHexSha256(textoPlano):
    digeridor = hashes.Hash(hashes.SHA256())
    digeridor.update(textoPlano.encode("utf-8"))
    resultadoBytes = digeridor.finalize()
    return resultadoBytes.hex()


def enteroDesdeTexto(textoPlano, minimo, maximo):
    resumen = hashHexSha256(textoPlano)
    fragmento = resumen[0:8]
    numero = int(fragmento, 16)

    rango = maximo - minimo + 1
    numero = numero % rango
    numero = numero + minimo
    return numero


class Juego:
    def __init__(self, nombreJuego, tipoJuego):
        self.JUEGO_NOMBRE = nombreJuego
        self.JUEGO_TIPO = tipoJuego
        self.JUEGO_ID = self.GenerarID()

    def GenerarID(self):
        textoId = self.JUEGO_NOMBRE + self.JUEGO_TIPO
        return hashHexMd5(textoId)

    def Imprimir(self):
        print(self.JUEGO_NOMBRE, "-", self.JUEGO_TIPO, "-", self.JUEGO_ID)


class Jugador:
    def __init__(self, nombreJugador, correoJugador):
        textoBase = nombreJugador + correoJugador
        self.JUGADOR_ID = enteroDesdeTexto(textoBase, 1000, 9999)
        self.JUGADOR_NAME = nombreJugador
        self.JUGADOR_MAIL = correoJugador
        self.JUGADOR_KEY = self.CrearKey()
        self.JUEGOS = {}

    def CrearKey(self):
        nombreLimpio = self.JUGADOR_NAME.strip()

        inicial = ""
        if len(nombreLimpio) > 0:
            inicial = nombreLimpio[0].upper()

        dosFinales = ""
        if len(nombreLimpio) >= 2:
            dosFinales = nombreLimpio[-2:].lower()

        patronKey = inicial + dosFinales + "ufv."
        return hashHexSha256(patronKey)

    def ListaJuegos(self, rutaRegistros, listaJuegos):
        juegosPorId = {}

        for textoJuego in listaJuegos:
            partesJuego = textoJuego.split("-", 1)
            if len(partesJuego) == 2:
                nombreJuego = partesJuego[0]
                tipoJuego = partesJuego[1]
                juegoObj = Juego(nombreJuego, tipoJuego)
                juegosPorId[juegoObj.JUEGO_ID] = juegoObj

        archivo = open(rutaRegistros, "r", encoding="utf-8")
        lineas = archivo.readlines()
        archivo.close()

        for linea in lineas:
            linea = linea.strip()
            if linea == "":
                continue

            campos = linea.split("||")
            if len(campos) != 4:
                continue

            idJuego = campos[0]
            keyJugador = campos[1]
            puntosTexto = campos[3]

            if keyJugador != self.JUGADOR_KEY:
                continue

            if idJuego not in juegosPorId:
                continue

            puntos = 0
            if puntosTexto.isdigit():
                puntos = int(puntosTexto)

            juegoObj = juegosPorId[idJuego]
            nombreJuego = juegoObj.JUEGO_NOMBRE

            if nombreJuego not in self.JUEGOS:
                self.JUEGOS[nombreJuego] = {"JUEGO": juegoObj, "PUNTOS": 0}

            puntosAcumulados = self.JUEGOS[nombreJuego]["PUNTOS"]
            puntosAcumulados = puntosAcumulados + puntos
            self.JUEGOS[nombreJuego]["PUNTOS"] = puntosAcumulados

    def Puntuacion(self, juegoSolicitado=None):
        if juegoSolicitado is None:
            for nombreJuego in self.JUEGOS:
                totalPuntos = self.JUEGOS[nombreJuego]["PUNTOS"]
                print(nombreJuego + ":", totalPuntos)
            return

        if juegoSolicitado in self.JUEGOS:
            totalPuntos = self.JUEGOS[juegoSolicitado]["PUNTOS"]
            print(juegoSolicitado + ":", totalPuntos)
            return

        print(juegoSolicitado + ":", 0)

    def Imprimir(self):
        print("Jugador:", self.JUGADOR_NAME, "-", self.JUGADOR_MAIL)
        print("ID:", self.JUGADOR_ID)
        print("KEY:", self.JUGADOR_KEY)


class ListaJugadores:
    def __init__(self, rutaPlayers):
        self.FICHERO = rutaPlayers
        self.JUGADORES = []
        self.cargarJugadores()

    def cargarJugadores(self):
        archivo = open(self.FICHERO, "r", encoding="utf-8")
        lineas = archivo.readlines()
        archivo.close()

        for linea in lineas:
            linea = linea.strip()
            if linea == "":
                continue

            datos = linea.split("@@")
            if len(datos) != 2:
                continue

            nombreJugador = datos[0].strip()
            correoJugador = datos[1].strip()

            jugadorObj = Jugador(nombreJugador, correoJugador)
            self.JUGADORES.append(jugadorObj)

    def Imprimir(self):
        for jugadorObj in self.JUGADORES:
            jugadorObj.Imprimir()


class Diagnostico:
    def __init__(self, rutaRegistro, listaJugadores, listaJuegos):
        self.FICHERO_REGISTRO = rutaRegistro
        self.JUGADORES = listaJugadores
        self.JUEGOS = listaJuegos

        self.clavesValidas = set()
        self.idsJuegosValidos = set()

        self.prepararValidos()

    def prepararValidos(self):
        for jugadorObj in self.JUGADORES:
            self.clavesValidas.add(jugadorObj.JUGADOR_KEY)

        for textoJuego in self.JUEGOS:
            partesJuego = textoJuego.split("-", 1)
            if len(partesJuego) == 2:
                nombreJuego = partesJuego[0]
                tipoJuego = partesJuego[1]
                juegoObj = Juego(nombreJuego, tipoJuego)
                self.idsJuegosValidos.add(juegoObj.JUEGO_ID)

    def GenFraudulentos(self):
        archivo = open(self.FICHERO_REGISTRO, "r", encoding="utf-8")
        lineas = archivo.readlines()
        archivo.close()

        salidas = []
        salidasUnicas = set()

        conteoPlayers = 0
        conteoJuegos = 0
        resumenFechas = {}

        for linea in lineas:
            linea = linea.strip()
            if linea == "":
                continue

            campos = linea.split("||")
            if len(campos) != 4:
                continue

            idJuego = campos[0]
            keyJugador = campos[1]
            fechaRegistro = campos[2]

            esJugadorFalso = False
            esJuegoFalso = False

            if keyJugador not in self.clavesValidas:
                esJugadorFalso = True

            if idJuego not in self.idsJuegosValidos:
                esJuegoFalso = True

            if esJugadorFalso:
                lineaSalida = "PLAYER##" + keyJugador + "##" + fechaRegistro
                if lineaSalida not in salidasUnicas:
                    salidasUnicas.add(lineaSalida)
                    salidas.append(lineaSalida)
                conteoPlayers = conteoPlayers + 1
                self.anadirTipoResumen(resumenFechas, fechaRegistro, "PLAYER")

            if esJuegoFalso:
                lineaSalida = "GAME##" + idJuego + "##" + fechaRegistro
                if lineaSalida not in salidasUnicas:
                    salidasUnicas.add(lineaSalida)
                    salidas.append(lineaSalida)
                conteoJuegos = conteoJuegos + 1
                self.anadirTipoResumen(resumenFechas, fechaRegistro, "GAME")

        archivoSalida = open("BAD_REGISTERS.log", "w+", encoding="utf-8")
        for lineaSalida in salidas:
            archivoSalida.write(lineaSalida + "\n")
        archivoSalida.close()

        return conteoPlayers, conteoJuegos, resumenFechas

    def anadirTipoResumen(self, resumenFechas, fechaRegistro, tipoRegistro):
        if fechaRegistro not in resumenFechas:
            resumenFechas[fechaRegistro] = []

        if tipoRegistro not in resumenFechas[fechaRegistro]:
            resumenFechas[fechaRegistro].append(tipoRegistro)

    def Informe(self, resumenFechas):
        fechasOrdenadas = sorted(resumenFechas.keys(), key=self.claveOrdenFecha)
        for fechaRegistro in fechasOrdenadas:
            tipos = resumenFechas[fechaRegistro]
            textoTipos = ", ".join(tipos)
            print(fechaRegistro + ":", textoTipos)

    def claveOrdenFecha(self, fechaRegistro):
        partes = fechaRegistro.split("/")
        if len(partes) != 3:
            return fechaRegistro

        dia = partes[0]
        mes = partes[1]
        anio = partes[2]

        return anio + mes + dia


def crearAnalizador():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--players", default="PLAYERS-1.txt")
    parser.add_argument("-r", "--registros", default="REGISTROS-2.log")
    return parser


if __name__ == "__main__":
    juegosDisponibles = [
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

    analizador = crearAnalizador()
    argumentos = analizador.parse_args()

    contenedorJugadores = ListaJugadores(argumentos.players)

    verificador = Diagnostico(argumentos.registros, contenedorJugadores.JUGADORES, juegosDisponibles)
    totalPlayersFalsos, totalJuegosFalsos, resumenFechas = verificador.GenFraudulentos()

    print("Registros falsos de jugadores:", totalPlayersFalsos)
    print("Registros falsos de juegos:", totalJuegosFalsos)
    print("Dias con registros falsos (y tipo):")
    verificador.Informe(resumenFechas)

    if len(contenedorJugadores.JUGADORES) > 0:
        primerJugador = contenedorJugadores.JUGADORES[0]
        primerJugador.ListaJuegos(argumentos.registros, juegosDisponibles)
        print("Puntuaciones del primer jugador:")
        primerJugador.Puntuacion()

