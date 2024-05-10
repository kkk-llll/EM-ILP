# 该模块用于计算求解器所需参数
from readFile import *
import random
import numpy as np

# 计算最大公约数，用于 lcm
def gcd(a, b):
    while a:
        a, b = b%a, a
    return b

# 计算最小公倍数，用于 HP
def lcm(a, b):
    return a*b/gcd(a, b)

# 计算超周期 HP，它等于所有任务周期的最小公倍数
def getHP(taskSet):
    HP = taskSet[0].period
    for task in taskSet:
        HP = lcm(HP, task.period)
    return HP

# 计算每个任务在超周期内释放作业数
def getWorksNum(HP, taskSet):
    for task in taskSet:
        task.worksNum = HP/task.period
    return taskSet

# 给定策略编号 X，计算剩余作业数 M，即统计 X 的二进制序列中中 1 的个数
def getM1(X):
    M = 0
    while X:
        X = X & (X-1)
        M += 1
    return M

# 计算策略 X_i+1_j+1 剩余作业数
def getM(i, j, X_book):
    # print(i,j,'\n',X_book)
    return X_book[i][j].count('1')

# 计算策略 X_i+1_j+1 剩余作业的位置
def getWorks(i, j, X_book):
    Works = []
    for k in range(len(X_book[i][j])):
        if (X_book[i][j][k] == '1'):
            Works.append(k+1)
    return Works


# 剔除任务数为 x ，任务总数为 Len，随机生成调度策略
def get_str(x, Len):
    str = ''
    book = []
    while len(book) != x:               # 先随机出 x 个 0 的位置，再在 str 中按位置填 0、1
        t = random.randint(0, Len-1)    # 更随机，更稳定，保证 x 个 0，Len - x 个 1
        if t not in book:
            book.append(t)
    for i in range(Len):
        if i in book:
            str += '0'
        else:
            str += '1'
    return str



# 计算使用策略 X 时，剩余作业的编号，即统计 X 的二进制序列中中 1 的位置
def getWorks1(X, WorksNum):
    Works = []
    for i in range(WorksNum+1):
        if X == (X | 2**(WorksNum-i)):
            Works.append(i)
    # print(Works,X,WorksNum)
    return Works

# 计算剩余作业的释放时间 R，R = (作业编号 - 1) * 释放周期
def getR(Works, p):
    R = []
    for i in Works:
        R.append((i-1)*p)
    return R

# 计算作业相对截止期 RD，RD = C + (相邻任务释放间隔 - C) * alpha
def getRD(R, C, alpha, HP):
    D = []
    L = len(R)-1
    for i in range(L):
        D.append(C+(R[i+1]-R[i]-C)*alpha)
    D.append(C+(HP-R[L]-C)*alpha)
    return D

# 计算作业相对截止期 RD，RD = C + (相邻任务释放间隔 - C) * alpha
def getRD_1(R, C, alpha, HP):
    D = []
    L = len(R)-1
    for i in range(L):
        D.append(C+(R[i+1]-R[i]-C)*alpha)
    D.append(R[0]+C+(HP-R[L]-C)*alpha)
    return D

# 计算作业绝对截止期 AD，AD = R + RD
def getAD(R, C, alpha, HP):
    D = []
    L = len(R)-1
    for i in range(L):
        D.append(R[i]+C+(R[i+1]-R[i]-C)*alpha)
    D.append(R[L]+C+(HP-R[L]-C)*alpha)
    return D

# 获得随机路径
def find_a_way(E, start, end):
    graph = {}
    way = []
    for e in E:
        graph[e[0]] = []
    for e in E:
        graph[e[0]].append(e[1])
    stack = []
    stack.append(start)
    while len(stack) > 0:
        vertex = stack.pop()
        way.append(vertex)
        if vertex == end:
            break
        nodes = graph[vertex]
        flag = len(nodes) * [0]
        ind = random.randint(0, len(nodes)-1)
        flag[ind] = 1
        stack.append(nodes[ind])
    return way


