/* @odoo-module */

import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { FormRenderer } from "@web/views/form/form_renderer";
import { _t } from "@web/core/l10n/translation";
import { useAutofocus, useService } from "@web/core/utils/hooks";
import { jsonrpc } from "@web/core/network/rpc_service";

patch(FormRenderer.prototype, {

    setup(parent, model, renderer, params) {
        super.setup();
        var self = this;
        this.notification = useService("notification");
        $(document).off('click', '.billed_to_gst_details_for_parties');
        $(document).on('click', '.billed_to_gst_details_for_parties', function (ev) { self._billed_to_gst_details_for_parties(ev) });
    },

    _billed_to_gst_details_for_parties: function (ev) {
        // Hide success message
        const successMessage = $('#success_message');
        if (successMessage) {
            $(successMessage).addClass('d-none');
        }
        const recordID = this.props.record.evalContext.id;
        var self = this;
        var gst_no = $('div[name="gst_no"] input').val();
        if (typeof gst_no === 'undefined'){
            var gst_no = $('div[name="gst_no"] span').text();
        }
        // Call the Python method using Odoo's JSON-RPC framework
        jsonrpc('/web/dataset/call_kw', {
            model: 'gst.details',
            method: 'get_gst_data_for_parties',
            args: [],
            kwargs: {'gst_no':gst_no,
                     'record_id': recordID}
        }).then(function (result) {
            if (result.error) {
                self.notification.add(
                    result.error,
                    { type: 'danger' }
                );
               return;
            }
            if (result.data) {
                const setData = (selector, value) => {
                    const element = document.querySelector(selector);
                    if (element) {
                        element.value = value;
                    }
                };

                const { data } = result;

                setData('div[name="tax_payer_type"] input', data.dty);
                setData('div[name="state_jurisdiction"] input', data.stj);
                setData('div[name="last_update"] input', data.rgdt);
                setData('div[name="party_name"] input', data.lgnm);
                setData('div[name="nature_of_business"] input', data.nba);
                setData('div[name="l10n_in_pan"] input', gst_no.slice(2,12));
                const prettyDataString = JSON.stringify(data, null, 4);

                // Update gst_api_response field in the form
                setData('div[name="gst_api_response"] textarea', prettyDataString);


                if (data.pradr?.addr) {
                    const address = data.pradr.addr;
                    const formattedAddress = [
                        address.flno, address.bno, address.bnm,
                        address.st, address.loc, address.stcd, address.pncd
                    ].filter(part => part).join(" ");
                    const partiesAddress1 = [
                        address.flno, address.bno, address.bnm
                    ].filter(part => part).join(" ");
                    const partiesAddress2 = [
                        address.st, address.loc
                    ].filter(part => part).join(" ");

                    setData('div[name="gst_state"] input', address.stcd);
                    setData('div[name="zip"] input', address.pncd);
                    setData('div[name="street"] input', partiesAddress1);
                    setData('div[name="street2"] input', partiesAddress2);
                } else {
                    setData('div[name="gst_state"] input', '');
                    setData('div[name="zip"] input', '');
                    setData('div[name="street"] input', '');
                    setData('div[name="street2"] input', '');
                }

                if (data.adadr && data.adadr[0]) {
                    const additionalAddress = data.adadr[0].addr;
                    const additionalFormattedAddress = [
                        additionalAddress.flno, additionalAddress.bno, additionalAddress.bnm,
                        additionalAddress.st, additionalAddress.loc, additionalAddress.stcd, additionalAddress.pncd
                    ].filter(part => part).join(" ");

                    setData('div[name="additional_place_of_business"] input', additionalFormattedAddress);
                    setData('div[name="nature_additional_place_of_business"] input', data.adadr[0].ntr);
                } else {
                    setData('div[name="additional_place_of_business"] input', '');
                    setData('div[name="nature_additional_place_of_business"] input', '');
                }

                // Show success message
                const successMessage = $('#success_message');
                if (successMessage) {
                    $(successMessage).removeClass('d-none');
                }

                // disable gst number field after getting response from api.
                var parentDiv = $('div[name="gst_no"]').parent();
                if (parentDiv.length) {
                    parentDiv.css('pointer-events', 'none');
                }

                //enable submit button
                const submitButton = document.getElementById('submit_gst_info');
                if (submitButton) {
                    submitButton.removeAttribute('disabled');
                }
            }
        }).catch(function (error) {
            // Handle any errors
            self.notification.add(
                'Unexpected Error: ' + error,
                { type: 'danger' }
            );
            console.error("Error calling Python method:", error);
        });
    },
});
