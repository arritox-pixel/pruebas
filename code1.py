import hashlib
import re
import exrex


class Country:
    def __init__(self, name):
        self.c_name = name
        self.alg = self.GetAlg()

    def SetAlgs(self):
        return {
            "SHA512": ["ES", "CHN", "SIN"],
            "SHA256": ["BEL", "EGY", "JAP"],
            "MD5": ["GER", "FR", "IT"]
        }

    def GetAlg(self):
        algoritmos = self.SetAlgs()
        for algoritmo in algoritmos:
            paises = algoritmos[algoritmo]
            if self.c_name in paises:
                return algoritmo
        return None


class Ship:
    def __init__(self, number, country_name):
        self.s_number = number
        self.country_name = country_name
        self.s_id = self.GenID()

    def GenID(self):
        texto = str(self.s_number) + "*" + self.country_name.upper()
        pais = Country(self.country_name)
        algoritmo = pais.alg

        if algoritmo == "SHA512":
            return hashlib.sha512(texto.encode()).hexdigest()
        if algoritmo == "SHA256":
            return hashlib.sha256(texto.encode()).hexdigest()
        if algoritmo == "MD5":
            return hashlib.md5(texto.encode()).hexdigest()
        return None

    def __str__(self):
        return "Ship " + str(self.s_number) + " " + self.country_name


class Port:
    def __init__(self, name, country):
        self.p_name = name
        self.country = country
        self.ships = {}
        texto = self.country.c_name.upper()
        if self.country.alg == "SHA512":
            self.p_id = hashlib.sha512(texto.encode()).hexdigest()
        if self.country.alg == "SHA256":
            self.p_id = hashlib.sha256(texto.encode()).hexdigest()
        if self.country.alg == "MD5":
            self.p_id = hashlib.md5(texto.encode()).hexdigest()

    def DecodeShipID(self, s_id):
        patron = r"[0-9]{1,2}\*[A-Z]{2,3}"
        opciones = list(exrex.generate(patron))

        algoritmos = ["SHA512", "SHA256", "MD5"]

        for opcion in opciones:
            for algoritmo in algoritmos:
                if algoritmo == "SHA512":
                    generado = hashlib.sha512(opcion.encode()).hexdigest()
                if algoritmo == "SHA256":
                    generado = hashlib.sha256(opcion.encode()).hexdigest()
                if algoritmo == "MD5":
                    generado = hashlib.md5(opcion.encode()).hexdigest()

                if generado == s_id:
                    return opcion
        return None

    def SetShips(self, ruta_fichero):
        fichero = open(ruta_fichero, "r", encoding="utf-8")
        lineas = fichero.readlines()
        fichero.close()

        for linea in lineas:
            datos = linea.strip().split("//")
            fecha = datos[0]
            tipo = datos[1]
            puerto_id = datos[2]
            ship_id = datos[3]

            if puerto_id == self.p_id:
                ship_claro = self.DecodeShipID(ship_id)

                if ship_claro is not None:
                    partes = ship_claro.split("*")
                    numero = int(partes[0])
                    pais = partes[1]
                    ship = Ship(numero, pais)

                    if tipo not in self.ships:
                        self.ships[tipo] = {}

                    if fecha not in self.ships[tipo]:
                        self.ships[tipo][fecha] = []

                    self.ships[tipo][fecha].append(ship)


class Report:
    def __init__(self, port, file):
        self.port = port
        self.file = file

    def GetReport(self, tipo=None):
        self.port.SetShips(self.file)

        nombre_salida = "report_" + self.port.p_name + ".txt"
        fichero = open(nombre_salida, "w+", encoding="utf-8")

        for registro in self.port.ships:
            if tipo is None or registro == tipo:
                fichero.write(registro + "\n")
                for fecha in self.port.ships[registro]:
                    fichero.write("  " + fecha + "\n")
                    for ship in self.port.ships[registro][fecha]:
                        fichero.write("    " + str(ship) + "\n")

        fichero.close()
