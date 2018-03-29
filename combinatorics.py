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
    Precondition : `sequences` is a sequence of sequences.
    Postcondition: `Product(*sequences)` is the sequence consisting of the Cartesian product of the sequences from `sequences`,
    produced in the lexicographic order derived from the orderings of each input sequence. String elements of `sequences`
    are treated as sequences of individual characters.
    (i.e., if given the sequence "ACB" as input, the output orders "C" before "B".)
    If `n` is a nonnegative integer, `Product(*sequences, repeat=n)` is the nth Cartesian power of `Product(*sequences)`.
    
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
    
    # Abstraction function: the tuple (t[1], ..., t[n]) represents the Cartesian product of the sequences s[1], ..., s[n],
    #   where t[i] = { tuple(s[i]) if s[i] is a string,
    #                { s[i]        otherwise.
    # Representation invariant: None of the sequences t[1], ..., s[n] are strings.
    #   See the comment on the various search methods for further discussion of why this is important.
    
    ################
    # Construction #
    ################
    
    def __init__(self, *sequences, repeat=1):
        """
        Initialize a new Product instance.
        
        Any string elements of `sequences` are first converted to tuples.
        """
        self._sequences = tuple( (s if not isinstance(s, str) else tuple(s)) for s in sequences ) * repeat
        
    def _seqtools_reversed(self):
        return self[::-1]
        # Equivalently: The order on the product is reversed by distributing the reversal over the orders of the factors:
        # return Product(*(Reversed(s) for s in self._sequences))
        # But this potentially allocates len(self._sequences) `Reversed` instances, passing every subscript through as many
        # index-reversal mappings, whereas the `self[::-1]` implementation just allocates one slice instance, and passes
        # subscripts through just one (more complex) slice-index mapping.
    
    def __repr__(self):
        return type(self).__name__ + "(" + ", ".join(repr(s) for s in self._sequences) + ")"
    
    def __eq__(self, other):
        if isinstance(other, Product):
            return self._sequences == other._sequences
        else:
            return NotImplemented

    ##########
    # Length #
    ##########

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
    
    ###############
    # Item access #
    ###############
    
    def __getitem__(self, index):
        """
        Return `self[index]`.
        """
        # Correctness: By division into cases:
        if isinstance(index, slice):
            return _ProductSlice(self, index) # See correctness argument in slice class
            # Future: Consider algebraic optimizations:
            # detect when step size divides length of last factor and return product object over smaller factor
            # if len(self._sequences[-1]) % index.step == 0: ...
            # & similar cases.
        else:
            # Bounds check
            L = self.len()
            if not (-L <= index < L):
                raise IndexError("Product index out of range")
                #if we didn't do this explicitly, the following would return `self[index % L]`
            
            return self._elem_at(self._multi_index(index))
            # Correctness argument:
            # _multi_index is specified to return a tuple such that
            # the action specified by _elem_at returns the desired item.
    
    def _multi_index(self, i):
        """
        Compute indices into each factor corresponding to index in product.
        
        Precondition : `i` is an integer.
        Postcondition: Let `self` be the product `Product(s[0], ..., s[n-1])` of `n` sequences.
        Then `self._multi_index(i)` is the tuple `(i[0], ..., i[n-1])` with the property that
        `(s[0][i[0]], ..., s[n-1][i[n-1]]) = self[i % len(self)]`.
        """
        indices = ()
        for s in reversed(self._sequences):
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
    
    #############
    # Iteration #
    #############
    
    def __iter__(self):
        return itertools.product(*self._sequences) #CPython implements this in C
        # Equivalent to:
        # return iter(self[::])
    def __reversed__(self):
        return iter(self[::-1])
    
    ##########
    # Search #
    ##########
    
    # The correctness of the __contains__, index, and count methods, which each call
    # the corresponding methods of the factor sequences, depends on string factors
    # being represented by their conversions to tuples.
    # This is because these methods of strings search for substrings, not characters,
    # and raise ValueError when strings are searched for non-string elements.
    # so, e.g., if `P = Product('AB', 'AB', 'AB')` then we must represent this as
    # `Product(('A', 'B'), ('A', 'B'), ('A', 'B'))` to avoid erroneous results such as
    #   ('AB', 'A', 'B') in P     -> True
    #   P.index(('AB', 'A', 'B')) -> 1
    #   P.count(('AB', 'A', 'B')) -> 1
    # without a lot of special-case logic to account for string factors in each method
    # and handle possible ValueErrors.
    # Instead we consolidated all the special-case handling to __init__'s conversion
    # of string factors to tuples.
    
    def __contains__(self, item):
        """Return `item in self`.
        
        Raises TypeError if `item` is not a tuple. Otherwise, returns True if each element of `item`
        is in the corresponding input to `self`, False otherwise.
        
        Examples:
            >>> (1, 'A') in Product((0,1), "AB")
            True
        
            >>> (0, 'C') in Product((0,1), "AB")
            False
        
            >>> (1, 1) in Product((0,1), "AB")
            False
        
            >>> 1 in Product((0,1), repeat=3)
            Traceback (most recent call last):
              ...
            TypeError: 'in <Product>' requires tuple as left operand, not int
        """
        if not isinstance(item, tuple):
            raise TypeError("'in <{}>' requires tuple as left operand, not {}".format(type(self).__name__, type(item).__name__))
        if len(item) != len(self._sequences): # Explicit test guarantees expected result of `zip` below
            return False
        return all(elem in factor for elem, factor in zip(item, self._sequences))
        # Correctness argument: This is the definition of the Cartesian product.
        
        # We could avoid the explicit length check by writing
        #   sentinel = (x for x in ()) # Empty generator
        #   return all(elem in factor for elem, factor in itertools.zip_longest(item, self._sequences, fillvalue=sentinel))
        # but this is somewhat mysterious to read.
    
    def index(self, item): #, start = 0, stop = None): # Future: consider supporting start, stop parameters
        if self._sequences == (): # Special case
            if item == ():
                return 0
            #else:
            raise ValueError("Product.index(x): x = {} not in Product".format(item))
        
        i = 0
        for elem, factor in zip(item, self._sequences): # If self._sequences is empty this falls through immediately & returns zero
                                                        # which is why we had to special-case that situation above.
            i *= len(factor) # Future: overflow safety?
            i += factor.index(elem) # Raises ValueError if `elem` not found in `factor`, therefore `item` not found in `self`.
        return i
    
    def count(self, item):
        """Count the number of occurrences of `item` in `self`."""
    
        if not isinstance(item, tuple):
            return 0
        if len(item) != len(self._sequences): # Same reasoning as in __contains__
            return 0
            
        # The number of ways that `item` can be formed as a tuple taking elements successively from `self._sequences`
        # is the product of the numbers of ways that each element of `item` occurs in its corresponding
        # factor of `self`.
        sentinel = object()
        elem_factor_pairs = zip(item, self._sequences)
        ways = 1
        for elem, factor in elem_factor_pairs:            
            ways *= factor.count(elem)
            if ways == 0:
                return 0
        return ways
        # Equivalent to:
        #   return functools.reduce(operator.mul, (factor.count(elem) for elem, factor in elem_factor_pairs), 1)
        # but this implementation short-circuits as soon as the element fails to be found in any factor.
            

class _ProductSlice(SeqSlice):
    def __iter__(self):
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
                # Started too late to capture any items.
                return
            elif start >= L and step < 0:
                # Clip to back.
                start = L - 1
            elif start < -L and step > 0:
                # Clip to front
                start = -L
        
        if self._seq._sequences == (): # Special case for product of empty sequence of sequences:
                                       # If we've gotten this far, capture the one item there and stop.
            yield ()
            return
        
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

if __name__ == "__main__":
    import doctest
    doctest.testmod()