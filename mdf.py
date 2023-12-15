import json
import numpy as np
import matplotlib.pyplot as plt


def read_mdf_file():
    file = open("mdf_input.json", "r")
    data = json.load(file)
    file.close()
    return data    

def output(saida):
    dict = {"path": saida}
    with open('mdf_output.json', 'w') as json_file:
        json.dump(dict, json_file)
    json_file.close()


data = read_mdf_file()

matriz = np.array(data)
matriz_len = len(matriz)
line_tam = len(matriz[0])

matriz_system = np.zeros((matriz_len, 5), dtype=int)
matriz_system_result = np.zeros(matriz_len)

for i in range(1, matriz_len - 1):
    for j in range(1, line_tam - 1):
        if matriz[i][j] == -1.0:
            matriz_system[i][0] = 4
            total = 0.0
            neighbors = [matriz[i - 1][j], matriz[i + 1][j], matriz[i][j - 1], matriz[i][j + 1]]
            for k in range(4):
                if neighbors[k] == -1.0:
                    matriz_system[i][k + 1] = -1
                else:
                    total += neighbors[k]
            matriz_system_result[i] = total

if matriz_system.shape[0] != matriz_system.shape[1]:
    T_result, _, _, _ = np.linalg.lstsq(matriz_system, matriz_system_result, rcond=None)
else:
    T_result = np.linalg.solve(matriz_system, matriz_system_result)
    
for i in range(1, matriz_len - 1):
    for j in range(1, line_tam - 1):
        if matriz[i][j] == -1.0:
            total = 0.0
            neighbors = [matriz[i - 1][j], matriz[i + 1][j], matriz[i][j - 1], matriz[i][j + 1]]
            for k in range(4):
                if neighbors[k] == -1.0:
                    total += T_result[k + 1]
                else:
                    total += neighbors[k]
            matriz[i][j] = round(total / 4, 2)



plt.imshow(matriz, cmap='hot', interpolation='nearest')
plt.colorbar()  
plt.title("Thermal Data Heatmap")
plt.xlabel("X-axis")
plt.ylabel("Y-axis")
plt.show()


# Write the output
output(matriz.tolist())


