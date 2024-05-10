#coding= gbk
from queue import Queue

class Pair:
    def __init__(self):
        self.workload = -1
        self.interval = -1

# ��ÿһ��(i,j)������Ӧ��(workload,interval size)
def compute(m,n,N,P,D,E,Store):
    # print(m,n)
    a = []
    d = []
    wkl = 0
    ins = 0
    for i in range(N):
        if i == 0:
            a.append(0)
        else:
            a.append(a[i - 1] + P[(m+i-1) % N])
        d.append(a[i] + D[(m+i) % N])
    # print(a,d)
    for j in range(m,m+n+1):
        wkl += E[j % N]
    ins = d[n]-a[0]
    # print(wkl,ins)
    pair = Pair()
    pair.workload = wkl
    pair.interval = ins
    Store.append(pair)
    return Store


# һ�˿�������(����)
# def partition(Store,first,last):
#     v = Store[first]
#     i = first + 1
#     j = last - 1
#     while True:
#         while Store[i].interval < v.interval and i <= first:
#             i += 1
#         while Store[j].interval > v.interval and j >= last:
#             j -= 1
#         if i > j:
#             break
#         x = Store[first]
#         Store[first] = Store[last]
#         Store[last] = x
#     return first

# print(Store[0].interval)
def partition(Store,first,last):
    Store[0]= Store[first]
    while(first < last):
        while(first < last and Store[last].interval > Store[0].interval):
            last -= 1
        if first < last:
            Store[first]= Store[last]
            first += 1
        while(first < last and Store[first].interval <= Store[0].interval):
            first += 1
        if first < last:
            Store[last] = Store[first]
            last -= 1
    Store[first] = Store[0]
    return first


def QSort(Store,left,right):
    q = Queue()
    begin = left
    end = right
    k = 0
    q.put(left)
    q.put(right)

    while q.empty() == 0:
        begin = q.get()
        end = q.get()
        k = partition(Store,begin,end)
        if begin < k-1:
            q.put(begin)
            q.put(k-1)
        if k+1 < end:
            q.put(k+1)
            q.put(end)
    return


# def QSort(Store,first,last):
#     if(first<last):
#         t = partition(Store,first,last)
#         QSort(Store,first,t-1)
#         QSort(Store,t+1,last)
#     return Store


# һ�˿�������(����)
def inpartition(Store,first,last):
    Store[0] = Store[first]
    while(first < last):
        while(first < last and Store[last].workload <= Store[0].workload):
            last -= 1
        if first < last:
            Store[first] = Store[last]
            first += 1
        while(first < last and Store[first].workload > Store[0].workload):
            first += 1
        if first < last:
            Store[last] = Store[first]
            last -= 1
    Store[first] = Store[0]
    return first

def inQSort(Store,left,right):
    q = Queue()
    begin = left
    end = right
    k = 0
    q.put(left)
    q.put(right)

    while q.empty() != 0:
        begin = q.get()
        end = q.get()
        k = inpartition(Store,begin,end)
        if begin < k-1:
            q.put(begin)
            q.put(k-1)
        if k+1 < end:
            q.put(k+1)
            q.put(end)
    return


# def inQSort(Store,first,last):
#     if (first < last):
#         s = inpartition(Store, first, last)
#         inQSort(Store, first, s - 1)
#         inQSort(Store, s + 1, last)
#     return Store


# ���ֲ����㷨
def binary_search(Final,begin,end,time):
    # print("binary-search")
    if begin > end:
        return 0
    mid = int((begin + end)/2)
    if Final[mid].interval <= time and (mid+1 >= len(Final) or Final[mid+1].interval > time):
        return Final[mid].workload
    elif Final[mid].interval >time:
        return binary_search(Final,begin,mid-1,time)
    else:
        return binary_search(Final,mid+1,end,time)

# # ������������ĳһʱ���µ�workload
# for i in range(Final[-1].interval+2):
#     result = binary_search(Final,0,len(Final),i)
#     print(i,result)

def compute_dbf(t,E,D,P):
    # print(t,'\n',E,'\n',D,'\n',P)
    Store = []  # �洢����pair
    Final = []  # �洢���ձ�ʣ�µ�pair
    N = len(E)
    Esum = 0
    Psum = 0
    Dmin = -1

    for i in E:
        Esum += i
    for j in P:
        Psum += j
    Dmin = min(D)
    # print(Esum,Psum,Dmin)
    if t < Dmin:
        dbf = 0
    else:
        init = Pair()
        Store.append(init)

        # ѭ����ʼ
        for i in range(len(E)):
            for j in range(len(E)):
                # print(i,j)
                Store = compute(i,j,N,P,D,E,Store)

        # print(Store)

        # ��interval size��������
        QSort(Store, 1, len(Store) - 1)
        # ��interval size��ͬ�ĶԽ���workload��������
        a = Store[1].interval
        left = 1
        for i in range(1, len(Store)):
            if Store[i].interval > a:
                inQSort(Store, left, i - 1)
                a = Store[i].interval
                left = i


        # ��ɾ�����������ԣ�ȷ�����ս���洢��Final��
        b = Store[1].workload
        Final.append(Store[1])
        for pair in Store[2:]:
            if pair.workload > b:
                Final.append(pair)
                b = pair.workload

        else:
            dbf = int((t-Dmin)/Psum) * Esum + binary_search(Final,0,len(Final),Dmin + (t-Dmin) % Psum)
    return dbf

