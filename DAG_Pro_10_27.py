from subprocess import run
import random
from readFile import *
from getParameter import *

# 由于 TGFF3.1 的局限性，只能生成比较好的单起始点、单终点的 DAG 图，因此还需要进一步处理，即再加 x 个起始点
# 该函数使用 TGFF 生成 n-x 个节点，m 条边的随机 DAG 图。正常情况下，要求 m > n。实际生成出来的 DAG 中 n m 略有误差
# 图例储存在 tgff_DAG.eps 中，拓扑信息储存在 tgff_DAG.vcg 和 tgff_DAG.tgff 中，需要添加的起始点数 x 作为函数返回值
def tgff_user(n, m, O_degree, I_degree):
    x = random.randint(1, 5)
    n -= x
    if m > 1.1*n:
        m -= 1.1*n
    else:
        m = 0
    seed = str(random.randint(1, 999))
    Note=open('tgff_DAG.tgffopt',mode='w')
    tgff_code = ''
    tgff_code += 'seed ' + seed +'\n'
    tgff_code += 'tg_cnt 1\n'
    tgff_code += 'task_cnt ' + str(n) + '.1 0.1\n'
    tgff_code += 'period_mul 1\n'
    tgff_code += 'gen_series_parallel true\n'
    tgff_code += 'series_must_rejoin true\n'
    tgff_code += 'task_degree ' + str(I_degree) + ' ' + str(O_degree) + '\n'
    tgff_code += 'series_local_xover ' + str(m)+'\n'
    tgff_code += 'tg_write\nvcg_write\neps_write\n'
    Note.write(tgff_code)
    Note.close()
    run('tgff3_1 tgff_DAG', shell = True)
    return x


# 按概率产生周期和最坏执行时间
def get_P():

    x = random.randint(33, 80)
    if x <= 3:
        return 1000
    elif x <= 5:
        return 2000
    elif x <= 7:
        return 5000
    elif x <= 32:
        return 10000
    elif x <= 57:
        return 20000
    elif x <= 60:
        return 50000
    elif x <= 80:
        return 100000
    elif x <= 81:
        return 200000
    else:
        return 1000000


def W_to_int(w):
    W = int(w)
    if w-W >= 0.5:
        W += 1
    return max(W, 1)


# 使用 UUniFast算法将一个数值 Sum 变成 n 个均匀分布的数值相加的形式
def UUnifast(n, Sum):
    U = []
    sumU = Sum
    for i in range(0, n - 1):
        nextSumU = sumU * random.random()**(1 / (n - i))
        U.append(sumU - nextSumU)
        sumU = nextSumU
    U.append(sumU)
    return U


# 读取 TGFF 生成的 DAG 图，添加 x 个起始点，将相关信息储存到 DAG.txt 中
def read_DAG(x, plat_C, U_rate_C, U_rate_N):
    taskNum = 0
    pre = []
    suc = []
    a = [U_rate_N,U_rate_N,U_rate_N]
    a[plat_C-1] = U_rate_C
    # flag = random.randint(1, 10)
    flag = 8
    with open('tgff_DAG.tgff', 'r') as f:
        while True:
            line = f.readline()
            if not line:
                break
            line = line.split()
            if len(line) and line[0] == 'TASK':
                taskNum += 1
                pre.append([])
                suc.append([])
            if len(line) and line[0] == 'ARC':
                suc[int(line[3][3:])].append(int(line[5][3:])+x+1)
                pre[int(line[5][3:])].append(int(line[3][3:])+x+1)
    n1 = int(random.uniform(2/9,4/9) * (taskNum + x))
    N1 = n1
    n2 = int(random.uniform(2/9,4/9) * (taskNum + x))
    N2 = n2
    U1 = UUnifast(n1, a[0])
    # print(U1)
    U2 = UUnifast(n2, a[1])
    U3 = UUnifast(taskNum+x-n1-n2, a[2])
    x1 = 0
    x2 = 0
    x3 = 0
    Note=open('DAG.txt',mode='w')
    Note.write(str(taskNum+x)+'\n')
    for i in range(x):
        P = get_P()
        if i < N1 :
            W = P*U1[x1]
            W = W_to_int(W)
            x1 += 1
        elif i < N1+N2:
            W = P*U2[x2]
            W = W_to_int(W)
            x2 += 1
        else:
            W = P*U3[x3]
            W = W_to_int(W)
            x3 += 1
        node = int(random.randint(x+2, x+taskNum))
        pre[node-x-1].append(i+1)
        line = str(i + 1) + ' ' + str(W) + ' ' + str(P) + ' (-1,) ('
        if node == x + 2 and flag <= 5:
            node = x + taskNum
        elif node == x + taskNum and flag <= 5:
            node = x + 2
        elif flag <= 5:
            node -= 1
        line += str(node) + ',) 1 0 '
        if n1:
            n1 -= 1
            line += '1\n'
        elif n2:
            n2 -= 1
            line += '2\n'
        else:
            line += '3\n'
        Note.write(line)
    if flag > 5:
        for i in range(taskNum):
            P = get_P()
            if i < N1-x:
                W = P*U1[x1]
                W = W_to_int(W)
                x1 += 1
            elif i < N1 + N2-x:
                W = P*U2[x2]
                W = W_to_int(W)
                x2 += 1
            else:
                W = P*U3[x3]
                W = W_to_int(W)
                x3 += 1
            line = str(i + x + 1) + ' ' + str(W) + ' ' + str(P) + ' ('
            for j in pre[i]:
                line += str(j) + ','
            if len(pre[i]) == 0:
                line += '-1,'
            line += ') ('
            for j in suc[i]:
                line += str(j) + ','
            if len(suc[i]) == 0:
                line += '-1,'
            line += ') '
            if len(pre[i]) == 0:
                line += '1 0 '
            elif len(suc[i]) == 0:
                line += '0 1 '
            else:
                line += '0 0 '
            if n1:
                n1 -= 1
                line += '1\n'
            elif n2:
                n2 -= 1
                line += '2\n'
            else:
                line += '3\n'
            Note.write(line)
    else:
        P = get_P()
        W = P*U1[x1]
        W = W_to_int(W)
        x1 += 1
        line = str(x + 1) + ' ' + str(W) + ' ' + str(P) + ' (-1,) ('
        for j in suc[0]:
            j = int(j)
            if j > x + 2:
                j -= 1
            elif j == x + 2:
                j = taskNum + x
            line += str(j) + ','
        if len(suc[0]) == 0:
            line += '-1,'
        line += ') 1 0 '
        if n1:
            n1 -= 1
            line += '1\n'
        elif n2:
            n2 -= 1
            line += '2\n'
        else:
            line += '3\n'
        Note.write(line)
        for i in range(2, taskNum):
            P = get_P()
            if i < N1-x+1:
                W = P*U1[x1]
                W = W_to_int(W)
                x1 += 1
            elif i < N1+N2-x+1:
                W = P*U2[x2]
                W = W_to_int(W)
                x2 += 1
            else:
                W = P*U3[x3]
                W = W_to_int(W)
                x3 += 1
            line = str(i + x) + ' ' + str(W) + ' ' + str(P) + ' ('
            for j in pre[i]:
                j = int(j)
                if j > x + 2:
                    j -= 1
                line += str(j) + ','
            if len(pre[i]) == 0:
                line += '-1,'
            line += ') ('
            for j in suc[i]:
                j = int(j)
                if j > x + 2:
                    j -= 1
                elif j == x + 2:
                    j = taskNum + x
                line += str(j) + ','
            if len(suc[i]) == 0:
                line += '-1,'
            line += ') '
            if len(pre[i]) == 0:
                line += '1 0 '
            elif len(suc[i]) == 0:
                line += '0 1 '
            else:
                line += '0 0 '
            if n1:
                n1 -= 1
                line += '1\n'
            elif n2:
                n2 -= 1
                line += '2\n'
            else:
                line += '3\n'
            Note.write(line)
        P = get_P()
        W = P*U2[x2]
        W = W_to_int(W)
        x2 += 1
        line = str(taskNum + x) + ' ' + str(W) + ' ' + str(P) + ' ('
        for j in pre[1]:
            j = int(j)
            if j > x + 2:
                j -= 1
            line += str(j) + ','
        line += ') (-1,) 0 1 '
        if n1:
            n1 -= 1
            line += '1\n'
        elif n2:
            n2 -= 1
            line += '2\n'
        else:
            line += '3\n'
        Note.write(line)
    Note.close()
    return


