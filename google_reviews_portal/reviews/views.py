from django.shortcuts import redirect, render
from google_auth_oauthlib.flow import Flow
import google.oauth2.credentials
import os
from django.conf import settings
from googleapiclient.discovery import build
from django.shortcuts import render
from django.conf import settings
from django.contrib.auth.decorators import login_required

# Define OAuth flow for Google authentication
flow = Flow.from_client_secrets_file(
    'path_to_client_secret.json',  # Download this from Google Cloud Console
    scopes=['https://www.googleapis.com/auth/business.manage'],
    redirect_uri=settings.GOOGLE_REDIRECT_URI
)

# View for starting the login process
def login(request):
    authorization_url, state = flow.authorization_url(access_type='offline')
    request.session['state'] = state
    return redirect(authorization_url)

# View for handling the OAuth callback
def callback(request):
    flow.fetch_token(authorization_response=request.build_absolute_uri())
    credentials = flow.credentials
    request.session['credentials'] = credentials_to_dict(credentials)
    return redirect('reviews:dashboard')

def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }



@login_required
def dashboard(request):
    credentials = google.oauth2.credentials.Credentials(**request.session['credentials'])

    # Build the Google My Business API service
    service = build('mybusiness', 'v4', credentials=credentials)

    # Fetch reviews for the specified location
    reviews = service.accounts().locations().reviews().list(
        parent='accounts/account_id/locations/location_id'
    ).execute()

    return render(request, 'reviews/dashboard.html', {'reviews': reviews['reviews']})





from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def respond_to_review(request, review_id):
    if request.method == 'POST':
        response_data = json.loads(request.body)
        response_text = response_data.get('responseText')

        # Use Google My Business API to respond to the review
        credentials = google.oauth2.credentials.Credentials(**request.session['credentials'])
        service = build('mybusiness', 'v4', credentials=credentials)
        
        review = service.accounts().locations().reviews().updateReply(
            name=f"accounts/account_id/locations/location_id/reviews/{review_id}",
            body={"comment": response_text}
        ).execute()

        return JsonResponse({'status': 'success'})
