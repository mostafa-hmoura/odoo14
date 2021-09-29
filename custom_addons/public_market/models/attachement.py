from odoo import api, fields, models,_
from decimal import *

from odoo.exceptions import UserError
from odoo.tools.convert import safe_eval
from . import function as fun

class PublicMarketAttachementLine(models.Model):
    _name = "public.market.attachement.line"

    @api.onchange("quantity_posee_prec", "quantity_posee_cum")
    def onchange_quantity_posee_cum(self):
        for line in self:
            quantity_posee = line.quantity_posee_cum - line.quantity_posee_prec
            line.quantity_posee = quantity_posee

    @api.onchange("quantity_posee")
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


    @api.onchange("price_unit", "quantity", "quantity_posee")
    def _compute_depense(self):
        for line in self:
            line.depense_cps = ((line.price_unit * line.quantity))
            line.depense = ((line.price_unit * line.quantity_posee))


    @api.onchange("depense_prec", "depense")
    def _compute_depense_cum(self):
        for line in self:
            line.depense_cum = ((line.depense_prec + line.depense))

    attachement_id = fields.Many2one("public.market.attachement", u"Attachement", ondelete="cascade")
    template_line_id = fields.Many2one("public.market.attachement.template.line", u"Template Line")
    price_number = fields.Char(u"N° prix", required=True,readonly=True)
    name = fields.Char(u"Description", required=True,readonly=True)
    uom = fields.Char(u"U", required=True,readonly=True)
    quantity = fields.Float(u"CPS", required=True,readonly=True)

    quantity_posee_prec = fields.Float(u"Ant.",readonly=True)
    quantity_posee = fields.Float(u"En cours", required=True, digits=(12, 4))
    quantity_posee_cum = fields.Float(u"Cumulée", readonly=False)
    quantity_posee_cum_percent = fields.Char(u"%", readonly=False)
    price_unit = fields.Float(u"P.U",readonly=True)

    # DEPENSE
    depense_cps = fields.Float(u"CPS",readonly=False)
    depense_prec = fields.Float(u"Antérieure",readonly=False)
    depense = fields.Float(u"En cours",readonly=False)
    depense_cum = fields.Float(u"Cumulée",readonly=False)

