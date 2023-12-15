import json
import matplotlib.pyplot as plt  
import numpy as np

def readJSON():
    with open("dem_input.json", 'r') as file:
        data = json.load(file)

    ne = len(data["coords"])
    x0 = np.empty((ne, 1), dtype=float)
    y0 = np.empty((ne, 1), dtype=float)
    conect = np.empty((ne, 5), dtype=int)
    force = np.empty((ne, 2), dtype=float)
    resistence = np.empty((ne, 2), dtype=int)

    for i in range(ne):
        x0[i] = data["coords"][i][0]
        y0[i] = data["coords"][i][1]
        for j in range(5):
            conect[i, j] = data["connective"][i][j]
        for j in range(2):
            force[i, j] = data["force"][i][j]
            resistence[i, j] = data["resistence"][i][j]

    mass = data["mass"]
    kspr = data["density"]

    return ne, x0, y0, conect, force, resistence, mass, kspr
def outputRes(_res):
    dict_result = {"resultado": _res}
    with open("dem_output.json", "w") as f:
        json.dump(dict_result, f, indent=4)

def main():
    
    N = 600
    h = 0.00004
    ne, x0, y0, conect, F, restrs, mass, kspr = readJSON()
    ndofs = 2 * ne
    raio = 1

    F = F.T.reshape((ndofs, 1))
    restrs = restrs.T.reshape((ndofs, 1))

    print("ne:", ne)

    u = np.zeros((ndofs, 1))
    v = np.zeros((ndofs, 1))
    a = np.zeros((ndofs, 1))
    res = np.zeros(N)

    fi = np.zeros((ndofs, 1))
    a = (F - fi) / mass
    for i in range(N):
        v += a * (0.5 * h)
        u += v * h
        fi.fill(0.0)
        for j in range(ne):
            if restrs[2 * j - 1] == 1:
                u[2 * j - 1] = 0.0
            if restrs[2 * j] == 1:
                u[2 * j] = 0.0
            xj = x0[j] + u[2 * j - 1]
            yj = y0[j] + u[2 * j]
            for index in range(int(conect[j, 0])):
                k = int(conect[j, index + 1]) - 1  
                xk = x0[k] + u[2 * k - 1]
                yk = y0[k] + u[2 * k]
                dX = xj - xk
                dY = yj - yk
                di = np.sqrt(dX**2 + dY**2)
                d2 = di - 2 * raio
                if di != 0:
                    dx = d2 * dX / di
                    dy = d2 * dY / di
                else:
                    dx = 0
                    dy = 0
                fi[2 * j - 1] += kspr * dx
                fi[2 * j] += kspr * dy
        a = (F - fi) / mass
        v += a * (0.5 * h)
        res[i] = u[33, 0]  

    outputRes(res)
    x = np.arange(1, N + 1)
    plt.plot(x, res)
    plt.show()

main()