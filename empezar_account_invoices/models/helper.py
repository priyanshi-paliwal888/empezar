""" -*- coding: utf-8 -*- """

import json
from datetime import date
import re
from odoo.exceptions import ValidationError


def calculate_gst_rate_value(charge_id, move_in_out_invoice):
    # Get GST rate names
    gst_rate = 0.0

    def extract_gst_percentage(rate):
        # Use a regular expression to extract the numeric part (handles both '1% IGST' and 'GST 18')
        match = re.search(r'(\d+\.?\d*)', rate)  # Extract numeric values
        if match:
            return float(match.group(1))  # Return the numeric value as a float
        return 0.0  # If no match, return 0 (fallback)

    if move_in_out_invoice.invoice_type == 'Others':
        other_charge_id = move_in_out_invoice.other_charge_id
        charge = move_in_out_invoice.env['product.template'].search([('id', '=', other_charge_id.id)], limit=1)
        if charge:
            gst_rate_names = charge.gst_rate.mapped('name')
            # Process each GST rate entry
            for rate in gst_rate_names:
                if 'IGST' in rate:
                    gst_rate += extract_gst_percentage(rate)
                elif 'CGST' in rate or 'SGST' in rate:
                    gst_rate += extract_gst_percentage(rate)
                else:
                    gst_rate += extract_gst_percentage(rate)
        else:
            raise ValidationError("Amount must be greater than 0. Please enter a valid amount.")
        return gst_rate
    else:
        charge = charge_id
        if charge:
            gst_rate_names = charge.charge_id.gst_rate.mapped('name')
            # Process each GST rate entry
            for rate in gst_rate_names:
                if 'IGST' in rate:
                    gst_rate += extract_gst_percentage(rate)
                elif 'CGST' in rate or 'SGST' in rate:
                    gst_rate += extract_gst_percentage(rate)
                else:
                    gst_rate += extract_gst_percentage(rate)
        else:
            pass
        return gst_rate

def prepare_generate_irn(move_in_out_invoice, location, charges, shipping_line_id, billed_party,
                         invoice_number, billed_to_gst_no):
    ItemList = []
    ValDtls = {
        "AssVal": 0,
        "CgstVal": 0,
        "SgstVal": 0,
        "IgstVal": 0,
        "TotInvVal": 0,
    }
    current_date = date.today()
    formatted_invoice_date = current_date.strftime("%d/%m/%Y")
    location_id = move_in_out_invoice.env['res.company'].search([('id', '=', location.id)], limit=1)
    billed_to_party = move_in_out_invoice.env['res.partner'].search([('id', '=', billed_party.id)], limit=1)
    billed_to_gst_no_id = move_in_out_invoice.env['gst.details'].search([('id', '=', billed_to_gst_no.id)], limit=1)

    if move_in_out_invoice.invoice_type == 'Others':
        other_charge_id = move_in_out_invoice.other_charge_id
        gst_breakup_cgst = 0
        gst_breakup_sgst = 0
        gst_breakup_igst = 0
        charge = move_in_out_invoice.env['product.template'].search([('id', '=', other_charge_id.id)], limit=1)
        gst_rate = calculate_gst_rate_value(charge, move_in_out_invoice)
        taxable_value = move_in_out_invoice.amount - (
                    gst_breakup_cgst + gst_breakup_sgst + gst_breakup_igst) if charge else 0.00
        # Calculate IGST using the taxable value and GST rate from the charge
        igst_amount = round(taxable_value * (gst_rate / 100)) if charge else 0.00
        total_item_value = round(
            move_in_out_invoice.amount + igst_amount + gst_breakup_cgst + gst_breakup_sgst, 2)
        total_item_value = f"{total_item_value:.2f}"
        igst_amount_final = f"{igst_amount:.2f}"
        ItemList.append({
            "SlNo": "1",
            "PrdDesc": charge.charge_name,
            "IsServc": "Y",
            "HsnCd": str(charge.hsn_code.code),
            "UnitPrice": move_in_out_invoice.amount,
            "TotAmt": move_in_out_invoice.amount,
            "AssAmt": move_in_out_invoice.amount,
            "GstRt": gst_rate,
            "IgstAmt": igst_amount,
            "CgstAmt": gst_breakup_cgst,
            "SgstAmt": gst_breakup_sgst,
            "TotItemVal": total_item_value,
        })

        ValDtls["AssVal"] = move_in_out_invoice.amount
        ValDtls["CgstVal"] = gst_breakup_cgst
        ValDtls["SgstVal"] = gst_breakup_sgst
        ValDtls["IgstVal"] = igst_amount
        ValDtls["TotInvVal"] = move_in_out_invoice.amount + igst_amount + gst_breakup_cgst + gst_breakup_sgst

    else:
        charge_ids = move_in_out_invoice.env['move.in.out.invoice.charge'].search(
            [('id', 'in', charges)])
        for index, charge in enumerate(charge_ids, start=1):
            gst_rate = calculate_gst_rate_value(charge, move_in_out_invoice)
            taxable_value = charge.total_amount - (
                    charge.gst_breakup_cgst + charge.gst_breakup_sgst + charge.gst_breakup_igst) if charge else 0.00

            # Calculate IGST using the taxable value and GST rate from the charge
            igst_amount = round(taxable_value * (gst_rate / 100)) if charge else 0.00
            total_item_value = round(
                charge.total_amount + igst_amount + charge.gst_breakup_cgst + charge.gst_breakup_sgst,
                2)
            total_item_value = f"{total_item_value:.2f}"
            igst_amount_final = f"{igst_amount:.2f}"
            ItemList.append({
                "SlNo": str(index),
                "PrdDesc": charge.charge_name,
                "IsServc": "Y",
                "HsnCd": str(charge.charge_id.hsn_code.code),
                "UnitPrice": charge.amount,
                "TotAmt": charge.total_amount,
                "AssAmt": charge.total_amount,
                "GstRt": gst_rate,
                "IgstAmt": igst_amount_final,
                "CgstAmt": charge.gst_breakup_cgst,
                "SgstAmt": charge.gst_breakup_sgst,
                "TotItemVal": total_item_value,
            })

            ValDtls["AssVal"] += charge.total_amount
            ValDtls["CgstVal"] += charge.gst_breakup_cgst
            ValDtls["SgstVal"] += charge.gst_breakup_sgst
            ValDtls["IgstVal"] += igst_amount
            ValDtls[
                "TotInvVal"] += charge.total_amount + igst_amount + charge.gst_breakup_cgst + charge.gst_breakup_sgst

    if billed_to_gst_no_id and billed_to_gst_no_id.nature_of_business == 'Special Economic Zone' and billed_to_gst_no_id.gst_rate:
        sub_type = 'SEZWP'
    elif billed_to_gst_no_id and billed_to_gst_no_id.nature_of_business == 'Special Economic Zone' and not billed_to_gst_no_id.gst_rate:
        sub_type = 'SEZWOP'
    else:
        sub_type = 'B2B'

    if location_id and shipping_line_id:
        matching_setting = location_id.invoice_setting_ids.filtered(
            lambda setting: setting.inv_shipping_line_id.id == shipping_line_id
        )
        lgname = f'{matching_setting.inv_applicable_at_location_ids.mapped("name")}{matching_setting.inv_shipping_line_id.name}'

    for key, val in ValDtls.items():
        ValDtls[key] = f"{val:.2f}"
    param = {
        "Version": "1.1",
        "TranDtls": {
            "TaxSch": "GST",
            "SupTyp": sub_type,
        },
        "DocDtls": {
            "Typ": "INV",
            "No": invoice_number,
            "Dt": formatted_invoice_date,
        },
        "SellerDtls": {
            "Gstin": matching_setting.gst_number,
            "LglNm": lgname,
            "Addr1": matching_setting.address_line_1,
            "Addr2": matching_setting.address_line_2,
            "Loc": matching_setting.city,
            "Pin": matching_setting.pincode,
            "Stcd": "29",  # state code with come here numberic code
        },
        "BuyerDtls": {
            "Gstin": "29AWGPV7107B1Z1", #billed_to_gst_no_id.gst_no, #29AWGPV7107B1Z1
            "LglNm": billed_to_party.party_name,
            "Addr1": billed_to_party.street,
            "Addr2": billed_to_party.street2,
            "Pos": "12",  # invoice supply to state code will come here
            "Loc": billed_to_party.gst_state,
            "Pin": billed_to_party.zip,
            "Stcd": "29",  # state code will come here
        },
        "ItemList": ItemList,
        "ValDtls": ValDtls,
        "PrecDocDtls": {
            "InvNo": invoice_number,
            "InvDt": formatted_invoice_date,
        },
    }
    return param

