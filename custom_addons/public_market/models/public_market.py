from odoo import api, fields, models
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from odoo.exceptions import UserError


class PublicMarketAvenant(models.Model):
    _name = "public.market.avenant"
    _desciption = "Public Market Avenant"

    num_avenant = fields.Char(u"N° Avenant", default='Nouveau',readonly=True)
    # num_avenant = fields.Char(string='N° Avenant', required=True, copy=False, readonly=True,
    #                         default=lambda self: _('New'))
    montant = fields.Float(u"Montant de l'avenant", required=True)
    date_av = fields.Date(u"Date d'approbation de l'avenant", default=datetime.today(), required=True)
    public_market_id = fields.Many2one("market", u"Marché")

    #_sql_constraints = [('num_uniq', 'unique (num_avenant)', u'Numéro d\'avenant unique !')]

    @api.model
    def create(self, vals):

        if vals['montant'] <= 0:
            raise UserError('Le montant du Avenant ne peut pas être égal à 0 ou Negat ou négative !')
            return

        var = self.env['public.market.avenant'].search([('public_market_id', '=', vals['public_market_id'])],
                                                      order='id desc', limit=1)

        marketName = self.env['market'].search([('id', '=', vals['public_market_id'])])

        if not var:
            vals['num_avenant'] = 'AV-' + marketName.name + '-1'

        else:
            vals['num_avenant'] = 'AV-' + marketName.name + '-' + str(int(var.num_avenant.split('-')[2])+1)

        res = super(PublicMarketAvenant, self).create(vals)
        return res


class PublicMarketStop(models.Model):
    _name = "public.market.stop"
    _desciption = "Public Market Stop"

    @api.depends("date_arret", "date_reprise")
    def _compute_duree(self):
        for rec in self:
            if (rec.date_arret < rec.date_reprise):
                duree = (fields.Date.from_string(rec.date_reprise) - fields.Date.from_string(rec.date_arret)).days
                rec.duree = duree + 1
            else:
                raise UserError('Sélectionnez une date d\'arrêt ou de reprise valide !')

    date_arret = fields.Date(u"Date d'arrêt", required=True)
    date_reprise = fields.Date(u"Date de reprise", required=True)
    stop_id = fields.Many2one("market", u"Marché")
    duree = fields.Integer(u"Durée", compute="_compute_duree", store=True)
    # duree = fields.Integer(u"Durée")


