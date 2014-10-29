# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Bool, Eval, If
from trytond.transaction import Transaction

__all__ = ['Product', 'ProductSupplierPrice', 'CreatePurchase']
__metaclass__ = PoolMeta


class Product:
    __name__ = 'product.product'

    # This method is added in trytond-patches. In trunk 'get_purchase_price'
    # use the new match() method of purchase.product_supplier.price
    def get_supplier_price(self, product_supplier, quantity, to_uom):
        pool = Pool()
        SupplierPrice = pool.get('purchase.product_supplier.price')
        Uom = pool.get('product.uom')

        res = None
        for price in SupplierPrice.search([
                    ('product_supplier', '=', product_supplier.id),
                    ('valid', '=', True),
                    ]):
            if Uom.compute_qty(self.purchase_uom,
                    price.quantity, to_uom) <= quantity:
                res = price.unit_price
        return res


class ProductSupplierPrice:
    __name__ = 'purchase.product_supplier.price'

    start_date = fields.Date('Start Date', domain=[
            ['OR',
                ('start_date', '=', None),
                If(Bool(Eval('end_date', None)),
                    ('start_date', '<=', Eval('end_date', None)),
                    ('start_date', '!=', None)),
                ]
            ], depends=['end_date'],
        help='Starting date for this price entry to be valid.')
    end_date = fields.Date('End Date', domain=[
            ['OR',
                ('end_date', '=', None),
                If(Bool(Eval('start_date', None)),
                    ('end_date', '>=', Eval('start_date', None)),
                    ('end_date', '!=', None)),
                ]
            ], depends=['start_date'],
        help='Ending date for this price entry to be valid.')
    valid = fields.Function(fields.Boolean('Valid'),
        'on_change_with_valid', searcher='search_valid')

    @classmethod
    def __setup__(cls):
        super(ProductSupplierPrice, cls).__setup__()
        cls._order.insert(0, ('start_date', 'DESC'))
        cls._order.insert(1, ('end_date', 'DESC'))
        cls._error_messages.update({
                'prices_overlap': ('The prices "%(first)s" and "%(second)s" '
                    'for supplier "%(supplier)s" overlap.'),
                })

    @fields.depends('start_date', 'end_date')
    def on_change_with_valid(self, name=None):
        Date = Pool().get('ir.date')

        context = Transaction().context
        today = (context['purchase_date'] if context.get('purchase_date')
            else Date.today())
        return ((not self.start_date or self.start_date <= today) and
            (not self.end_date or self.end_date >= today))

    @classmethod
    def search_valid(cls, name, clause):
        Date = Pool().get('ir.date')

        context = Transaction().context
        today = (context['purchase_date'] if context.get('purchase_date')
            else Date.today())
        return [
            ['OR',
                ('start_date', '=', None),
                ('start_date', '<=', today),
                ],
            ['OR',
                ('end_date', '=', None),
                ('end_date', '>=', today),
                ],
            ]

    @classmethod
    def validate(cls, prices):
        super(ProductSupplierPrice, cls).validate(prices)
        for price in prices:
            price.check_dates()

    def check_dates(self):
        cursor = Transaction().cursor
        table = self.__table__()

        domain = [
            ('product_supplier', '=', self.product_supplier.id),
            ('quantity', '=', self.quantity),
            ('id', '!=', self.id),
            ]
        if self.start_date and self.end_date:
            domain += [
                ['OR',
                    ('start_date', '=', None),
                    ('start_date', '<=', self.end_date),
                    ],
                ['OR',
                    ('end_date', '=', None),
                    ('end_date', '>=', self.start_date),
                    ],
                ]
        elif self.start_date:  # end_date == None
            domain += [
                ['OR',
                    ('end_date', '=', None),
                    ('end_date', '>=', self.start_date),
                    ],
                ]
        elif self.end_date:  # start_date == None
            domain += [
                ['OR',
                    ('start_date', '=', None),
                    ('start_date', '<=', self.end_date),
                    ],
                ]
        # if start_date and end_date == None => any with same supplier and
        # quantity is wrong
        overlapping_prices = self.search(domain)
        if overlapping_prices:
            self.raise_user_error('prices_overlap', {
                    'first': str(self.unit_price),
                    'second': str(overlapping_prices[0].unit_price),
                    'supplier': self.product_supplier.party.rec_name,
                    })


class CreatePurchase:
    __name__ = 'purchase.request.create_purchase'

    @classmethod
    def compute_purchase_line(cls, request, purchase):
        with Transaction().set_context(purchase_date=purchase.purchase_date):
            return super(CreatePurchase, cls).compute_purchase_line(request,
                purchase)
