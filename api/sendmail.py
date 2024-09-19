from decouple import config
from mailjet_rest import Client

def sendWelcomeEmail(user_name,recipient_email, user_lang='en'):
    api_key = config('MJ_APIKEY_PUBLIC')
    api_secret = config('MJ_APIKEY_PRIVATE')
    mailjet = Client(auth=(api_key, api_secret), version='v3.1')

    # Define the entire email content in different languages
    email_content = {
        'en': {
            'subject': 'Welcome to Habts Us!',
            'greeting': f'Hi {user_name},',  # Include the user's name
            'message': 'Thank you for signing up for Habts Us. We are excited to have you on board! Here’s what you can do next:',
            'steps': [
                'Track your habits and routines daily.',
                'Set reminders to stay consistent.',
                'Monitor your progress and celebrate your achievements.'
            ],
            'button_text': 'Get Started',
            'footer_message': 'If you have any questions, feel free to reply to this email.',
            'closing': 'Best regards,',
            'team': 'Habts Us Team',
        },
        'fr': {
            'subject': 'Bienvenue chez Habts Us!',
            'greeting': f'Bonjour {user_name},',  # Include the user's name
            'message': 'Merci de vous être inscrit à Habts Us. Nous sommes ravis de vous accueillir! Voici ce que vous pouvez faire ensuite:',
            'steps': [
                'Suivez vos habitudes et routines quotidiennement.',
                'Définissez des rappels pour rester cohérent.',
                'Surveillez vos progrès et célébrez vos réalisations.'
            ],
            'button_text': 'Commencer',
            'footer_message': 'Si vous avez des questions, n\'hésitez pas à répondre à cet e-mail.',
            'closing': 'Cordialement,',
            'team': 'L\'équipe Habts Us',
        },
        'de': {
            'subject': 'Willkommen bei Habts Us!',
            'greeting': f'Hallo {user_name},',  # Include the user's name
            'message': 'Vielen Dank, dass Sie sich bei Habts Us angemeldet haben. Wir freuen uns, Sie an Bord zu haben! Hier ist, was Sie als Nächstes tun können:',
            'steps': [
                'Verfolgen Sie täglich Ihre Gewohnheiten und Routinen.',
                'Setzen Sie Erinnerungen, um konsequent zu bleiben.',
                'Überwachen Sie Ihre Fortschritte und feiern Sie Ihre Erfolge.'
            ],
            'button_text': 'Loslegen',
            'footer_message': 'Wenn Sie Fragen haben, können Sie gerne auf diese E-Mail antworten.',
            'closing': 'Mit freundlichen Grüßen,',
            'team': 'Habts Us Team',
        }
    }

    # Fallback to English if the user's language is not supported
    email_data = email_content.get(user_lang, email_content['en'])

    # Prepare the email body with translation
    steps_html = ''.join([f'<li>{step}</li>' for step in email_data['steps']])

    data = {
        'Messages': [
            {
                "From": {
                    "Email": 'contact@habts.us',
                    "Name": "Habts Us"
                },
                "To": [
                    {
                        "Email": recipient_email,
                        "Name": recipient_email
                    }
                ],
                "Subject": email_data['subject'],
                "TextPart": f"{email_data['greeting']} {email_data['message']}",
                "HTMLPart": f"""
                    <div>
                        <p>{email_data['greeting']}</p>
                        <p>{email_data['message']}</p>
                        <ul>{steps_html}</ul>
                        <p style="text-align: center;">
                            <a href="https://habts.us/dashboard" style="display: inline-block; padding: 10px 20px; background-color: #b0a7f7; color: #fff; text-decoration: none; border-radius: 5px;">{email_data['button_text']}</a>
                        </p>
                        <p>{email_data['footer_message']}</p>
                        <p>{email_data['closing']}<br/>{email_data['team']}</p>
                        <div style="width: 100%; text-align: center; background-color:#EFEDFD">
                            <div style="display: inline-block; width: 70px;">
                                <img src="https://habts.us/output-onlinegiftools.gif" alt="Animated GIF" style="max-width: 100%; height: auto; margin: 0 auto;">
                            </div>
                        </div>
                    </div>
                """
            }
        ]
    }

    result = mailjet.send.create(data=data)
    return result.status_code



