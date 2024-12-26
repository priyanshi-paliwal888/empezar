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
       this.canGenerateEDIMoveOut =false;
       onWillStart(async () => {

        this.canGenerateEDIMoveOut = await this.user.hasGroup("empezar_base.group_generate_edi_move_out");

        });
       $(document).off('click', '#generate_edi_records');
       $(document).on("click", "#generate_edi_records", function(e) { self.generate_move_out_edi_records(e); });
   },
    async generate_out_edi_records(){
       var self = this
       const selectedRecords = await this.getSelectedResIds();
       if (selectedRecords.length > 0) {
           // Call the 'send_list_view_rec_edis' method with selected record IDs
            const get_response = await this.orm.call(
                'edi.settings',
                'send_move_out_list_view_rec_edis',
                [selectedRecords]
            );
            if (get_response.error){
                return self.notification.add(
                    get_response.error,
                    { type: 'danger' }
                );
            }
            if (get_response.success){
                var message = 'Updated EDI email has been sent to location'
                return self.notification.add(
                    message,
                    { type: 'success' }
                );
            }
       } else {
            console.log("No Record Founds.");
       }
   },
   get generateOutEDIConfirmationDialog() {
        var self = this;
        let body = _t("Are you sure you want to generate EDI?");
        return {
           title: _t("Generate EDI"),
           body,
           confirmLabel: _t("Yes, Confirm"),
           confirm: () => self.generate_out_edi_records(), // Call the function here
           cancel: () => {},
           cancelLabel: _t("Cancel"),
       };
   },
   generate_move_out_edi_records: function(e) {
       var self = this;
       self.dialogService.add(ConfirmationDialog, self.generateOutEDIConfirmationDialog);
   }
});

export class HelpButtonMoveOut extends ListController {
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

registry.category("views").add("move_out_help_button", {
   ...listView,
   Controller: HelpButtonMoveOut,
   buttonTemplate: "move_out_help_button.ListView.Buttons",
});
