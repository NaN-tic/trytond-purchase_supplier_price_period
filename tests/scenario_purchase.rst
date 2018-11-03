=================
Purchase Scenario
=================

Imports::

    >>> import datetime
    >>> from dateutil.relativedelta import relativedelta
    >>> from decimal import Decimal
    >>> from operator import attrgetter
    >>> from proteus import Model, Wizard, Report
    >>> from trytond.tests.tools import activate_modules
    >>> from trytond.modules.company.tests.tools import create_company, \
    ...     get_company
    >>> from trytond.modules.account.tests.tools import create_fiscalyear, \
    ...     create_chart, get_accounts, create_tax
    >>> from trytond.modules.account_invoice.tests.tools import \
    ...     set_fiscalyear_invoice_sequences, create_payment_term
    >>> today = datetime.date.today()
    >>> yesterday = today + relativedelta(days=-1)
    >>> in10days = today + relativedelta(days=10)

Install purchase::

    >>> config = activate_modules('purchase_supplier_price_period')

Create company::

    >>> _ = create_company()
    >>> company = get_company()

Create fiscal year::

    >>> fiscalyear = set_fiscalyear_invoice_sequences(
    ...     create_fiscalyear(company))
    >>> fiscalyear.click('create_period')

Create chart of accounts::

    >>> _ = create_chart(company)
    >>> accounts = get_accounts(company)
    >>> revenue = accounts['revenue']
    >>> expense = accounts['expense']
    >>> cash = accounts['cash']

Create tax::

    >>> tax = create_tax(Decimal('.10'))
    >>> tax.save()

Create parties::

    >>> Party = Model.get('party.party')
    >>> supplier = Party(name='Supplier')
    >>> supplier.save()
    >>> customer = Party(name='Customer')
    >>> customer.save()

Create product::

    >>> ProductUom = Model.get('product.uom')
    >>> unit, = ProductUom.find([('name', '=', 'Unit')])
    >>> ProductTemplate = Model.get('product.template')

    >>> template = ProductTemplate()
    >>> template.name = 'product'
    >>> template.default_uom = unit
    >>> template.type = 'goods'
    >>> template.purchasable = True
    >>> template.salable = True
    >>> template.list_price = Decimal(10)
    >>> template.cost_price_method = 'fixed'
    >>> template.account_expense = expense
    >>> template.account_revenue = revenue
    >>> template.supplier_taxes.append(tax)
    >>> product, = template.products
    >>> product.cost_price = Decimal(5)
    >>> template.save()
    >>> product, = template.products

    >>> ProductSupplier = Model.get('purchase.product_supplier')
    >>> ps = ProductSupplier()
    >>> ps.product = template
    >>> ps.party = supplier
    >>> ps.delivery_time = 2
    >>> ps.save()

    >>> SupplierPrice = Model.get('purchase.product_supplier.price')
    >>> price1 = SupplierPrice()
    >>> price1.product_supplier = ps
    >>> price1.quantity = 0
    >>> price1.unit_price = Decimal(10)
    >>> price1.save()

Create payment term::

    >>> payment_term = create_payment_term()
    >>> payment_term.save()

Purchase 5 products::

    >>> Purchase = Model.get('purchase.purchase')
    >>> PurchaseLine = Model.get('purchase.line')
    >>> purchase = Purchase()
    >>> purchase.party = supplier
    >>> purchase.payment_term = payment_term
    >>> purchase_line1 = PurchaseLine()
    >>> purchase.lines.append(purchase_line1)
    >>> purchase_line1.product = product
    >>> purchase_line1.quantity = 1.0
    >>> purchase_line1.unit_price == Decimal(10)
    True
    >>> price1.end_date = yesterday
    >>> price1.save()
    >>> purchase_line2 = PurchaseLine()
    >>> purchase.lines.append(purchase_line2)
    >>> purchase_line2.product = product
    >>> purchase_line2.quantity = 1.0
    >>> purchase_line2.unit_price == Decimal(5)
    True
    >>> price2 = SupplierPrice()
    >>> price2.product_supplier = ps
    >>> price2.quantity = 0
    >>> price2.start_date = in10days
    >>> price2.unit_price = Decimal(20)
    >>> price2.save()
    >>> purchase_line3 = PurchaseLine()
    >>> purchase.lines.append(purchase_line3)
    >>> purchase_line3.product = product
    >>> purchase_line3.quantity = 3.0
    >>> purchase_line3.unit_price == Decimal(5)
    True
    >>> price3 = SupplierPrice()
    >>> price3.product_supplier = ps
    >>> price3.quantity = 0
    >>> price3.start_date = today
    >>> price3.end_date = in10days - relativedelta(days=1)
    >>> price3.unit_price = Decimal(30)
    >>> price3.save()
    >>> purchase_line4 = PurchaseLine()
    >>> purchase.lines.append(purchase_line4)
    >>> purchase_line4.product = product
    >>> purchase_line4.quantity = 4.0
    >>> purchase_line4.unit_price == Decimal(30)
    True

Purchase in the future::

    >>> Purchase = Model.get('purchase.purchase')
    >>> PurchaseLine = Model.get('purchase.line')
    >>> purchase = Purchase()
    >>> purchase.purchase_date = in10days
    >>> purchase.party = supplier
    >>> purchase.payment_term = payment_term
    >>> purchase_line1 = PurchaseLine()
    >>> purchase.lines.append(purchase_line1)
    >>> purchase_line1.product = product
    >>> purchase_line1.quantity = 1.0
    >>> purchase_line1.unit_price == Decimal(20)
    True

Purchase in the past::

    >>> Purchase = Model.get('purchase.purchase')
    >>> PurchaseLine = Model.get('purchase.line')
    >>> purchase = Purchase()
    >>> purchase.purchase_date = yesterday
    >>> purchase.party = supplier
    >>> purchase.payment_term = payment_term
    >>> purchase_line1 = PurchaseLine()
    >>> purchase.lines.append(purchase_line1)
    >>> purchase_line1.product = product
    >>> purchase_line1.quantity = 1.0
    >>> purchase_line1.unit_price == Decimal(10)
    True
