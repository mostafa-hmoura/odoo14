from odoo import api, fields, models
from datetime import datetime, timedelta

from decimal import *

class PublicMarketAttachementLine(models.Model):
    _name = "public.market.attachement.line"

    @api.onchange("quantity_posee_prec", "quantity_posee_cum")
    def onchange_quantity_posee_cum(self):
        for line in self:
            quantity_posee = line.quantity_posee_cum - line.quantity_posee_prec
            line.quantity_posee = quantity_posee

    @api.depends("quantity_posee_prec", "quantity_posee")
    def _compute_quantity_posee_cum(self):
        for line in self:
            cumul = line.quantity_posee_prec + line.quantity_posee
            val = u"0%"
            if line.quantity > 0:
                value = (cumul / line.quantity) * 100.0
                value_str = moneyfmt(Decimal(value), places=0, sep='', dp='')
                val = value_str + "%"

            line.quantity_posee_cum = cumul
            line.quantity_posee_cum_percent = val


    @api.depends("price_unit", "quantity", "quantity_posee")
    def _compute_depense(self):
        for line in self:
            line.depense_cps = ((line.price_unit * line.quantity))
            line.depense = ((line.price_unit * line.quantity_posee))


    @api.depends("depense_prec", "depense")
    def _compute_depense_cum(self):
        for line in self:
            line.depense_cum = ((line.depense_prec + line.depense))

    attachement_id = fields.Many2one("public.market.attachement", u"Attachement", ondelete="cascade")
    template_line_id = fields.Many2one("public.market.attachement.template.line", u"Template Line")
    price_number = fields.Char(u"N° prix", required=True)
    # cps_id = fields.Many2one("public.market.cps",u"Désignation",required=True)
    name = fields.Char(u"Description", required=True)
    uom = fields.Char(u"U", required=True)
    # uom_id = fields.Many2one("cps.uom",u"U",required=True)
    quantity = fields.Float(u"CPS", required=True)

    quantity_posee_prec = fields.Float(u"Ant.")
    quantity_posee = fields.Float(u"En cours", required=True, digits=(12, 4))
    quantity_posee_cum = fields.Float(u"Cumulée", compute="_compute_quantity_posee_cum", store=True, readonly=False)
    quantity_posee_cum_percent = fields.Char(u"%", compute="_compute_quantity_posee_cum", store=True, readonly=False)
    price_unit = fields.Float(u"P.U")

    # DEPENSE
    depense_cps = fields.Float(u"CPS", compute="_compute_depense")
    depense_prec = fields.Float(u"Antérieure")
    depense = fields.Float(u"En cours", compute="_compute_depense")
    depense_cum = fields.Float(u"Cumulée", compute="_compute_depense_cum")

class PublicMarketAttachement(models.Model):
    _name = "public.market.attachement"
    _desciption = "Public Market Attachement"

    @api.depends("line_ids", "line_ids.depense_cps")
    def _compute_depense_cps_total(self):
        for rec in self:
            rec.total_depense_cps = sum([line.depense_cps for line in self.line_ids])

    @api.depends("line_ids", "line_ids.depense_prec")
    def _compute_depense_prec_total(self):
        for rec in self:
            rec.total_depense_prec = sum([line.depense_prec for line in self.line_ids])

    @api.depends("line_ids", "line_ids.depense")
    def _compute_depense_total(self):
        for rec in self:
            rec.total_depense = sum([line.depense for line in self.line_ids])

    @api.depends("line_ids", "line_ids.depense_cum")
    def _compute_depense_cum_total(self):
        for rec in self:
            rec.total_depense_cum = sum([line.depense_cum for line in self.line_ids])

    # total
    total_depense_cps = fields.Float(u"Total CPS",compute="_compute_depense_cps_total")
    total_depense_prec = fields.Float(u"Total Antérieure",compute="_compute_depense_prec_total")
    total_depense = fields.Float(u"Total des En cours",compute="_compute_depense_total")
    total_depense_cum = fields.Float(u"Total des Cumulées",compute="_compute_depense_cum_total")
    #####


    number = fields.Char(u"N° attachement", required=True,
                         states={'draft': [('readonly', False)], 'paied': [('readonly', False)]})
    name = fields.Char(u"Description", required=True,
                       states={'draft': [('readonly', False)], 'paied': [('readonly', False)]})

    objet = fields.Text(u"Objet", required=True,
                        states={'draft': [('readonly', False)], 'paied': [('readonly', False)]})

    public_market_id = fields.Many2one("market",u"Marché",required=True,states={'draft': [('readonly', False)],'paied': [('readonly', False)]})

    date = fields.Date(u"Date",required=True,default=fields.Date.context_today,states={'draft': [('readonly', False)],'paied': [('readonly', False)]})

    start = fields.Boolean(u"Premier mois?", states={'draft': [('readonly', False)],'paied': [('readonly', False)]})

    template_attachement_id = fields.Many2one("public.market.attachement.template", u"Template",
                                              states={'draft': [('readonly', False)], 'paied': [('readonly', False)]},
                                              ondelete="restrict")


    mois = fields.Char(u"Mois",required=True,states={'draft': [('readonly', False)],'paied': [('readonly', False)]})

    line_ids = fields.One2many("public.market.attachement.line", "attachement_id", u"Lignes",
                               states={'draft': [('readonly', False)], 'paied': [('readonly', False)]})

    real = fields.Boolean(u"Attachement réel?", states={'draft': [('readonly', False)],'paied': [('readonly', False)]})

    state = fields.Selection(
        [('draft', 'Attachement en saisie'), ('done', 'Décompte Validé'), ('paied', 'Décompte payé')], 'Statut',
        default="draft")

    footer_line_ids = fields.One2many("public.market.attachement.footer", "attachement_id", u"Résumé", readonly=True,
                                      states={'draft': [('readonly', False)], 'paied': [('readonly', False)]})

    #montant_att = fields.Float(u"Montant attachement")
    #banque = fields.Many2one(related='public_market_id.partner_bank_id', string="Banque")

    _sql_constraints = [
        ('number_uniq', 'unique (real,number,public_market_id)', u"Numéro d'attachement unique par marché!"),
        ('first_uniq', 'unique (id,start,public_market_id)', u'Un seul début !')]  # LE DEUX CHECK EST DESACTIVÉ

    def _check_start_value(self):
        for att in self:
            if att.start:
                prev = self.search([('id', '!=', att.id), ('real', '=', att.real), ('start', '=', True),
                                    ('public_market_id', '=', att.public_market_id.id)])
                if prev:
                    return False
        return True

    _constraints = [(_check_start_value, 'Erreur : Un seul début !', ['start'])]

    @api.onchange("template_attachement_id")
    def onchange_template_attachement_id(self):
        self.name = self.template_attachement_id.name

    @api.onchange("public_market_id")
    def onchange_public_market_id(self):
        self.objet = self.public_market_id.objet

    @api.onchange("attachement_id")
    def onchange_attachement_id(self):
        self.template_attachement_id = self.attachement_id.template_attachement_id.id


