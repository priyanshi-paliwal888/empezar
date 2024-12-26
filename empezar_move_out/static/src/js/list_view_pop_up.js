/** @odoo-module */
import { _t } from "@web/core/l10n/translation";
import {
    ConfirmationDialog,
} from "@web/core/confirmation_dialog/confirmation_dialog";
import { ListController } from "@web/views/list/list_controller";
import { patch } from '@web/core/utils/patch';
import { useService } from "@web/core/utils/hooks";

// Patch the ListController
patch(ListController.prototype, {
    setup() {
        super.setup();
        this.dialogService = useService("dialog");
        this.orm = useService("orm");
    },

    // Modify openRecord to wait for confirmation before proceeding
    async openRecord(record) {
        let confirmed = true;
        if (this.props.resModel === 'move.in')
        {
            confirmed = await this.open_list_confirmation_popup(record); // Wait for confirmation
        }
        else if (this.props.resModel === 'move.out'){
            confirmed = await this.open_move_out_list_confirmation_popup(record); // Wait for confirmation
        }
        else if (this.props.resModel === 'container.master'){
            confirmed = await this.open_container_master_confirmation_popup(record); // Wait for confirmation
        }

        if (confirmed) {
            return super.openRecord(record);
        }
        return;
    },

    // Helper function to show confirmation dialog
    showConfirmationDialog(title, body) {
        return new Promise((resolve) => {
            this.dialogService.add(ConfirmationDialog, {
                title: _t(title),
                body: _t(body),
                confirm: () => resolve(true),   // Confirmed: resolve with true
                confirmLabel: _t("Yes, Confirm"),
                cancel: () => resolve(false),   // Canceled: resolve with false
            });
        });
    },

    // Modify open_list_confirmation_popup to return a Promise
    async open_container_master_confirmation_popup(record)  {
            return this.showConfirmationDialog(
                "EDI Files Movement",
                "EDI files for daily movement would have been transmitted to the carrier already for this container. Click Confirm to proceed with editing this container."
            );
        return Promise.resolve(true);  // Default to proceed with edit
    },

    // Modify open_list_confirmation_popup to return a Promise
    async open_list_confirmation_popup(record)  {
        const resId = record.resId;
        const get_response = await this.orm.call('move.in', 'get_edit_popup_message', [resId]);

        if (!get_response) {
            return Promise.resolve(true);  // Continue if no popup is required
        }

        const { is_gate_pass_generated, is_edi_generated, is_damage_edi_generated } = get_response;

        // No gate pass and no EDI generated
        if (!is_gate_pass_generated && !is_edi_generated && !is_damage_edi_generated) {
            return Promise.resolve(true);  // No confirmation needed, proceed
        }

        // EDI or Damage EDI already generated but no gate pass
        if (!is_gate_pass_generated && (is_edi_generated || is_damage_edi_generated)) {
            return this.showConfirmationDialog(
                "EDI Already Sent",
                "EDI is already sent for this Move In Record. You will need to generate the EDI from the listing page. Click Confirm to proceed with the edit of Move In record."
            );
        }

        // Gate pass already generated but no EDI or Damage EDI
        if (is_gate_pass_generated && (!is_edi_generated && !is_damage_edi_generated)) {
            return this.showConfirmationDialog(
                "Gate Pass Already Generated",
                "Gate Pass is already generated for this Move In Record. You will need to regenerate the Gate Pass. Click Confirm to proceed with the edit of Move In record."
            );
        }

        // Gate pass and EDI both already generated
        if (is_gate_pass_generated && (is_edi_generated || is_damage_edi_generated)) {
            return this.showConfirmationDialog(
                "Gate Pass Generated & EDI Sent",
                "Gate Pass is already generated & EDI is sent for this Move In Record. You will need to regenerate the Gate Pass and resend the EDI. Click Confirm to proceed with the update."
            );
        }

        return Promise.resolve(true);  // Default to proceed with edit
    },

    // Modify open_list_confirmation_popup to return a Promise
    async open_move_out_list_confirmation_popup(record) {
        const resId = record.resId;
        const get_response = await this.orm.call('move.out', 'get_edit_move_out_popup_message', [resId]);

        if (!get_response) {
            return Promise.resolve(true);  // Continue if no popup is required
        }

        const { is_gate_pass_generated, is_edi_generated, is_repair_edi_generated } = get_response;

        // No gate pass and no EDI generated
        if (!is_gate_pass_generated && !is_edi_generated && !is_repair_edi_generated) {
            return Promise.resolve(true);  // No confirmation needed, proceed
        }

        // EDI or Damage EDI already generated but no gate pass
        if (!is_gate_pass_generated && (is_edi_generated || is_repair_edi_generated)) {
            return this.showConfirmationDialog(
                "EDI Already Sent",
                "EDI is already sent for this Move Out Record. You will need to generate the EDI from the listing page. Click Confirm to proceed with the edit of Move Out record."
            );
        }

        // Gate pass already generated but no EDI or Damage EDI
        if (is_gate_pass_generated && (!is_edi_generated && !is_repair_edi_generated)) {
            return this.showConfirmationDialog(
                "Gate Pass Already Generated",
                "Gate Pass is already generated for this Move Out Record. You will need to regenerate the Gate Pass. Click Confirm to proceed with the edit of Move Out record."
            );
        }

        // Gate pass and EDI both already generated
        if (is_gate_pass_generated && (is_edi_generated || is_repair_edi_generated)) {
            return this.showConfirmationDialog(
                "Gate Pass Generated & EDI Sent",
                "Gate Pass is already generated & EDI is sent for this Move Out Record. You will need to regenerate the Gate Pass and resend the EDI. Click Confirm to proceed with the update."
            );
        }

        return Promise.resolve(true);  // Default to proceed with edit
    }

});
