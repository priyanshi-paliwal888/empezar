/* @odoo-module */

import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { jsonrpc } from "@web/core/network/rpc_service";
import { _t } from "@web/core/l10n/translation";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { useService } from "@web/core/utils/hooks";

patch(FormController.prototype, {
    setup() {
        super.setup(...arguments);
        this.notification = useService("notification");
        this.dialogService = useService("dialog"); 
        this.orm = useService("orm");
    },
    async fetchContainerLocation(containerNo) {
        const records = await jsonrpc('/web/dataset/call_kw', {
            model: 'container.inventory',
            method: 'search_read',
            args: [
                [['name', '=', containerNo]] // Domain: Search for records with matching container_no
            ],
            kwargs: {}
        });

        if (records.length > 0) {
            const locationId = records[0].location_id;
            if (locationId) {
                const locationName = locationId[1]; // The name of the location is in index 1
                return locationName; // Return the location name
            }
        }
        return null; // If no records found, return null
    },

    async onWillSaveRecord(record, changes) {

        if (this.props.resModel === 'repair.pending') {
            const containerNo = record.data.container_no;
            const currentCompanyId = record.data.location_id[0];

            const domain = [
                ['name', '=', containerNo],
                ['location_id', '!=', currentCompanyId]
            ];
            const inventoryRecords = await this.orm.call('container.inventory', 'search_count', [domain]);
            const locationName = await this.fetchContainerLocation(containerNo);
            if (inventoryRecords > 0) {
                // const otherLocationName = inventoryRecords[0].location_id;
                return new Promise((resolve) => {
                    this.dialogService.add(ConfirmationDialog, {
                        title: _t("Container Presence Confirmation"),
                        body: _t(`Container is present in the ${locationName} inventory. Do you still want to continue? Yes/No`),
                        confirm: () => {
                            resolve(true);  // Proceed with saving if "Yes" is selected
                        },
                        cancel: () => {
                            resolve(false); // Prevent save if "No" is selected
                        },
                        confirmLabel: _t("Yes"),
                        cancelLabel: _t("No"),
                    });
                });
            }
        }
        return super.onWillSaveRecord(record, changes); // Continue if not in 'repair.pending' model
    }
});
