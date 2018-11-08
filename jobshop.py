from copy import deepcopy
#import networkx as nx

from util import flatten, cumsum, unfold, GGraph

class Problem:
	def __init__(self, machines, processing_times):
		"""
		Initialize the needed representation data
		structures for a job shop scheduling problem.
		"""

		self.machines = machines
		self.processing_times = processing_times

		# D: weight of operations
		self._D = tuple(flatten(processing_times))
		# N: amount of nodes
		self.N = len(self._D)+2
		# V: nodes
		self.V = (-1,) + tuple(range(self.N-2)) + (self.N-2,)
		# J: amount of operations in jobs
		self.J = tuple(len(x) for x in machines)

		# A: edges encoding the job precedence constraints
		self.A = {i:[i+1] for i in range(self.N-2) if i+1 not in cumsum(self.J)}
		self.A[-1] = [x for x in [0]+cumsum(self.J)[:-1]]
		for i in cumsum(self.J): self.A[i-1] = [self.N-2]
		self.A[self.N-2] = []

		# E: edges encoding the machine constraints
		self.E = dict()
		for node in self.V:
			self.E[node] = []
		e = [None]*len(machines)
		for i,j in enumerate(flatten(machines)):
			if e[j]: e[j].append(i)
			else: e[j] = [i]
		self.e = [x for x in e if x]
		for el in self.e:
			for i in el:
				self.E[i] = list(set(el)-set([i]))

		# r: start time of node (also length from start node)
		self._r = list(flatten([[0]+cumsum(x)[:-1] for x in processing_times]))
		# t: length to end node
		self._t = list(flatten([
			list(reversed(cumsum(tuple(reversed(x)))))[1:]+[0] 
			for x in processing_times
			]))

		self.machines = tuple(flatten(self.machines))
		self.optimize()

	def optimize(self):
		# hardcodes several parameters for performance
		self._PMP = dict()
		self._SMP = dict()
		self._PM = deepcopy(self.E)
		self._PJ = {-1:[], (self.N-2):[x-1 for x in cumsum(self.J)]}
		for node in self.V: 
			self._PMP[node] = []
			self._SMP[node] = []
			if node in self._PJ.keys(): pass
			elif node in [0]+cumsum(self.J)[:-1]: self._PJ[node] = [-1]
			else: self._PJ[node] = [node-1]

		self._DD = dict()
		for node in self.V:
			if node<0 or node>=self.N-2:
				self._DD[node] = 0
			else:
				self._DD[node] = self._D[node]

	# Getters/setters
	def NbMachines(self):
		return max(self.machines)+1

	def NbJobs(self):
		return len(self.machines)

	def getMachine(self, node):
		return self.machines[node]

	def SJ(self, node):
		return self.A[node]

	def PJ(self, node):
		return self._PJ[node]

	def SM(self, node):
		return self.E[node]

	def SMP(self, node):
		return self._SMP[node]

	def PM(self, node):
		return self._PM[node]

	def PMP(self, node):
		return self._PMP[node]

	def getD(self, node):
		return self._DD[node]

	def setD(self, node, value):
		self._D[node] = value

	def gett(self, node):
		if node<0 or node>=self.N-2:
			return 0
		return self._t[node]

	def sett(self, node, value):
		if node>=self.N-2 or node<0:
			return
		self._t[node] = value
	
	def getr(self, node):
		if node<0 or node>=self.N-2:
			return 0
		return self._r[node]

	def setr(self, node, value):
		if node>=self.N-2 or node<0:
			return
		self._r[node] = value

	def getC(self, node):
		return self.getr(node) + self.getD(node)

	def node_cost(self,i):
		return self.getr(i) + self.getD(i) + self.gett(i)

	def get_cost(self):
		return  max([ self.node_cost(i) for i in range(self.N-2) ])


	def removeArc(self, start, end):
		""" Removes arc from E """
		self.E[start].remove(end)
		self._PM[end].remove(start)
		self._PMP[end].remove(start)
		self._SMP[start].remove(end)


	def addArc(self, start, end):
		""" Adds arc to E """
		self.E[start].append(end)
		self._PM[end].append(start)
		self._PMP[end].append(start)
		self._SMP[start].append(end)

	def followers(self, node):
		""" Returns all nodes with a path from given input node """
		for col in (self.SJ(node), self.SMP(node)):
			for i in col:
				if i not in self.fol:
					self.fol.append(i)
					if i not in self.R:
						self.followers(i)

	def predecessors(self, node):
		""" Returns all nodes with a path to given input node """
		for col in (self.PJ(node), self.PMP(node)):
			for i in col:
				if i not in self.pre:
					self.pre.append(i)
					if i not in self.L:
						self.predecessors(i)


	def top_sort(self,node):
		""" 
		Returns a topological sorting of 
		G(V,AUE), starting from a given node
		"""

		def visit(node):
			if marking[node] == 2: return
			if marking[node] == 1:
				print(node)
				self.draw()
				raise ValueError()
			marking[node] = 1
			for col in (self.PMP(node), self.PJ(node)):
				for i in col:
					if i in self.fol:
						visit(i)
			marking[node] = 2
			self.tsort.append(node)
		
		if node == -1:
			self.fol = list(self.V)
			self.fol.remove(-1)
		else:
			self.fol = []
			self.followers(node)

		self.tsort = []
		marking = [0]*(self.N-1)
		while any(not marking[x] for x in self.fol):	# O(n²)
			nex = tuple(x for x in self.fol if not marking[x])[0]
			visit(nex)
		return self.tsort

	def top_sort_reversed(self, node):
		"""
		Returns a topological sorting of 
		G, in which all arcs are reversed,
		starting from a given node
		"""
		
		def visit(node):
			if marking[node] == 1: return
			for col in (self.SMP(node), self.SJ(node)):
				for i in col:
					if i in self.pre: 
						visit(i)
			marking[node] = 1
			self.tsort.append(node)
		
		if node == self.N-2:
			self.pre = list(self.V)
			self.pre.remove(self.N-2)
		else:
			self.pre = []
			self.predecessors(node)

		self.tsort = []
		marking = [0]*(self.N-1)
		while any(not marking[x] for x in self.pre):
			nex = tuple(x for x in self.pre if not marking[x])[0]
			visit(nex)
		return self.tsort

	def update_r(self, node):
		"""
		Updates all r values of the 
		followers of a given node.
		"""
		tsort = self.top_sort(node)
		for i in tsort:
			m1 = max( self.getr(x)+self.getD(x) for x in self.PJ(i) )
			try: m2 = max( self.getr(x)+self.getD(x) for x in self.PMP(i) )
			except: m2 = 0
			self.setr(i, max((m1, m2)))
		

	def update_t(self, node):
		"""
		Updates all r values of the 
		predecessors of a given node.
		"""
		tsort = self.top_sort_reversed(node)
		for i in tsort:
			m1 = max( self.gett(x)+self.getD(x) for x in self.SJ(i) )
			try: m2 = max( self.gett(x)+self.getD(x) for x in self.SMP(i) )
			except: m2 = 0
			self.sett(i, max((m1, m2)))



	# utility functions for debugging (not compatible with pypy)
	def draw(self, weights=True, name='g'):
		G = GGraph(name)
		G.add_nodes(self.V)
		if weights:
			G.add_weights(self._D)
		G.add_edges(unfold(self.A), 'black')
		G.add_edges(unfold(self.E), 'red')
		G.render()


	def is_feasible(self):
		import networkx as nx
		G = nx.DiGraph()
		edg = tuple(set(unfold(self.A))|set(unfold(self.E)))
		G.add_edges_from(edg)
		return nx.is_directed_acyclic_graph(G)

	def get_makespan(self):
		import networkx as nx
		G = nx.DiGraph()
		edg = tuple(set(unfold(self.A))|set(unfold(self.E)))
		edg_weighted = [(x[0],x[1],-self.getD(x[0])) for x in edg]
		G.add_weighted_edges_from(edg_weighted)

		s = nx.johnson(G, weight='weight')[-1][self.N-2]
		return sum([self.getD(x) for x in s])
