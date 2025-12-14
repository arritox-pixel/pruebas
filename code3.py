from cryptography.hazmat.primitives import hashes


def obtener_hash_hex(algoritmo, texto):
    if algoritmo == "SHA512":
        generador = hashes.Hash(hashes.SHA512())
    elif algoritmo == "SHA256":
        generador = hashes.Hash(hashes.SHA256())
    elif algoritmo == "MD5":
        generador = hashes.Hash(hashes.MD5())
    else:
        return None

    generador.update(str(texto).encode("utf-8"))
    return generador.finalize().hex()


class Country:
    def __init__(self, name):
        self.c_name = str(name).upper()
        self.alg = self.GetAlg()

    def SetAlgs(self):
        return {
            "SHA512": ["ES", "CHN", "SIN"],
            "SHA256": ["BEL", "EGY", "JAP"],
            "MD5": ["GER", "FR", "IT"]
        }

    def GetAlg(self):
        algs = self.SetAlgs()
        for algoritmo in algs:
            paises = algs[algoritmo]
            for pais in paises:
                if pais == self.c_name:
                    return algoritmo
        return None


class Ship:
    def __init__(self, number, country_name):
        self.s_number = int(number)
        self.country_name = str(country_name).upper()
        self.s_id = self.GenID()

    def GenID(self):
        pais = Country(self.country_name)
        if pais.alg is None:
            raise ValueError("country_name no soportado")

        numero_texto = str(self.s_number).zfill(2)
        texto = numero_texto + "*" + self.country_name
        resultado = obtener_hash_hex(pais.alg, texto)

        if resultado is None:
            raise ValueError("Algoritmo no soportado")

        return resultado

    def __str__(self):
        id_claro = str(self.s_number).zfill(2) + "*" + self.country_name
        return "Ship { id_claro: " + id_claro + ", country: " + self.country_name + ", number: " + str(self.s_number) + " }"


class Port:
    def __init__(self, name, country):
        self.p_name = str(name)
        self.country = country
        self.ships = {"ENTRADA": {}, "SALIDA": {}}

        if self.country is None or self.country.alg is None:
            raise ValueError("Country inválido o sin algoritmo")

        self.p_id = obtener_hash_hex(self.country.alg, self.country.c_name)

    def DecodeShipID(self, s_id):
        if s_id is None:
            return None

        ship_hash = str(s_id).strip().lower()
        diccionario = self.country.SetAlgs()

        for algoritmo in diccionario:
            paises = diccionario[algoritmo]
            for pais in paises:
                pais_mayus = str(pais).upper()

                numero = 0
                while numero <= 99:
                    id_claro = str(numero).zfill(2) + "*" + pais_mayus
                    calculado = obtener_hash_hex(algoritmo, id_claro)

                    if calculado == ship_hash:
                        return id_claro

                    numero += 1

        return None

    def _crear_ship_desde_id_claro(self, id_claro):
        partes = str(id_claro).split("*")
        if len(partes) != 2:
            return None

        numero_texto = partes[0]
        pais = partes[1]

        if len(numero_texto) != 2:
            return None
        if not numero_texto.isdigit():
            return None

        return Ship(int(numero_texto), pais)

    def SetShips(self, ruta_fichero_registro):
        fichero = open(ruta_fichero_registro, "r", encoding="utf-8")
        lineas = fichero.readlines()
        fichero.close()

        for linea in lineas:
            linea_limpia = linea.strip()
            if linea_limpia == "":
                continue

            partes = linea_limpia.split("//")
            if len(partes) != 4:
                continue

            fecha = partes[0].strip()
            registro = partes[1].strip().upper()
            puerto_id = partes[2].strip().lower()
            ship_id = partes[3].strip().lower()

            if registro != "ENTRADA" and registro != "SALIDA":
                continue

            if puerto_id != str(self.p_id).lower():
                continue

            id_claro = self.DecodeShipID(ship_id)
            if id_claro is None:
                continue

            barco = self._crear_ship_desde_id_claro(id_claro)
            if barco is None:
                continue

            if fecha not in self.ships[registro]:
                self.ships[registro][fecha] = []

            self.ships[registro][fecha].append(barco)


class Report:
    def __init__(self, port, file):
        self.port = port
        self.file = file

    def GetReport(self, tipo=None):
        self.port.SetShips(self.file)

        tipo_solicitado = None
        if tipo is not None:
            tipo_solicitado = str(tipo).strip().upper()
            if tipo_solicitado != "ENTRADA" and tipo_solicitado != "SALIDA":
                raise ValueError("tipo debe ser ENTRADA, SALIDA o None")

        nombre_tipo = "completo"
        if tipo_solicitado == "ENTRADA":
            nombre_tipo = "entrada"
        if tipo_solicitado == "SALIDA":
            nombre_tipo = "salida"

        nombre_puerto = self.port.p_name.replace(" ", "_")
        nombre_salida = "reporte_" + nombre_puerto + "_" + nombre_tipo + ".txt"

        salida = open(nombre_salida, "w+", encoding="utf-8")

        salida.write("REPORTE DE PUERTO\n")
        salida.write("Puerto: " + self.port.p_name + "\n")
        salida.write("Pais: " + self.port.country.c_name + "\n")
        salida.write("Archivo registros: " + str(self.file) + "\n")
        salida.write("\n")

        tipos = []
        if tipo_solicitado is None:
            tipos.append("ENTRADA")
            tipos.append("SALIDA")
        else:
            tipos.append(tipo_solicitado)

        for tipo_registro in tipos:
            salida.write("=== " + tipo_registro + " ===\n")

            fechas = list(self.port.ships[tipo_registro].keys())
            fechas.sort()

            if len(fechas) == 0:
                salida.write("Sin registros.\n\n")
                continue

            for fecha in fechas:
                salida.write(fecha + ":\n")
                barcos = self.port.ships[tipo_registro][fecha]
                for barco in barcos:
                    salida.write("  - " + str(barco) + "\n")
                salida.write("\n")

        salida.close()
        return nombre_salida


def main():
    ruta_fichero = "ShipsRegisters.log"

    pais_puerto = Country("ES")
    puerto = Port("Barcelona", pais_puerto)

    reporte = Report(puerto, ruta_fichero)

    salida = reporte.GetReport()
    print("Reporte generado:", salida)


if __name__ == "__main__":
    main()

