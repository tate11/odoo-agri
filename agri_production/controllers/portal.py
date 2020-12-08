from odoo import http, _
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import AccessError, MissingError
from odoo.http import request


class PortalProductionPlan(CustomerPortal):
    def _prepare_home_portal_values(self):
        values = super(PortalProductionPlan,
                       self)._prepare_home_portal_values()
        partner = request.env.user.partner_id

        ProductionPlan = request.env['agri.production.plan']
        plan_count = ProductionPlan.search_count([
            ('message_partner_ids', 'child_of',
             [partner.commercial_partner_id.id])
        ])
        values['plan_count'] = plan_count
        return values

    # ------------------------------------------------------------
    # My Production Plans
    # ------------------------------------------------------------

    def _plan_get_page_view_values(self, plan, access_token, **kwargs):
        values = {
            'page_name': 'plan',
            'plan': plan,
        }
        return self._get_page_view_values(plan, access_token, values,
                                          'my_plan_history', False, **kwargs)

    @http.route(['/my/plans', '/my/plans/page/<int:page>'],
                type='http',
                auth="user",
                website=True)
    def portal_my_plans(self,
                        page=1,
                        date_begin=None,
                        date_end=None,
                        sortby=None,
                        **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        ProductionPlan = request.env['agri.production.plan']
        domain = [('message_partner_ids', 'child_of',
                   [partner.commercial_partner_id.id])]

        searchbar_sortings = {
            'name': {
                'label': _('Name'),
                'order': 'name asc'
            },
            'season': {
                'label': _('Season'),
                'order': 'season_id asc'
            },
            'yield': {
                'label': _('Gross Yield'),
                'order': 'gross_yield asc'
            },
            'state': {
                'label': _('Status'),
                'order': 'state'
            },
        }
        # default sort by order
        if not sortby:
            sortby = 'name'
        order = searchbar_sortings[sortby]['order']

        archive_groups = self._get_archive_groups(
            'agri.production.plan',
            domain) if values.get('my_details') else []
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin),
                       ('create_date', '<=', date_end)]

        # count for pager
        plan_count = ProductionPlan.search_count(domain)
        # pager
        pager = portal_pager(url="/my/plans",
                             url_args={
                                 'date_begin': date_begin,
                                 'date_end': date_end,
                                 'sortby': sortby
                             },
                             total=plan_count,
                             page=page,
                             step=self._items_per_page)
        # content according to pager and archive selected
        plans = ProductionPlan.search(domain,
                                      order=order,
                                      limit=self._items_per_page,
                                      offset=pager['offset'])
        request.session['my_plans_history'] = plans.ids[:100]

        values.update({
            'date': date_begin,
            'plans': plans,
            'page_name': 'plan',
            'pager': pager,
            'archive_groups': archive_groups,
            'default_url': '/my/plans',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render("agri_production.portal_my_plans", values)

    @http.route(['/my/plans/<int:plan_id>'],
                type='http',
                auth="public",
                website=True)
    def portal_my_plans_detail(self,
                               plan_id,
                               access_token=None,
                               report_type=None,
                               download=False,
                               **kw):
        try:
            plan_sudo = self._document_check_access('agri.production.plan',
                                                    plan_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(
                model=plan_sudo,
                report_type=report_type,
                report_ref='agri_production.agri_production_plans',
                download=download)

        values = self._plan_get_page_view_values(plan_sudo, access_token, **kw)

        return request.render("agri_production.portal_plan_page", values)
