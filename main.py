# 该模块使用其他模块定义的函数进行求解
from readFile import *
from gurobipy import *
from model import *
import random
import os
import shutil
from glob import glob
from DAG_Pro_10_27 import *

import time


def tsteps(ways,taskNum, taskSet, sensorTask, controlTask, E, HP, plat,da_limit,rt_limit,isR):
    m_1 = Model('M1')
    alpha = set_alpha(0.75, 0.2, taskNum)  # 设置每个 job 的比例系数
    saveTaskSet(HP, taskSet, "taskSet.txt")
    X = setX(m_1, taskSet, controlTask)   # 新建求解器下的布尔型变量组 X[]
    X_book = setXbook(X, taskSet, controlTask)
    saveX(X, X_book)
    B = setB(m_1, E)          # 新建求解器浮点型变量组 B[]
    U = getU(X, X_book, HP, taskSet, plat)
    m_1 = addCon(m_1, X, U)      # 添加基础约束
    m_1.setParam('OutputFlag', 0)  # 省略求解过程
    m_1.optimize()
    m_1.write('model.lp')  # 将模型输出到 model.lp 中
    saveSolution(m_1, "solution.txt")  # 将解输出到 solution.txt 中
    if m_1.status == 2:
        print("DBF")
        C, D, P = computefromX(X, X_book, taskSet, alpha, HP)  # 计算初始解下的 C、D、P 参数
        times = 0
        cons2 = []
        for j in range(len(plat)):  # 遍历每一个计算平台
            t = 1000
            result, coeff = computefromt(t, X, C, D, P, plat, j)  # 计算当前解在初始 t下的 dbf值
            while t <= HP:
                if result > t:  # dbf约束被违背
                    print(t)
                    times += 1
                    m_1 = addCons3(m_1, t, X, coeff, times, plat, j)
                    cons2.append([t, coeff, times, j])
                # m_1.setParam('OutputFlag', 0)
                m_1.optimize()
                t += 2500
                try:
                    result, coeff = computefromt(t, X, C, D, P, plat, j)
                except:
                    break
        if m_1.status == 2:
            print("ETE")
            flag = False
            chosen = countfromX(X)
            loop = 1
            while not flag:
                m_1, flag = ETEfromX(m_1, chosen, X, X_book, taskSet, ways, alpha, HP, loop, da_limit, rt_limit)
                m_1.optimize()
                if m_1.status == 2:
                    chosen = countfromX(X)
                    loop += 1
                else:
                    break
            m_1.write('modelII.lp')
            saveSolution(m_1, "solutionII.txt")
            if m_1.status == 3:
                return 1,0
        elif m_1.status == 3:
            return 1,0
    elif m_1.status == 3:
        return 1,0
    if isR:
        u = computeU(X, X_book, HP, taskSet, plat)
        return 0,u

    return 0,(m_1.objVal/3.0)

def mycopyfile(srcfile, dstpath):   # 复制函数
    if not os.path.isfile(srcfile):
        print("%s not exist!" % (srcfile))
    else:
        fpath, fname = os.path.split(srcfile)  # 分离文件名和路径
        if not os.path.exists(dstpath):
            os.makedirs(dstpath)  # 创建路径
        shutil.copy(srcfile, dstpath + fname)  # 复制文件

