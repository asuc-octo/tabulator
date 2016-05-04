#############################################################
#                       Tabulator.py                        #
#             Created by: Alton Zheng & Yun Park            #
#                   Edited by; Lisa Lee                     #
#              Copyright Elections Council 2014             #
#############################################################

import json
import csv
import copy
from pprint import pprint
from Race import *


class Candidate:

    def __init__(self, number, name, position, party):
        self.number = number
        self.name = name
        self.position = position
        self.party = party
        self.score = 0
        self.ballots = []
        self.state = RUNNING
        self.quotaPlace = 0 # Maintains the order of candidates to quota'd

    def __eq__(self, other):
        return (other.number == self.number) and (other.name == self.name) and (other.position == self.position) and (other.party == self.party)

    def __str__(self):
        return str(self.number) + ". " + self.name + " " + str(self.position) + " " + self.party + " SCORE: " + str(self.score) + " STATE: " + STATES[self.state]

    def __hash__(self):
        return self.number

    def getName(self):
        return self.name

class Election:

    def __init__(self, frame):
        # self.ballots is an array of Ballot objects
        self.ballots = []

        # self.candidates is a dictionary mapping positions to an array of Candidate objects
        self.candidates = {}

        # self.frame is the GUI frame that's displaying the election
        self.frame = frame

        self.race = None

    def loadBallotsFromJSONFile(self, filepath):
        self.ballots = []
        with open(filepath) as data_file:
            data = json.load(data_file) 
        for json_ballot in data["ballots"]:
            # Create a new dictionary that has keys as integers instead of strings
            votes = {}
            for key in json_ballot.keys():
                try:
                    votes[int(key)] = json_ballot[key]
                except ValueError:
                    print('Invalid key in json: ' + key)

            ballot = Ballot(votes)
            self.ballots.append(ballot)

    # Same as loadBallotsFromJSONFile, except reading from CSV 
    def loadBallotsFromCSVFile(self, filepath):
        self.ballots = []
        with open(filepath) as csv_data:
            data = csv.reader(csv_data)
            rownum = 0
            for row in data:
                votes = {}
                # Skip through two empty rows on top and save header row.
                if rownum <= 2:
                    header = row
                    rownum += 1
                    continue
                else:
                    colnum = 0
                    for col in row:
                        # print '%-8s: %s' % (header[colnum], col)
                        # Look for the position asked in the question
                        position = self.findPositionValue(header[colnum])
                        if position not in range(1, 7):
                            colnum += 1
                            continue
                        # Find the candidates number based on the answer
                        # Returns None if candidate not found
                        number = self.findCandidateNumber(position, col.split('|', 1)[0][:-1])
                        # print number
                        if number == None:
                            colnum += 1
                            continue
                        # Include candidate in vote
                        if position not in votes.keys():
                            votes[position] = [number]
                        else:
                            votes[position].append(number)
                        colnum += 1

                # Create a new ballot with the votes and add it to overall ballots
                ballot = Ballot(votes)
                self.ballots.append(ballot)
                rownum += 1

    def findCandidateNumber(self, position, name):
        candidateList = self.candidates[position]
        # Remove all characters that aren't letters, numbers, '', -, !
        newName = ''
        for c in name:
            if (c >= 'A' and c <= 'Z') or (c >= 'a' and c <= 'z') or (c >= '0' and c <= '9') or c == '-' or c == '"' or c == ' ':
                newName += c
        for c in candidateList:
            if c.getName() == newName:
                return c.number
        return None

    def loadCandidatesFromJSONFile(self, filepath):
        with open(filepath) as data_file:
            data = json.load(data_file)
        self.candidates[SENATOR] = []
        for candidate in data["senator"]:
            self.__addJSONCandidate__(candidate, SENATOR)
        self.candidates[PRESIDENT] = []
        for candidate in data["president"]:
            self.__addJSONCandidate__(candidate, PRESIDENT)
        self.candidates[EXECUTIVE_VP] = []
        for candidate in data["executive_vp"]:
            self.__addJSONCandidate__(candidate, EXECUTIVE_VP)
        self.candidates[EXTERNAL_VP] = []
        for candidate in data["external_vp"]:
            self.__addJSONCandidate__(candidate, EXTERNAL_VP)
        self.candidates[ACADEMIC_VP] = []
        for candidate in data["academic_vp"]:
            self.__addJSONCandidate__(candidate, ACADEMIC_VP)
        self.candidates[STUDENT_ADVOCATE] = []
        for candidate in data["student_advocate"]:
            self.__addJSONCandidate__(candidate, STUDENT_ADVOCATE)

    # Reads candidate information from a textfile, assuming the format of
    # Position:
    # candidate name | candidate party
    def loadCandidatesFromTextFile(self, filepath):
        data = open(filepath)
        line = data.readline()
        number = 1
        oldPosition = 0
        while not line == '':
            position = self.findPositionValue(line.split(':')[0])
            # If position is invalid, it means it read in a name
            # print position
            if position == 0:
                name = line.split('|', 1)[0][:-1]
                party = line.split('|', 2)[1][1:-1]
                c = Candidate(number, name, oldPosition, party)
                if oldPosition not in self.candidates.keys():
                    self.candidates[oldPosition] = [c]
                else:
                    self.candidates[oldPosition].append(c)
                number += 1
            else:
                oldPosition = position
            line = data.readline()

    # Returns position value or 0 if invalid position
    def findPositionValue(self, position):
        if "Executive Vice President" in position:
            return EXECUTIVE_VP
        elif "External Affairs Vice President" in position:
            return EXTERNAL_VP
        elif "Academic Affairs Vice President" in position:
            return ACADEMIC_VP
        elif "President" in position:
            return PRESIDENT
        elif "Student Advocate" in position:
            return STUDENT_ADVOCATE
        elif "Senate" in position:
            return SENATOR
        else:
            return 0

    def __addJSONCandidate__(self, candidate, position):
        self.candidates[position].append(Candidate(int(candidate["number"]), candidate["name"], position, candidate["party"]))

    # Used for debugging
    def displayCandidates(self):
        for position in self.candidates:
            print(position)
            print("-------------------------------------------------")
            candidates = self.candidates[position]
            for candidate in candidates:
                print(candidate)
            print("")

    # Used for debugging
    def finishRace(self):
        if self.race:
            status = CONTINUE
            while status != FINISHED:
                status = self.stepFunction()
                if status == STOP:
                    self.race.candidates.sort(key=lambda x: -1 * x.score)
                    for cand in self.race.candidates:
                        print(cand)
                    raw_input()
                pass

    def iterateRace(self):
        if self.race:
            return self.stepFunction()

    def resetRace(self):
        if self.race:
            for candidate in self.race.candidates:
                candidate.score = 0
                candidate.ballots = []
                candidate.state = RUNNING
                candidate.quotaPlace = 0
        self.race = None

    def startRace(self, position):
        candidates = self.candidates[position]
        if not self.ballots: raise ElectionError("No ballots have been entered.")
        ballot_copy = copy.deepcopy(self.ballots)
        self.race = Race(self, position, candidates, ballot_copy, tabulator=self, num_sen=NUM_SENATORS)
        if (position != SENATOR):
            self.stepFunction = self.race.runStepExecutives
        else:
            self.stepFunction = self.race.runStepSenator
        return self.race.quota

    def startResignationRace(self, originalRace, resignee_ballots):
        print "Starting second race"
        candidates = self.candidates[SENATOR]
        original_winners = originalRace.winner

        original_losers = []
        for candidate in candidates:
            if candidate not in original_winners:
                original_losers.append(candidate)

        print "ORIGINAL LOSERS: " + repr([loser.name for loser in original_losers])
        print "ORIGINAL WINNERS: " + repr([winner.name for winner in original_winners])

        self.resetRace()
        if not self.ballots: raise ElectionError("No ballots have been entered.")
        print "Copying ballot for the resignation election"
        
        ballot_copy = copy.deepcopy(resignee_ballots)

        for ballot in ballot_copy:
            ballot.reset_rankings()

        self.race = Race(self, SENATOR, original_losers, ballot_copy, num_sen=1)
        self.stepFunction = self.race.runStepSenator
        
        value = -1
        while value != FINISHED:
            value = self.race.runStepSenator()
        
        print "Completed resignation election"
        return self.race.quota
