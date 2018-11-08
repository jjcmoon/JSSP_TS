import random

from util import cumsum, unfold, flatten, GGraph
from jobshop import Problem


class BidirProblem(Problem):
	def __init__(self, machines, processing_times, c=3):
		Problem.__init__(self, machines, processing_times)
		self.c = c
		self.EH = [[] for _ in self.e]
		self.EHr = [[] for _ in self.e]
		self.E2 = {i:[] for i in self.E.keys()}


	def directArc(self, end, start):
		"""
		Turns a undirectional arc in E, into
		a directional arc from end to start.
		"""
		self.E[end].remove(start)
		self._PM[start].remove(end)
		self._PMP[end].append(start)
		self._SMP[start].append(end)

	def exCleaner(self, node):
		""" Removes unnessesary connections """
		m = self.getMachine(node)
		if self.EH[m]:
			exnode = self.EH[m].pop()
			self.E2[exnode] += [node]
			for i in self.SM(exnode):
				if (i!=node):
					self.removeArc(exnode,i)
		self.EH[self.getMachine(node)].append(node)

	def exCleaner_reversed(self, node):
		m = self.getMachine(node)
		if self.EHr[m]:
			exnode = self.EHr[m].pop()
			self.E2[node] += [exnode]
			for i in self.PM(exnode):
				if (i!=node):
					self.removeArc(i,exnode)
		self.EHr[self.getMachine(node)].append(node)


	def orientate(self, node):
		""" Orients all egdes in E away from a given node """
		for i in self.SM(node):
			if node in self.E[i]:
				self.directArc(i,node)
						
	def orientate_reversed(self, node):
		""" Orients all egdes in E towards a given node """
		for i in self.PM(node):
			if i in self.E[node]:
				self.directArc(node,i)
			


	def choose(self):
		""" 
		Estimates the scheduling cost of the nodes in S,
		and chooses a random one of the c best 
		"""
		est = []
		for i in self.S:
			em1 = self.getD(self.SJ(i)[0]) + self.gett(self.SJ(i)[0])
			try:
				em2 = max([ self.getD(j) + self.gett(j) for j in self.SM(i)])
			except:
				em2 = 0
			e = self.getr(i) + self.getD(i) + max(em1,em2)
			est.append(e)
		ind = random.choice(sorted(est)[:self.c])
		return self.S[est.index(ind)]


	def choose_reverse(self):
		""" 
		Estimates the scheduling cost of the nodes in T,
		and chooses a random one of the c best 
		"""
		est = []
		for i in self.T:
			em1 = self.getD(self.PJ(i)[0]) + self.getr(self.PJ(i)[0])
			try:
				em2 = max([ self.getD(j) + self.getr(j) for j in self.PM(i)])
			except:
				em2 = 0
			e = self.gett(i) + self.getD(i) + max(em1, em2)
			est.append(e)
		ind = random.choice(sorted(est)[:self.c])
		return self.T[est.index(ind)]

	def binder(self):
		"""
		Finishes representation at the end of bidir,
		by binding the forward and backward parts.
		"""
		for i in range(len(self.EH)):
			if self.EH[i] and self.EHr[i]:
				self.E2[self.EH[i][0]] += self.EHr[i]


	def bidir(self):
		self.L, self.R = [-1], [self.N-2]
		self.S = list(self.SJ(-1))
		self.T = list(self.PJ(self.N-2))

		while len(self.R)+len(self.L)!=self.N:
			s = self.choose()			
			self.orientate(s)
			self.S.remove(s)
			self.L.append(s)
			if s in self.T:
				self.T.remove(s)
			for sj in self.SJ(s): # 1 el except -1
				if sj not in self.R: 
					self.S.append(sj)
			self.update_r(s)
			self.exCleaner(s)
			

			if len(self.R)+len(self.L) == self.N:
				break
			s = self.choose_reverse()
			self.orientate_reversed(s)
			self.T.remove(s)
			self.R.append(s)
			if s in self.S:
				self.S.remove(s)
			for pj in self.PJ(s):
				if pj not in self.L:
					self.T.append(pj)
			self.update_t(s)
			self.exCleaner_reversed(s)
			
		self.R = []
		self.L = []
		self.binder()



if __name__ == '__main__':

	macg = [[0, 1, 2],
			[0, 2, 1],
			[1, 2]]

	procg = [[3, 2, 2], 
			[2, 1, 4],
			[4, 3]]

	x = BidirProblem(macg, procg, c=1)
	x.bidir()
	print(max([ x.getr(i)+x.getD(i)+x.gett(i) for i in range(x.N-1) ]))
	x.draw(weights=False)
