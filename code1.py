import hashlib


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
        diccionario = self.SetAlgs()
        for algoritmo in diccionario:
            paises = diccionario[algoritmo]
            for pais in paises:
                if pais == self.c_name:
                    return algoritmo
        return None


class Ship:
    def __init__(self, number, country_name):
        self.s_number = int(number)
        self.country_name = str(country_name).upper()

        if self.s_number < 0 or self.s_number > 99:
            raise ValueError("s_number debe estar entre 0 y 99")

        self.s_id = self.GenID()

    def GenID(self):
        pais = Country(self.country_name)
        algoritmo = pais.alg
        if algoritmo is None:
            raise ValueError("country_name no soportado")

        texto = str(self.s_number).zfill(2) + "*" + self.country_name

        if algoritmo == "SHA512":
            return hashlib.sha512(texto.encode("utf-8")).hexdigest()
        if algoritmo == "SHA256":
            return hashlib.sha256(texto.encode("utf-8")).hexdigest()
        if algoritmo == "MD5":
            return hashlib.md5(texto.encode("utf-8")).hexdigest()

        raise ValueError("Algoritmo no soportado")

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

        self.p_id = self._generar_id_puerto(self.country.c_name, self.country.alg)

    def _generar_id_puerto(self, nombre_pais, algoritmo):
        texto = str(nombre_pais).upper().encode("utf-8")

        if algoritmo == "SHA512":
            return hashlib.sha512(texto).hexdigest()
        if algoritmo == "SHA256":
            return hashlib.sha256(texto).hexdigest()
        if algoritmo == "MD5":
            return hashlib.md5(texto).hexdigest()

        raise ValueError("Algoritmo no soportado")

    def _hash_texto(self, algoritmo, texto):
        dato = str(texto).encode("utf-8")

        if algoritmo == "SHA512":
            return hashlib.sha512(dato).hexdigest()
        if algoritmo == "SHA256":
            return hashlib.sha256(dato).hexdigest()
        if algoritmo == "MD5":
            return hashlib.md5(dato).hexdigest()

        return None

    def _es_fecha_valida(self, fecha):
        partes = str(fecha).split("-")
        if len(partes) != 3:
            return False

        anio = partes[0]
        mes = partes[1]
        dia = partes[2]

        if len(anio) != 4 or len(mes) != 2 or len(dia) != 2:
            return False

        if not anio.isdigit() or not mes.isdigit() or not dia.isdigit():
            return False

        mes_num = int(mes)
        dia_num = int(dia)

        if mes_num < 1 or mes_num > 12:
            return False
        if dia_num < 1 or dia_num > 31:
            return False

        return True

    def DecodeShipID(self, s_id):
        if s_id is None:
            return None

        ship_hash = str(s_id).strip().lower()
        diccionario = Country("ES").SetAlgs()

        for algoritmo in diccionario:
            paises = diccionario[algoritmo]
            for pais in paises:
                pais_mayus = str(pais).upper()

                numero = 0
                while numero <= 99:
                    id_claro = str(numero).zfill(2) + "*" + pais_mayus
                    calculado = self._hash_texto(algoritmo, id_claro)
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
            tipo = partes[1].strip().upper()
            puerto_id = partes[2].strip().lower()
            ship_id = partes[3].strip().lower()

            if tipo != "ENTRADA" and tipo != "SALIDA":
                continue

            if not self._es_fecha_valida(fecha):
                continue

            if puerto_id != self.p_id.lower():
                continue

            id_claro = self.DecodeShipID(ship_id)
            if id_claro is None:
                continue

            ship_obj = self._crear_ship_desde_id_claro(id_claro)
            if ship_obj is None:
                continue

            if fecha not in self.ships[tipo]:
                self.ships[tipo][fecha] = []

            self.ships[tipo][fecha].append(ship_obj)


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
        salida.write("Pais: " + str(self.port.country.c_name).upper() + "\n")
        salida.write("Archivo registros: " + str(self.file) + "\n")
        salida.write("\n")

        tipos_a_escribir = []
        if tipo_solicitado is None:
            tipos_a_escribir.append("ENTRADA")
            tipos_a_escribir.append("SALIDA")
        else:
            tipos_a_escribir.append(tipo_solicitado)

        for tipo_registro in tipos_a_escribir:
            salida.write("=== " + tipo_registro + " ===\n")

            fechas = list(self.port.ships[tipo_registro].keys())
            fechas.sort()

            if len(fechas) == 0:
                salida.write("Sin registros.\n\n")
            else:
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
    codigo_pais_puerto = "ES"
    nombre_puerto = "Barcelona"
    tipo_reporte = None

    pais = Country(codigo_pais_puerto)
    if pais.alg is None:
        print("Pais no soportado: " + str(codigo_pais_puerto))
        return

    puerto = Port(nombre_puerto, pais)
    reporte = Report(puerto, ruta_fichero)

    try:
        salida = reporte.GetReport(tipo_reporte)
        print("Reporte generado: " + salida)
    except Exception as e:
        print("Error: " + str(e))


if __name__ == "__main__":
    main()
