from odoo import models, fields, api, _
from odoo.exceptions import UserError


class DateRangeType(models.Model):
    _inherit = "date.range.type"

    is_calendar_period = fields.Boolean(string='Is Calendar Period',
                                        default=False)
    is_season = fields.Boolean(string='Is Season', default=False)

    def unlink(self):
        for rec in self:
            if (rec.is_calendar_period or
                    rec.is_season) and not self._context.get('force_delete'):
                raise UserError(
                    _('You cannot delete a date range type with '
                      'flag "is_calendar_period" or "is_season"'))
        return super(DateRangeType, self).unlink()
