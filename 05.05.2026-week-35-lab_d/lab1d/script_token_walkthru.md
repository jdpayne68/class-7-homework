Get your script here: https://github.com/BalericaAI/lambda/blob/main/lessond_cognito/python/easier_get_token.py

Or https://github.com/BalericaAI/lambda/blob/main/lessond_cognito/python/flavor_get_token.py

Then:

    python3 easier_get_token.py


Should look like this

    Username: student1
    Password:
    Enter MFA Code: 123456


Output

    ========== TOKENS ==========
    
    Access Token:
    eyJraWQiOiJ...
    
    ============================
    
Make sure that....

App Client: ---> NO CLIENT SECRET or...... SECRET_HASH required
