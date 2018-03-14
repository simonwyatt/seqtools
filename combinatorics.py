#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module provides sequence types implementing combinatoric operations over other sequences.

In comparison to the built-in itertools module, combinatoric sequences provide the richer sequence interface but require sequence inputs.

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

class Product():
    def __init__(self, *iterables, repeat=1):
        raise NotImplementedError()
    
    def __len__(self):
        raise NotImplementedError()
    
    def __contains__(self):
        raise NotImplementedError()
    
    def __getitem__(self):
        raise NotImplementedError()
    
    def __iter__(self):
        raise NotImplementedError()
    
    def __reversed__(self):
        raise NotImplementedError()

collections.abc.Sequence.register(Product)

if __name__ == "__main__":
    import doctest
    doctest.testmod()