import resend
resend.api_key = "re_DWH1yFN3_DLj37K7o7dx1AEcTxYUNLgbe"

def send_email(email, price, origin, destination):

    r = resend.Emails.send({
    "from": "SkyDeals <onboarding@resend.dev>",
    "to": [email],
    "subject": f"The lowest price for your flight, heading from {origin} to {destination} is: {price}",
    "html": "<p>Thanks for using <strong>✈️SkyDeals✈️</strong>, we wish you a safe and a happy flight!</p>"
    })
    return r