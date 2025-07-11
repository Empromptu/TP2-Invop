import sys
import csv
import time
import cplex
from cplex import SparsePair


TOLERANCE =10e-6 

class InstanciaRecorridoMixto:
    def __init__(self):
        self.cant_clientes = 0
        self.costo_repartidor = 0
        self.d_max = 0
        self.refrigerados = []
        self.exclusivos = []
        self.distancias = []        
        self.costos = []        

    def leer_datos(self,filename):
        # abrimos el archivo de datos
        f = open(filename)
        #f = open('instancia_5.txt')

        # leemos la cantidad de clientes
        self.cant_clientes = int(f.readline())
        # leemos el costo por pedido del repartidor
        self.costo_repartidor = int(f.readline())
        # leemos la distamcia maxima del repartidor
        self.d_max = int(f.readline())
        
        # inicializamos distancias y costos con un valor muy grande (por si falta algun par en los datos)
        self.distancias = [[1000000 for _ in range(self.cant_clientes)] for _ in range(self.cant_clientes)]
        self.costos = [[1000000 for _ in range(self.cant_clientes)] for _ in range(self.cant_clientes)]
        
        # leemos la cantidad de refrigerados
        cantidad_refrigerados = int(f.readline())
        # leemos los clientes refrigerados
        for i in range(cantidad_refrigerados):
            self.refrigerados.append(int(f.readline()))
        
        # leemos la cantidad de exclusivos
        cantidad_exclusivos = int(f.readline())
        # leemos los clientes exclusivos
        for i in range(cantidad_exclusivos):
            self.exclusivos.append(int(f.readline()))
        
        # leemos las distancias y costos entre clientes
        lineas = f.readlines()
        for linea in lineas:
            row = list(map(int,linea.split(' ')))
            self.distancias[row[0]-1][row[1]-1] = row[2]
            self.distancias[row[1]-1][row[0]-1] = row[2]
            self.costos[row[0]-1][row[1]-1] = row[3]
            self.costos[row[1]-1][row[0]-1] = row[3]
        
        # cerramos el archivo
        f.close()

def agregar_variables(prob, instancia):
    n = instancia.cant_clientes
    nombres_vc = []
    nombres_vb = []

    # Variables VC y VB
    for i in range(n):
        for j in range(n):
            if i != j:
                nombres_vc.append(f"VC_{i}_{j}")
                nombres_vb.append(f"VB_{i}_{j}")

    prob.variables.add(names=nombres_vc, types=['B'] * len(nombres_vc))
    prob.variables.add(names=nombres_vb, types=['B'] * len(nombres_vb))

    # Variables u_i (orden de visita)
    nombres_u = [f"u_{i}" for i in range(1, n)]
    prob.variables.add(names=nombres_u, lb=[0] * (n - 1), ub=[float(n)] * (n - 1), types=["C"] * (n - 1))
    # variable u_0 = 0 (se empieza recorrido en deposito)
    prob.variables.add(names=["u_0"], lb=[0], ub=[0],types=["C"])
    
    # Variables delta_i (binarias, indican si una bici fue usada o no)
    nombres_delta = [f"delta_{i}" for i in range(n)]
    prob.variables.add(names=nombres_delta, types=["B"] * n)


def agregar_restricciones(prob, instancia):
    n = instancia.cant_clientes
    d = instancia.distancias
    dist_max = instancia.d_max
    refrigerados = instancia.refrigerados

    # 1. Conservación de flujo del camión
    for k in range(n):
        entrada = [f"VC_{i}_{k}" for i in range(n) if i != k]
        salida = [f"VC_{k}_{j}" for j in range(n) if j != k]
        prob.linear_constraints.add(
            lin_expr=[SparsePair(entrada + salida, [1] * len(entrada) + [-1] * len(salida))],
            senses=["E"],
            rhs=[0],
            names=[f"flujo_camion_{k}"]
        )

    # 3. Cada cliente es visitado una sola vez (ahora solo con VC)
    for j in range(n):
        nombres = [f"VC_{i}_{j}" for i in range(n) if i != j]
        prob.linear_constraints.add(
            lin_expr=[SparsePair(nombres, [1] * len(nombres))],
            senses=["E"],
            rhs=[1],
            names=[f"visita_unica_{j}"]
        )


    # 4. MTZ: evitar ciclos disjuntos
    for i in range(1, n):
        for j in range(1, n):
            if i != j:
                prob.linear_constraints.add(
                    lin_expr=[SparsePair([f"u_{i}", f"u_{j}", f"VC_{i}_{j}"], [1.0, -1.0, float(n)])],
                    senses=["L"],
                    rhs=[n - 1],
                    names=[f"MTZ_{i}_{j}"]
                )
 
 

def agregar_funcion_objetivo(prob, instancia):
    n = instancia.cant_clientes
    obj_names = []
    obj_coefs = []

    for i in range(n):
        for j in range(n):
            if i != j:
                obj_names.append(f"VC_{i}_{j}")
                obj_coefs.append(instancia.costos[i][j])

                obj_names.append(f"VB_{i}_{j}")
                obj_coefs.append(instancia.costo_repartidor)

    prob.objective.set_sense(prob.objective.sense.minimize)
    prob.objective.set_linear(list(zip(obj_names, obj_coefs)))

def armar_lp(prob, instancia):

    # Agregar las variables
    agregar_variables(prob, instancia)
   
    # Agregar las restricciones 
    agregar_restricciones(prob, instancia)

    # Setear el sentido del problema
    agregar_funcion_objetivo(prob,instancia)

    # Escribir el lp a archivo
    prob.write('recorridoMixto.lp')

def resolver_lp(prob):

    # Resolver el problema
    prob.solve()


def correr_experimentos(archivos_instancias, nombre_salida_csv):
    resultados = []

    for archivo in archivos_instancias:
        print(f"📝 Resolviendo instancia: {archivo}")
        
        instancia = InstanciaRecorridoMixto()
        instancia.leer_datos(archivo)

        prob = cplex.Cplex()
        armar_lp(prob, instancia)

        inicio = time.time()
        resolver_lp(prob)
        fin = time.time()
        tiempo = fin - inicio

        # Obtenemos resultados
        status = prob.solution.get_status_string(status_code=prob.solution.get_status())
        try:
            valor_obj = prob.solution.get_objective_value()
        except:
            valor_obj = None  # Si es infactible o sin solución

        print(f"✅ Resultado: {status} | Objetivo: {valor_obj} | Tiempo: {tiempo:.2f} segundos")

        # Guardamos los resultados
        resultados.append({
            'archivo': archivo,
            'status': status,
            'valor_objetivo': valor_obj,
            'tiempo_segundos': tiempo
        })

    # Guardar en CSV
    with open(nombre_salida_csv, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['archivo', 'status', 'valor_objetivo', 'tiempo_segundos'])
        writer.writeheader()
        for fila in resultados:
            writer.writerow(fila)

    print(f"\n📊 Resultados guardados en {nombre_salida_csv}")

# Ejecución
if __name__ == '__main__':
    m = 30
    archivos = [f'instancia_{i}_30_clientes.txt' for i in range(m)]
    correr_experimentos(archivos, 'resultados_experimentos_modelo_viejo_30clientes.csv')