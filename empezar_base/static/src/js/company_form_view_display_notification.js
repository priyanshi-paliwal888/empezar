/* @odoo-module */

import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { FormRenderer } from "@web/views/form/form_renderer";
import { _t } from "@web/core/l10n/translation";
import { useAutofocus, useService } from "@web/core/utils/hooks";
import { jsonrpc } from "@web/core/network/rpc_service";
import { onMounted } from "@odoo/owl";


patch(FormController.prototype, {
    setup() {
        super.setup(...arguments);
        this.notification = useService("notification");
    },
    // display notification while save the record in database.
    async onRecordSaved(record) {
        if (this.props.resModel != 'res.config.settings'
        && this.props.resModel != 'upload.inventory.wizard'
        && this.props.resModel != 'update.container.wizard'
        && this.props.resModel != 'change.password.wizard'
        && this.props.resModel != 'release.container.wizard'
        && this.props.resModel != 'hold.release.container.wizard'
        && this.props.resModel != 'booking.import.wizard'
        && this.props.resModel != 'unlink.container.wizard'
        && this.props.resModel != 'unlink.container.confirmation'
        && this.props.resModel != 'monthly.lock.wizard'
        && this.props.resModel != 'update.tariff.wizard'
        && this.props.resModel != 'shipping.line.confirmation.wizard'
        && this.props.resModel != 'edit.estimate.wizard'
        && this.props.resModel != 'update.allocation.wizard'
        && this.props.resModel != 'view.update.allocation.wizard'
        && this.props.resModel != 'e.invoice.wizard'
        && this.props.resModel != 'invoice.cancellation.wizard'
        && this.props.resModel != 'credit.note.invoice'
        && this.props.resModel != 'movement.and.inventory.reports'
        && this.props.resModel != 'edit.estimate.wizard'
        && this.props.resModel != 'shipping.line.confirmation.wizard'
        && this.props.resModel != 'credit.note.cancellation.wizard'
        && this.props.resModel != 'gst.details'){
            var context = record.evalContext.context;
            var isShippingView = context.is_shipping_view;
            var isCmsPartiesView = context.is_cms_parties_view;
            var isChargeProductView = context.is_charge_product_view;
            var isSealWizardView = context.is_seal_wizard_view
            var isLocationView = context.is_res_company_location_view
            var recordUpdated = !!record.evalContext.id;
            var message;

            if (isShippingView) {
                message = recordUpdated ? "Shipping Line updated successfully." : "Shipping Line saved successfully.";
            } else if (isCmsPartiesView) {
                message = recordUpdated ? "Party Details updated successfully." : "Party created successfully.";
            } else if (isChargeProductView) {
                message = recordUpdated ? "Charge updated successfully." : "Charge created successfully.";
            } else if (isSealWizardView) {
                return;
            } else if (isLocationView) {
                message = recordUpdated ? "Location updated successfully." : "Location saved successfully.";
            } else if (this.props.resModel == 'res.company'  && !isLocationView) {
                message = "Company setting updated successfully."
            } else if (this.props.resModel == 'res.groups') {
                message = recordUpdated ? "Role updated successfully." : "Role saved successfully.";
            }else if (this.props.resModel == 'vessel.booking') {
                message = recordUpdated ? "Vessel Booking updated successfully." : "Vessel Booking saved successfully.";
            } else if (this.props.resModel == 'move.in') {
                message = recordUpdated ? "Move In Entry updated successfully." : "Move In Entry created successfully";
            } else if (this.props.resModel == 'move.out') {
                message = recordUpdated ? "Move Out Entry updated successfully." : "Move Out Entry created successfully";
            } else if (this.props.resModel == 'repair.reports') {
                message = recordUpdated ? "Email Sent Successfully." : "Email Sent Successfully";
            }else if (this.props.resModel == 'delivery.order') {
                message = recordUpdated ? "Delivery Order updated successfully." : "Delivery Order saved successfully.";
            } else if (this.props.resModel == 'invoice.cancellation.wizard') {
                message = "Invoice cancelled successfully.";
            } else if (this.props.resModel == 'move.in.out.invoice') {
                message = recordUpdated ? "Invoice updated successfully." : "Invoice saved successfully.";
            } else if (this.props.resModel == 'pending.invoices') {
                message = "Invoice saved successfully.";
                location.reload();
            } else if (this.props.resModel == 'ir.rule' || this.props.resModel == 'ir.model.access') {
                message = "Permissions saved successfully.";
            } else if (this.props.resModel == 'repair.pending') {
                message = recordUpdated ? "Container added successfully." : "Container added successfully.";
            } else if (this.props.resModel == 'container.facilities') {
                const facilityTypeArray = this.props.fields.facility_type.selection;
                const facilityType = record.data.facility_type;
                let output = false;
                for (let i = 0; i < facilityTypeArray.length; i++) {
                if (facilityTypeArray[i][0] === facilityType) {
                    output = facilityTypeArray[i][1];
                    break;
                }
                }
                if (recordUpdated) {
                    message = `${output} Details updated successfully.`;
                } else {
                    message = `${output} Details created successfully.`;
                }
            }
            else {
                message = recordUpdated ? "updated successfully." : "created successfully.";
                this.getModelName(this.props.resModel, message);
                return;
            }

            this.notification.add(_t(message), {
                title: _t("Success"),
                type: "success",
            });
            return true;
        }

        if (this.props.resModel == 'change.password.wizard'){
            var message = 'Password Updated Successfully.'
            this.notification.add(_t(message), {
                title: _t("Success"),
                type: "success",
            });
            return true;
        }

        if (this.props.resModel == 'unlink.container.confirmation'){
            var message = 'The container number is unliked from the Vessel booking.'
            this.notification.add(_t(message), {
                title: _t("Success"),
                type: "success",
            });
            return true;
        }

        if (this.props.resModel == 'gst.details'){
            var message = 'GST No. updated successfully.'
            this.notification.add(_t(message), {
                title: _t("Success"),
                type: "success",
            });
            return true;
        }

        if (this.props.resModel == 'res.groups') {
            var context = record.evalContext.context;
            var recordUpdated = !!record.evalContext.id;
            var message;

            if (recordUpdated) {
                message = `Role updated successfully.`;
            } else {
                message = `Role saved successfully.`;
            }

            this.notification.add(_t(message), {
                title: _t("Success"),
                type: "success",
            });
            return true;
    }
        return true;
    },

    getModelName(activeModel, message) {
            var self = this;
            console.log(activeModel)
            const a = jsonrpc('/web/dataset/call_kw', {
            model: 'res.company',
            method: 'get_model_description',
            args: [activeModel],
            kwargs: {}
        }).then(function (result) {
            self.notification.add(_t("%s %s",result.model_name, message), {
                title: _t("Success"),
                type: "success",
                });
        })
        },

});