# Floyd 算法求最短路，n 为节点数，E 为边集
def Floyd_S(n, E, start, end):
    Vtx = []
    S_way = []
    P = []
    BS = 0
    for i in range(n):
        temp1 = []
        temp2 = []
        for j in range(n):
            if [i+1, j+1] in E:
                temp1.append(1)
                temp2.append([i, j])
            else:
                temp1.append(99999)
                temp2.append([])
        Vtx.append(temp1)
        S_way.append(temp2)
    for k in range(n):
        for i in range(n):
            for j in range(n):
                if Vtx[i][j] > Vtx[i][k]+Vtx[k][j]:
                    Vtx[i][j] = Vtx[i][k]+Vtx[k][j]
                    S_way[i][j] = S_way[i][k] + S_way[k][j][1:]
    S = S_way[start-1][end-1]
    return S

def getU(X, X_book, HP, taskSet, plat):
    U = []
    time = 0
    for (i,j) in plat:
        i -= 1
        u = 0
        for k in range(i,j):
            for t in range(len(X[k])):
                # u += getM(k, t, X_book)*taskSet[k].C*int(X[k][t].x)
                u += getM(k, t, X_book) * taskSet[k].C * X[k][t]
        u /= HP
        # U[time] = u
        U.append(u)
        time += 1
    return U

def computeU(X, X_book, HP, taskSet, plat):
    # U = []
    for (i,j) in plat:
        time = 0
        i -= 1
        u = 0
        for k in range(i,j):
            for t in range(len(X[k])):
                u += getM(k, t, X_book)*taskSet[k].C*int(X[k][t].x)
                # u += getM(k, t, X_book) * taskSet[k].C * X[k][t]
        u /= HP
        # U.append(u)
        return u


# Floyd 算法求最长路，n 为节点数，E 为边集
def Floyd_L(n, E, start, end):
    Vtx = []
    L_way = []
    P = []
    BL = 0
    for i in range(n):
        temp1 = []
        temp2 = []
        for j in range(n):
            if [i+1, j+1] in E:
                temp1.append(1)
                temp2.append([i, j])
            else:
                temp1.append(-99999)
                temp2.append([])
        Vtx.append(temp1)
        L_way.append(temp2)
    for k in range(n):
        for i in range(n):
            for j in range(n):
                if Vtx[i][j] < Vtx[i][k]+Vtx[k][j]:
                    Vtx[i][j] = Vtx[i][k]+Vtx[k][j]
                    L_way[i][j] = L_way[i][k] + L_way[k][j][1:]
    L = L_way[start-1][end-1]
    return L

def Floyd_L1(n, E):
    Vtx = []
    L_way = []
    L = []
    for i in range(2*n):
        L.append(0)
    for i in range(n):
        temp1 = []
        temp2 = []
        for j in range(n):
            if [i+1, j+1] in E:
                temp1.append(1)
                temp2.append([i, j])
            else:
                temp1.append(-99999)
                temp2.append([])
        Vtx.append(temp1)
        L_way.append(temp2)
    for k in range(n):
        for i in range(n):
            for j in range(n):
                if Vtx[i][j] < Vtx[i][k]+Vtx[k][j]:
                    Vtx[i][j] = Vtx[i][k]+Vtx[k][j]
                    L_way[i][j] = L_way[i][k] + L_way[k][j][1:]
    for i in range(n):
        for j in range(n):
            if Vtx[i][j] > 0:
                L[Vtx[i][j]] += 1
    for i in range(1, 2*n):
        if L[i] != 0:
            print(i, L[i])
    return


# 计算正态分布的概率密度, mu 为均值，sigma 为方差。sigma 越小，f(x) 越陡峭
def f(x, mu, sigma):
    return np.exp(-((x - mu)**2)/(2*sigma**2)) / (sigma * np.sqrt(2*np.pi))

# mu 为均值，sigma 为方差，根据正态分布概率生成一个 alpha 值
def get_alpha(mu, sigma):
    alpha = [0.25, 0.5, 0.75, 1]
    density_of_alpha = []
    for a in alpha:
        density_of_alpha.append(f(a, mu, sigma))
    sum_density = sum(density_of_alpha)
    for i in range(len(density_of_alpha)):
        density_of_alpha[i] = int(100 * density_of_alpha[i] / sum_density)
    sum_density = sum(density_of_alpha)
    # print(density_of_alpha)
    # print(sum_density)
    rand = random.randint(1, sum_density)
    density = 0
    for i in range(len(density_of_alpha)):
        density += density_of_alpha[i]
        if rand <= density:
            return alpha[i]
    return 1

def set_alpha(mu, sigma, taskNum):
    a = []
    for i in range(taskNum):
        a.append(get_alpha(mu, sigma))
    return a