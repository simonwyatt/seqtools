#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module provides sequence types implementing combinatoric operations over other sequences.

In comparison to the built-in itertools module, combinatoric sequences provide the richer sequence interface but require sequence inputs.
All classes fully support 

Classes:
    Product: Cartesian product of sequences.
    
This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program. If not, see <http://www.gnu.org/licenses/>.
"""
__author__ = "Simon Wyatt"
__email__ = "simon.d.wyatt@gmail.com"
__version__ = "2018.03.14"
__license__ = "GPLv3"

import collections.abc
import itertools, functools, operator
from functools import reduce

class Product():
    """
    Product(*sequences, repeat=1) --> Product object
    
    Cartesian product of input sequences.
    Equivalent to list(itertools.product(*sequences, repeat)) but without storing a large list.
    
    >>> list(Product((0,1), repeat=3))
    [(0, 0, 0), (0, 0, 1), (0, 1, 0), (0, 1, 1), (1, 0, 0), (1, 0, 1), (1, 1, 0), (1, 1, 1)]
    
    >>> all(x==y for x, y in zip(Product((0,1), repeat=3), itertools.product((0,1), repeat=3)))
    True
    
    >>> list(Product((0,), (1,), (2,)))
    [(0, 1, 2)]
    
    >>> list(Product())
    [()]
    """
    def __init__(self, *sequences, repeat=1):
        self._sequences = sequences * repeat
    
    def len(self):
        """Compute number of elements in Cartesian product (integer product of lengths of factors).
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
        """The initial value 1 is necessary to correctly compute the length of the cartesian product of no sets.
        (The empty tuple is the only way of choosing one element from each of no sets.)"""
    
    def __len__(self):
        """Compute number of elements in Cartesian product.
        
        This method just calls and returns `self.len()`.
        
        However, in CPython, the builtin `len` raises an OverflowError if its value would exceed `sys.maxsize` (2**31 - 1 on 64-bit platforms).
        When working with large sequences, it's easy to exceed this limit; at this point you can no longer use the full sequence interface and must call Product.len instead."""
        return self.len()
    
    def __contains__(self, item):
        """Membership test. Returns true iff each element of `item` is in the corresponding input to `self`.
        Returns false iff `item` has a plausible type to belong to `self` but doesn't; `TypeError` is not caught.
        
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
    
    def _multi_index(self, i):
        indices = []
        for s in self._sequences[::-1]:
            i, j = divmod(i, len(s))
            indices = [j,] + indices
        return indices
        
    def _elem_at(self, indices):
        return [s[indices[i]] for i,s in enumerate(self._sequences)]
    
    def _genitems(self, start = None, stop = None, step = None):
        if self._sequences == (): #Special case for product of empty sequence of sequences.
            yield ()
            return
    
        #Initialize generator state.
        if step == 0:
            raise ValueError("slice step cannot be zero")
        if step is None:
            step = 1
        
        if start is None:
            start = 0 if step>0 else -1
        elif start >= self.len():
            return
        start = self._multi_index(start)
        indices = start
        item = self._elem_at(indices)
        
        if stop is not None:
            stop = self._multi_index(stop)
        
        #Generate items.
        yield tuple(item) #The first one.
        while stop is None or (step>0 and indices < stop) or (step<0 and stop < indices): #If stop is None we'll explicitly break when done.
            indices[-1] += step
            pos = len(self._sequences) - 1
            #Carry overflows back through multi-index, updating item as we go.
            #We only update the entries of the item that need updating, instead of regenerating the entire item tuple when any part of the index changes.
            while pos > 0 and not (0 <= indices[pos] < len(self._sequences[pos])):
                q, indices[pos] = divmod(indices[pos], len(self._sequences[pos]))
                indices[pos - 1] += q
                item[pos] = self._sequences[pos][indices[pos]]
                pos -= 1
            if pos == 0 and not (0 <= indices[pos] < len(self._sequences[pos])): #Ran off end of product.
                break
            #else
            item[pos] = self._sequences[pos][indices[pos]] #One more time for last carry.
            yield tuple(item)
    
    def __getitem__(self, index):
        if isinstance(index, slice):
            return self._genitems(index.start, index.stop, index.step)
            #TODO: detect when step size divides length of last factor and return product object over smaller factor
            #& otherwise provide for slices to be proper sequences too, not just iterators
        else:
            if not (-self.len() <= index < self.len()):
                raise IndexError("Product index out of range")
            #else
            return tuple(self._elem_at(self._multi_index(index)))
    
    def __iter__(self):
        #return itertools.product(*self._sequences)
        return self._genitems()
    
    def __reversed__(self):
        return self[::-1]
        #TODO: implement a Reversed sequence (and maybe Zipped?), algebraically distribute reversal over factors
    
    def __repr__(self):
        return type(self).__name__ + "(" + ", ".join(repr(s) for s in self._sequences) + ")"
    
    #TODO: index searching

collections.abc.Sequence.register(Product)

if __name__ == "__main__":
    import doctest
    doctest.testmod()