class Market(models.Model):
    _name = "market"
    _desciption = "Market"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(u"Marché n°", required=True)
    name2 = fields.Char(string="Appel d'offre n°")
    partner_id = fields.Char(string="Maitre d'ouvrage")
    partner_id2 = fields.Char(string="Maitre d'ouvrage délégué")
    passation_mode_id = fields.Char(string="Mode de passation")
    hors_taxe = fields.Boolean()
    date_abjudication = fields.Date(string="Date d'abjudication")
    date_visa = fields.Date(string="Date de VISA")
    objet = fields.Text(u"Objet",compute="_compute_objet",store=True)
    chantier_id = fields.Char(string="Objet")
    zone_id = fields.Char(string="Zone")
    description = fields.Text(string="Appellation")

    situation_id = fields.Many2one("public.market.situation", u"Situation")

    date_approbation_scheduled = fields.Date(u"Date prévue d'approbation", compute="_compute_date", store=True,
                                             readonly=False, help=u"Date d'adjudication + 75 jours")
    date_approbation = fields.Date(u"Date effective d'approbation")
    date_start_scheduled = fields.Date(u"Date prévue de commencement", compute="_compute_date", store=True,
                                       readonly=False, help=u"Date prévue d'approbation + 30 jours")
    date_start = fields.Date(u"Date effective de commencement", default=datetime.today())
    duree = fields.Integer(u"Durée ( En mois )")
    date_stop_scheduled = fields.Date(u"Date prévue de fin", compute="_compute_date", store=True, readonly=False,
                                      help=u"Date prévue de commencement + Durée ( En mois )")
    date_stop = fields.Date(u"Date effective de fin", compute="_compute_date", store=True, readonly=False,
                            help=u"Date prévue de fin + nombres de jours d'arrêt")

    partner_bank_id = fields.Char(string="Banque")
    nantissement = fields.Char(string="Nantissement")
    total_amount = fields.Float(string="Montant du marché")

    montant_avance = fields.Float(u"Montant avance", compute="_compute_avance", store=True, readonly=False)

    total_apres_avenant = fields.Float(u"Montant du marché aprés des avenants")
    mandat_recu = fields.Float(string="Mandats reçus", compute="_compute_mandat_recu",
                                      readonly=False)
    depense_cum = fields.Float(string="Total des travaux réalisés")
    remaining = fields.Float(string="Reste à réaliser")
    caution_provisoire = fields.Float(string="Montant de la caution provisoire")
    caution_definitive = fields.Float(u"Montant de la caution définitive (3%)", compute="_compute_amount", store=True,
                                      readonly=False)
    retenue_garantie = fields.Float(u"Montant de la retenue de garantie (7%)", compute="_compute_amount", store=True,
                                    readonly=False)
    date_caution_provisoire = fields.Date("Date")
    date_caution_definitive = fields.Date("Date")
    date_retenue_garantie = fields.Date("Date")
    date_reception_provisoire = fields.Date(string="Date de la reception provisoire")
    date_reception_definitive = fields.Date(string="Date de la reception définitive")

    employee_id = fields.Char(string="Nom du chef de projet")

    stop_ids = fields.One2many("public.market.stop", 'stop_id', u"Arrêts")
    avenant_ids = fields.One2many("public.market.avenant", 'public_market_id', u"Avenants")

    total_avenant = fields.Float(u"Total des avenants", compute="_compute_avenant", store=True)

    duree_arret = fields.Integer(u"Durée  des arrêts", compute="_compute_duree_arret", store=True)

    state = fields.Selection(
        [('draft', 'En Cours'), ('stop', 'En Arrêt'), ('prov', 'Récéption provisoire'), ('def', 'Récéption définitive'),
         ('done', 'Liquidé')], 'Statut', default="draft")

    @api.depends("mandat_recu","total_avenant")
    def _compute_mandat_recu(self):
        for rec in self:
            rec.mandat_recu += rec.total_avenant

    @api.depends("stop_ids", "stop_ids.date_arret", "stop_ids.date_reprise")
    def _compute_duree_arret(self):
        for rec in self:
            rec.duree_arret = sum([line.duree for line in self.stop_ids])
            '''rec.date_stop = rec.date_reception_provisoire = fields.Date.from_string(rec.date_start) + timedelta(
                days=rec.duree_arret)'''

    @api.depends("avenant_ids", "avenant_ids.montant", "avenant_ids.date_av")
    def _compute_avenant(self):
        for rec in self:
            rec.total_avenant = sum([line.montant for line in self.avenant_ids])
            rec.total_apres_avenant = rec.total_amount + rec.total_avenant

    @api.onchange("situation_id")
    def onchange_action_liquide(self):
        if self.situation_id.name == "Liquidé":
            self.state = 'done'

    @api.depends("chantier_id")
    def _compute_objet(self):
        #self.objet = self.chantier_id.name
        self.objet = self.chantier_id
        print('>>>> test')

    @api.depends('date_abjudication', 'date_approbation_scheduled', 'date_start_scheduled', 'duree', 'duree_arret')
    def _compute_date(self):
        for market in self:
            date_approbation_scheduled = date_start_scheduled = date_stop_scheduled = date_stop = date_reception_provisoire = False
            if market.date_abjudication:
                date_approbation_scheduled = fields.Date.from_string(market.date_abjudication) + relativedelta(days=+75)
                date_start_scheduled = date_approbation_scheduled + relativedelta(days=+30)
                date_stop_scheduled = date_start_scheduled + relativedelta(months=+int(market.duree))
                date_stop = date_reception_provisoire = fields.Date.from_string(market.date_start) + relativedelta(
                    months=+int(market.duree)) + timedelta(days=market.duree_arret)
                market.date_approbation_scheduled = date_approbation_scheduled
                market.date_start_scheduled = date_start_scheduled
                market.date_stop_scheduled = date_stop_scheduled
                market.date_stop = market.date_reception_provisoire = date_stop
                market.date_reception_definitive = date_stop + relativedelta(months=+12)

    @api.depends("total_amount")
    def _compute_avance(self):

        for rec in self:
            mAvance = False
            tm = rec.total_amount
            if tm >= 10000000:
                tm_10 = 10000000 * 0.1
            else:
                tm_10 = tm * 0.1
            rest_5 = (tm - 10000000) * 0.05
            avance_amout = tm_10 + rest_5
            avance_max = 20000000
            mAvance = avance_max if avance_amout > avance_max else avance_amout
            if rec.total_amount:
                rec.montant_avance = mAvance

    @api.depends('total_amount')
    def _compute_amount(self):
        for market in self:
            market.caution_definitive = int(round(market.total_amount * (3.0 / 100.0)))
            market.retenue_garantie = market.total_amount * (7.0 / 100.0)


class PublicMarketSituation(models.Model):
    _name = "public.market.situation"
    _desciption = "Public Market Situation"

    name = fields.Char("Nom", required=True)

