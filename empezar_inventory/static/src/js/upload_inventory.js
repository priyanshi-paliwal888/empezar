/** @odoo-module */
import { ListController } from "@web/views/list/list_controller";
import { registry } from '@web/core/registry';
import { listView } from '@web/views/list/list_view';
import { jsonrpc } from "@web/core/network/rpc_service";
import { patch } from '@web/core/utils/patch';
import { useState, onWillStart } from "@odoo/owl";

patch(ListController.prototype, {
   setup() {
       super.setup();
       var self = this
       this.canHoldButton =false;
       onWillStart(async () => {

        this.canHoldButton = await this.user.hasGroup("empezar_base.group_hold_container");

        });
       $(document).on("click", "#inventory_download_template",function(e){self.inventory_download_template_function(e)});
       $(document).on("click", "#upload_inventory",function(e){self.open_inventory_wizard(e)});
       $(document).on("click", "#update_container_status_tamplate",function(e){self.update_container_status_tamplate_function(e)});
       $(document).on("click", "#open_wizard_upload_container_status",function(e){self.open_upload_container_status_wizard(e)});
       $(document).on("click", "#update_hold_release_template",function(e){self.update_hold_release_template_function(e)});
       $(document).on("click", "#open_wizard_hold_release_containers",function(e){self.open_hold_release_containers_wizard(e)});
   
    },

   inventory_download_template_function() {
      const view_id = this.env.config.viewId;
      jsonrpc('/web/dataset/call_kw', {
            model: 'upload.inventory',
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
   open_inventory_wizard: function (e) {
      var self = this;
      return self.actionService.doAction({
           type: 'ir.actions.act_window',
           res_model: 'upload.inventory.wizard',
           name: 'Upload Inventory',
           view_mode: 'form',
           view_type: 'form',
           views: [[false, 'form']],
           target: 'new',
           res_id: false,
      });
  },

    update_container_status_tamplate_function() {
        const view_id = this.env.config.viewId;
        jsonrpc('/web/dataset/call_kw', {
            model: 'update.container.status',
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
    open_upload_container_status_wizard: function (e) {
        var self = this;
        return self.actionService.doAction({
            type: 'ir.actions.act_window',
            res_model: 'update.container.wizard',
            name: 'Upload Container Status ',
            view_mode: 'form',
            view_type: 'form',
            views: [[false, 'form']],
            target: 'new',
            res_id: false,
        });
    },

    update_hold_release_template_function() {
        const view_id = this.env.config.viewId;
        jsonrpc('/web/dataset/call_kw', {
            model: 'hold.release.containers',
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

    open_hold_release_containers_wizard: function (e) {
        var self = this;
        return self.actionService.doAction({
            type: 'ir.actions.act_window',
            res_model: 'hold.release.container.wizard',
            name: 'Hold/Release Containers',
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

registry.category("views").add("upload_inventory_help_button", {
   ...listView,
   Controller: HelpButtonLolo,
   buttonTemplate: "upload_inventory_help_button.ListView.Buttons",
});