class PublicMarketAttachement(models.Model):
    _name = "public.market.attachement"
    _desciption = "Public Market Attachement"
    _rec_name = "number"

    @api.onchange("public_market_id")
    def _compute_attachement_id(self):
        real = self.env.context.get("default_real")
        domain = [('public_market_id', '=', self.public_market_id.id), ('real', '=', real)]
        if isinstance(self.id, int):
            domain.append(('id', '<', self.id))
        attachements = self.search(domain, order="id desc")
        if attachements:
            self.attachement_id = attachements[0].id
            self.number = str(int(attachements[0].number) + 1)
            self.start = False
        else:
            self.number = 1
            self.start = True

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

    @api.depends("template_attachement_id")
    def onchange_template_attachement_id(self):
        self.name = self.template_attachement_id.name

    @api.depends("public_market_id")
    def onchange_public_market_id(self):
        self.objet = self.public_market_id.objet

    # total
    total_depense_cps = fields.Float(u"Total CPS",compute="_compute_depense_cps_total", store=True)
    total_depense_prec = fields.Float(u"Total Antérieure",compute="_compute_depense_prec_total", store=True)
    total_depense = fields.Float(u"Total des En cours",compute="_compute_depense_total", store=True)
    total_depense_cum = fields.Float(u"Total des Cumulées",compute="_compute_depense_cum_total", store=True)
    #####

    public_market_id = fields.Many2one("market",u"Marché",required=True,states={'draft': [('readonly', False)],'paied': [('readonly', False)]})

    template_attachement_id = fields.Many2one("public.market.attachement.template", u"Template",
                                              states={'draft': [('readonly', False)], 'paied': [('readonly', False)]},
                                              ondelete="restrict",domain="[('code', '=', public_market_id)]")

    attachement_id = fields.Many2one("public.market.attachement", u"Attachement précédent",
                                    ondelete = "restrict")

    line_ids = fields.One2many("public.market.attachement.line", "attachement_id", u"Lignes", readonly=True,
                               states={'draft': [('readonly', False)], 'paied': [('readonly', False)]})

    number = fields.Char(u"N° attachement", required=True,
                         states={'draft': [('readonly', False)], 'paied': [('readonly', False)]})

    name = fields.Char(u"Description", required=True,
                       states={'draft': [('readonly', False)], 'paied': [('readonly', False)]})

    objet = fields.Text(u"Objet", required=True,
                        states={'draft': [('readonly', False)], 'paied': [('readonly', False)]})

    date = fields.Date(u"Date",required=True,default=fields.Date.context_today,states={'draft': [('readonly', False)],'paied': [('readonly', False)]})

    start = fields.Boolean(u"Premier mois?", states={'draft': [('readonly', False)],'paied': [('readonly', False)]})

    mois = fields.Char(u"Mois",required=True,states={'draft': [('readonly', False)],'paied': [('readonly', False)]})

    line_ids = fields.One2many("public.market.attachement.line", "attachement_id", u"Lignes",
                               states={'draft': [('readonly', False)], 'paied': [('readonly', False)]})

    real = fields.Boolean(u"Attachement réel?", states={'draft': [('readonly', False)],'paied': [('readonly', False)]})

    state = fields.Selection(
        [('draft', 'Attachement en saisie'), ('done', 'Décompte Validé'), ('paied', 'Décompte payé')], 'Statut',
        default="draft")

    footer_line_ids = fields.One2many("public.market.attachement.footer", "attachement_id", u"Résumé", readonly=True,
                                      states={'draft': [('readonly', False)], 'paied': [('readonly', False)]})


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

    def get_caution_value(self):
        for line in self.footer_line_ids:
            if line.code == "CRDG":
                return line.depense
        return 0

    def action_add_cps(self):
        line_obj = self.env["public.market.attachement.template.line"]
        a_line_obj = self.env["public.market.attachement.line"]
        template_cps_ids = []
        cps_ids = [l.template_line_id.id for l in self.line_ids]
        if self.line_ids:
            template = self.line_ids[0].template_line_id.attachement_id
            template_cps_ids.extend([l.id for l in template.line_ids])
        add_ids = [t_id for t_id in template_cps_ids if t_id not in cps_ids]
        for line in line_obj.browse(add_ids):
            total = line.price_unit * line.price_unit
            data = {
                "price_number": line.price_number,
                "name": line.name,
                "uom": line.uom,
                "quantity": line.quantity,
                "quantity_posee": 0.0,
                "price_unit": line.price_unit,
                "depense": 0.0,
                "attachement_id": self.id,
                "template_line_id": line.id,
            }
            a_line_obj.create(data)
        return True

    def action_compute_line(self):
        self.ensure_one()
        line_obj = self.env["public.market.attachement.line"]
        cps_ids = []
        if self.start:
            for line in self.template_attachement_id.line_ids:
                data = {
                    "price_number": line.price_number,
                    "name": line.name,
                    "uom": line.uom,
                    "quantity": line.quantity,
                    "quantity_posee": 0.0,
                    "price_unit": line.price_unit,
                    "depense": 0.0,
                    "attachement_id": self.id,
                    "template_line_id": line.id,
                }

                new = line_obj.create(data)
        else:

            for line in self.attachement_id.line_ids:
                print('>> ',line.depense_cum)
                data = {
                    "price_number": line.price_number,
                    "name": line.name,
                    "uom": line.uom,
                    "quantity": line.quantity,
                    "quantity_posee_prec": line.quantity_posee_cum,
                    "quantity_posee": 0.0,
                    "price_unit": line.price_unit,
                    "depense_prec": (line.quantity_posee_cum * line.price_unit) ,
                    "depense": 0.0,
                    "attachement_id": self.id,
                    "template_line_id": line.template_line_id.id,
                }

                new = line_obj.create(data)

    def action_compute_line_delete(self):
        self.ensure_one()
        self.line_ids.unlink()

    def action_update_line(self):
        for line in self.line_ids:
            for line_prec in self.attachement_id.line_ids:
                if line.template_line_id.id == line_prec.template_line_id.id:
                    line.quantity_posee_prec = line_prec.quantity_posee_cum
                    line.depense_prec = line_prec.depense_cum
            line.depense_cps = ((line.price_unit * line.quantity))
            line.depense = ((line.price_unit * line.quantity_posee))
            line.depense_cum = ((line.depense_prec + line.depense))

    def action_compute_footer(self):

        self.ensure_one()
        labels = self.env['public.market.attachement.label'].search([], order="seq asc")

        data = {}

        for label in labels:

            if label.code == 'THT' and label.seq == 1:
                data = fun.calcul_tht(self,label.name)
                if data:
                    self.env['public.market.attachement.footer'].create(data)

            elif label.code == 'TVA' and label.seq == 2:
                data = fun.calcul_tva(self,data,label.name)
                if data:
                    self.env['public.market.attachement.footer'].create(data)

            elif label.code == 'TTC' and label.seq == 3:
                data = fun.calcul_ttc(self,data,label.name)
                if data:
                    self.env['public.market.attachement.footer'].create(data)

            elif label.code == 'RDP' and label.seq == 4:
                self.env['public.market.attachement.footer'].create(fun.calcul_rdp(self,label.name))

            elif label.code == 'TRDP' and label.seq == 5:
                data = fun.calcul_trdp(self,data,fun.calcul_rdp(self,label.name),label.name)
                if data:
                    self.env['public.market.attachement.footer'].create(data)

            elif label.code == 'RG7' and label.seq == 6:
                data = fun.calcul_rg7(self,label.name)
                if data:
                    self.env['public.market.attachement.footer'].create(data)

            elif label.code == 'RG10' and label.seq == 7:
                data = fun.calcul_rg10(self,label.name)
                if data:
                    self.env['public.market.attachement.footer'].create(data)

            elif label.code == 'MCRG' and label.seq == 8:
                data = fun.calcul_mcrg(self,label.name)
                if data:
                    self.env['public.market.attachement.footer'].create(data)

            elif label.code == 'MRRG' and label.seq == 9:
                data = fun.calcul_mrrg(self,label.name)
                if data:
                    self.env['public.market.attachement.footer'].create(data)

            elif label.code == 'TGTTC' and label.seq == 10:
                data = fun.calcul_tgttc(self,label.name)
                if data:
                    self.env['public.market.attachement.footer'].create(data)

            elif label.code == 'RL10' and label.seq == 11:
                data = fun.calcul_rl10(self,label.name)
                if data:
                    self.env['public.market.attachement.footer'].create(data)

            elif label.code == 'TGTTAR' and label.seq == 12:
                data = fun.calcul_tgttar(self,label.name)
                if data:
                    self.env['public.market.attachement.footer'].create(data)

    def action_compute_footer_delete(self):
        self.ensure_one()
        self.footer_line_ids.unlink()

class PublicMarketAttachementFooter(models.Model):
    _name = "public.market.attachement.footer"

    attachement_id = fields.Many2one("public.market.attachement", u"Attachement")
    label_id = fields.Many2one("public.market.attachement.label")

    nom = fields.Char(u"Nom")
    depense_cps = fields.Float(u"CPS")
    depense_prec = fields.Float(u"Antérieure")
    depense = fields.Float(u"En cours")
    depense_cum = fields.Float(u"Cumulée", store=True, readonly=False)


class PublicMarketAttachemenLabel(models.Model):
    _name = "public.market.attachement.label"

    code = fields.Char(u"Code")

    name = fields.Char(u'name')

    seq = fields.Integer(u'Sequence')

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