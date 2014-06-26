#!/usr/bin/env python
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import datetime
import doctest
import unittest
from dateutil.relativedelta import relativedelta
from decimal import Decimal

import trytond.tests.test_tryton
from trytond.tests.test_tryton import POOL, DB_NAME, USER, CONTEXT, test_view,\
    test_depends
from trytond.transaction import Transaction


class TestCase(unittest.TestCase):
    'Test module'

    def setUp(self):
        trytond.tests.test_tryton.install_module(
            'purchase_supplier_price_period')
        self.uom = POOL.get('product.uom')
        self.uom_category = POOL.get('product.uom.category')
        self.category = POOL.get('product.category')
        self.template = POOL.get('product.template')
        self.product = POOL.get('product.product')
        self.company = POOL.get('company.company')
        self.party = POOL.get('party.party')
        self.account = POOL.get('account.account')
        self.product_supplier = POOL.get('purchase.product_supplier')
        self.supplier_price = POOL.get('purchase.product_supplier.price')
        self.user = POOL.get('res.user')

    def test0005views(self):
        'Test views'
        test_view('purchase_supplier_price_period')

    def test0006depends(self):
        'Test depends'
        test_depends()

    def test0010get_supplier_price(self):
        'Test get_supplier_price and get_purchase_price'
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            company, = self.company.search([
                    ('rec_name', '=', 'Dunder Mifflin'),
                    ])
            self.user.write([self.user(USER)], {
                'main_company': company.id,
                'company': company.id,
                })

            # Prepare product
            uom_category, = self.uom_category.create([{'name': 'Test'}])
            uom, = self.uom.create([{
                        'name': 'Test',
                        'symbol': 'T',
                        'category': uom_category.id,
                        'rate': 1.0,
                        'factor': 1.0,
                        }])
            category, = self.category.create([{'name': 'ProdCategoryTest'}])
            template, = self.template.create([{
                        'name': 'ProductTest',
                        'default_uom': uom.id,
                        'category': category.id,
                        'account_category': True,
                        'list_price': Decimal(0),
                        'cost_price': Decimal(10),
                        }])
            product, = self.product.create([{
                        'template': template.id,
                        }])

            # Prepare supplier
            receivable, = self.account.search([
                ('kind', '=', 'receivable'),
                ('company', '=', company.id),
                ])
            payable, = self.account.search([
                ('kind', '=', 'payable'),
                ('company', '=', company.id),
                ])
            supplier, = self.party.create([{
                        'name': 'supplier',
                        'account_receivable': receivable.id,
                        'account_payable': payable.id,
                        }])

            # Prepare product supplier
            product_supplier, = self.product_supplier.create([{
                        'product': template.id,
                        'company': company.id,
                        'party': supplier.id,
                        'delivery_time': 2,
                        }])

            # Prepare dates
            today = datetime.date.today()
            yesterday = today + relativedelta(days=-1)
            in10days = today + relativedelta(days=10)

            with Transaction().set_context(supplier=supplier.id):
                # Check without supplier price
                self.assertIsNone(product.get_supplier_price(product_supplier,
                        0, product.default_uom))
                self.assertEqual(
                    self.product.get_purchase_price([product])[product.id],
                    Decimal(10))

                # Check supplier price without dates
                supplier_price, = self.supplier_price.create([{
                            'product_supplier': product_supplier.id,
                            'quantity': 0,
                            'unit_price': Decimal(12),
                            }])
                self.assertIsNotNone(
                    product.get_supplier_price(product_supplier, 0,
                        product.default_uom))
                self.assertEqual(
                    self.product.get_purchase_price([product])[product.id],
                    Decimal(12))

                # Check supplier price with old date
                supplier_price.end_date = yesterday
                supplier_price.save()
                self.assertIsNone(product.get_supplier_price(product_supplier,
                        0, product.default_uom))
                self.assertEqual(
                    self.product.get_purchase_price([product])[product.id],
                    Decimal(10))

                # Check supplier price with old and future date
                supplier_price, = self.supplier_price.create([{
                            'product_supplier': product_supplier.id,
                            'quantity': 0,
                            'start_date': in10days,
                            'unit_price': Decimal(14),
                            }])
                self.assertIsNone(product.get_supplier_price(product_supplier,
                        0, product.default_uom))
                self.assertEqual(
                    self.product.get_purchase_price([product])[product.id],
                    Decimal(10))

                # Check supplier price with current dates
                supplier_price, = self.supplier_price.create([{
                            'product_supplier': product_supplier.id,
                            'quantity': 0,
                            'start_date': today,
                            'end_date': in10days + relativedelta(days=-1),
                            'unit_price': Decimal(16),
                            }])
                self.assertIsNotNone(
                    product.get_supplier_price(product_supplier, 0,
                        product.default_uom))
                self.assertEqual(
                    self.product.get_purchase_price([product])[product.id],
                    Decimal(16))

                # Check supplir price for past purchase date
                with Transaction().set_context(purchase_date=yesterday):
                    self.assertEqual(
                        self.product.get_purchase_price([product])[product.id],
                        Decimal(12))

                # Check supplir price for future purchase date
                with Transaction().set_context(purchase_date=in10days):
                    self.assertEqual(
                        self.product.get_purchase_price([product])[product.id],
                        Decimal(14))


def suite():
    suite = trytond.tests.test_tryton.suite()
    from trytond.modules.company.tests import test_company
    for test in test_company.suite():
        if test not in suite:
            suite.addTest(test)
    from trytond.modules.account.tests import test_account
    for test in test_account.suite():
        if test not in suite and not isinstance(test, doctest.DocTestCase):
            suite.addTest(test)
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestCase))
    return suite
