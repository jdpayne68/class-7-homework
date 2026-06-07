# Task 8 — Test

Without Token --->

        curl https://<api>/prod/python 

 --> 401 Unauthorized

With Token -->  

        curl https://<api>/prod/python \
          -H "Authorization: <ACCESS_TOKEN>" 

→ 200 OK

    curl https://c7568gfesl.execute-api.us-west-2.amazonaws.com/prod/python \
          -H "Authorization: eyJraWQiOiJrMzcycEZ1RnFJZjNLVmhNWENUVzRMM1l0c2E2aWhmZG4yMWNwemVLNnVRPSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiIyODIxZjNiMC02MGQxLTcwMDYtNmI5Ny0xYmM3ZTFiNWIyOTYiLCJpc3MiOiJodHRwczovL2NvZ25pdG8taWRwLnVzLXdlc3QtMi5hbWF6b25hd3MuY29tL3VzLXdlc3QtMl92Z0tucjJScVAiLCJjbGllbnRfaWQiOiIycWdqamc1OXM1YW1zYzM5dG1ia2xmZmw5bSIsIm9yaWdpbl9qdGkiOiI1MzE3NjUyZS1kZDgxLTQ1M2MtOTM3MS0yNjU2MzA0OTAxNzQiLCJldmVudF9pZCI6ImQ5YzdjY2M1LTBhYjktNGEwZC1iMzU0LWRkZjFhODA2ZGQ1YyIsInRva2VuX3VzZSI6ImFjY2VzcyIsInNjb3BlIjoiYXdzLmNvZ25pdG8uc2lnbmluLnVzZXIuYWRtaW4iLCJhdXRoX3RpbWUiOjE3ODA2MzI1ODEsImV4cCI6MTc4MDYzNjE4MSwiaWF0IjoxNzgwNjMyNTgxLCJqdGkiOiI3YjM1YjJlNy03Y2JkLTQzOWQtYjg5Yi04ZTU4NDBkYTFkZjYiLCJ1c2VybmFtZSI6ImpwYWRtaW4ifQ.F-SxTOrFycCq6Yy8nJJG_QJqpIre-tiQJlO9r950HedV_5D8UAQPkk0s0lcWnBH_RZlgX_QF9Is4NOTuMtquy03S-QK-1ANJRS7r4C6Er4QAZELMs-eYB7qr31ju-vz9TqKCXz6ylSSFUWMyNdotZyiBiosYkJGSWVdVApDCxr68cOgSTQoFSVT9m3TUMRdg-1ZHiEIZTesy_2Gf1gDvWeRpreMObT4I84qCJf4H1cnuiGrMzMqQjdWeRsMZXNxsTdHjWdiU0KpzEss2EEBZnn9W1SbdTfwcpEg3iVw-GChfoWhhfICeBCZWZgTSdz3JFifd1tTc_O677YUsGatkZw" 
          

# Task 9 - Verify Behavior

1. Did Lambda run when no token? No
2. Where was request blocked? At the API gateway
3. What changed in event?

Final Explanation

    What Cognito does? 
    - Cognito verifies that the user is who they say they are
    
    What API Gateway does? 
    - The API Gateway, as per the name, gate keeps incoming traffic. It checks the incoming tracking for correction permissions before allowing it to pass through to the lambda.
    
    What MFA adds? 
    - MFA adds an additional layer of protection and requires an additional form verification (e.g. the code from Google Authenticator app).

    Why AccessToken matters?
    - Access tokens matter because they enforce user access rights. They limit what a user can do in app. They are also only valid for a limited amount of time which is in line with security best practices.
