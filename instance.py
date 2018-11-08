from bidir import BidirProblem
from tabu import TabuProblem
import timeit
import time
import random
import numpy as np 
 

def getInstances(name):
	""" Returns the jobshop instances from a file with given name """
	
	def getMP(M):
		tail = []
		for row in [x.split(" ") for x in M]:
			tail.append([int(x.strip()) for x in row if x]) 
		mac = []
		for row in tail:
			mac.append(row[::2])
		proc = []
		for row in tail:
			proc.append(row[1::2])

		return mac, proc
	
	name += '.txt'
	with open(name, 'r') as f:
		l = f.read()
	l = l.split("\n")
	while l:
		i = l.pop(0)
		if not l: continue
		nBMac = int([x for x in i.split(" ") if x][0])
		yield getMP(l[:nBMac])
		l = l[nBMac:]

opt_law = [666, 655, 597, 590, 593, 926, 890, 863, 951, 958, 1222, 1039, 1150, 1292, 1207, 945, 784, 848, 842, 902, 1046, 927, 1032, 935, 977, 1218, 1235, 1216, 1152, 1355, 1784, 1850, 1719, 1721, 1888, 1268, 1397, 1196, 1233, 1233]
# yamada optima aren't the proven optimal, but the best found in the paper
opt_yam = [967, 945, 951, 1052]
law = tuple(getInstances('lawrence'))
yam = tuple(getInstances('yamada'))


def mainBidir(begin=0, end=40, it=5, c=3, inst='law'):
	if inst == 'law':
		data = law
		opt = opt_law
	elif inst == 'yam':
		data = yam
		opt = opt_yam
	else:
		raise ValueError('unknown instance')
	avg_Z = []
	
	for i,inst in enumerate(data[begin:end]):
		solution_best = float('inf')
		mac, proc = inst
		x = BidirProblem(mac, proc)
		m = x.NbMachines()
		n = len(mac)
		dt = []
		for r in range(it):
			x = BidirProblem(mac, proc, c=c)
			t1 = time.time()
			x.bidir()
			t2 = time.time()
			dt.append(t2-t1)
			solution = x.get_cost()
			if solution<solution_best:
				solution_best = solution
		optimum = opt_law[i+begin]
		Delta = (solution_best-optimum)/optimum*100
		avg_Z.append(Delta)
		dt = sum(dt)/len(dt)
		print("LA%02d: %-4d (opt: %-4d), Z=%.02f, t=%f"%(i+begin+1, solution_best, optimum , Delta, dt))
		# LATEX printing:
		#print("LA%02d & %d & %d & %d & %d & %.02f & %.04f \\\\" % (i+begin+1, n,m, optimum, solution_best, Delta, dt))
	avg_Z = sum(avg_Z)/len(avg_Z)
	
	return avg_Z, dt




def mainTabu(begin=0, end=40, it=5, c=3):
	avg_Z = []
	for i, inst in enumerate(law[begin:end]):
		solution_best = float('inf')
		mac, proc = inst
		dt = []
		x = BidirProblem(mac, proc)
		m = x.NbMachines()
		n = len(mac)
		bsols = []
		for r in range(it*5):
			x = BidirProblem(mac, proc, c=c)
			x.bidir()
			bsols.append((x.get_cost(),x.E2))
		es = sorted(bsols, key=lambda x:x[0])
		for r in range(it):
			x = TabuProblem(mac, proc, es[r][1])
			t1 = time.time()
			x.TB()
			t2 = time.time()
			dt.append(t2-t1)
			solution = x.get_cost()
			if solution<solution_best:
				solution_best = solution
		optimum = opt_law[i+begin]
		Delta = (solution_best-optimum)/optimum*100
		avg_Z.append(Delta)
		dt = sum(dt)/len(dt)
		#print("LA%02d: %d (opt: %d), Z=%02f"%(i+begin+1, solution_best, optimum , Delta))
		# LATEX printing
		print("LA%02d & %d & %d & %d & %d & %.02f & %d & %.04f \\\\" % (i+begin+1, n,m, optimum, solution_best, Delta, es[r][0], dt))

	return avg_Z

def main():
	mainBidir(c=2, it=10)
	#mainTabu(c=2, it=5)
	
if __name__ == '__main__':
	main()