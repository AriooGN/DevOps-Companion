import requests
import json
import base64
import datetime
import os
import urllib.parse
class OutlookEmailSender:
    def __init__(self, access_token):
        self.access_token = access_token
        self.graph_url = 'https://graph.microsoft.com/v1.0'

    def send_mail(self, subject, body, to_recipients):
        """
        Create a draft email using a deep link.
        """
        encoded_subject = urllib.parse.quote(subject)
        encoded_body = urllib.parse.quote(body)
        try:
            # Construct the deep link URL
            deep_link_url = f"https://outlook.office.com/mail/deeplink/compose?subject={encoded_subject}&body={encoded_body}&to={','.join(to_recipients)}"

            print("Draft created successfully! Open the following link to view and send the draft:")
            print(deep_link_url)
            return deep_link_url
        except Exception as e:
            print(f"An error occurred: {e}")
            return f"An error occurred: {e}"

    def fetch_emails(self):
        url = f'{self.graph_url}/me/mailFolders/inbox/messages'
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        params = {
            '$filter': f'receivedDateTime ge {datetime.datetime.now() - datetime.timedelta(days=14)}',
            '$orderby': 'receivedDateTime DESC'
        }

        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                emails = response.json().get('value', [])
                for email in emails:
                    print(f"Subject: {email['subject']}, Received: {email['receivedDateTime']}")
                return emails
            else:
                print(f'Error fetching emails: {response.status_code} - {response.text}')
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
            return None

    def book_meeting(self, subject, start_time, end_time, attendees, location=None, body=None):
        """
        Book a meeting using Microsoft Graph API.
        """
        url = f'{self.graph_url}/me/events'
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

        # Construct the meeting details
        event = {
            "subject": subject,
            "start": {
                "dateTime": start_time,
                "timeZone": "UTC"
            },
            "end": {
                "dateTime": end_time,
                "timeZone": "UTC"
            },
            "attendees": [
                {
                    "emailAddress": {"address": attendee, "name": attendee.split('@')[0]},
                    "type": "required"
                } for attendee in attendees
            ],
            "location": {
                "displayName": location or "Online Meeting"
            },
            "body": {
                "contentType": "Text",
                "content": body or "Please join the meeting."
            }
        }

        try:
            response = requests.post(url, headers=headers, json=event)
            if response.status_code == 201:  # Created
                meeting = response.json()
                print("Meeting booked successfully!")
                print(f"Meeting ID: {meeting.get('id')}")
                return meeting
            else:
                print(f"Error booking meeting: {response.status_code} - {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
            return None
