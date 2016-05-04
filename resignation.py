### In case of resignation

class PositionRankings:

	def __init__(self, rankings):
		"""
		:rankings: a list of rankings for a particular ASUC position
		"""

		self.immutable_rankings = list(rankings)
		self.mutable_rankings = list(rankings)

	def popNew(self, index=0):
		return self.mutable_rankings.pop(index)

	def __len__(self):
		return len(self.mutable_rankings)

	def __repr__(self):
		return repr(self.immutable_rankings)

	def __str__(self):
		return str(self.immutable_rankings)

	def get_immutable_rankings(self):
		return self.immutable_rankings

	def reset_ranking(self):
		self.mutable_rankings = list(self.immutable_rankings)


