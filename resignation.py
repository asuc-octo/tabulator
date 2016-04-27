### In case of resignation

class PositionRankings:

	def __init__(self, rankings):
		"""
		:rankings: a list of rankings for a particular ASUC position
		"""

		self.immutable_rankings = rankings
		self.mutable_rankings = rankings

	def pop(self, index=0):
		return self.mutable_rankings.pop(index)

	def __len__(self):
		return len(self.mutable_rankings)

