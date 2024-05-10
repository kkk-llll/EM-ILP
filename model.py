# 该模块用于求解器初始化
from gurobipy import *
from getParameter import *
from dbf import *
import copy

def setDemand(m,n,pn):
    Demand = []
    for i in range(pn):
        name = 'Demand_'+str(n)+'_'+str(i+1)
        Demand.append(m.addVar(vtype=GRB.CONTINUOUS, name = name))
    m.update()
    return Demand

# 变量生成，X[]是二维列表，X_i_j 的值表示示第 i 个任务的第 j 种策略被选中
def setX(m, taskSet, controlTask):
    X = []
    ind = 0
    for task in taskSet:
        temp = []
        ind += 1
        if ind not in controlTask:
            for i in range(2**task.worksNum-1):
                name = 'X_'+str(ind)+'_'+str(i+1)
                temp.append(m.addVar(lb=0, ub=1,vtype=GRB.BINARY, name = name))
        else:
            name = 'X_' + str(ind) + '_' + str(1)
            temp.append(m.addVar(lb=0, ub=1,vtype=GRB.BINARY, name=name))
        X.append(temp)
    m.update()
    return X

def setXbook(X,taskSet, controlTask):
    X_book = []
    for i in range(len(X)):
        book_temp = []
        if i+1 not in controlTask:
            for j in range(2**taskSet[i].worksNum-1):
                book = bin(j+1)[2:]
                while len(book) < taskSet[i].worksNum:
                    book = '0'+book
                book_temp.append(book)
        else:
            book = ''
            while len(book) < taskSet[i].worksNum:
                book = '1'+book
            book_temp.append(book)
        X_book.append(book_temp)
    return X_book


def get_X_index(x):
    name = str(x)
    name = name.split('_')
    return int(name[2][:-1])

def get_X_index2(x):
    name = str(x)
    name = name.split('_')
    name = name[2][:2]
    if name[-1] == ' ':
        name = name[:-1]
    return int(name)


# 变量生成，B 是哈希表（字典）
def setB(m, E):
    B = {}
    for i, j in E:
        i = int(i)
        j = int(j)
        name = str(i)+'_'+str(j)
        temp = m.addVar(vtype=GRB.CONTINUOUS, name = 'B_'+name)
        B[name] = temp
    m.update()
    return B

# 设置目标函数
def setObj(m, U):
    obj = quicksum(U[i] for i in range(len(U)))
    m.setObjective(obj, GRB.MAXIMIZE)
    m.update()
    return m


# 添加约束一，每个任务有且只有一种剔除策略被选中
def addCon1(m, X):
    ind = 0
    for x_i in X:
        con = 0
        ind += 1
        for x_i_j in x_i:
            m.addConstr(x_i_j <= 1)
            m.addConstr(x_i_j >= 0)
            con += x_i_j
        name = 'C_1_'+str(ind)
        m.addConstr(con == 1, name)
    m.update()
    return m

# 添加约束二 每个资源平台的利用率要小于1
def addCons2(m,U):
    for i in range(len(U)):
        name = 'C_2_'+str(i+1)
        m.addConstr(U[i]<=1,name)
    m.update()
    return m

# 添加约束三 dbf <= t
def addCons3(m,t,X,coeff,times,plat,core):
    demand = quicksum(coeff[i-(plat[core][0]-1)][j]*X[i][j] for i in range(plat[core][0]-1,plat[core][1]) for j in range(len(X[i])))
    name = 'C_3_'+str(times)+'_'+str(core+1)
    m.addConstr(demand<=t,name)
    m.update()
    return m

"""
function : 寻找当前解下task_i的剩余作业编号以及对应的释放时间、结束时间
token ：标记，用于辨识生成单周期数据还是双周期数据
"""
def getWRD(i, chosen, taskSet, X_book, alpha, HP, token):
    works_i = getWorks(i - 1, chosen[i - 1], X_book)
    r_i = getR(works_i, taskSet[i - 1].period)
    d_i = getAD(r_i, taskSet[i - 1].C, alpha[i - 1], HP)
    if token == 2:
        for r in range(len(works_i)):
            r_i.append(r_i[r] + HP)
        for d in range(len(works_i)):
            d_i.append(d_i[d] + HP)
        d_i.append(d_i[len(works_i)] + HP)
        for w in range(len(works_i)):
            works_i.append(works_i[w] + taskSet[i - 1].worksNum)
    return works_i, r_i, d_i

