from copy import deepcopy
import random

from jobshop import Problem
from bidir import BidirProblem


class TabuProblem(Problem):
	def __init__(self, machines, processing_times, E):
		# initialize
		Problem.__init__(self, machines, processing_times)

		# normalize from initial solution
		self.E = E
		self._PM = {i:[] for i in self.E.keys()}
		for i in self.E.keys():
			if self.E[i]:
				self._PM[self.E[i][0]] = [i]
		self._PMP = deepcopy(self._PM)
		self._SMP = deepcopy(self.E)
		self.update_r(-1)
		self.update_t(self.N-2)
		self.R = []
		self.L = []

	def lpath(self, Q, fl):
		"""
		Calculates the cost of a inversion 
		of a set of nodes to Q.
		"""
		D = self._DD
		a = Q[0]
		q = len(Q)
		r = self._r
		re = list(r)
		pj = self.PJ(a)[0]
		pm = self.PM(fl[0])
		if pm: re[a] = max(self.getr(pj) + D[pj], r[pm[0]] + D[pm[0]] )
		else: re[a] = self.getr(pj) + D[pj]

		for i in range(1,q):
			b = Q[i]
			pj = self.PJ(b)[0]
			re[b] = max(self.getr(pj)+D[pj], re[a]+D[a])
			a = b
		
		b = Q[q-1]
		t = self._t
		te = list(t)
		sj = self.SJ(b)[0]
		sm = self.SM(fl[1])
		if sm: te[b] = max(self.gett(sj) + D[sj], t[sm[0]] + D[sm[0]] )
		else: te[b] = self.gett(sj) + D[sj]
		
		for i in range(q-2, -1, -1):
			a = Q[i]
			sj = self.SJ(a)[0]
			te[a] = max(self.gett(sj)+D[sj], te[b]+D[b])
			b = a

		return max( re[i]+self.getD(i)+te[i] for i in Q ),re,te
		

	def get_critical_nodes(self):
		""" Returns all nodes on a longest path """
		l = []
		m = self.get_cost()
		for node in self.V:
			if self.node_cost(node) == m:
				l.append(node)
		return l + [-1, self.N-2]

	def get_critical_path(self):
		""" Returns a longest path trough G(V,EUA) """
		nodes = [-1]
		m = max([self.node_cost(x) for x in self.SJ(-1)])
		snodes = [x for x in self.SJ(-1) if self.node_cost(x)==m]
		first = max(snodes, key=lambda x:self.gett(x))
		nodes.append(first)

		while nodes[-1]!=(self.N-2):
			sj = self.SJ(nodes[-1])
			sm = self.SM(nodes[-1])
			if sm:
				smc = self.node_cost(sm[0])
			else:
				nodes.append(sj[0])
				continue
			sjc = self.node_cost(sj[0])
			if sjc>smc:
				nodes.append(sj[0])
			elif sjc<smc:
				nodes.append(sm[0])
			elif sjc==smc:
				if self.getr(sj[0])<self.getr(sm[0]):
					nodes.append(sj[0])
				else:
					nodes.append(sm[0])
		return nodes

	def estim_NA(self, u, v):
		""" 
		Estimates the cost of a swap of u and v,
		including permutations using PM and SM.
		"""
		c = (v,u),(u,v)
		est = [(c, self.lpath(*c))]
		if self.PM(u):
			w = self.PM(u)[0]
			c = (v,w,u), (w,v)
			est.append((c, self.lpath(*c)))
			c = (v,u,w),(w,v)
			est.append((c, self.lpath(*c)))
		if self.SM(v):
			w = self.SM(v)[0]
			c = (v,w,u),(u,w)
			est.append((c, self.lpath(*c)))
			c = (w,v,u),(u,w)
			est.append((c, self.lpath(*c)))
		return est

	def RNA(self):
		""" Returns neighborhood RNA """
		neighborhood = []
		cpath = self.get_critical_path()
		pairs = [(cpath[i],cpath[i+1]) for i in range(1,len(cpath)-2)]
		for i, pair in enumerate(pairs):
			u,v = pair
			
			if v not in self.SM(u):
				continue
			if self.PM(u) and self.SM(v):
				if self.PM(u)[0] in cpath and self.SM(v)[0] in cpath:
					continue
			neighborhood += self.estim_NA(u,v)
		return neighborhood

	def getBlocks(self):
		"""
		Returns all the blocks in the solution.
		These are sequences of operations, executed on
		the same machine directly after each other.
		"""
		cpath = self.get_critical_path()
		r = [[cpath[0]]]
		for i, g in enumerate(cpath[1:]):
			if self.PM(g) and self.PM(g)[0] == cpath[i]:
				r[-1].append(g)
			else:
				r.append([g])
		return r

	def block_solver(self, block, i):
		""" 
		Returns a feasible set of swaps for 
		node at block[i] to the start of a
		given block.
		"""
		if i<2:
			return False
		node = block[i]
		c = self.getr(self.PJ(node)[0])
		if any(self.getC(self.SJ(k)[0])<=c for k in block[:i]):
			return self.block_solver(block[1:], i-1)
		return ([node] + block[:i],(block[0],block[i]))

	def block_solver_reversed(self, block, i):
		""" 
		Returns a feasible set of swaps for 
		node at block[i] to the end of a
		given block.
		"""
		if i>len(block)-3:
			return False
		node = block[i]
		c = self.getC(self.SJ(node)[0])
		if any(self.getr(self.PJ(k)[0]) >= c for k in block[i:]):
			return self.block_solver_reversed(block[:-1], i)
		return (block[i+1:] + [node],(block[i],block[-1]))

	def NB(self):
		""" Returns the neighborhood NB """
		neighborhood = []
		for block in self.getBlocks():
			# prevent RNA overlaps
			if len(block)<5: continue

			for i, node in enumerate(block[2:-2]):
				i +=2
				#forwards swap
				s = self.block_solver(block, i)
				if s:
					neighborhood.append((s, self.lpath(*s)))
				
				#backwards swap
				s = self.block_solver_reversed(block, i)
				if s:
					neighborhood.append((s, self.lpath(*s)))
		return neighborhood

	def NC(self):
		""" Returns the neighborhood NC """
		return tuple(self.RNA())+tuple(self.NB())


	def save(self):
		""" save current solution attributes """
		s = [None]*6
		s[0] =  deepcopy(self.E)
		s[1] = deepcopy(self._r)
		s[2] = deepcopy(self._t)
		s[3] = deepcopy(self._PM)
		s[4] = deepcopy(self._PMP)
		s[5] = deepcopy(self._SMP)
		return s

	def restore(self, s):
		""" restore to saved solution """
		self.E = s[0]
		self._r = s[1]
		self._t = s[2]
		self._PM = s[3]
		self._PMP = s[4]
		self._SMP = s[5]



	def TB(self):
		""" Performs the tabu search algorithm """

		def aspiration(cost):
			""" Returns whether a cost is aspirated """
			if best_cost>cost:
				return True
			return False

		def resetTabuList():
			self.TM = [ [0 for i in range(self.N-2)] \
					for j in range(self.N-2) ]

		def setTabu(s):
			self.TM[s[1]][s[0]] = Delta

		def isTabu(s,c):
			return self.TM[s[0]][s[1]] > Delta - tabu_length \
				and not aspiration(c)

		def resetWitness():
			self.witnessCost = [ [0 for i in range(self.N-2)] \
					for j in range(self.N-2) ]
			self.witnessValue = [ [0 for i in range(self.N-2)] \
					for j in range(self.N-2) ]

		def hasWitnessed(s, c):
			if self.witnessCost[s[0]][s[1]] != c:
				self.witnessCost[s[0]][s[1]] = c
				self.witnessValue[s[0]][s[1]] = 0
				return False

			if self.witnessValue[s[0]][s[1]] >= TCYCLE:
				self.witnessValue[s[0]][s[1]] = 0
				return True
			self.witnessValue[s[0]][s[1]] += 1
			return False


		#########################################
		# --- initialization of tabu search --- #
		#########################################

		best_s = self.save()
		best_cost = self.get_cost()
		rb_s = self.save()
		rb_cost = self.get_cost()
		tabu_length = 1

		MAXDELTA = 800
		Delta = MAXDELTA
		restarts = 0
		MAXRESTARTS = 50

		MIN_ABS = 2
		INT_OFFSET = (self.NbJobs()+self.NbMachines())//3
		MAX_OFFSET = 6
		MINMAX_RESET = 5
		minmax = 1

		prev_cost = 0

		resetTabuList()
		resetWitness()
		TCYCLE = 3

		while restarts < MAXRESTARTS:
			Delta -= 1
			minmax -=1

			#randomize tabu length min/max
			if minmax == 0:
				minmax = MINMAX_RESET
				min_length = random.randint(MIN_ABS, MIN_ABS+INT_OFFSET)
				max_length = random.randint(min_length+MAX_OFFSET, min_length+MAX_OFFSET+INT_OFFSET)


			##############################################
			# --- choose candidate from neighborhood --- #
			##############################################

			# calculate neighborhoods
			cand = []
			RNA = self.RNA()
			NB = self.NB()

			# append RNA candidates that aren't tabu
			for x in RNA:
				s = x[0][0]
				sc = x[1][0]
				if len(s)==3:
					if isTabu(s[:-1],sc) or isTabu(s[1:],sc) or isTabu((s[0],s[2]),sc):
						continue
				elif len(x[0])==2:
					if isTabu(s, sc):
						continue
				cand.append(x)

			# append NB candidates that aren't tabu
			for x in NB:
				s = x[0][0]
				sc = x[1][0]
				if isTabu(s[-2:], sc):
					continue
				cand.append(x)

			# All candidates tabu?
			if not cand:
				# can't choose length 3, because an infeasible solution might be chosen
				try:
					cand = [random.choice([x for x in RNA if len(x[0][0])==2])]
				except:
					cand = [random.choice( [x for x in tuple(NB)] )]
			
			# choose move from candidates			
			((s,lm), (sc,te,re)) = min(cand, key=lambda x: x[1][0])
			
			# if candidate already witnessed, randomize move
			if hasWitnessed(s[:2], sc):
				try:
					cand = [random.choice([x for x in RNA if len(x[0][0])==2])]
				except:
					cand = [random.choice( [x for x in tuple(NB)])]
				((s,lm), (sc,te,re)) = cand[0]
			

			#################################
			# --- Make chosen move tabu --- #
			#################################
			cnodes = self.get_critical_nodes()

			if len(s)==2 and \
					self.SM(s[1]) not in cnodes and \
					self.PM(s[0]) not in cnodes:
				setTabu(s)

			elif len(s)==2:
				setTabu(s)
				if self.SM(s[0]):
					setTabu((s[0],self.SM(s[0])[0]))
				if self.PM(s[1]):
					setTabu((s[1],self.PM(s[1])[0]))

			elif len(s)==3:
				setTabu(s[:-1])
				setTabu(s[1:])

			else:
				swaps = [(s[i], s[i+1]) for i in range(len(s)-1)]
				for swap in swaps:
					setTabu(swap)
			
			##########################################
			# --- Update solution to chosen move --- #
			##########################################
			pm = self.PM(lm[0])
			sm = self.SM(lm[1])
			if pm:
				self.addArc(pm[0], s[0])
				self.removeArc(pm[0], lm[0])
			if sm:
				self.addArc(s[-1], sm[0])
				self.removeArc(lm[1], sm[0])

			# remove old arcs from E
			if len(s)==2:
				self.removeArc(lm[0],lm[1])
			else:
				Qs = list(s)
				Qs.remove(lm[0])
				Qs.remove(lm[1])
				self.removeArc(lm[0],Qs[0])
				self.removeArc(Qs[-1],lm[1])
				for i in range(len(Qs)-1):
					self.removeArc(Qs[i],Qs[i+1])
			
			# add new arcs to E
			for i in range(len(s)-1):
				self.addArc(s[i],s[i+1])

			if pm and len(s)==2:
				self.update_r(self.PJ(lm[1])[0])
			else:
				self.update_r(-1)
			if sm and len(s)==2:
				self.update_t(self.SJ(lm[0])[0])
			else:
				self.update_t(self.N-2)
			sc_check = self.get_cost()
			
			###########################
			# --- Tabu strategies --- #
			###########################

			# check actual cost, (usually larger than estimate)
			# and save solution if new optimal
			if sc_check<rb_cost:
				rb_cost = sc_check
				rb_s = self.save()

			
			# adjust tabu list length
			if prev_cost > sc:
				# improving phase --> decrease length
				if tabu_length>min_length:
					tabu_length -= 1
			else:
				# not improving phase --> increasing length
				if tabu_length<max_length:
					tabu_length += 1

			# new optimum (estimated)?
			if sc < best_cost:
				self.update_t(self.N-2)
				self.update_r(-1)
				resetTabuList()
				resetWitness()
				best_cost = sc
				best_s = self.save()
				Delta = MAXDELTA
				tabu_length = 1
				

			# restarting
			if Delta <= 0:
				resetTabuList()
				resetWitness()
				self.restore(best_s)
				Delta = MAXDELTA
				restarts += 1

		self.restore(rb_s)
		self.update_r(-1)
		self.update_t(self.N-2)

if __name__ == '__main__':

	macg = [[0, 1, 2],
			[0, 2, 1],
			[1, 2]]

	procg = [[3, 2, 2],
			[2, 1, 4],
			[4, 3]]

	print("BIDIR")
	xB = BidirProblem(macg, procg, c=1)
	xB.bidir()
	xT = TabuProblem(macg, procg, xB.E2)

	
	print("cost found:", xB.get_cost())
	print("feasibilty passed:", xB.is_feasible())
	print("STARTING TABU SEARCH")
	xT.TB()
	
	print("cost found:", xT.get_cost())
	print("actual cost:", xT.get_makespan())
	print("feasibilty passed:", xT.is_feasible())

