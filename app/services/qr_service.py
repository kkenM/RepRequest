from io import BytesIO

import qrcode
from flask import url_for

# Build the full web address stored inside a machine's QR Code
def machine_scan_url(machine):
    return url_for("scan.machine", public_id=machine.public_id, _external=True)

# Draws a machine QR Code and returns it as a PNG
def machine_qr_png(machine):
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(machine_scan_url(machine))
    qr.make(fit=True)

    buffer = BytesIO()
    qr.make_image(fill_color="black", back_color="white").save(buffer, format="PNG")
    return buffer.getvalue()