"""
    function : 寻找一条任务链下的first/last reaction
    P : 任务链
    chosen : 当前解中每个任务被选中的 mode 索引号（下标从0开始）
    da_limit : data age 的上界系数
    re_limit : reactive time 的上界系数
"""
def findreactions(P, chosen, X_book, taskSet, alpha, HP, da_limit, rt_limit):
    da_limit = da_limit * HP * len(P)
    rt_limit = rt_limit * HP * len(P)
    result = []
    start = P[0]
    worksnum = []                                           # 存储每个任务中的剩余作业数
    for s in range(len(chosen)):
        worksnum.append(getM(s,chosen[s],X_book))
    works_i, r_start, d_start = getWRD(start, chosen, taskSet, X_book, alpha, HP, 2)
    fr_reaction = []
    lr_reaction = []
    lr_find = []
    count = -1
    # tempR = -1
    for job in range(len(works_i)):
        ps = 0                                              # 是否已经无路可选
        jump = 0                                            # 在一条中job chain已经找不到reaction时,跳出，进入下一条job chain
        FD = 0                                              # first reaction的截止日期
        LD = 0
        temp = []
        fr_job = job
        i = start
        if job == 0:
            R = 0 - taskSet[start - 1].period
        else:
            R = r_start[job-1]
        temp.append([start,job+1])
        r_i = r_start
        d_i = d_start
        if fr_job >= int(len(r_i) / 2):                            # 开始考虑第二个超周期内的 job
            fr_job -= int(len(r_i) / 2)
            R -= HP
        if len(fr_reaction) <= 1 and fr_job == int(len(works_i)/2) -1 :
            ps = 1
        for p in P[i-start+1:]:
            if jump == 1:
                break
            works_j, r_j, d_j = getWRD(p, chosen, taskSet, X_book, alpha, HP, 2)
            for react in range(len(r_j)):
                if (d_i[fr_job] <= r_j[react] and d_i[fr_job+1] > r_j[react]) or (len(works_j) == 2 and ((len(works_i) == 2) or ps == 1)):
                    if react >= int(len(r_j)/2):
                        react -= int(len(r_j)/2)
                        FD += HP
                    elif len(works_j) == 2:
                        FD += HP
                    temp.append([p,react+1])
                    r_i = r_j
                    d_i = d_j
                    i = p
                    fr_job = react
                    tFD = FD - R + d_j[fr_job]
                    # print(tFD/ (HP * len(P)))
                    if tFD > rt_limit:
                        # print("超出RT-Bound了！")
                        result.append(-1)
                        result.append(temp)
                        return result
                    if p == P[-1]:
                        FD += d_j[react]
                        LD = FD - taskSet[p-1].period
                    break
                else:
                    if react == len(r_j)-1:
                        jump = 1
                    continue
        # print(temp)
        if jump != 1:
            f_find = copy.deepcopy(temp)
            f_find.insert(0,FD-R)
            fr_reaction.append(f_find)
            # print('aaaaaaa',FD,FR,fr_reaction)
            # print('reactive Time',(FD - R) / (HP * len(P)))
            if FD - R > rt_limit:
                # print("超出RT-Bound了！")
                result.append(-1)
                result.append(temp)
                return result
            # print('fffffffind',fr_reaction)
            # print(LD - R)
            # print('data Age',(LD - R) / (HP * len(P)))
            if LD - R > da_limit and count >= 0:
                # print("超出DA-Bound了！")
                lr_find.append(count)
                break
            count += 1
            """
            for i in range(len(temp)):
                lr_find.append((temp[i][1]-1 + worksnum[temp[i][0]-1]) % int(worksnum[temp[i][0]-1]))
            """
    if len(fr_reaction) == 0:
        result.append(-3)
        result.append(P)
        return result

    if len(lr_find) >0:
        sen_job = lr_find[0]
        lr_reaction.append(fr_reaction[sen_job][1])
        for next_job in fr_reaction[sen_job+1][2:]:
            next_job[1] = next_job[1]-1
            if next_job[1] == 0:
                next_job[1] +=  worksnum[next_job[0]-1]
            lr_reaction.append(next_job)
        works_j, r_j, d_j = getWRD(lr_reaction[-1][0], chosen, taskSet, X_book, alpha, HP, 1)
        for k in range(len(lr_reaction)-1,0,-1):
            RJ = r_j[lr_reaction[k][1] - 1]
            if RJ == 0:
                RJ += HP
            works_i, r_i, d_i = getWRD(lr_reaction[k-1][0], chosen, taskSet, X_book, alpha, HP, 1)
            if len(works_i) == 1:
                r_j = r_i
                d_j = d_i
                works_j = works_i
                continue
            DI = d_i[lr_reaction[k-1][1] - 1]
            while(RJ < DI):
                lr_reaction[k-1][1] -= 1
                if lr_reaction[k-1][1] == 0:
                    lr_reaction[k - 1][1] = worksnum[lr_reaction[k-1][0]-1]
                    DI = d_i[lr_reaction[k-1][1] - 1]- HP
                else:
                    works_i, r_i, d_i = getWRD(lr_reaction[k - 1][0], chosen, taskSet, X_book, alpha, HP, 1)
                    DI = d_i[lr_reaction[k - 1][1] - 1]
            r_j = r_i
            d_j = d_i
            works_j = works_i
        result.append(-2)
        result.append(lr_reaction)
        return result
    result.append(0)
    result.append([fr_reaction[:int(len(fr_reaction)/2)],lr_reaction])
    return result

