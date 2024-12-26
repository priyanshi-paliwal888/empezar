/** @odoo-module */
import { ListController } from "@web/views/list/list_controller";
import { registry } from '@web/core/registry';
import { listView } from '@web/views/list/list_view';
import { jsonrpc } from "@web/core/network/rpc_service";
import { patch } from '@web/core/utils/patch';

export class HelpButtonGroups extends ListController {
   setup() {
       super.setup();
   }

   HelpButtonGroups() {
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

registry.category("views").add("res_groups_help_button", {
   ...listView,
   Controller: HelpButtonGroups,
   buttonTemplate: "res_groups_help_button.ListView.Buttons",
});



