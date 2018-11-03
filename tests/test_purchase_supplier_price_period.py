#!/usr/bin/env python
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import doctest
import unittest

import trytond.tests.test_tryton
from trytond.tests.test_tryton import ModuleTestCase
from trytond.tests.test_tryton import doctest_teardown, doctest_checker


class PurchaseSupplierPricePeriodTestCase(ModuleTestCase):
    'Test Purchase Supplier Price Period module'
    module = 'purchase_supplier_price_period'

def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
            PurchaseSupplierPricePeriodTestCase))
    suite.addTests(doctest.DocFileSuite('scenario_purchase.rst',
            tearDown=doctest_teardown, encoding='UTF-8',
            optionflags=doctest.REPORT_ONLY_FIRST_FAILURE,
            checker=doctest_checker))
    return suite