"""
function : 寻找一条越界job链的相似mode集合--前驱
result : 示例：[[6, 5], [15, 1], [16, 1], [11, 3], [17, 1]]
"""
def getsequence(result1, chosen, X_book, taskSet, alpha, HP):
    # print(result)
    result = copy.deepcopy(result1)
    if(len(result) >= 2):
        for p in range(len(result)-1):
            i,a = result[p]
            j,b = result[p+1]
            works_i, r_i, d_i = getWRD(i,chosen,taskSet,X_book,alpha,HP,2)
            works_j, r_j, d_j = getWRD(j, chosen, taskSet, X_book, alpha, HP, 2)
            start = r_i[a-1]
            end = r_j[b-1]
            if start >= end:
                end += HP
            # print(start,end)
            left = -1
            right = -1
            for k in range(taskSet[i-1].worksNum * 2):
                if left == -1 and k * taskSet[i-1].period >= start:
                    left = k
                if left != -1 and k * taskSet[i-1].period < end:
                    right = k
            string = X_book[i - 1][chosen[i - 1]]
            if right < taskSet[i-1].worksNum:
                slice = string[left:right+1]
            else:
                slice = string[left:]+string[:right-taskSet[i-1].worksNum+1]
            set = match(i-1,left,right,taskSet,X_book,slice)
            result[p][1] = set
    result[-1][1] = [chosen[result[-1][0]-1]]
    return result
"""
function : 寻找一条越界job链的相似mode集合--后继
result : 示例：[[6, 5], [15, 1], [16, 1], [11, 3], [17, 1]]
"""
def getsequence2(result2, chosen, X_book, taskSet, alpha, HP):
    result = copy.deepcopy(result2)
    set = [chosen[0]]
    if(len(result) >= 2):
        for p in range(1,len(result)):
            i,a = result[p-1]
            j,b = result[p]
            result[p-1][1] = set
            works_i, r_i, d_i = getWRD(i,chosen,taskSet,X_book,alpha,HP,2)
            works_j, r_j, d_j = getWRD(j, chosen, taskSet, X_book, alpha, HP, 2)
            start = d_i[a-1]
            end = d_j[b-1]
            if start >= end:
                end += HP
            left = -1
            right = -1
            for k in range(taskSet[j-1].worksNum * 2):
                if left == -1 and k * taskSet[j-1].period >= start:
                    left = k
                if left != -1 and k * taskSet[j-1].period < end:
                    right = k
            string = X_book[j - 1][chosen[j - 1]]
            if right < taskSet[j-1].worksNum:
                slice = string[left:right+1]
            else:
                slice = string[left:]+string[:right-taskSet[j-1].worksNum+1]
            set = match(j-1,left,right,taskSet,X_book,slice)
            if p == len(result)-1:
                result[p][1] = set
            # print(set)
    result[0][1] = [chosen[result[0][0]-1]]
    return result

