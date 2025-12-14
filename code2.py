import argparse
from cryptography.hazmat.primitives import hashes


def calcular_hex(algoritmo, texto):
    if algoritmo == "SHA256":
        calculadora = hashes.Hash(hashes.SHA256())
    else:
        if algoritmo == "SHA512":
            calculadora = hashes.Hash(hashes.SHA512())
        else:
            if algoritmo == "MD5":
                calculadora = hashes.Hash(hashes.MD5())
            else:
                return None

    calculadora.update(texto.encode("utf-8"))
    return calculadora.finalize().hex()


def numero_por_texto(texto, minimo, maximo):
    hex_total = calcular_hex("SHA256", texto)
    parte = hex_total[0:8]
    valor = int(parte, 16)

    rango = maximo - minimo + 1
    valor = valor % rango
    valor = valor + minimo
    return valor


def dos_digitos(numero):
    if numero < 10:
        return "0" + f"{numero}"
    return f"{numero}"


def lista_letras():
    resultado = []
    codigo = ord("a")
    while codigo <= ord("z"):
        resultado.append(chr(codigo))
        codigo = codigo + 1
    return resultado


class Cliente:
    def __init__(self, nombre, cif, algoritmo):
        self.CL_NAME = f"{nombre}"
        self.CL_CIF = f"{cif}"
        self.algoritmo = f"{algoritmo}"

        texto_base_id = self.CL_CIF + "--" + self.CL_NAME
        self.CL_ID = numero_por_texto(texto_base_id, 5000, 6500)

        self.CL_PASS = self.GenerarPass(self.algoritmo)

    def GenerarPass(self, algoritmo):
        texto_base = self.CL_CIF + "--" + self.CL_NAME + "--" + f"{self.CL_ID}"
        semilla = numero_por_texto(texto_base, 0, 999999)

        opciones = ["-", "?", "*"]
        posicion = semilla % 3
        simbolo = opciones[posicion]

        letras = lista_letras()

        pos_1 = semilla % 26
        pos_2 = (semilla // 26) % 26

        letra_1 = letras[pos_1]
        letra_2 = letras[pos_2]

        numero = semilla % 100
        numero_texto = dos_digitos(numero)

        clave_clara = simbolo + letra_1 + letra_2 + numero_texto + "-"

        clave_hash = calcular_hex(algoritmo, clave_clara)
        if clave_hash is None:
            raise ValueError("Algoritmo no soportado")

        return clave_hash

    def DescifrarPass(self):
        simbolos = ["-", "?", "*"]
        letras = lista_letras()

        indice_simbolo = 0
        while indice_simbolo < len(simbolos):
            simbolo = simbolos[indice_simbolo]

            i = 0
            while i < len(letras):
                j = 0
                while j < len(letras):
                    letra_1 = letras[i]
                    letra_2 = letras[j]

                    numero = 0
                    while numero <= 99:
                        numero_texto = dos_digitos(numero)
                        clave_clara = simbolo + letra_1 + letra_2 + numero_texto + "-"

                        calculado = calcular_hex(self.algoritmo, clave_clara)
                        if calculado == self.CL_PASS:
                            return clave_clara

                        numero = numero + 1

                    j = j + 1
                i = i + 1

            indice_simbolo = indice_simbolo + 1

        return None

    def RealizarEnvio(self):
        url_cliente = self.DescifrarPass()
        if url_cliente is None:
            print("No se pudo descifrar la password del cliente")
            return

        enlace = "https://www.petrol.com/cliente/" + url_cliente
        print(enlace)

    def ImprimirDatos(self):
        print("CLIENTE")
        print("CL_ID:", self.CL_ID)
        print("CL_NAME:", self.CL_NAME)
        print("CL_CIF:", self.CL_CIF)
        print("CL_PASS:", self.CL_PASS)
        print("ALGORITMO:", self.algoritmo)


class Petrolera:
    def __init__(self, nombre, direccion, suministros):
        self.NOM_PETROLERA = f"{nombre}"
        self.DIR_PETROLERA = f"{direccion}"
        self.SUMINISTROS = int(suministros)

        texto_base_id = self.NOM_PETROLERA + "--" + self.DIR_PETROLERA
        self.ID_PETROLERA = numero_por_texto(texto_base_id, 1, 50)

        self.CONTABILIDAD = {}
        self.fecha_guardada = None

    def RealizarContabilidad(self, ruta_archivo):
        archivo = open(ruta_archivo, "r", encoding="utf-8")
        lineas = archivo.readlines()
        archivo.close()

        for linea in lineas:
            linea_limpia = linea.strip()
            if linea_limpia == "":
                continue

            datos = linea_limpia.split("--")
            if len(datos) != 6:
                continue

            fecha = datos[0].strip()
            cif_cliente = datos[1].strip()
            nombre_cliente = datos[2].strip()
            pedido = datos[3].strip()
            id_petrolera = datos[4].strip()
            importe_texto = datos[5].strip()

            if id_petrolera != f"{self.ID_PETROLERA}":
                continue

            algoritmo = "SHA256"
            if self.ID_PETROLERA % 2 != 0:
                algoritmo = "SHA512"

            cliente = Cliente(nombre_cliente, cif_cliente, algoritmo)

            importe = float(importe_texto)

            self.CONTABILIDAD[pedido] = [importe, fecha, cliente]
            self.fecha_guardada = fecha

    def ObtenerPedidosCliente(self, cl_id):
        hay = False

        for pedido in self.CONTABILIDAD:
            registro = self.CONTABILIDAD[pedido]
            importe = registro[0]
            fecha = registro[1]
            cliente = registro[2]

            if cliente.CL_ID == cl_id:
                hay = True
                print("ID_PEDIDO:", pedido, "IMPORTE:", importe, "FECHA:", fecha)

        if hay is False:
            print("No hay pedidos para el cliente con CL_ID:", cl_id)

    def ReporteContabilidad(self):
        suma = 0.0

        for pedido in self.CONTABILIDAD:
            registro = self.CONTABILIDAD[pedido]
            importe = registro[0]
            suma = suma + importe

        fecha = self.fecha_guardada
        if fecha is None:
            fecha = "SIN_FECHA"

        ruta_salida = "reporte_petrolera_" + f"{self.ID_PETROLERA}" + ".txt"
        salida = open(ruta_salida, "w+", encoding="utf-8")

        linea = f"{self.ID_PETROLERA}" + "@@" + f"{suma}" + "@@" + f"{fecha}"
        salida.write(linea)
        salida.close()

        return ruta_salida

    def ImprimirDatos(self):
        print("PETROLERA")
        print("ID_PETROLERA:", self.ID_PETROLERA)
        print("NOM_PETROLERA:", self.NOM_PETROLERA)
        print("DIR_PETROLERA:", self.DIR_PETROLERA)
        print("SUMINISTROS:", self.SUMINISTROS)
        print("PEDIDOS EN CONTABILIDAD:", len(self.CONTABILIDAD))


def crear_fichero_prueba(ruta, petrolera_a, petrolera_b):
    registros = []

    registros.append("2025-04-10--A11111111--Ana--P1001--" + f"{petrolera_a.ID_PETROLERA}" + "--1200.50")
    registros.append("2025-04-11--B22222222--Luis--P1002--" + f"{petrolera_a.ID_PETROLERA}" + "--300.00")
    registros.append("2025-04-12--C33333333--Marta--P1003--" + f"{petrolera_a.ID_PETROLERA}" + "--75.25")

    registros.append("2025-05-01--D44444444--Pablo--P2001--" + f"{petrolera_b.ID_PETROLERA}" + "--500.00")
    registros.append("2025-05-02--E55555555--Sara--P2002--" + f"{petrolera_b.ID_PETROLERA}" + "--999.99")
    registros.append("2025-05-03--F66666666--Nerea--P2003--" + f"{petrolera_b.ID_PETROLERA}" + "--10.00")

    archivo = open(ruta, "w+", encoding="utf-8")
    for linea in registros:
        archivo.write(linea + "\n")
    archivo.close()


def obtener_cliente_cualquiera(petrolera):
    for pedido in petrolera.CONTABILIDAD:
        registro = petrolera.CONTABILIDAD[pedido]
        cliente = registro[2]
        return cliente
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fichero", required=True)
    parametros = parser.parse_args()

    petrolera_1 = Petrolera("Petrol Norte", "Calle 1", 100)
    petrolera_2 = Petrolera("Petrol Sur", "Calle 2", 200)

    crear_fichero_prueba(parametros.fichero, petrolera_1, petrolera_2)

    petrolera_1.RealizarContabilidad(parametros.fichero)
    petrolera_2.RealizarContabilidad(parametros.fichero)

    petrolera_1.ImprimirDatos()
    petrolera_2.ImprimirDatos()

    cliente_1 = obtener_cliente_cualquiera(petrolera_1)
    if cliente_1 is not None:
        cliente_1.ImprimirDatos()
        cliente_1.RealizarEnvio()
        petrolera_1.ObtenerPedidosCliente(cliente_1.CL_ID)

    cliente_2 = obtener_cliente_cualquiera(petrolera_2)
    if cliente_2 is not None:
        cliente_2.ImprimirDatos()
        cliente_2.RealizarEnvio()
        petrolera_2.ObtenerPedidosCliente(cliente_2.CL_ID)

    salida_1 = petrolera_1.ReporteContabilidad()
    salida_2 = petrolera_2.ReporteContabilidad()

    print("Reporte creado:", salida_1)
    print("Reporte creado:", salida_2)


if __name__ == "__main__":
    main()