def checkWay(way, taskSet):
    p_Num = 0
    book = {}
    ind = [10000, 20000, 50000, 100000]
    for i in ind:
        book[i] = 0
    for node in way:
        book[taskSet[node - 1].period] += 1
    for i in ind:
        if book[i] != 0:
            p_Num += 1
            if book[i] == 1 or book[i] > 5:
                return 1
    if p_Num > 3:
        return 1
    return 0


# 出入度上限在 tgff_user 里更改
def checkDAG(taskNum, sensorTask, controlTask, E, n, way_Number, taskSet, HP, plat,plat_C, Ave_rate_C, Ave_rate_N):
    ways = []
    for i in sensorTask:
        for j in controlTask:
            way_num = 0
            S = Floyd_S(taskNum, E, i, j)
            if len(S) >= n:
                return 1, 1
            book_ways = []
            for k in range(100):
                way = find_a_way(E, i, j)
                if way not in book_ways:
                    book_ways.append(way)
                    if checkWay(way, taskSet):
                        continue
                    if len(way) < n:
                        ways.append(way)
                        way_num += 1
                if way_num == way_Number:
                    break
            if way_num < way_Number:
                return 1, 1
            pf = 0
            for (i,j) in plat:
                pf += 1
                if pf != plat_C:
                    Ave_rate = Ave_rate_N
                else:
                    Ave_rate = Ave_rate_C
                utilization = 0
                for k in range(i-1,j):
                    utilization += taskSet[k].C * taskSet[k].worksNum
                utilization /= HP
                # print('Ave_rate=',Ave_rate)
                if utilization < Ave_rate*0.8 or utilization > Ave_rate*1.2:
                    # if utilization < Ave_rate * 0.8:
                    #     print('资源利用率不足')
                    # if utilization > Ave_rate * 1.2:
                    #     print('资源利用率过载')
                    return 1,1
                # print(utilization)
    return 0, ways

# n 节点数 m 边数 Length_Limit 关键路径长度上限 way_number 关键路径数目下限 rate_Limit 平均利用率
def DAG_Prodecter(n, m, Length_Limit, way_Number, O_degree, I_degree, plat_C, U_rate_C, U_rate_N, Ave_rate_C, Ave_rate_N):
    Flag = True
    num = 0
    while Flag and num < 500:
        # print(num)
        num += 1
        x = tgff_user(n, m, O_degree, I_degree)
        read_DAG(x, plat_C, Ave_rate_C, Ave_rate_N)
        taskNum, taskSet, sensorTask, controlTask, E, HP, plat = readDAG("DAG.txt")
        Flag, ways = checkDAG(taskNum, sensorTask, controlTask, E, Length_Limit, way_Number, taskSet, HP, plat,plat_C, Ave_rate_C, Ave_rate_N)
    if num == 500:
        return 1, 1
    return 0, ways


# # 例：生成一个10个节点 20条边的图
# if __name__ == '__main__':
#     x = tgff_user(10, 25, 4, 4)
#     read_DAG(x)