"""
function : 匹配目标mode中的片段
index : 任务的索引(下表从0开始)
left : 目标片段的释放时间下界
right : 目标片段的释放时间上界
mode ： 剪切后的目标 mode  
"""
def match(index,left,right,taskSet,X_book,mode):
    set = []
    ind = 0
    for string in X_book[index]:
        if right < taskSet[index].worksNum:
            slice = string[left:right + 1]
        else:
            slice = string[left:] + string[:right - taskSet[index].worksNum + 1]
        if slice == mode:
            set.append(ind)
        ind += 1
    return set


def addCons4_1(m, chosen, result, XII, times, loop):
    set = []
    for r in result:
            set.append(r-1)
    aga = []
    for x in set:
        aga.append(XII[x][chosen[x]])
    sum = quicksum(aga[i] for i in range(len(aga)))
    name = 'C_4_'+str(loop)+'_'+str(times)
    m.addConstr(sum <= len(aga)-1,name)
    m.update()
    return m

def addCons4_2(m, chosen, result, XII, times, loop):
    set = []
    for r in result:
        set.append(r[0]-1)
    aga = []
    ind = 0
    for x in set:
        for i in result[ind][1]:
            aga.append(XII[x][i])
        ind += 1
    sum = quicksum(aga[i] for i in range(len(aga)))
    name = 'C_4_'+str(loop)+'_'+str(times)
    m.addConstr(sum <= len(result)-1,name)
    m.update()
    return m

def computefromX(X,X_book,taskSet,alpha,HP):
    C = []
    P = []
    D = []
    for i in range(len(X)):
        z = []
        CI = []
        DI = []
        PI = []
        for j in range(len(X[i])):  # 第 i 个任务的第 j 种策略
            CJ = []
            PJ = []
            a = get_X_index2(X[i][j])
            works = getWorks(i, a-1 ,X_book)
            r = getR(works, taskSet[i].period)
            r.append(r[0] + HP)
            for job in works:
                CJ.append(taskSet[i].C)
            for p in range(len(r) - 1):
                PJ.append(r[p + 1] - r[p])
            DJ = getRD_1(r[:-1], taskSet[i].C, alpha[i], HP)
            CI.append(CJ)
            DI.append(DJ)
            PI.append(PJ)
        C.append(CI)
        P.append(PI)
        D.append(DI)
    return C,D,P

def computefromt(t, X, C, D, P, plat, core):
    coeff =[]
    for i in range(plat[core][0]-1,plat[core][1]):
        z = []
        for j in range(len(X[i])):                                              # 第 i 个任务的第 j 种策略
            z.append(compute_dbf(t, C[i][j], D[i][j], P[i][j]))
        coeff.append(z)
    demand = sum(coeff[i-(plat[core][0]-1)][j] * X[i][j].x for i in range(plat[core][0] - 1, plat[core][1]) for j in range(len(X[i])))
    return demand,coeff

def countfromX(X):
    chosen = []
    for i in range(len(X)):
        for xia in X[i]:
            a = get_X_index2(xia)
            if X[i][a-1].x > 0.9:
                chosen.append(a-1)
    return chosen

"""
function : 从解 X 验证端到端约束
"""
def ETEfromX(m, chosen, XII, X_book, taskSet, ways, alpha, HP, loop, da_limit, rt_limit):
    # print('times:-----------------------------------------',loop)
    times = 1
    num = 0
    for way in ways:
        result = findreactions(way, chosen, X_book, taskSet, alpha, HP, da_limit, rt_limit)
        if result[0] == 0:
            num +=1
        elif result[0] == -1:
            flag = False
            result1 = getsequence(result[1], chosen, X_book, taskSet, alpha, HP)
            result2 = getsequence2(result[1], chosen, X_book, taskSet, alpha, HP)
            # print(result1,'\n',result2)
            for i in range(len(result1)):
                a = result1[i][1]
                b = result2[i][1]
                result1[i][1] = [j for j in a if j in b]
            m = addCons4_2(m, chosen, result1, XII, times, loop)
            times += 1
        elif result[0] == -2:
            flag = False
            result = getsequence(result[1], chosen, X_book, taskSet, alpha, HP)
            m = addCons4_2(m, chosen, result, XII, times, loop)
            times += 1
        elif result[0] == -3:
            flag = False
            m = addCons4_1(m, chosen, result[1], XII, times, loop)
            times += 1

    if num == len(ways):
        flag = True
    m.update()
    return m, flag

# 添加基础约束
def addCon(m, X, U):
    m = setObj(m, U)
    m = addCon1(m, X)
    m = addCons2(m,U)
    return m