def nodes():
    DAGNum = 1
    # Nodes = [10,20,30,40,50,60,70,80,90,100]
    # Edges = [30,50,70,90,110,130,150,170,190,210]
    # Rate = [0.45,0.28,0.2,0.17,0.13,0.11,0.09,0.08,0.08,0.07]
    Nodes = [10,30,50,70,90]
    Edges = [30,70,110,150,190]
    Rate = [0.45,0.2,0.13,0.09,0.08]
    for ne in range(len(Nodes)):
        for plat_C in range(1,2):
            unschdule = 0
            Max = -1
            Min = 1e9
            with open("result_Final.txt",'a') as file:
                nodes = Nodes[ne]                                                      # 节点数
                edges = Edges[ne]                                                     # 边数
                Length_Limit = 15                                               # 关键路径长度上限
                way_Number = 3                                                  # 关键路径条数下限
                O_degree = 6                                                    # 出度上限
                I_degree = 6                                                    # 入度上限
                da_limit = 0.9                                                  # data age 松紧系数
                rt_limit = 0.9                                                  # reactive time松紧系数
                Ave_rate_C = 0.6                                                # 关键平台利用率
                Ave_rate_N = 0.6                                                # 非关键平台利用率
                U_rate_C = Rate[ne]
                U_rate_N = Rate[ne]
                Ti = 0                                                          # 执行时间
                Obj = 0
                iteration_times = 50                                            # 迭代次数
                for iteration in range(iteration_times):
                    flag,ways = DAG_Prodecter(nodes, edges, Length_Limit, way_Number, O_degree, I_degree, plat_C, U_rate_C, U_rate_N, Ave_rate_C,Ave_rate_N)
                    while flag:
                        print('数据生成失败')
                        flag, ways = DAG_Prodecter(nodes, edges, Length_Limit, way_Number, O_degree, I_degree, plat_C, U_rate_C,U_rate_N, Ave_rate_C,Ave_rate_N)
                    # f = open("dbf.txt",'w')
                    taskNum, taskSet, sensorTask, controlTask, E, HP, plat = readDAG("DAG.txt")     # 读文件、计算基础参数
                    start = time.perf_counter()
                    isschdule,objval = tsteps(ways,taskNum, taskSet, sensorTask, controlTask, E, HP, plat,da_limit,rt_limit,0)
                    unschdule += isschdule
                    end = time.perf_counter()
                    Max = max(Max, end - start)
                    Min = min(Min, end - start)
                    Ti += end - start

                    mycopyfile('./DAG.txt','./data/nodes/')
                    filename = './data/nodes/' + str(DAGNum) + '.txt'
                    with open("./data/nodes/DAG.txt",'r+') as f3:
                        old = f3.read()
                        f3.seek(0)
                        f3.write(str(ways)+'\n')
                        f3.write(old)
                    try:
                        os.rename('./data/nodes/DAG.txt', filename)
                    except:
                        os.remove(filename)
                        os.rename('./data/nodes/DAG.txt', filename)
                    DAGNum += 1
                # Ti -= Max + Min
                UnR = (iteration_times - unschdule) / iteration_times * 100
                Ti /= iteration_times
                if iteration_times-unschdule != 0:
                    Obj /= (iteration_times - unschdule)

                print('nodes = ', nodes, ', edges = ', edges, ', Length_Limit = ', Length_Limit, ', way_number = ', way_Number, file=file)
                print('O_degree = ', O_degree, ', I_degree = ', I_degree, ', da_limit = ', da_limit, ', rt_limit = ', rt_limit, ', Ave_rate = ', Ave_rate_C,', plat_C = ', plat_C, ', Ave_rate_N = ',Ave_rate_N, ', U_rate_N = ',U_rate_N, file=file)
                print('无解数目', str(unschdule), file=file)
                print('成功调度率: ' + str(UnR) + '%', file=file)
                print("平均运行时间：" + str(Ti) + 's\n', file=file)


def rates():
    DAGNum = 1
    uRate = [0.03, 0.08, 0.11, 0.15, 0.18]
    aRate = [0.1, 0.3, 0.5, 0.7, 0.9]
    for plat_C in range(1, 2):
        for times in range(len(uRate)):
            unschdule = 0

            Max = -1
            Min = 1e9
            with open("result_Final.txt",'a') as file:
                nodes = 50                                                      # 节点数
                edges = 110                                                     # 边数
                Length_Limit = 15                                               # 关键路径长度上限
                way_Number = 3                                                  # 关键路径条数下限
                O_degree = 6                                                    # 出度上限
                I_degree = 6                                                    # 入度上限
                da_limit = 0.9                                                  # data age 松紧系数
                rt_limit = 0.9                                                  # reactive time松紧系数
                Ave_rate_C = aRate[times]                                       # 关键平台利用率
                Ave_rate_N = 0.6                                                # 非关键平台利用率
                U_rate_C = uRate[times]
                U_rate_N =0.13
                Ti = 0                                                          # 执行时间（）
                Obj = 0

                iteration_times = 50                                            # 迭代次数
                for iteration in range(iteration_times):
                    flag, ways = DAG_Prodecter(nodes, edges, Length_Limit, way_Number, O_degree, I_degree, plat_C,
                                               U_rate_C, U_rate_N, Ave_rate_C, Ave_rate_N)
                    # print(ways)
                    while flag:
                        print('数据生成失败')
                        flag, ways = DAG_Prodecter(nodes, edges, Length_Limit, way_Number, O_degree, I_degree,
                                                   plat_C, U_rate_C, U_rate_N, Ave_rate_C, Ave_rate_N)
                    # f = open("dbf.txt",'w')
                    taskNum, taskSet, sensorTask, controlTask, E, HP, plat = readDAG("DAG.txt")  # 读文件、计算基础参数
                    start = time.perf_counter()
                    isschdule,objval = tsteps(ways, taskNum, taskSet, sensorTask, controlTask, E, HP, plat, da_limit,
                                        rt_limit,1)
                    unschdule += isschdule
                    end = time.perf_counter()
                    Max = max(Max, end - start)
                    Min = min(Min, end - start)
                    Ti += end - start
                    start2 = time.perf_counter()
                    mycopyfile('./DAG.txt', './data/rates/')
                    filename = './data/rates/' + str(DAGNum) + '.txt'
                    with open("./data/rates/DAG.txt", 'r+') as f3:
                        old = f3.read()
                        f3.seek(0)
                        f3.write(str(ways) + '\n')
                        f3.write(old)
                    try:
                        os.rename('./data/rates/DAG.txt', filename)
                    except:
                        os.remove(filename)
                        os.rename('./data/rates/DAG.txt', filename)
                    DAGNum += 1
                # Ti -= Max + Min
                UnR = (iteration_times - unschdule) / iteration_times * 100

                Ti /= iteration_times - 2

                if iteration_times - unschdule != 0:
                    Obj /= (iteration_times - unschdule)

                print('nodes = ', nodes, ', edges = ', edges, ', Length_Limit = ', Length_Limit, ', way_number = ',
                      way_Number, file=file)
                print('O_degree = ', O_degree, ', I_degree = ', I_degree, ', da_limit = ', da_limit,
                      ', rt_limit = ', rt_limit, ', Ave_rate = ', Ave_rate_C, ', plat_C = ', plat_C,
                      ', Ave_rate_N = ', Ave_rate_N, ', U_rate_N = ', U_rate_N, file=file)
                print('无解数目', str(unschdule), file=file)
                print('成功调度率: ' + str(UnR) + '%', file=file)
                print("平均运行时间：" + str(Ti) + 's\n', file=file)



