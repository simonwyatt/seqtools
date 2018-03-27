#!/usr/bin/env python3
# -*- coding: utf-8 -*-

##################################################################################
# seqtools Copyright (C) 2018 Simon Wyatt <simon.d.wyatt@gmail.com>              #
# This program is free software: you can redistribute it and/or modify it under  #
# the terms of the GNU General Public License as published by the Free Software  #
# Foundation, either version 3 of the License, or (at your option) any later     #
# version.                                                                       #
#                                                                                #
# This program is distributed in the hope that it will be useful, but WITHOUT    #
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS  #
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details. #
#                                                                                #
# You should have received a copy of the GNU General Public License along with   #
# this program. If not, see <http://www.gnu.org/licenses/>.                      #
##################################################################################

"""
This module provides sequence types implementing combinatoric operations over other sequences.

Combinatoric sequences versus combinatoric generators from `itertools`:
    + Are sequences, and support e.g. `len`, `in`, subscripts, and slicing.
    - Require sequence inputs (not merely iterables).

Combinatoric sequences versus constructing a tuple from an `itertools` generator:
    + Evaluate lazily, avoiding explicitly storing each element.
    - Lazy evaluation is by reference to the original inputs, so providing mutable inputs
      and then mutating them may result in undefined behavior.

Classes:
    Product: Cartesian product of sequences.
"""

import itertools, functools, operator
from functools import reduce

from reversed import Reversed, SeqReversible
from seqslice import SeqSlice

class Product(SeqReversible):
    """
    Precondition : `sequences` is an immutable sequence of immutable sequences.
    Postcondition: `Product(*sequences)` is the sequence consisting of the Cartesian product of the sequences from `sequences`,
    produced in the lexicographic order derived from the orderings of each input sequence.
    (i.e., if given the sequence "ACB" as input, the output orders "C" before "B".)
    `Product(*sequences, repeat=n)` is the nth Cartesian power of `Product(*sequences)`.
    
    Standard warning about combinatoric sequences: Providing mutable inputs and then mutating them may result in undefined behavior.
    
    Examples:
        >>> list(Product((0,1), repeat=3))
        [(0, 0, 0), (0, 0, 1), (0, 1, 0), (0, 1, 1), (1, 0, 0), (1, 0, 1), (1, 1, 0), (1, 1, 1)]
    
        >>> all(x==y for x, y in zip(Product((0,1), repeat=3), itertools.product((0,1), repeat=3)))
        True
    
        >>> list(Product((0,), (1,), (2,)))
        [(0, 1, 2)]
    
        >>> list(Product())
        [()]
    """
    
    """
    Abstraction function: the tuple (s1, ..., sn) represents the Cartesian product of the sequences s1, ..., sn.
    Representation invariant: The sequences s1, ..., sn are immutable.
    """
    def __init__(self, *sequences, repeat=1):
        self._sequences = sequences * repeat
    
    def len(self):
        """Compute length, avoiding CPython's implementation constraint that the return value of `__len__` may not exceed `sys.maxsize`."""
        """
        >>> Product((0,1), repeat=3).len()
        8
        
        >>> Product().len()
        1
        
        >>> Product(range(2), range(3), range(3), range(7), range(11), range(31), range(151), range(331)).len()
        2147483646
        
        >>> Product(range(1000000), repeat=10).len()
        1000000000000000000000000000000000000000000000000000000000000
        """
        return functools.reduce(operator.mul, (len(s) for s in self._sequences), 1)
        # Correctness argument: This is the well-known formula for the cardinality of the Cartesian product of finite sets.
        # (Recall that the empty Cartesian product is {()}, the set whose sole element is the empty tuple.)
        
    
    def __len__(self):
        return self.len()
    
    def __contains__(self, item):
        """Return `item in self`.
        True iff each element of `item` is in the corresponding input to `self`.
        False iff `item` has a plausible type to belong to `self` but doesn't; `TypeError` is not caught.
        
        Examples:
            >>> (1, 'A') in Product((0,1), "AB")
            True
        
            >>> (0, 'C') in Product((0,1), "AB")
            False
        
            >>> (1, 1) in Product((0,1), "AB")
            Traceback (most recent call last):
              ...
            TypeError: 'in <string>' requires string as left operand, not int
        
            >>> 1 in Product((0,1), repeat=3)
            Traceback (most recent call last):
              ...
            TypeError: 'int' object is not subscriptable
        """
        return all(item[i] in s for i,s in enumerate(self._sequences))
        # Correctness argument: This is the definition of the Cartesian product.
        
        # THIS METHOD NEEDS TO BE RETHOUGHT.
        # `(1, 0) in Product((0,1), "AB")` raises TypeError:
        #   first we see that `1 in (0,1)`, so then we check `0 in "AB"` and raise TypeError.
        # BUT
        # `(2, 0) in Product((0,1), "AB")` returns False:
        #   because `2 in (0, 1)` is False, evaluation of `all` short-circuits.
        # PROPOSAL: only raise TypeError in a case like `1 in Product((0,1), repeat=3)` where the given item is not even a tuple.
        # if not isinstance(item, tuple):
        #   raise TypeError("'in <{}>' requires tuple as left operand, not {}".format(type(self), type(item)))
        # otherwise catch TypeErrors where an element of `item` is incompatible with the corresponding factor and return False
    
    def _multi_index(self, i):
        """
        Compute indices into each factor corresponding to index in product.
        
        Precondition : `i` is an integer.
        Postcondition: Let `self` be the product `Product(s[0], ..., s[n-1])` of `n` sequences.
        Then `self._multi_index(i)` is the tuple `(i[0], ..., i[n-1])` with the property that
        `(s[0][i[0]], ..., s[n-1][i[n-1]]) = self[i % len(self)]`.
        """
        indices = ()
        for s in self._sequences[::-1]:
            i, j = divmod(i, len(s))
            indices = (j,) + indices
        return indices
        # Correctness argument:
        # PENDING. Inductive. On number of factors? On i?
        
    def _elem_at(self, indices):
        """
        Get one element from each factor using tuple of indices.
        
        Precondition : `indices` is a sequence `(i[0], ..., i[n-1])` of `n` integers,
            where `self` is the product `Product(s[0], ..., s[n-1])` of `n` sequences.
        Postcondition: `self._elem_at(indices)` is the tuple `(s[0][i[0]], ..., s[n-1][i[n-1]])`.
        """
        return tuple(s[indices[i]] for i, s in enumerate(self._sequences))
        # Correctness argument: (s[indices[i]] for i, s in enumerate(self._sequences))
        # is equivalent to (self._sequences[i][indices[i]] for i in range(len(self._sequences))),
        # which is a generator expression for the sequence of values required by the postcondition.
    
    def __getitem__(self, index):
        """
        
        """
        if isinstance(index, slice):
            return _ProductSlice(self, index)
            # TODO: detect when step size divides length of last factor and return product object over smaller factor
            # if len(self._sequences[-1]) % index.step == 0: ...
            # & similar cases.
        else:
            L = self.len()
            if not (-L <= index < L):
                raise IndexError("Product index out of range")
                #if we didn't do this explicitly, the following would return `self[index % L]`
            #else
            return self._elem_at(self._multi_index(index))
        # Correctness argument: PENDING
    
    def __iter__(self):
        return itertools.product(*self._sequences) #CPython implements this in C
        # Alternatively:
        # return iter(self[::])
    
    def __reversed__(self):
        return iter(self[::-1])
    def _seqtools_reversed(self):
        return Product(*(Reversed(s) for s in self._sequences))
    
    def __repr__(self):
        return type(self).__name__ + "(" + ", ".join(repr(s) for s in self._sequences) + ")"
    
    def __eq__(self, other):
        if isinstance(other, Product):
            return self._sequences == other._sequences
        else:
            return NotImplemented
    
    #TODO: index, count

