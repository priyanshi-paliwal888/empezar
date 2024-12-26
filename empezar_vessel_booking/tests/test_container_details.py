# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from odoo import fields


class TestContainerDetails(TransactionCase):

    def setUp(self):
        super().setUp()

        self.partner_shipping_line = self.env["res.partner"].create(
            {
                "name": "Shipping Line",
                "is_shipping_line": True,
            }
        )

        self.partner_transporter = self.env["res.partner"].create(
            {
                "name": "Transporter",
                "parties_type_ids": [(0, 0, {"name": "Transporter"})],
            }
        )

        self.location = self.env["res.company"].create(
            {
                "name": "Location",
            }
        )

        self.container_type = self.env["container.type.data"].create(
            {
                "name": "20 FT",
                "company_size_type_code": "20FT",
                "is_refer": "no",
                "active": True,
                "company_id": self.env.company.id,
            }
        )

        self.container_type_2 = self.env["container.type.data"].create(
            {
                "name": "30 FT",
                "company_size_type_code": "30FT",
                "is_refer": "no",
                "active": True,
                "company_id": self.env.company.id,
            }
        )

        self.container_type = self.env["container.type.data"].create(
            {
                "name": "20 FT",
                "company_size_type_code": "20FT",
                "is_refer": "no",
                "active": True,
                "company_id": self.env.company.id,
            }
        )

        self.container_detail = self.env["container.details"].create(
            {
                "container_size_type": self.container_type.id,
                "container_qty": 10,
                "balance": 5,
            }
        )
        self.booking = self.env["vessel.booking"].create(
            {
                "shipping_line_id": self.partner_shipping_line.id,
                "transporter_name": self.partner_transporter.id,
                "location": [(6, 0, [self.location.id])],
                "booking_no": "BOOK001",
                "booking_date": fields.Date.today(),
                "validity_datetime": fields.Datetime.now(),
                "cutoff_datetime": fields.Datetime.now(),
                "vessel": "Test Vessel",
                "voyage": "12345",
                "container_details": [(6, 0, [self.container_detail.id])],
            }
        )

    def test_unique_container_size_type(self):
        with self.assertRaises(ValidationError):
            self.env["container.details"].create(
                {
                    "booking_id": self.booking.id,
                    "container_size_type": self.container_type.id,
                    "container_qty": 10,
                    "balance": 5,
                }
            )