class PublicMarketAttachementFooter(models.Model):
    _name = "public.market.attachement.footer"

    attachement_id = fields.Many2one("public.market.attachement", u"Attachement")
    label_id = fields.Many2one("public.market.attachement.label", "Nom", required=True)
    depense_cps = fields.Float(u"CPS")
    depense_prec = fields.Float(u"Antérieure")
    depense = fields.Float(u"En cours")
    depense_cum = fields.Float(u"Cumulée", store=True, readonly=False)
    code = fields.Char(u"Code", compute="_compute_code", store=True)


class PublicMarketAttachemenLabel(models.Model):
    _name = "public.market.attachement.label"

    code = fields.Char(u"Code", required=True)
    name = fields.Char(u"Nom", required=True)
    factor = fields.Float(u"Facteur", default=100, help="value*(factor/100) for vat")
    sequence = fields.Integer("Sequence", default=1000)
    usage = fields.Selection([('1', 'Attachement théorique'), ('2', 'Attachement réel')], u"Ajouter dans le résumé de")

    _sql_constraints = [('code_uniq', 'unique (code)', u'Code unique !')]
### Function
def tronquer(decimale):
    return float(Decimal(decimale).quantize(Decimal('.01'), rounding=ROUND_DOWN))

def moneyfmt(value, places=2, curr='', sep=',', dp='.',
             pos='', neg='-', trailneg=''):
    """Convert Decimal to a money formatted string.

    places:  required number of places after the decimal point
    curr:    optional currency symbol before the sign (may be blank)
    sep:     optional grouping separator (comma, period, space, or blank)
    dp:      decimal point indicator (comma or period)
             only specify as blank when places is zero
    pos:     optional sign for positive numbers: '+', space or blank
    neg:     optional sign for negative numbers: '-', '(', space or blank
    trailneg:optional trailing minus indicator:  '-', ')', space or blank

    >>> d = Decimal('-1234567.8901')
    >>> moneyfmt(d, curr='$')
    '-$1,234,567.89'
    >>> moneyfmt(d, places=0, sep='.', dp='', neg='', trailneg='-')
    '1.234.568-'
    >>> moneyfmt(d, curr='$', neg='(', trailneg=')')
    '($1,234,567.89)'
    >>> moneyfmt(Decimal(123456789), sep=' ')
    '123 456 789.00'
    >>> moneyfmt(Decimal('-0.02'), neg='<', trailneg='>')
    '<0.02>'

    """
    q = Decimal(10) ** -places      # 2 places --> '0.01'
    sign, digits, exp = value.quantize(q).as_tuple()
    result = []
    digits = list(map(str, digits))
    build, next = result.append, digits.pop
    if sign:
        build(trailneg)
    for i in range(places):
        build(next() if digits else '0')
    build(dp)
    if not digits:
        build('0')
    i = 0
    while digits:
        build(next())
        i += 1
        if i == 3 and digits:
            i = 0
            build(sep)
    build(curr)
    build(neg if sign else pos)
    return ''.join(reversed(result))