def rt():
    DAGNum = 1
    rct = [0.5, 0.7, 0.9, 1.1, 1.3]
    for r in range(len(rct)):
        for plat_C in range(1,2):
            unschdule = 0

            Max = -1
            Min = 1e9
            with open("result_Final.txt",'a') as file:
                nodes = 50                                                      # 节点数
                edges = 110                                                     # 边数
                Length_Limit = 15                                               # 关键路径长度上限
                way_Number = 3                                                  # 关键路径条数下限
                O_degree = 6                                                    # 出度上限
                I_degree = 6                                                    # 入度上限
                da_limit = 0.9                                                  # data age 松紧系数
                rt_limit = rct[r]                                               # reactive time松紧系数
                # plat_C = 2                                                    # 关键平台
                Ave_rate_C = 0.6                                                # 关键平台利用率
                Ave_rate_N = 0.6                                                # 非关键平台利用率
                U_rate_C = 0.13
                U_rate_N = 0.13
                Ti = 0                                                          # 执行时间（）
                Obj = 0

                iteration_times = 50                                            # 迭代次数
                for iteration in range(iteration_times):
                    flag, ways = DAG_Prodecter(nodes, edges, Length_Limit, way_Number, O_degree, I_degree, plat_C,
                                               U_rate_C, U_rate_N, Ave_rate_C, Ave_rate_N)
                    while flag:
                        print('数据生成失败')
                        flag, ways = DAG_Prodecter(nodes, edges, Length_Limit, way_Number, O_degree, I_degree, plat_C,
                                                   U_rate_C, U_rate_N, Ave_rate_C, Ave_rate_N)
                    # f = open("dbf.txt",'w')
                    taskNum, taskSet, sensorTask, controlTask, E, HP, plat = readDAG("DAG.txt")  # 读文件、计算基础参数
                    start = time.perf_counter()
                    isschdule, objval = tsteps(ways, taskNum, taskSet, sensorTask, controlTask, E, HP, plat,
                                               da_limit, rt_limit,0)
                    unschdule += isschdule
                    end = time.perf_counter()
                    Max = max(Max, end - start)
                    Min = min(Min, end - start)
                    Ti += end - start

                    mycopyfile('./DAG.txt', './data/rct/')
                    filename = './data/rct/' + str(DAGNum) + '.txt'
                    with open("./data/rct/DAG.txt", 'r+') as f3:
                        old = f3.read()
                        f3.seek(0)
                        f3.write(str(ways) + '\n')
                        f3.write(old)
                    try:
                        os.rename('./data/rct/DAG.txt', filename)
                    except:
                        os.remove(filename)
                        os.rename('./data/rct/DAG.txt', filename)
                    DAGNum += 1
                # Ti -= Max + Min
                UnR = (iteration_times - unschdule) / iteration_times * 100

                Ti /= iteration_times - 2

                if iteration_times - unschdule != 0:
                    Obj /= (iteration_times - unschdule)

                print('nodes = ', nodes, ', edges = ', edges, ', Length_Limit = ', Length_Limit, ', way_number = ',
                      way_Number, file=file)
                print('O_degree = ', O_degree, ', I_degree = ', I_degree, ', da_limit = ', da_limit, ', rt_limit = ',
                      rt_limit, ', Ave_rate = ', Ave_rate_C, ', plat_C = ', plat_C, ', Ave_rate_N = ', Ave_rate_N,
                      ', U_rate_N = ', U_rate_N, file=file)
                print('无解数目', str(unschdule), file=file)
                print('成功调度率: ' + str(UnR) + '%', file=file)
                print("平均运行时间：" + str(Ti) + 's\n', file=file)


