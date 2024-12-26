/** @odoo-module */
import { _t } from "@web/core/l10n/translation";
import {
    ConfirmationDialog,
} from "@web/core/confirmation_dialog/confirmation_dialog";
import { ListController } from "@web/views/list/list_controller";
import { patch } from '@web/core/utils/patch';
import { useService, useBus } from "@web/core/utils/hooks";
import { jsonrpc } from "@web/core/network/rpc_service";
import { registry } from '@web/core/registry';
import { listView } from '@web/views/list/list_view';
import { useState, onWillStart } from "@odoo/owl";


patch(ListController.prototype, {
   setup() {
       super.setup();
       this.dialogService = useService("dialog");
       var self = this;
       this.user = useService("user");
       this.canSeeButton = false;
       this.addNewButton =false;
       onWillStart(async () => {

    this.canSeeButton = await this.user.hasGroup("empezar_base.group_move_to_damage");
    this.addNewButton = await this.user.hasGroup("empezar_base.group_add_new_to_seal");

    });
   $(document).on("click", "#add_new_seal", function(e) { self.generate_seal_number_wizard(e); });
   $(document).on("click", "#move_to_damage_records", function(e) { self.move_to_damage_records(e); });
   },
   generate_seal_number_wizard: function(e) {
       var self = this;
       return self.actionService.doAction({
           type: 'ir.actions.act_window',
           res_model: 'seal.management.wizard',
           name: 'Add New Seal',
           view_mode: 'form',
           view_type: 'form',
           views: [[false, 'form']],
           target: 'new',
           res_id: false,
           context: { 'is_seal_wizard_view': true }
       });
   },
    async move_to_damage_records_1(){
       const selectedRecords = await this.getSelectedResIds();
       if (selectedRecords.length > 0) {
       jsonrpc("/web/dataset/call_kw/seal.management/write", {
                        model: 'seal.management',
                        method: 'write',
                        args: [selectedRecords, {rec_status: 'damaged'}],
                        kwargs: {},
                    });

       this.notification.add(_t("Seal Numbers are updated successfully"), {
                title: _t("Success"),
                type: "success",
            });
       } else {
            console.log("No Record Founds.")
       }
       window.location.reload();
   },
   get damageConfirmationDialog() {
        var self = this;
        let body = _t("Are you sure you want to move these records to damaged?");
        return {
           title: _t("Move to Damaged"),
           body,
           confirmLabel: _t("Yes, Confirm"),
           confirm: () => self.move_to_damage_records_1(), // Call the function here
           cancel: () => {},
           cancelLabel: _t("Cancel"),
       };
   },
   move_to_damage_records: function(e) {
       var self = this;
       self.dialogService.add(ConfirmationDialog, self.damageConfirmationDialog);
   }
});

export class HelpButtonSeals extends ListController {
   setup() {
       super.setup();
   }

  HelpButtonSeal() {
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

registry.category("views").add("seal_help_button", {
   ...listView,
   Controller: HelpButtonSeals,
   buttonTemplate: "seal_help_button.ListView.Buttons",
});