patch(FormRenderer.prototype, {

    setup(parent, model, renderer, params) {
        super.setup();
        var self = this;
        this.notification = useService("notification");
        $(document).off('click', '.get_gst_details');
        $(document).off('click', '.get_gst_details_for_parties');
        $(document).on('click', '#b2b_toggle_password', function (ev) { self._company_toggle_password(ev) });
        $(document).on('click', '.get_gst_details', function (ev) { self._get_gst_details(ev) });
        $(document).on('click', '.get_gst_details_for_parties', function (ev) { self._get_gst_details_for_parties(ev) });
        onMounted(this.onMounted);
    },
    onMounted() {
        this._checkAndDisableSubmitButton();
    },
    _company_toggle_password: function (ev) {

        $(ev.currentTarget).toggleClass("fa-eye fa-eye-slash");

        if ($(ev.currentTarget).parents('.client_secret').find('div[name="client_secret"] input').attr("type") == "password") {
            $(ev.currentTarget).parents('.client_secret').find('div[name="client_secret"] input').attr('type', 'text');
        }
        else {
            $(ev.currentTarget).parents('.client_secret').find('div[name="client_secret"] input').attr('type', 'password');
        }
        if ($(ev.currentTarget).parents('.client_secret').find('div[name="password"] input').attr("type") == "password") {
            $(ev.currentTarget).parents('.client_secret').find('div[name="password"] input').attr('type', 'text');
        }
        else {
            $(ev.currentTarget).parents('.client_secret').find('div[name="password"] input').attr('type', 'password');
        }
    },
    _get_gst_details: function (ev) {
        // Hide success message
        const successMessage = $('#success_message');
        if (successMessage) {
            $(successMessage).addClass('d-none');
        }
        const recordID = this.props.record.evalContext.id;
        var self = this;
        var gst_no = $('div[name="gst_no"] input').val();
        var company_id = this.props.record.data.company_id[0]
        if (typeof gst_no === 'undefined'){
            var gst_no = $('div[name="gst_no"] span').text();
        }
        // Call the Python method using Odoo's JSON-RPC framework
        jsonrpc('/web/dataset/call_kw', {
            model: 'gst.details',
            method: 'get_gst_data',
            args: [],
            kwargs: {'gst_no':gst_no,
                     'company_id': company_id,
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
                setData('div[name="status"] input', data.sts);
                setData('div[name="legal_name"] input', data.lgnm);

                // Convert the `data` object to a string for the char field
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

                    setData('div[name="place_of_business"] input', formattedAddress);
                    setData('div[name="state"] input', address.stcd);
                    setData('div[name="gst_pincode"] input', address.pncd);
                    setData('div[name="parties_add_line_1"] input', partiesAddress1);
                    setData('div[name="parties_add_line_2"] input', partiesAddress2);
                } else {
                    setData('div[name="place_of_business"] input', '');
                    setData('div[name="state"] input', '');
                    setData('div[name="gst_pincode"] input', '');
                    setData('div[name="parties_add_line_1"] input', '');
                    setData('div[name="parties_add_line_2"] input', '');
                }

                if (data.adadr && data.adadr[0]) {
                    const additionalAddress = data.adadr[0].addr;
                    const additionalFormattedAddress = [
                        additionalAddress.flno, additionalAddress.bno, additionalAddress.bnm,
                        additionalAddress.st, additionalAddress.loc, additionalAddress.stcd, additionalAddress.pncd
                    ].filter(part => part).join(" ");

                    setData('div[name="additional_place_of_business"] input', additionalFormattedAddress);
                    setData('div[name="nature_of_business"] input', data.adadr[0].ntr);
                } else {
                    setData('div[name="additional_place_of_business"] input', '');
                    setData('div[name="nature_of_business"] input', '');
                }

                // Show success message
                const successMessage = $('#success_message');
                if (successMessage) {
                    $(successMessage).removeClass('d-none');
                }

                // disable gst number field after getting response from api.
                var parentDiv = $('div[name="gst_no"]').parent().parent();
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
    _get_gst_details_for_parties: function (ev) {
        // Hide success message
        const successMessage = $('#success_message');
        if (successMessage) {
            $(successMessage).addClass('d-none');
        }
        const recordID = this.props.record.evalContext.id;
        var partner_id = null
        if (this.props.record.data && this.props.record.data.partner_id){
            var partner_id = this.props.record.data.partner_id[0];
        }
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
                     'record_id': recordID,
                     'partner_id': partner_id}
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

                // Convert the `data` object to a string for the char field
                const prettyDataString = JSON.stringify(data, null, 4);

                // Update gst_api_response field in the form
                setData('div[name="gst_api_response"] textarea', prettyDataString);
                setData('div[name="parties_gst_api_response"] textarea', prettyDataString);

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
    _checkAndDisableSubmitButton: function () {
        const recordID = this.props.record.evalContext.id;
        const submitButton = document.getElementById('submit_gst_info');
        if (!recordID && submitButton) {
            submitButton.setAttribute('disabled', 'true');
        } else if (submitButton) {
            submitButton.removeAttribute('disabled');
        }
    },
});
