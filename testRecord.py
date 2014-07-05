#!/usr/bin/env python

import record
import unittest

class TestRecord(unittest.TestCase):

    def test_parseDtraceEntryList(self):
        sample = """   ID   PROVIDER   MODULE         FUNCTION NAME
                     3169   pid33494   testModule1    testFunction1 with spaces entry
                     3170   pid33494   testModule2    testFunction2_with8#@9%$#$^* entry"""
        expected = [
            ['3169', 'pid33494', 'testModule1', 'testFunction1 with spaces'],
            ['3170', 'pid33494', 'testModule2', 'testFunction2_with8#@9%$#$^*']]
        self.assertEqual(record._parseDtraceEntryList(sample), expected)

if __name__ == '__main__':
    unittest.main()