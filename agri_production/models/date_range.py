from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class DateRange(models.Model):
    _inherit = "date.range"

    calendar_period_ids = fields.Many2many('date.range',
                                           'date_range_calendar_period_rel',
                                           'date_range_id',
                                           'calendar_period_id',
                                           string='Calendar Periods',
                                           readonly=True)

    def _get_calendar_month_ids(self):
        DateRange = self.env['date.range']
        DateRangeType = self.env['date.range.type']
        ids = []
        month_start = date(self.date_start.year, self.date_start.month, 1)
        date_range_type = DateRangeType.search(
            [('is_calendar_period', '=', True),
             ('name', '=', 'Calendar Month')],
            limit=1)
        if date_range_type:
            while month_start < self.date_end:
                date_range = DateRange.search([
                    ('company_id', '=', self.company_id.id),
                    ('date_start', '=', month_start.strftime('%Y-%m-%d')),
                    ('type_id', '=', date_range_type.id)
                ])
                if not date_range:
                    date_range = DateRange.create({
                        'name':
                        month_start.strftime('%b %Y'),
                        'company_id':
                        self.company_id.id,
                        'date_start':
                        month_start,
                        'date_end':
                        month_start + relativedelta(months=1),
                        'type_id':
                        date_range_type.id
                    })
                ids.append(date_range.id)
                month_start = month_start + relativedelta(months=1)
        return ids

    def _get_calendar_week_ids(self):
        DateRange = self.env['date.range']
        DateRangeType = self.env['date.range.type']
        ids = []
        isocalendar = self.date_start.isocalendar()
        week_start = self.date_start - relativedelta(days=isocalendar[2] - 1)
        date_range_type = DateRangeType.search(
            [('is_calendar_period', '=', True),
             ('name', '=', 'Calendar Week')],
            limit=1)
        if date_range_type:
            while week_start < self.date_end:
                date_range = DateRange.search([
                    ('company_id', '=', self.company_id.id),
                    ('date_start', '=', week_start.strftime('%Y-%m-%d')),
                    ('type_id', '=', date_range_type.id)
                ])
                if not date_range:
                    date_range = DateRange.create({
                        'name':
                        week_start.strftime('CW %U'),
                        'company_id':
                        self.company_id.id,
                        'date_start':
                        week_start,
                        'date_end':
                        week_start + relativedelta(weeks=1),
                        'type_id':
                        date_range_type.id
                    })
                ids.append(date_range.id)
                week_start = week_start + relativedelta(weeks=1)
        return ids

    def _update_calendar_period_ids(self):
        for date_range in self:
            if date_range.type_id.is_season:
                calendar_period_ids = []
                calendar_period_ids += date_range._get_calendar_month_ids()
                calendar_period_ids += date_range._get_calendar_week_ids()
                date_range.write(
                    {'calendar_period_ids': [(6, 0, calendar_period_ids)]})

    @api.model
    def create(self, vals):
        date_range = super(DateRange, self).create(vals)
        date_range._update_calendar_period_ids()
        return date_range

    def write(self, vals):
        res = super(DateRange, self).write(vals)
        if 'date_start' in vals or 'date_end' in vals:
            date_range = self.browse(self.id)
            date_range._update_calendar_period_ids()
        return res
