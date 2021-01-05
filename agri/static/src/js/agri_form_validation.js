odoo.define('agri.AgriFormValidation', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');

    publicWidget.registry.AgriFormValidation = publicWidget.Widget.extend({
        selector: '.o_form_needs_validation',
        events: {
            'click .o_form_submit': '_onSubmit',
        },
        /**
         * @private
         * @param {MouseEvent} ev
         */
        _onSubmit: function (ev) {
            _.each(this.$target, function (target) {
                if (target.checkValidity && !target.checkValidity()) {
                    ev.preventDefault();
                    ev.stopPropagation();
                }
    
                target.classList.add('was-validated');
            })
        },
    })
})    