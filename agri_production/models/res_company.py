from odoo import api, fields, models, _


class Company(models.Model):
    _inherit = 'res.company'
    _check_company_auto = True

    def _create_activity_record_sequence(self):
        activity_record_vals = []
        for company in self:
            activity_record_vals.append({
                'name':
                '%s Activity Record Seq' % company.name,
                'code':
                'agri.activity.record',
                'company_id':
                company.id,
                'prefix':
                'AG/AR/',
                'padding':
                6,
                'number_next':
                1,
                'number_increment':
                1
            })
        if activity_record_vals:
            self.env['ir.sequence'].create(activity_record_vals)

    def _create_production_record_sequence(self):
        production_record_vals = []
        for company in self:
            production_record_vals.append({
                'name':
                '%s Production Record Seq' % company.name,
                'code':
                'agri.production.record',
                'company_id':
                company.id,
                'prefix':
                'AG/PR/',
                'padding':
                6,
                'number_next':
                1,
                'number_increment':
                1
            })
        if production_record_vals:
            self.env['ir.sequence'].create(production_record_vals)

    def _create_calendar_periods(self):
        date_range_type_vals = []
        for company in self:
            date_range_type_vals += [{
                'name': 'Calendar Month',
                'allow_overlap': True,
                'company_id': company.id,
                'is_calendar_period': True,
            }, {
                'name': 'Calendar Week',
                'allow_overlap': True,
                'company_id': company.id,
                'is_calendar_period': True,
            }]
        if date_range_type_vals:
            self.env['date.range.type'].create(date_range_type_vals)

    def _create_seasons(self):
        date_range_type_vals = []
        for company in self:
            date_range_type_vals.append({
                'name': 'Season',
                'allow_overlap': True,
                'company_id': company.id,
                'is_season': True,
            })
        if date_range_type_vals:
            self.env['date.range.type'].create(date_range_type_vals)

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

    def _create_missing_calendar_periods(self):
        company_ids = self.env['res.company'].search([])
        company_has_calendar_periods = self.env['date.range.type'].search([
            ('is_calendar_period', '=', True)
        ]).mapped('company_id')
        company_todo = company_ids - company_has_calendar_periods
        company_todo._create_calendar_periods()

    def _create_missing_seasons(self):
        company_ids = self.env['res.company'].search([])
        company_has_season = self.env['date.range.type'].search([
            ('is_season', '=', True)
        ]).mapped('company_id')
        company_todo = company_ids - company_has_season
        company_todo._create_seasons()

    @api.model
    def create_missing_sequences(self):
        self._create_missing_activity_record_sequences()
        self._create_missing_production_record_sequences()

    @api.model
    def create_missing_date_range_types(self):
        self._create_missing_calendar_periods()
        self._create_missing_seasons()

    def _create_per_company_sequences(self):
        self.ensure_one()
        self._create_activity_record_sequence()
        self._create_production_record_sequence()

    def _create_per_company_date_range_types(self):
        self.ensure_one()
        self._create_calendar_periods()
        self._create_seasons()

    @api.model
    def create(self, vals):
        company = super(Company, self).create(vals)
        company.sudo()._create_per_company_sequences()
        company.sudo()._create_per_company_date_range_types()
        return company
