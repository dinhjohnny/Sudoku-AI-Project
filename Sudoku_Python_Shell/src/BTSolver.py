# Authors:  Johnny Dinh and David Liu

from cgitb import small
import SudokuBoard
import Variable
from Variable import Variable
import Domain
import Trail
import Constraint
import ConstraintNetwork
import time
import random
from collections import defaultdict
from operator import attrgetter

class BTSolver:

    # ==================================================================
    # Constructors
    # ==================================================================

    def __init__ ( self, gb, trail, val_sh, var_sh, cc ):
        self.network = ConstraintNetwork.ConstraintNetwork(gb)
        self.hassolution = False
        self.gameboard = gb
        self.trail = trail

        self.varHeuristics = var_sh
        self.valHeuristics = val_sh
        self.cChecks = cc

    # ==================================================================
    # Consistency Checks
    # ==================================================================

    # Basic consistency check, no propagation done
    def assignmentsCheck ( self ):
        for c in self.network.getConstraints():
            if not c.isConsistent():
                return False
        return True

    """
        Part 1 TODO: Implement the Forward Checking Heuristic

        This function will do both Constraint Propagation and check
        the consistency of the network

        (1) If a variable is assigned then eliminate that value from
            the square's neighbors.

        Note: remember to trail.push variables before you assign them
        Return: a tuple of a dictionary and a bool. The dictionary contains all MODIFIED variables, mapped to their MODIFIED domain.
                The bool is true if assignment is consistent, false otherwise.
    """
    def forwardChecking ( self ):
        self.trail.placeTrailMarker()
        mod_var = {}

        assignedVars = []

        for c in self.network.constraints:
            for var in c.vars:
                if var.isAssigned():
                    assignedVars.append(var)
        
        for var in assignedVars:
            for neighbor in self.network.getNeighborsOfVariable(var):
                if neighbor.isChangeable() and not neighbor.isAssigned() and neighbor.getDomain().contains(var.getAssignment()):
                    self.trail.push(neighbor)
                    neighbor.removeValueFromDomain(var.getAssignment())
                    if neighbor.domain.size() == 0:
                        self.trail.undo()
                        return (mod_var, False)
                    mod_var[neighbor] = neighbor.getDomain()
                    
        self.trail.trailMarker.pop()
        return (mod_var, True)
    # =================================================================
	# Arc Consistency
	# =================================================================
    def arcConsistency( self ):
        assignedVars = []
        for c in self.network.constraints:
            for v in c.vars:
                if v.isAssigned():
                    assignedVars.append(v)
        while len(assignedVars) != 0:
            av = assignedVars.pop(0)
            for neighbor in self.network.getNeighborsOfVariable(av):
                if neighbor.isChangeable and not neighbor.isAssigned() and neighbor.getDomain().contains(av.getAssignment()):
                    neighbor.removeValueFromDomain(av.getAssignment())
                    if neighbor.domain.size() == 1:
                        neighbor.assignValue(neighbor.domain.values[0])
                        assignedVars.append(neighbor)

    
    """
        Part 2 TODO: Implement both of Norvig's Heuristics

        This function will do both Constraint Propagation and check
        the consistency of the network

        (1) If a variable is assigned then eliminate that value from
            the square's neighbors.

        (2) If a constraint has only one possible place for a value
            then put the value there.

        Note: remember to trail.push variables before you assign them
        Return: a pair of a dictionary and a bool. The dictionary contains all variables 
		        that were ASSIGNED during the whole NorvigCheck propagation, and mapped to the values that they were assigned.
                The bool is true if assignment is consistent, false otherwise.
    """
    def norvigCheck ( self ):
        
        # reuse forward checking!!!

        # maybe make it so that if you only have 1 value left in your domain, assign it?
        # then maybe rerun the check?

        # remove all assigned ones first
        # clear the list of the assigned vars
        # the moment it finds a variable that isn't assigned with only 1 possible value, go back to take it out from the neighbor's domain
        # remove assigned from square neighbors
        assigned = {}
        if (self.forwardChecking()[1]):
            for c in self.network.constraints:
                for var in c.vars:
                    if not var.isAssigned() and var.domain.size() == 1:
                        assigned[var] = True
                        self.trail.push(var)
                        var.assignValue(var.domain.values[0])
                        if (not self.forwardChecking()[1]):
                            return (assigned, False)
                    else:
                        assigned[var] = False
    

        return (assigned, True)

    """
         Optional TODO: Implement your own advanced Constraint Propagation

         Completing the three tourn heuristic will automatically enter
         your program into a tournament.
     """
    def getTournCC ( self ):
        return False

    # ==================================================================
    # Variable Selectors
    # ==================================================================

    # Basic variable selector, returns first unassigned variable
    def getfirstUnassignedVariable ( self ):
        for v in self.network.variables:
            if not v.isAssigned():
                return v

        # Everything is assigned
        return None

    """
        Part 1 TODO: Implement the Minimum Remaining Value Heuristic

        Return: The unassigned variable with the smallest domain
    """
    def getMRV ( self ):
        unassignedVars = []

        for c in self.network.constraints:
            for v in c.vars:
                if not v.isAssigned():
                    unassignedVars.append(v)

        if len(unassignedVars) == 0:
            return None 

        sortedByDomainSize = sorted(unassignedVars, key = lambda x: x.size())
        
        return sortedByDomainSize[0]
       
    """
        Part 2 TODO: Implement the Minimum Remaining Value Heuristic
                       with Degree Heuristic as a Tie Breaker

        Return: The unassigned variable with the smallest domain and affecting the  most unassigned neighbors.
                If there are multiple variables that have the same smallest domain with the same number of unassigned neighbors, add them to the list of Variables.
                If there is only one variable, return the list of size 1 containing that variable.
    """
    def MRVwithTieBreaker ( self ):

        unassigned_vars = []
        size_db = {}
        for c in self.network.constraints:
            for v in c.vars:
                if not v.isAssigned():
                    size = v.size()
                    if size in size_db:
                        size_db[size].append(v)
                    else:
                        size_db[size] = [v]
                    unassigned_vars.append(v)
        if not size_db:
            return [None]
        smallest_size = min(size_db.keys())

        if len(size_db[smallest_size]) == 1:
            return size_db[smallest_size]
        else:
            # we need to check for most affect on unassigned neighbors
            # have another dict to keep track of affected?
            neigh_db = {}
            
            for var in size_db[smallest_size]:
                count = 0
                for neigh in self.network.getNeighborsOfVariable(var):
                    if not neigh.isAssigned():
                        count += 1
                if count in neigh_db:
                    neigh_db[count].append(var)
                else:
                    neigh_db[count] = [var]
        return neigh_db[max(neigh_db.keys())]

    """
         Optional TODO: Implement your own advanced Variable Heuristic

         Completing the three tourn heuristic will automatically enter
         your program into a tournament.
     """
    def getTournVar ( self ):
        return None

    # ==================================================================
    # Value Selectors
    # ==================================================================

    # Default Value Ordering
    def getValuesInOrder ( self, v ):
        values = v.domain.values
        return sorted( values )

    """
        Part 1 TODO: Implement the Least Constraining Value Heuristic

        The Least constraining value is the one that will knock the least
        values out of it's neighbors domain.

        Return: A list of v's domain sorted by the LCV heuristic
                The LCV is first and the MCV is last
    """
    def getValuesLCVOrder ( self, v ):
        d = {}
        v_domain = v.getDomain().values

        for var in v_domain:
            d[var] = 0

        for n in self.network.getNeighborsOfVariable(v):
            n_values = n.getDomain().values
            for test_val in n_values:
                if test_val in d:
                    d[test_val] += 1

        #sorted_list = sorted(d.items(), key = lambda x: x[1]); 
        
        sorted_var = [key for key, val in sorted(d.items(), key = lambda x: x[1])]  
        # -> list of variables
        # -> list of variable domains


        return sorted_var
    """
         Optional TODO: Implement your own advanced Value Heuristic

         Completing the three tourn heuristic will automatically enter
         your program into a tournament.
     """
    def getTournVal ( self, v ):
        return None

    # ==================================================================
    # Engine Functions
    # ==================================================================

    def solve ( self, time_left=600):
        if time_left <= 60:
            return -1

        start_time = time.time()
        if self.hassolution:
            return 0

        # Variable Selection
        v = self.selectNextVariable()

        # check if the assigment is complete
        if ( v == None ):
            # Success
            self.hassolution = True
            return 0

        # Attempt to assign a value
        for i in self.getNextValues( v ):

            # Store place in trail and push variable's state on trail
            self.trail.placeTrailMarker()
            self.trail.push( v )

            # Assign the value
            v.assignValue( i )

            # Propagate constraints, check consistency, recur
            if self.checkConsistency():
                elapsed_time = time.time() - start_time 
                new_start_time = time_left - elapsed_time
                if self.solve(time_left=new_start_time) == -1:
                    return -1
                
            # If this assignment succeeded, return
            if self.hassolution:
                return 0

            # Otherwise backtrack
            self.trail.undo()
        
        return 0

    def checkConsistency ( self ):
        if self.cChecks == "forwardChecking":
            return self.forwardChecking()[1]

        if self.cChecks == "norvigCheck":
            return self.norvigCheck()[1]

        if self.cChecks == "tournCC":
            return self.getTournCC()

        else:
            return self.assignmentsCheck()

    def selectNextVariable ( self ):
        if self.varHeuristics == "MinimumRemainingValue":
            return self.getMRV()

        if self.varHeuristics == "MRVwithTieBreaker":
            return self.MRVwithTieBreaker()[0]

        if self.varHeuristics == "tournVar":
            return self.getTournVar()

        else:
            return self.getfirstUnassignedVariable()

    def getNextValues ( self, v ):
        if self.valHeuristics == "LeastConstrainingValue":
            return self.getValuesLCVOrder( v )

        if self.valHeuristics == "tournVal":
            return self.getTournVal( v )

        else:
            return self.getValuesInOrder( v )

    def getSolution ( self ):
        return self.network.toSudokuBoard(self.gameboard.p, self.gameboard.q)
