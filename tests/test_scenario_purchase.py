import datetime
import unittest
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from proteus import Model
from trytond.modules.account.tests.tools import (create_chart,
                                                 create_fiscalyear, create_tax,
                                                 get_accounts)
from trytond.modules.account_invoice.tests.tools import (
    create_payment_term, set_fiscalyear_invoice_sequences)
from trytond.modules.company.tests.tools import create_company, get_company
from trytond.tests.test_tryton import drop_db
from trytond.tests.tools import activate_modules


class Test(unittest.TestCase):

    def setUp(self):
        drop_db()
        super().setUp()

    def tearDown(self):
        drop_db()
        super().tearDown()

    def test(self):

        today = datetime.date.today()
        yesterday = today + relativedelta(days=-1)
        in10days = today + relativedelta(days=10)

        # Install purchase
        activate_modules('purchase_supplier_price_period')

        # Create company
        _ = create_company()
        company = get_company()

        # Create fiscal year
        fiscalyear = set_fiscalyear_invoice_sequences(
            create_fiscalyear(company))
        fiscalyear.click('create_period')

        # Create chart of accounts
        _ = create_chart(company)
        accounts = get_accounts(company)
        revenue = accounts['revenue']
        expense = accounts['expense']

        # Create tax
        tax = create_tax(Decimal('.10'))
        tax.save()

        # Create parties
        Party = Model.get('party.party')
        supplier = Party(name='Supplier')
        supplier.save()
        customer = Party(name='Customer')
        customer.save()

        # Create account categories
        ProductCategory = Model.get('product.category')
        account_category = ProductCategory(name="Account Category")
        account_category.accounting = True
        account_category.account_expense = expense
        account_category.account_revenue = revenue
        account_category.save()
        account_category_tax, = account_category.duplicate()
        account_category_tax.supplier_taxes.append(tax)
        account_category_tax.save()

        # Create product
        ProductUom = Model.get('product.uom')
        unit, = ProductUom.find([('name', '=', 'Unit')])
        ProductTemplate = Model.get('product.template')
        template = ProductTemplate()
        template.name = 'product'
        template.default_uom = unit
        template.type = 'goods'
        template.purchasable = True
        template.list_price = Decimal(10)
        template.cost_price_method = 'fixed'
        template.account_category = account_category
        product, = template.products
        product.cost_price = Decimal(5)
        template.save()
        product, = template.products
        ProductSupplier = Model.get('purchase.product_supplier')
        ps = ProductSupplier()
        ps.product = template
        ps.party = supplier
        ps.save()
        SupplierPrice = Model.get('purchase.product_supplier.price')
        price1 = SupplierPrice()
        price1.product_supplier = ps
        price1.quantity = 0
        price1.unit_price = Decimal(10)
        price1.save()

        # Create payment term
        payment_term = create_payment_term()
        payment_term.save()

        # Purchase 5 products
        Purchase = Model.get('purchase.purchase')
        PurchaseLine = Model.get('purchase.line')
        purchase = Purchase()
        purchase.party = supplier
        purchase.payment_term = payment_term
        purchase_line1 = PurchaseLine()
        purchase.lines.append(purchase_line1)
        purchase_line1.product = product
        purchase_line1.quantity = 1.0
        self.assertEqual(purchase_line1.unit_price, Decimal(10))
        price1.end_date = yesterday
        price1.save()
        purchase_line2 = PurchaseLine()
        purchase.lines.append(purchase_line2)
        purchase_line2.product = product
        purchase_line2.quantity = 1.0
        purchase_line2.unit_price = product.cost_price
        price2 = SupplierPrice()
        price2.product_supplier = ps
        price2.quantity = 0
        price2.start_date = in10days
        price2.unit_price = Decimal(20)
        price2.save()
        purchase_line3 = PurchaseLine()
        purchase.lines.append(purchase_line3)
        purchase_line3.product = product
        purchase_line3.quantity = 3.0
        purchase_line3.unit_price = product.cost_price
        price3 = SupplierPrice()
        price3.product_supplier = ps
        price3.quantity = 0
        price3.start_date = today
        price3.end_date = in10days - relativedelta(days=1)
        price3.unit_price = Decimal(30)
        price3.save()
        purchase_line4 = PurchaseLine()
        purchase.lines.append(purchase_line4)
        purchase_line4.product = product
        purchase_line4.quantity = 4.0
        purchase_line4.unit_price = product.cost_price

        # Purchase in the future
        Purchase = Model.get('purchase.purchase')
        PurchaseLine = Model.get('purchase.line')
        purchase = Purchase()
        purchase.purchase_date = in10days
        purchase.party = supplier
        purchase.payment_term = payment_term
        purchase_line1 = PurchaseLine()
        purchase.lines.append(purchase_line1)
        purchase_line1.product = product
        purchase_line1.quantity = 1.0
        purchase_line1.unit_price = product.cost_price

        # Purchase in the past
        Purchase = Model.get('purchase.purchase')
        PurchaseLine = Model.get('purchase.line')
        purchase = Purchase()
        purchase.purchase_date = yesterday
        purchase.party = supplier
        purchase.payment_term = payment_term
        purchase_line1 = PurchaseLine()
        purchase.lines.append(purchase_line1)
        purchase_line1.product = product
        purchase_line1.quantity = 1.0
        purchase_line1.unit_price = product.cost_price
