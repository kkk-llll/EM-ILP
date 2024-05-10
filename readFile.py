# 该模块用于定义数据结构以及读文件并计算初始参数
from getParameter import *


class Task:                     # 一个Task()实体表示一个任务
    def __init__(self):
        self.worksNum = 0       # 剔除前超周期内释放作业数
        self.period = 0         # 释放作业周期
        self.pre = []           # 前驱节点
        self.nxt = []           # 后继节点
        self.C = 0              # 作业执行时间 (WCET)
        self.platform = 0       # 任务所在平台


def readDAG(filename):
    taskNum = 0
    taskSet = []
    sensorTask = []
    controlTask = []
    E = []
    plat = []
    platform = []
    with open(filename, 'r') as f:
        taskNum = int(f.readline())
        while True:
            line = f.readline()
            if not line:
                break
            line = line.split()
            temp = Task()
            temp.C = int(line[1])
            temp.period = int(line[2])
            pre = line[3][1:-2].split(',')
            for i in pre:
                temp.pre.append(int(i))
            nxt = line[4][1:-2].split(',')
            for i in nxt:
                temp.nxt.append(int(i))
            temp.platform = int(line[7])
            platform.append(int(line[7]))
            taskSet.append(temp)
            start = int(line[0])
            end = line[4][1:-2]
            end = end.split(',')
            for i in end:
                i = int(i)
                if i == -1:
                    break
                E.append([start, i])
            if line[5] == '1':
                sensorTask.append(int(line[0]))
            if line[6] == '1':
                controlTask.append(int(line[0]))
    HP = int(getHP(taskSet))
    for task in taskSet:
        task.worksNum = int(HP/task.period)
    a = platform[0]
    c = [1]
    for i in range(len(platform)):
        if platform[i] == a and i != len(platform)-1:
            continue
        elif platform[i] != a:
            c.append(i)
            plat.append(c)
            c = []
            a = platform[i]
            c.append(i+1)
        if i == len(platform)-1:
            c.append(i+1)
            plat.append(c)

    return taskNum, taskSet, sensorTask, controlTask, E, HP, plat


# 将 taskSet 参数写入 taskSet.txt
def saveTaskSet(HP, taskSet, filename):
    f = open(filename,"w")
    i = 0
    print('HP = ', HP, file = f)
    for temp in taskSet:
        i += 1
        print('-----------------', file = f)
        print('task', i, ':', file = f)
        print('period = ', temp.period, file = f)
        print('C = ', temp.C, file = f)
        print('worksNum = ', temp.worksNum, file = f)
    f.close()
    return

def saveX(X, X_book):
    f = open('X.txt',"w")
    i1 = 0
    for i in X:
        i2 = 0
        for j in i:
            name = str(j)
            name = name.split()[-1][:-1]
            print(name, '  ', X_book[i1][i2], file = f)
            i2 += 1
        i1 += 1
    f.close()
    return

# 将问题的解写入 solution.txt
def saveSolution(m, filename):
    bestX = []
    f = open(filename,"w")
    if m.status != 2:
        print('Failed. No soution.')
        print('No soution.', file = f)
        return
    print('Solved successfully.')
    for v in m.getVars():                       
        print('%s %g' % (v.varName, v.x), file = f)
        if (v.varName[0] == 'X' or v.varName[0] == 'Y') and v.x == 1:
            bestX.append(v.varName)
    print('Obj: %g' % m.objVal, file = f)
    print('\nThe bestX are as follows:', file = f)
    print(bestX, file = f)
    f.close()
    return