def e_invoice_integration(move_in_out_invoice):
    irn_data = prepare_generate_irn(move_in_out_invoice=move_in_out_invoice,location=move_in_out_invoice.location_id,
                                         charges=move_in_out_invoice.charge_ids.ids,
                                         shipping_line_id=move_in_out_invoice.shipping_line_id.id,
                                         billed_party=move_in_out_invoice.billed_to_party,
                                         invoice_number=move_in_out_invoice.invoice_number,
                                         billed_to_gst_no=move_in_out_invoice.billed_to_gst_no)
    try:
        try:
            api_response = move_in_out_invoice.authenticate_einvoice_api()

            # Check if the authentication response is successful
            if api_response and api_response['status_cd'] == 'Sucess':
                auth_token = api_response['data'].get('AuthToken')
                move_in_out_invoice.auth_token = auth_token
            else:
                error_messages = json.loads(api_response['status_desc'])

                # Prepare a structured output
                errors = []
                for error in error_messages:
                    errors.append(
                        f"ErrorCode: {error['ErrorCode']}, ErrorMessage: {error['ErrorMessage']}")

                # Join all error messages into a single string or store them in a field
                all_errors = "\n".join(errors)
                move_in_out_invoice.response_error = all_errors
        except Exception as e:
            # Handle any exception during IRN generation
            print(f"Error generating IRN: {e}")

        try:
            # Generate IRN (Invoice Reference Number)
            irn_data = move_in_out_invoice.generate_irn(auth_token, body_data=irn_data)

            if irn_data and irn_data['status_cd'] == '1':
                move_in_out_invoice.ack_date = irn_data['data'].get('AckDt')
                move_in_out_invoice.ack_number = irn_data['data'].get('AckNo')
                move_in_out_invoice.irn_no = irn_data['data'].get('Irn')
                move_in_out_invoice.jwt_string = irn_data['data'].get('SignedQRCode')
                generate_irn_response = json.dumps(irn_data, indent=8)
                move_in_out_invoice.generate_irn_response = generate_irn_response
                move_in_out_invoice.is_success = True
            else:
                error_messages = json.loads(irn_data['status_desc'])

                # Prepare a structured output
                errors = []
                for error in error_messages:
                    errors.append(
                        f"ErrorCode: {error['ErrorCode']}, ErrorMessage: {error['ErrorMessage']}")

                # Join all error messages into a single string or store them in a field
                all_errors = "\n".join(errors)
                move_in_out_invoice.response_error = all_errors

        except Exception as e:
            # Handle any exception during IRN generation
            print(f"Error generating IRN: {e}")
    except KeyError as e:
        # Handle missing keys in the response
        print(f"Error generating IRN: {e}")
