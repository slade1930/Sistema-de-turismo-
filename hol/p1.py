import mysql.connector

conexion = mysql.connector.connect(
    host="localhost", user="slade", password="Slade_152502", database="estadio_camp_nou"
)

cursor = conexion.cursor()


def crear_zona():
    nombre = input("Nombre zona: ")
    capacidad = int(input("Capacidad: "))
    precio = float(input("Precio boleto: "))

    sql = "INSERT INTO zonas_estadio (nombre_zona, capacidad, precio_boleto) VALUES (%s,%s,%s)"
    valores = (nombre, capacidad, precio)

    cursor.execute(sql, valores)
    conexion.commit()
    print("Zona agregada")


def leer_zonas():
    cursor.execute("SELECT * FROM zonas_estadio")
    for fila in cursor.fetchall():
        print(fila)


def actualizar_zona():
    id = int(input("ID a actualizar: "))
    precio = float(input("Nuevo precio: "))

    sql = "UPDATE zonas_estadio SET precio_boleto=%s WHERE id=%s"
    cursor.execute(sql, (precio, id))
    conexion.commit()


def eliminar_zona():
    id = int(input("ID a eliminar: "))
    sql = "DELETE FROM zonas_estadio WHERE id=%s"
    cursor.execute(sql, (id,))
    conexion.commit()


while True:

    print("\nCRUD CAMP NOU")
    print("1 Crear")
    print("2 Leer")
    print("3 Actualizar")
    print("4 Eliminar")
    print("5 Salir")

    opcion = input("Seleccione: ")

    if opcion == "1":
        crear_zona()
    elif opcion == "2":
        leer_zonas()
    elif opcion == "3":
        actualizar_zona()
    elif opcion == "4":
        eliminar_zona()
    elif opcion == "5":
        break
