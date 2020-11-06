from odoo import api, SUPERUSER_ID, _
from odoo.exceptions import UserError


def uninstall_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {'force_delete': True})
    date_range_types = env['date.range.type'].search(
        ['|', ('is_calendar_period', '=', True), ('is_season', '=', True)])
    date_ranges = env['date.range'].search([('type_id', 'in',
                                             date_range_types.ids)])
    try:
        date_ranges.unlink()
        date_range_types.unlink()
    except Exception as e:
        raise UserError(
            _('Production Plans cannot be deleted though uninstalling this '
              'module.\n\nPlease manually delete all Production Plans before '
              'uninstalling module.'))
