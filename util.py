def cumsum(l):
	return [sum(l[:i+1]) for i in range(len(l))]


def unfold(d):
	r = []
	for i in d.items():
		for j in i[1]:
			r.append((i[0], j))
	return r


def flatten(l):
	return (y for x in l for y in x)


class GGraph:
	""" graphviz graph renderer """
	def __init__(self, name):
		import graphviz as gv
		self._g = gv.Digraph(format='svg')
		self.name = name
		self.weights = None

	def add_weights(self, weights):
		self.weights = weights

	def get_weight(self, node):
		if node < 0 or node >= len(self.weights):
			return 0
		return self.weights[node]

	def add_nodes(self, nodes):
		for n in nodes:
			self._g.node(str(n))

	def add_edges(self,edges, color):
		if self.weights:
			for e in edges:
				self._g.edge(*[str(x) for x in e], color=color, label=str(self.get_weight(e[0])))
		else:
			for e in edges:
				self._g.edge(*[str(x) for x in e], color=color)

	def render(self):
		self._g.render(filename=self.name, view=True)