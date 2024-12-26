/** @odoo-module */
import { FormController } from "@web/views/form/form_controller";
import { patch } from "@web/core/utils/patch";
import { useSetupView } from "@web/views/view_hook";
patch(FormController.prototype, {
/* Patch FormController to restrict auto save in form views */
   setup(){
      super.setup(...arguments);
      this.beforeLeaveHook = false
      useSetupView({
          beforeLeave: () => this.beforeLeave(),
          beforeUnload: (ev) => this.beforeUnload(ev),
      });
   },
   async beforeLeave() {
   /* function will work before leave the form */
      if (this.model == 'gst.details') {
            if(this.model.root.isDirty && this.beforeLeaveHook == false){
              this.beforeLeaveHook = true
              this.model.root.discard();
        }
      }

   },
   beforeUnload: async (ev) => {
       ev.preventDefault();
   }
});