def da():
    DAGNum = 1
    dte = [0.5, 0.7, 0.9, 1.1, 1.3]
    for d in range(len(dte)):
        for plat_C in range(1,2):
            unschdule = 0

            Max = -1
            Min = 1e9
            with open("result_Final.txt",'a') as file:
                nodes = 50                                                      # 节点数
                edges = 110                                                     # 边数
                Length_Limit = 15                                               # 关键路径长度上限
                way_Number = 3                                                  # 关键路径条数下限
                O_degree = 6                                                    # 出度上限
                I_degree = 6                                                    # 入度上限
                da_limit = dte[d]                                                  # data age 松紧系数
                rt_limit = 0.9                                               # reactive time松紧系数
                # plat_C = 2                                                    # 关键平台
                Ave_rate_C = 0.6                                                # 关键平台利用率
                Ave_rate_N = 0.6                                                # 非关键平台利用率
                U_rate_C = 0.13
                U_rate_N = 0.13
                Ti = 0                                                          # 执行时间
                Obj = 0
                iteration_times = 50                                            # 迭代次数
                for iteration in range(iteration_times):
                    flag, ways = DAG_Prodecter(nodes, edges, Length_Limit, way_Number, O_degree, I_degree, plat_C,
                                               U_rate_C, U_rate_N, Ave_rate_C, Ave_rate_N)
                    while flag:
                        print('数据生成失败')
                        flag, ways = DAG_Prodecter(nodes, edges, Length_Limit, way_Number, O_degree, I_degree, plat_C,
                                                   U_rate_C, U_rate_N, Ave_rate_C, Ave_rate_N)
                    taskNum, taskSet, sensorTask, controlTask, E, HP, plat = readDAG("DAG.txt")  # 读文件、计算基础参数
                    start = time.perf_counter()
                    isschdule,objval = tsteps(ways, taskNum, taskSet, sensorTask, controlTask, E, HP, plat, da_limit,
                                        rt_limit,0)
                    unschdule += isschdule
                    end = time.perf_counter()
                    Max = max(Max, end - start)
                    Min = min(Min, end - start)
                    Ti += end - start
                    Obj += objval
                    mycopyfile('./DAG.txt', './data/dte/')
                    filename = './data/dte/' + str(DAGNum) + '.txt'
                    with open("./data/dte/DAG.txt", 'r+') as f3:
                        old = f3.read()
                        f3.seek(0)
                        f3.write(str(ways) + '\n')
                        f3.write(old)
                    try:
                        os.rename('./data/dte/DAG.txt', filename)
                    except:
                        os.remove(filename)
                        os.rename('./data/dte/DAG.txt', filename)
                    DAGNum += 1
                UnR = (iteration_times - unschdule) / iteration_times * 100
                # Ti -= Max + Min
                Ti /= iteration_times - 2

                if iteration_times - unschdule != 0:
                    Obj /= (iteration_times - unschdule)
                print('nodes = ', nodes, ', edges = ', edges, ', Length_Limit = ', Length_Limit, ', way_number = ',
                      way_Number, file=file)
                print('O_degree = ', O_degree, ', I_degree = ', I_degree, ', da_limit = ', da_limit, ', rt_limit = ',
                      rt_limit, ', Ave_rate = ', Ave_rate_C, ', plat_C = ', plat_C, ', Ave_rate_N = ', Ave_rate_N,
                      ', U_rate_N = ', U_rate_N, file=file)
                print('无解数目', str(unschdule), file=file)
                print('成功调度率: ' + str(UnR) + '%', file=file)
                print("平均运行时间：" + str(Ti) + 's\n', file=file)




if __name__ == '__main__':
    rates()
    # nodes()
    # rt()
    # da()