def sendPassReset(reset_link, recipient_email, user_name, user_lang='en'):
    api_key = config('MJ_APIKEY_PUBLIC')
    api_secret = config('MJ_APIKEY_PRIVATE')
    mailjet = Client(auth=(api_key, api_secret), version='v3.1')

    # Define the entire email content in different languages
    email_content = {
        'en': {
            'subject': 'Password Reset Request',
            'greeting': f'Hi {user_name},',  # Include the user's name
            'message': 'We received a request to reset your password. Please click the button below to reset your password:',
            'button_text': 'Reset Password',
            'alt_text': 'Or copy and paste the following link into your browser:',
            'footer_message': 'If you did not request this, you can safely ignore this email.',
            'closing': 'Best regards,',
            'team': 'Habts Us Team',
        },
        'fr': {
            'subject': 'Demande de réinitialisation de mot de passe',
            'greeting': f'Bonjour {user_name},',
            'message': 'Nous avons reçu une demande de réinitialisation de votre mot de passe. Veuillez cliquer sur le bouton ci-dessous pour réinitialiser votre mot de passe :',
            'button_text': 'Réinitialiser le mot de passe',
            'alt_text': 'Ou copiez et collez le lien suivant dans votre navigateur :',
            'footer_message': 'Si vous n\'avez pas demandé cela, vous pouvez ignorer cet e-mail en toute sécurité.',
            'closing': 'Cordialement,',
            'team': 'L\'équipe Habts Us',
        },
        'de': {
            'subject': 'Passwort-Zurücksetzungsanfrage',
            'greeting': f'Hallo {user_name},',
            'message': 'Wir haben eine Anfrage zum Zurücksetzen Ihres Passworts erhalten. Klicken Sie bitte auf die Schaltfläche unten, um Ihr Passwort zurückzusetzen:',
            'button_text': 'Passwort zurücksetzen',
            'alt_text': 'Oder kopieren und fügen Sie den folgenden Link in Ihren Browser ein:',
            'footer_message': 'Wenn Sie dies nicht angefordert haben, können Sie diese E-Mail ignorieren.',
            'closing': 'Mit freundlichen Grüßen,',
            'team': 'Habts Us Team',
        }
    }

    # Fallback to English if the user's language is not supported
    email_data = email_content.get(user_lang, email_content['en'])

    data = {
        'Messages': [
            {
                "From": {
                    "Email": 'contact@habts.us',
                    "Name": "Habts Us"
                },
                "To": [
                    {
                        "Email": recipient_email,
                        "Name": user_name  # Update with the user's name
                    }
                ],
                "Subject": email_data['subject'],
                "TextPart": f"{email_data['greeting']} {email_data['message']}",
                "HTMLPart": f"""
                    <div>
                        <p>{email_data['greeting']}</p>
                        <p>{email_data['message']}</p>
                        <p style="text-align: center;">
                            <a href="{reset_link}" style="display: inline-block; padding: 10px 20px; background-color: #b0a7f7; color: #fff; text-decoration: none; border-radius: 5px;">
                                {email_data['button_text']}
                            </a>
                        </p>
                        <p>{email_data['alt_text']}</p>
                        <p style="text-align: center;">{reset_link}</p>
                        <p>{email_data['footer_message']}</p>
                        <p>{email_data['closing']}<br/>{email_data['team']}</p>
                        <div style="width: 100%; text-align: center; background-color:#EFEDFD">
                            <div style="display: inline-block; width: 70px;">
                                <img src="https://habts.us/output-onlinegiftools.gif" alt="Animated GIF" style="max-width: 100%; height: auto; margin: 0 auto;">
                            </div>
                        </div>
                    </div>
                """
            }
        ]
    }

    result = mailjet.send.create(data=data)
    return result.status_code
