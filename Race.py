#############################################################
#							Race.py 						#
#			  Created by: Alton Zheng & Yun Park			#
#			   Copyright Elections Council 2013				#
#############################################################

from constants import *
from random import shuffle
import math
import time
import sys
import csv
from resignation import PositionRankings

class Race:
# A race refers to an election for one particular position
	def __init__(self, election, position, candidates, ballots):
		self.election = election
		self.position = position
		self.candidates = candidates
		self.ballots = ballots
		self.validVotes = 0
		self.winners = 0
		self.spentBallots = 0
		self.iterationNumber = 0
		self.positions = ['President', 'Executive VP', 'External Affairs VP', 'Academic Affairs VP', 'Student Advocate', 'Senator']

		self.finished = False
		self.current_ballots = ballots
		self.redistribute_ballots = []
		self.numValidVotes = self.countValidVotes(ballots)
		if position != SENATOR:
			self.quota = round((self.numValidVotes + 1)/2.0)
		else:
			self.quota = round(float(self.numValidVotes)/(NUM_SENATORS+1) + 1)
		self.winner = []

		# For senators
		self.current_winners = []
		self.current_runners = candidates[:]

		# (HACK) Can't hash candidates, so temporarily use their candidate number as a key
		self.numToCandidate = {candidate.number: candidate for candidate in candidates}


	def applyBallot(self, ballot):
		"""Increment a candidates score, and pop his number off the vote"""
		if self.position not in ballot.votes.keys():
			raise ElectionError("Position not found in ballot!")
		vote = ballot.votes[self.position]

		while True:
			if not vote:
				self.spentBallots += ballot.value
				return False
			candidate_num = int(vote.pop(0))
			if candidate_num not in self.numToCandidate.keys():
				raise ElectionError("Candidate " + str(candidate_num) + " not found!")
			if self.numToCandidate[candidate_num].state == RUNNING:
				break

		candidate = self.numToCandidate[candidate_num]
		candidate.score += ballot.value
		candidate.ballots.append(ballot)
		ballot.candidate = candidate
		return True

	def countValidVotes(self, ballots):
		count = 0
		for ballot in ballots:
			if self.position not in ballot.votes.keys():
				raise ElectionError("Position not found in ballot!")
			vote = ballot.votes[self.position]
			if vote:
				count += 1
		return count

	def initializeFirstVotes(self, ballot):
		if self.applyBallot(ballot):
			self.validVotes += 1

	def numOfRunners(self):
		"""Return the number of candidates still running"""
		count = 0
		for candidate in self.candidates:
			if candidate.state == RUNNING:
				count += 1
		return count

	def runStepExecutives(self):
		if self.finished:
			return FINISHED
		if self.current_ballots:
			ballot = self.current_ballots.pop(0)
			if ballot.candidate and ballot.candidate.state == LOSE:
				ballot.candidate.score -= ballot.value
			self.applyBallot(ballot)
			return CONTINUE
		elif self.numOfRunners() == 1:
			for candidate in self.candidates:
				if candidate.state == RUNNING:
					candidate.state = WIN
					candidate.score = self.quota
					self.finished = True
					self.winner.append(candidate)
					self.outputVotes()
					return FINISHED
		for candidate in self.candidates:
			if candidate.score >= self.quota:
				candidate.state = WIN
				candidate.score = self.quota
				self.finished = True
				self.winner.append(candidate)
				self.outputVotes()
				return FINISHED
		self.candidates.sort(key=lambda x: -1 * x.score)
		worst_score = sys.maxint
		for candidate in reversed(self.candidates):
			if candidate.state == RUNNING and candidate.score <= worst_score:
				self.current_ballots += candidate.ballots
				candidate.state = LOSE
				worst_score = candidate.score
		return STOP

	def runStepSenator(self):
		if self.finished:
			return FINISHED
		if self.current_ballots:
			self.applyCurrentBallot()
			return CONTINUE
		if (len(self.current_winners) + len(self.current_runners)) <= NUM_SENATORS:
			self.current_runners.sort(key=lambda x: -1 * x.score)
			if self.current_runners[0].score >= self.quota:
				candidate = self.current_runners.pop(0)
				self.makeCandidateWin(candidate)
				return CONTINUE
			self.winner = self.current_winners + self.current_runners
			self.finished = True
			return FINISHED
		if len(self.current_winners) == NUM_SENATORS:
			self.winner = self.current_winners
			self.finished = True
			self.outputVotes()
			return FINISHED

		self.current_runners.sort(key=lambda x: x.score)
		top_candidate = self.current_runners[-1]
		top_score = top_candidate.score

		if top_score >= self.quota:
			self.current_runners.sort(key=lambda x: -1 * x.score)
			while self.current_runners[0].score >= self.quota and len(self.current_winners) < NUM_SENATORS:
				candidate = self.current_runners.pop(0)
				self.makeCandidateWin(candidate)
			return CONTINUE
		else:
			last_candidate = self.current_runners.pop(0)
			self.current_ballots += last_candidate.ballots
			last_candidate.state = LOSE
			# Take out all tied candidates
			while True:
				if self.current_runners[0].score == last_candidate.score:
					curr_candidate = self.current_runners.pop(0)
					self.current_ballots += curr_candidate.ballots
					curr_candidate.state = LOSE
				else:
					break
			shuffle(self.current_ballots)
			self.outputVotes()
			return STOP

	def outputVotes(self):
		try:
			in_file = open("vote_printouts.csv", 'rb')
			reader = csv.reader(in_file)
		except IOError:
			reader = None
		rows_to_write = []
		
		written = False
		wroteMoreParts = False
		i = 0
		if reader:
			for row in reader:
				# if not row:
				# 	rows_to_write.append([])
				# 	continue
				if row[0] == self.positions[self.position - 1]:
					row += ["count " + str(len(row))]
					written = True
					rows_to_write.append(row)
					wroteMoreParts = True
					continue
				if row[0] in self.positions and row[0] != self.positions[self.position - 1]:
					written = False
				if written:
					# relying on the fact that they should be in the same order
					row += [self.candidates[i].score]
					i += 1
					if (i == len(self.candidates)):
						written = False
				rows_to_write.append(row)
			in_file.close()
		if not written and not wroteMoreParts:
			print(self.positions[self.position - 1])
			rows_to_write.append([' '])
			row_head = [self.positions[self.position - 1], "count 1"]
			rows_to_write.append(row_head)
			for cand in self.candidates:
				row_temp = [cand.name, cand.score]
				rows_to_write.append(row_temp)

		out_file = open("vote_printouts.csv", "wb")
		writer = csv.writer(out_file)
		for row in rows_to_write:
			writer.writerow(row)
		out_file.close()

	def makeCandidateWin(self, candidate):
		candidate.state = WIN
		self.current_winners.append(candidate)
		for ballot in candidate.ballots:
			ballot.value = ballot.value * float(candidate.score - self.quota)/candidate.score
			self.current_ballots.append(ballot)
		candidate.score = self.quota
		candidate.quotaPlace = NUM_SENATORS - len(self.current_winners) + 1

	def applyCurrentBallot(self):
		ballot = self.current_ballots.pop(0)
		if ballot.candidate and ballot.candidate.state == LOSE:
			ballot.candidate.score -= ballot.value
		self.applyBallot(ballot)

class ElectionError(Exception):

	def __init__(self, message):
		self.message = message

	def __str__(self):
		return repr(self.message)

class BallotError(ElectionError):
	pass

class Ballot:

	def __init__(self, votes):
		# Votes is a dictionary matching position to an array of candidate numbers.
		# The position of the candidate number in the array refers to rank of the vote.

		# Check that all keys are valid
		for position in votes.keys():
			if position not in POSITIONS:
				raise BallotError("Position " + str(position) + " not found!");

		# Create keys if they no votes were assigned to that position
		for position in POSITIONS:
			if position not in votes.keys():
				votes[position] = []

		self.candidate = None

		position_ranking_vote_dict = {}
		for asuc_position, ranking_list in votes.iteritems():
			position_ranking_vote_dict[asuc_position] = PositionRankings(ranking_list)

		self.votes = position_ranking_vote_dict
		self.value = 1

	def setValue(self, val):
		self.value = val

	def __str__(self):
		return str(self.votes)


