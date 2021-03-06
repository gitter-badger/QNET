# This file is part of QNET.
#
#    QNET is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#    QNET is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with QNET.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright (C) 2012-2017, QNET authors (see AUTHORS file)
#
###########################################################################

from sympy import symbols
import unittest
import pytest

from qnet.algebra.abstract_algebra import (
        Operation, assoc, orderby, filter_neutral, CannotSimplify,
        match_replace_binary, idem)
from qnet.algebra.ordering import expr_order_key
from qnet.algebra.pattern_matching import pattern_head, wc
from qnet.algebra.operator_algebra import (
        LocalSigma, OperatorTimes, Displace, II)
from qnet.algebra.hilbert_space_algebra import LocalSpace


class TestOperationSimplifcations(unittest.TestCase):

    def setUp(self):

        class Flat(Operation):
            _simplifications = [assoc, ]


        class Orderless(Operation):
            order_key = expr_order_key
            _simplifications = [orderby, ]


        class FilterNeutral(Operation):
            neutral_element = object()
            _simplifications = [filter_neutral, ]

        def mult_str_int_if_pos(s, i):
            if i >= 0:
                return s * i
            raise CannotSimplify()

        def mult_inv_str_int_if_neg(s, i):
            return s[::-1]*(-i)

        a_int = wc("a", head=int)
        a_negint = wc("a", head=int, conditions=[lambda a: a < 0, ])
        a_str = wc("a", head=str)
        b_str = wc("b", head=str)

        class MatchReplaceBinary(Operation):
            _binary_rules = [
                (pattern_head(a_int, b_str),
                    lambda a, b: mult_str_int_if_pos(b,a)),
                (pattern_head(a_negint, b_str),
                    lambda a, b: mult_inv_str_int_if_neg(b,a)),
                (pattern_head(a_str, b_str),
                    lambda a, b: a + b)
            ]
            neutral_element = 1
            _simplifications = [assoc, match_replace_binary]


        class Idem(Operation):
            order_key = expr_order_key
            _simplifications = [assoc, idem]

        self.Flat = Flat
        self.Orderless = Orderless
        self.FilterNeutral = FilterNeutral
        self.MatchReplaceBinary = MatchReplaceBinary
        self.Idem = Idem


    def testFlat(self):
        assert self.Flat.create(1,2,3, self.Flat(4,5,6),7,8) == \
                         self.Flat(1,2,3,4,5,6,7,8)


    def testOrderless(self):
        assert self.Orderless.create(3,1,2) == self.Orderless(1,2,3)


    def testFilterNeutral(self):
        one = self.FilterNeutral.neutral_element
        assert self.FilterNeutral.create(1,2,3,one,4,5,one) == \
                         self.FilterNeutral(1,2,3,4,5)
        assert self.FilterNeutral.create(one) == one


    def testSimplifyBinary(self):
        assert self.MatchReplaceBinary.create(1,2,"hallo") == "hallohallo"
        assert self.MatchReplaceBinary.create(-1,"hallo") == "ollah"
        assert self.MatchReplaceBinary.create(-3,"hallo") == "ollahollahollah"
        assert self.MatchReplaceBinary.create(2,-2,"hallo") == \
                         "ollahollahollahollah"
        assert self.MatchReplaceBinary.create("1","2","3") == "123"


    def testIdem(self):
        assert self.Idem.create(2,3,3,1,2,3,4,1,2) == \
                         self.Idem(1,2,3,4)


def test_match_replace_binary_complete():
    """Test that replace_binary works correctly for a non-trivial case"""
    x, y, z, alpha = symbols('x y z alpha')
    hs = LocalSpace('f')
    ops = [LocalSigma(0, 0, hs=hs),
           Displace(-alpha, hs=hs),
           Displace(alpha, hs=hs),
           LocalSigma(0, 0, hs=hs)]
    res = OperatorTimes.create(*ops)
    assert res == LocalSigma(0, 0, hs=hs)


def test_singleton_substitute():
    """Test that calling the substitute method on a Singleton returns the
    Singleton"""
    assert II.substitute({}) is II
