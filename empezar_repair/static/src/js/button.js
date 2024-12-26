/** @odoo-module */
import { ListController } from "@web/views/list/list_controller";
import { registry } from '@web/core/registry';
import { listView } from '@web/views/list/list_view';
import { jsonrpc } from "@web/core/network/rpc_service";
import { patch } from '@web/core/utils/patch';

patch(ListController.prototype, {
   setup() {
       super.setup();
       var self = this
       $(document).on("click", "#tariff_download_template",function(e){self.tariff_download_template_function(e)});
       $(document).on("click", "#update_tariff",function(e){self.open_tariff_wizard(e)});
    },

   tariff_download_template_function() {
      const view_id = this.env.config.viewId;
      jsonrpc('/web/dataset/call_kw', {
            model: 'update.tariff',
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
   open_tariff_wizard: function (e) {
      var self = this;
      return self.actionService.doAction({
           type: 'ir.actions.act_window',
           res_model: 'update.tariff.wizard',
           name: 'Update Tariff',
           view_mode: 'form',
           view_type: 'form',
           views: [[false, 'form']],
           target: 'new',
           res_id: false,
      });
  },


});

export class HelpButton extends ListController {
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

registry.category("views").add("update_tariff_help_button", {
   ...listView,
   Controller: HelpButton,
   buttonTemplate: "update_tariff_help_button.ListView.Buttons",
});