class _ProductSlice(SeqSlice):
    def __iter__(self):
        if self._seq._sequences == (): #Special case for product of empty sequence of sequences.
            yield ()
            return
    
        ###############################
        # Initialize generator state: #
        ###############################
        
        start, stop, step = self._slice.start, self._slice.stop, self._slice.step
        
        # Initialize step: Normalize by rejecting zero and defaulting None -> 1
        if step == 0:
            raise ValueError("slice step cannot be zero")
        if step is None:
            step = 1

        # Initialize start: Normalize by clipping to bounds, handling None
        L = self._baselen() # Precompute base length for repeated reuse
        if start is None:
            start = 0 if step>0 else -1
        else:
            if ((start >= L and step > 0)
            or  (start < -L and step < 0)):
                # Start too late to capture any items.
                return
            elif start >= L and step < 0:
                # Clip to back.
                start = L - 1
            elif start < -L and step > 0:
                # Clip to front
                start = -L
        
        # Initialize stop: None is okay, handled explicitly by generator. Convert to multi-index.
        if stop is not None:
            stop = list(self._seq._multi_index(stop)) # We won't mutate `stop`, but it has to be comparable to the mutable `indices`.
            
        ###################
        # Generate items. #
        ###################
        
        indices = list( self._seq._multi_index(start) )
        item = list(self._seq._elem_at(indices))
        yield tuple(item) #The first one.
        while stop is None or (step > 0 and indices < stop) or (step < 0 and stop < indices): # If stop is None we'll explicitly break when done.
            indices[-1] += step
            pos = len(self._seq._sequences) - 1
            # Propagate carries back through multi-index, updating item as we go.
            # We only update the entries of the item that need updating, instead of regenerating the entire item tuple when any part of the index changes,
            # which is our principal efficiency gain over iteration by direct access to a range of individual elements.
            while pos > 0 and not (0 <= indices[pos] < len(self._seq._sequences[pos])):
                q, indices[pos] = divmod(indices[pos], len(self._seq._sequences[pos]))
                indices[pos - 1] += q
                item[pos] = self._seq._sequences[pos][indices[pos]]
                pos -= 1
            if pos == 0 and not (0 <= indices[pos] < len(self._seq._sequences[pos])): #Ran off end of product.
                break # Here's the explicit break for if stop was None.
            # else
            item[pos] = self._seq._sequences[pos][indices[pos]] # One more time for last carry.
            yield tuple(item)
        
        # Correctness argument:
        # PENDING. Most complex and most important method for products, will have most complex & important proof.
        # CURRENTLY KNOWN BUGGY. stop element is included!
        #   believed to be off by one error in the loop

if __name__ == "__main__":
    import doctest
    doctest.testmod()