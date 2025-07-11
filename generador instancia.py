import random
import math

def crearInstancia(n,m, costo_repartidor = -1, dist_max = -1, cant_refrigerados = -1, cant_exclusivos = -1):
    # n es la cantidad de clientes que quiere que tenga esta instancia
    # m es el numero\identificador de la instancia generada
    # si no completan los demas datos, los generamos aleatoriamente
    if costo_repartidor < 0:
        costo_repartidor = random.randint(0,1000)
    if dist_max < 0:
        dist_max = random.randint(1,1000)
    if cant_refrigerados < 0 or cant_refrigerados > n:
        cant_refrigerados = random.randint(0,n)
    if cant_exclusivos > n or cant_exclusivos <0:
        cant_exclusivos = random.randint(0,n)

    #seleccionamos los clientes exlusivos y los refrigerados aleatoriamente:
    refrigerados = random.sample(range(1,n+1),cant_refrigerados)
    exclusivos = random.sample(range(1,n+1),cant_exclusivos)

    #generamos la posicion de los clientes y calculamos la distancia euclidea entre ellos:
    posiciones = []
    distancias = [[0 for _ in range(n)] for _ in range(n)]
    for i in range(n):
        posiciones.append((random.random(),random.random()))
    for i in range(n):
        for j in range(i+1,n):
            d = math.dist(posiciones[i],posiciones[j])
            distancias[i][j] = distancias[j][i] = d

    #generamos la instancia en un archivo de texto:
    with open(f'instancia_{m}_{n}_clientes.txt', 'w') as archivo:
        archivo.write(f'{n}\n')
        archivo.write(f'{costo_repartidor}\n')
        archivo.write(f'{dist_max}\n')
        archivo.write(f'{cant_refrigerados}\n')
        #escribimos una linea por cada id de los clientes que tienen productos refrigerados
        for idr in refrigerados: 
            archivo.write(f'{idr}\n')
        #escribimos una linea por cada id de los clientes que deben ser visitados exlusivamente por el camion
        archivo.write(f'{cant_exclusivos}\n')
        for ide in exclusivos:
            archivo.write(f'{ide}\n')
        #escribimos las distancias entre todos los clientes, y el costo de moverse entre ellos con el camion
        for i in range(n):
            for j in range(n):
                if i !=j:
                    archivo.write(f'{i+1} {j+1} {distancias[i][j]*1000:.0f} {distancias[i][j] * 10000:.0f}\n')

if __name__ == "__main__":
    n = int(input("Ingrese la cantidad de clientes: "))
    m = int(input('Ingrese la cantidad de archivos/instancias a generar: '))
    for i in range(m):
        crearInstancia(n,i)
        print(f"Instancia de {n} clientes generada correctamente.")
