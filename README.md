# PreachSelah

PreachSelah is a small Flask app with email accounts, Scripture-based sermon prompts, and a King James Version Bible reader.

## Run locally

1. Create and activate a virtual environment (optional but recommended).
2. Install dependencies: `pip install -r requirements.txt`
3. Start the app: `python app.py`
4. Visit [http://127.0.0.1:5000](http://127.0.0.1:5000), create an account with your email and password, and sign in.

## Publish on Render

The included `render.yaml` configures a Render web service with a persistent disk for account data, a generated session secret, secure session cookies, and a production WSGI server.

1. Push this project to a GitHub repository. The `.venv/` environment and `instance/` account database are excluded; do not upload local account data.
2. In Render, choose **New + → Blueprint**, connect the repository, and apply the `render.yaml` configuration.
3. Wait for the service to finish deploying, then open its `onrender.com` URL. The same URL works on laptops and phones.

The service uses a persistent disk, which may incur hosting charges. Keep the generated `PREACHSELAH_SECRET_KEY` private and do not replace it after users have signed in; changing it signs everyone out. A custom domain can be connected in the Render service settings.

## What’s inside

- An email sign-in and account creation screen as the first interface.
- Passwords stored as secure hashes in a local SQLite database (`instance/accounts.sqlite3`).
- A personalized welcome popup after registration or sign-in; the name is derived from the email address.
- A sign-out control and a dashboard protected behind sign-in.
- A topic finder with Scripture references, sermon hints, and possible outline threads.
- A full Bible reader with all 66 books and chapter navigation.

KJV chapters are loaded on demand from bible-api.com, so reading them requires an internet connection. Account creation does not send a verification email. Set the `PREACHSELAH_SECRET_KEY` environment variable to a long random value when deploying; without it, the app creates a temporary key for local development and existing sessions will expire when the app restarts. Custom topic ideas are sermon-planning prompts, not a substitute for reading and interpreting the full passage.
