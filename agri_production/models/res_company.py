from odoo import api, fields, models, _


class Company(models.Model):
    _inherit = 'res.company'
    _check_company_auto = True

    def _create_activity_record_sequence(self):
        activity_record_vals = []
        for company in self:
            activity_record_vals.append({
                'name': '%s Activity Record Seq' % company.name,
                'code': 'agri.activity.record',
                'company_id': company.id,
                'prefix': 'AG/AR/',
                'padding': 6,
                'number_next': 1,
                'number_increment': 1
            })
        if activity_record_vals:
            self.env['ir.sequence'].create(activity_record_vals)

    def _create_production_record_sequence(self):
        production_record_vals = []
        for company in self:
            production_record_vals.append({
                'name': '%s Production Record Seq' % company.name,
                'code': 'agri.production.record',
                'company_id': company.id,
                'prefix': 'AG/PR/',
                'padding': 6,
                'number_next': 1,
                'number_increment': 1
            })
        if production_record_vals:
            self.env['ir.sequence'].create(production_record_vals)

    def _create_missing_activity_record_sequences(self):
        company_ids = self.env['res.company'].search([])
        company_has_activity_record_seq = self.env['ir.sequence'].search([
            ('code', '=', 'agri.activity.record')
        ]).mapped('company_id')
        company_todo_sequence = company_ids - company_has_activity_record_seq
        company_todo_sequence._create_activity_record_sequence()

    def _create_missing_production_record_sequences(self):
        company_ids = self.env['res.company'].search([])
        company_has_production_record_seq = self.env['ir.sequence'].search([
            ('code', '=', 'agri.production.record')
        ]).mapped('company_id')
        company_todo_sequence = company_ids - company_has_production_record_seq
        company_todo_sequence._create_production_record_sequence()

    @api.model
    def create_missing_sequences(self):
        self._create_missing_activity_record_sequences()
        self._create_missing_production_record_sequences()

    def _create_per_company_sequences(self):
        self.ensure_one()
        self._create_activity_record_sequence()
        self._create_production_record_sequence()

    @api.model
    def create(self, vals):
        company = super(Company, self).create(vals)
        company.sudo()._create_per_company_sequences()
        return company
