# -*- coding: utf8 -*-
# C&C NLP tools
# Copyright (c) Universities of Edinburgh, Oxford and Sydney
# Copyright (c) James R. Curran
#
# This software is covered by a non-commercial use licence.
# See LICENCE.txt for the full text of the licence.
#
# If LICENCE.txt is not included in this distribution
# please email candc@it.usyd.edu.au to obtain a copy.

from SOAPpy import SOAPProxy
import SOAPpy.Types
import SOAPpy.Config

SOAPpy.Config.debug = 1

def test(method, description, input, output):
  try:
    result = unicode(method(input), "utf8")
    if result != output:
      print "FAILED %s" % description
      print "  INPUT   %s" % input
      print "  OUTPUT  %s" % result
      print "  CORRECT %s" % output
  except SOAPpy.Types.faultType, e:
    print "FAILED %s with exception %s" % (description, e.detail)

def error(method, description, input, error):
  try:
    method(input)
    print "FAILED %s expected exception %s" % (description, error)
  except SOAPpy.Types.faultType, e:
    if e.detail == error:
      return
    else:
      print "FAILED %s expected exception %s not %s" % (description, error, e.detail)
  print "  INPUT   %s" % input

pos = SOAPProxy('http://localhost:9100', namespace='urn:basser-qa-pos')
chunk = SOAPProxy('http://localhost:9101', namespace='urn:basser-qa-chunk')
ner = SOAPProxy('http://localhost:9102', namespace='urn:basser-qa-ner')

ILLEGAL_PRE_WS = "illegal whitespace before the beginning of the sentence"
ILLEGAL_POST_WS = "illegal trailing whitespace after the sentence"
ADJACENT_WS = "illegal adjacent spaces (words must be separated by one space)"

test(pos.pos, "empty string", "", "")
test(pos.pos, "single character", "A", "A|DT")
test(pos.pos, "single word", "The", "The|DT")
test(pos.pos, "single digit", "6", "6|CD")
test(pos.pos, "single number", "123456789", "123456789|CD")
test(pos.pos, "two words 1", "A A", "A|NNP A|NNP")
test(pos.pos, "two words 2", "An A", "An|DT A|NN")
test(pos.pos, "two words 3", "An a", "An|NNP a|DT")
error(pos.pos, "line of whitespace", " ", ILLEGAL_PRE_WS)
error(pos.pos, "beginning of line whitespace 1", " This is a test", ILLEGAL_PRE_WS)
error(pos.pos, "beginning of line whitespace 2", "   This is a test", ILLEGAL_PRE_WS)
error(pos.pos, "end of line whitespace 1", "This is a test ", ILLEGAL_POST_WS)
error(pos.pos, "end of line whitespace 2", "This is a test    ", ADJACENT_WS)
error(pos.pos, "adjacent whitespace 1", "This  is a test", ADJACENT_WS)
error(pos.pos, "adjacent whitespace 2", "This is  a test", ADJACENT_WS)
error(pos.pos, "adjacent whitespace 3", "This     is a test", ADJACENT_WS)
