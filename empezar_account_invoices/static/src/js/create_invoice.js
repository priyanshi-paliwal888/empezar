/** @odoo-module */
import { ListController } from "@web/views/list/list_controller";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { registry } from '@web/core/registry';
import { listView } from '@web/views/list/list_view';
import { jsonrpc } from "@web/core/network/rpc_service";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";
import { useState, onWillStart } from "@odoo/owl";

patch(ListController.prototype, {
    setup() {
        super.setup();
        var self = this;
        this.addNewInvoice =false;
       onWillStart(async () => {

        this.addNewInvoice = await this.user.hasGroup("empezar_base.group_add_new_invoice");

        });
        $(document).on("click", "#generate_invoices_records", function(e) {
            self.generate_invoices_records(e);
        });
        this.actionService = useService("action");
        this.dialogService = useService("dialog");
    },

    async generate_invoices_records() {
        const selectedRecords = await this.getSelectedResIds();
        if (selectedRecords.length > 0) {
            const recordsData = await this.fetchRecordsData(selectedRecords);
            if (this.validateSelectedRecords(recordsData)) {
                localStorage.setItem("billToPartyId", recordsData[0]["billed_to_party"][0])
                await this.openFormViewWithSelectedRecords(selectedRecords);
            } else {
                this.dialogService.add(ConfirmationDialog, {
                        title: _t("Validation Error"),
                        body: _t("Invoice cannot be created as the shipping line , billing party and location combination for all the selected records is not same"),
                    });
            }
        } else {
            console.log("No records found.");
        }
    },

    async fetchRecordsData(selectedRecordIds) {
        const records = await jsonrpc('/web/dataset/call_kw', {
            model: 'pending.invoices',
            method: 'read',
            args: [selectedRecordIds, ['shipping_line_id', 'location_id', 'billed_to_party']],
            kwargs: {}
        });
        return records;
    },

    validateSelectedRecords(records) {
        if (records.length === 0) return false;
        const shippingLineId = records[0].shipping_line_id[1];
        const locationId = records[0].location_id[1];
        const billedToParty = records[0].billed_to_party[1];
        const isValid = records.every(record =>
            record.shipping_line_id[1] === shippingLineId &&
            record.location_id[1] === locationId &&
            record.billed_to_party[1] === billedToParty
        );
        return isValid;
    },

    async openFormViewWithSelectedRecords(selectedRecordIds) {
        await this.actionService.doAction({
            name: "View Invoice",
            type: "ir.actions.act_window",
            res_model: "pending.invoices",
            views: [[false, 'form']],
            target: "new",
            context: {
                'default_selected_record_ids': selectedRecordIds,
            },
        });
    },
});

export class HelpButtonInvoice extends ListController {
   setup() {
       super.setup();
   }

  HelpButton() {
  var view_id = this.env.config.viewId;
  jsonrpc('/web/dataset/call_kw', {
        model: 'help.document',
        method: 'download_help_doc',
        args: [],
        kwargs: {'view_id': view_id}
    }).then(function (result) {
        if (result && result.type === 'ir.actions.act_url') {
            // Handle the action URL result
            console.log(result);
            window.open(result.url, '_blank'); // Open the URL in a new tab/window
        } else {
            // Handle other types of results or errors
            console.error('Unexpected result:', result);
        }
    }).catch(function (error) {
        // Handle JSON-RPC call error
        console.error('JSON-RPC error:', error);
    });
 }
}
export class HelpInvoice extends ListController {
   setup() {
       super.setup();
   }

  HelpButton() {
  var view_id = this.env.config.viewId;
  jsonrpc('/web/dataset/call_kw', {
        model: 'help.document',
        method: 'download_help_doc',
        args: [],
        kwargs: {'view_id': view_id}
    }).then(function (result) {
        if (result && result.type === 'ir.actions.act_url') {
            // Handle the action URL result
            console.log(result);
            window.open(result.url, '_blank'); // Open the URL in a new tab/window
        } else {
            // Handle other types of results or errors
            console.error('Unexpected result:', result);
        }
    }).catch(function (error) {
        // Handle JSON-RPC call error
        console.error('JSON-RPC error:', error);
    });
 }
}
export class MonthlyHelpButton extends ListController {
   setup() {
       super.setup();
   }

  HelpButton() {
  var view_id = this.env.config.viewId;
  jsonrpc('/web/dataset/call_kw', {
        model: 'help.document',
        method: 'download_help_doc',
        args: [],
        kwargs: {'view_id': view_id}
    }).then(function (result) {
        if (result && result.type === 'ir.actions.act_url') {
            // Handle the action URL result
            console.log(result);
            window.open(result.url, '_blank'); // Open the URL in a new tab/window
        } else {
            // Handle other types of results or errors
            console.error('Unexpected result:', result);
        }
    }).catch(function (error) {
        // Handle JSON-RPC call error
        console.error('JSON-RPC error:', error);
    });
 }
}

export class HelpCreditNote extends ListController {
    setup() {
        super.setup();
    }
 
   HelpButton() {
   var view_id = this.env.config.viewId;
   jsonrpc('/web/dataset/call_kw', {
         model: 'help.document',
         method: 'download_help_doc',
         args: [],
         kwargs: {'view_id': view_id}
     }).then(function (result) {
         if (result && result.type === 'ir.actions.act_url') {
             // Handle the action URL result
             console.log(result);
             window.open(result.url, '_blank'); // Open the URL in a new tab/window
         } else {
             // Handle other types of results or errors
             console.error('Unexpected result:', result);
         }
     }).catch(function (error) {
         // Handle JSON-RPC call error
         console.error('JSON-RPC error:', error);
     });
  }
 }


registry.category("views").add("invoice_help_button", {
   ...listView,
   Controller: HelpButtonInvoice,
   buttonTemplate: "invoice_help_button.ListView.Buttons",
});

registry.category("views").add("move_invoice_help_button", {
   ...listView,
   Controller: HelpInvoice,
   buttonTemplate: "move_invoice_help_button.ListView.Buttons",
});

registry.category("views").add("credit_note_help_button", {
    ...listView,
    Controller: HelpInvoice,
    buttonTemplate: "credit_note_help_button.ListView.Buttons",
 });
registry.category("views").add("monthly_lock_help_button", {
   ...listView,
   Controller: MonthlyHelpButton,
   buttonTemplate: "monthly_lock_help_button.ListView.Buttons",
});
