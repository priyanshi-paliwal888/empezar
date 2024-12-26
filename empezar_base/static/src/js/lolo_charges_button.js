/** @odoo-module */
import { ListController } from "@web/views/list/list_controller";
import { registry } from '@web/core/registry';
import { listView } from '@web/views/list/list_view';
import { jsonrpc } from "@web/core/network/rpc_service";
import { patch } from '@web/core/utils/patch';
import { useState, onWillStart } from "@odoo/owl";
import { useService, useBus } from "@web/core/utils/hooks";

patch(ListController.prototype, {
   setup() {
       super.setup();
       var self = this
       this.user = useService("user");
       this.canViewButton = false;
       onWillStart(async () => {

    this.canViewButton = await this.user.hasGroup("empezar_base.group_upload_lolo_charges");

    });
       $(document).on("click", "#download_template",function(e){self.download_template_function(e)});
       $(document).on("click", "#upload_lolo_charges",function(e){self.open_import_records_wizard(e)});
   },
   
   download_template_function() {
      const view_id = this.env.config.viewId;
      jsonrpc('/web/dataset/call_kw', {
            model: 'lolo.charge',
            method: 'download_xlsx_file',
            args: [],
            kwargs: {}
      }).then(function (result) {
            if (result && result.type === 'ir.actions.act_url') {
               window.open(result.url, '_blank'); // Open the URL in a new tab/window
            } else {
               console.error('Unexpected result:', result);
            }
      }).catch(function (error) {
            console.error('JSON-RPC error:', error);
      });
   },
   open_import_records_wizard: function (e) {
      var self = this;
      return self.actionService.doAction({
           type: 'ir.actions.act_window',
           res_model: 'bulk.import.wizard',
           name: 'Upload LOLO Charges',
           view_mode: 'form',
           view_type: 'form',
           views: [[false, 'form']],
           target: 'new',
           res_id: false,
      });
  },
});

export class HelpButtonLolo extends ListController {
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

registry.category("views").add("lolo_charge_help_button", {
   ...listView,
   Controller: HelpButtonLolo,
   buttonTemplate: "lolo_charge_help_button.ListView.Buttons",
});
