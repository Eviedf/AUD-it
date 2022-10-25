"""
author: Natalia Mordvanyuk
email: natalia.mordvanyuk@udg.edu
created 15/08/2019
updated 18/03/2020

This file form part of the implementation of the vertTIRP algorithm described in the article:

Natalia Mordvanyuk, Beatriz López, Albert Bifet,
vertTIRP: Robust and efficient vertical frequent time interval-related pattern mining,
Expert Systems with Applications,
Volume 168,
2021,
114276,
ISSN 0957-4174,
https://doi.org/10.1016/j.eswa.2020.114276.
(https://www.sciencedirect.com/science/article/pii/S0957417420309842)
Abstract: Time-interval-related pattern (TIRP) mining algorithms find patterns such as “A starts B” or “A overlaps B”. The discovery of TIRPs is computationally highly demanding. In this work, we introduce a new efficient algorithm for mining TIRPs, called vertTIRP which combines an efficient representation of these patterns, using their temporal transitivity properties to manage them, with a pairing strategy that sorts the temporal relations to be tested, in order to speed up the mining process. Moreover, this work presents a robust definition of the temporal relations that eliminates the ambiguities with other relations when taking into account the uncertainty in the start and end time of the events (epsilon-based approach), and includes two constraints that enable the user to better express the types of TIRPs to be learnt. An experimental evaluation of the method was performed with both synthetic and real datasets, and the results show that vertTIRP requires significantly less computation time than other state-of-the-art algorithms, and is an effective approach.
Keywords: Time Interval Related Patterns; Temporal data mining; Sequential pattern mining; Temporal relations
"""

# This file contains classes that allows insert into a linked list
# time intervals following the sorting criteria as defined in vertTIRP algorithm
# and taking into account that we are inserting into a sorted list
# values in a sorted fashion
import pandas as pd


class TI:
    # Constructor to initialize the TI object
    def __init__(self, sym="", start=None, end=None):
        self.sym = sym
        self.start = start
        self.end = end

    def __str__(self):
        return self.sym +" "+ str(self.start) +" "+ str(self.end)

    def __eq__(self, node):
        if self.sym != node.sym:
            return False
        else:
            if self.start != node.start:
                return False
            else:
                return self.end == node.end

    def __lt__(self, node):
        if self.start < node.start:
            return True
        else:
            if self.start == node.start:
                if self.end < node.end:
                    return True
                else:
                    if self.end == node.end:
                        return self.sym < node.sym
                    else:  # self.ti.end > node.ti.end
                        return False
            else:  # self.ti.start > node.ti.start:
                return False


class TI_node:
    # Constructor to initialize the TI_node object
    def __init__(self, sym="", start=None, end=None):
        self.ti = TI(sym, start, end)
        self.next = None
        self.ant = None

    def __str__(self):
        return "{sym: "+str(self.ti.sym)+", start: "+str(self.ti.start)+", end: "+str(self.ti.end)+"}"

    def __lt__(self, node):
        if self.ti.start < node.ti.start:
            return True
        else:
            if self.ti.start == node.ti.start:
                if self.ti.end < node.ti.end:
                    return True
                else:
                    if self.ti.end == node.ti.end:
                        return self.ti.sym < node.ti.sym
                    else:  # self.ti.end > node.ti.end
                        return False
            else:  # self.ti.start > node.ti.start:
                return False


class LinkedList:

    def __init__(self):
        self.first = None
        self.last = None
        self.size = 0

    def __iter__(self):
        # attr for the iterator
        self.current = self.first
        while self.current:
            yield self.current
            self.current = self.current.next

    def empty(self):
        return self.size == 0

    def setEnd(self, node, new_end):
        # to not iterate prev_node is the node before node
        # new end will always be greater that previous one
        if (node.next is None) or (new_end < node.next.ti.end):
            node.ti.end = new_end
        else:
            # 1 - delete pointers of node from the structure
            if node.ant is not None:  # node was not the first element

                node.ant.next = node.next
                node.next.ant = node.ant
                node.ti.end = new_end
                present = node.ant
            else:
                # node was the first element
                node.next.ant = None
                self.first = node.next
                node.ti.end = new_end
                present = self.first

            # 2 - find out the node before the point of insertion
            while (present.next is not None) and (present.next < node):
                present = present.next

            # 3 - insert the node before the point of insertion
            node.next = present.next
            if node.next is None:  # if last is the last element the correct pointer
                self.last = node
            else:
                present.next.ant = node

            present.next = node
            node.ant = present

    def insert(self, new_node):
        # insert a new_node after the last inserted

        # Special case for the empty linked list
        if self.first is None:
            self.first = new_node
            self.last = new_node
            # no necessari
            new_node.next = None
            new_node.ant = None
        else:
            # new node will be added at the end
            self.last.next = new_node  # previous last points to new last
            new_node.ant = self.last   # new last prev points to the last
            self.last = new_node  # last pointers points to the new last
        self.size += 1

    def sortedInsert(self, new_node, last_inserted=None):
        # last_inserted: where the search begins, in case of sorted list
        # Special case for the empty linked list
        if self.first is None:
            self.first = new_node
            self.last = new_node
            # no necessari
            new_node.next = None
            new_node.ant = None

        #  Special case for the first item at the end
        elif new_node < self.first:
            new_node.next = self.first  # new_node --> self.first
            self.first.ant = new_node  # new_node <-- self.first
            self.first = new_node  # new_node (first)

        else:
            # from which point begin to search
            if last_inserted and (last_inserted.ant is not None):
                present = last_inserted.ant
            else:
                present = self.first

            # find out the node before the point of insertion
            while (present.next is not None) and (present.next < new_node):
                present = present.next

            new_node.next = present.next
            if new_node.next is None:  # if last is the last element the correct pointer
                self.last = new_node
            else:
                present.next.ant = new_node

            present.next = new_node
            new_node.ant = present

        self.size += 1

    def concatenate(self, anotherList):
        self.last.next = anotherList.first
        anotherList.first.ant = self.last
        self.last = anotherList.last
        self.size += anotherList.size

    def getAll(self):
        start_vector = []
        end_vector = []
        sym_vector = []
        temp = self.first
        while temp:
            # print(temp.sym)
            start_vector.append(temp.ti.start)
            end_vector.append(temp.ti.end)
            sym_vector.append(temp.ti.sym)
            temp = temp.next
        return start_vector, end_vector, sym_vector

    def printList(self, out_file=None, mode='a', user=""):
        if out_file is None:
            temp = self.first
            while temp:
                print(user+" sym: " +str(temp.ti.sym)+" start: " +str(temp.ti.start)+" end: " +str(temp.ti.end))
                temp = temp.next
        else:
            with open(out_file, mode) as o_file:
                temp = self.first
                while temp:
                    o_file.write(user + ";" + str(temp.ti.sym) + ";" + str(temp.ti.start) + ";" + str(temp.ti.end) + "\n")
                    temp = temp.next
