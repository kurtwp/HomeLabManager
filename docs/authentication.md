# Authentication

Home Lab Manager includes optional user authentication to protect your data and settings from unauthorized access.

## How It Works

- **Auth is optional** — if no user account exists, the app runs without login (open access)
- **First visit with no users** → you're prompted to create an admin account (one-time setup)
- **After setup** → all pages require login, redirecting to `/login` if not authenticated
- **Session-based** — login persists via NiceGUI's user storage (browser cookie)

## First-Time Setup

On first launch (or after a fresh install), visiting any page shows the **Create Admin Account** screen:

1. Choose a username (defaults to "admin")
2. Set a password (minimum 4 characters)
3. Confirm the password
4. Click "Create Account"

You're automatically logged in after setup.

## Logging In

After setup, visiting any page while not authenticated redirects to `/login`:

1. Enter your username and password
2. Press Enter or click "Sign In"
3. You're redirected to the Dashboard

## Logging Out

Click the **logout icon** (→) in the top-right corner of the navigation bar. You'll be redirected to the login page.

## Changing Your Password

1. Go to Tools → Settings (`/settings`)
2. Scroll to the **Change Password** section at the bottom
3. Enter your current password, new password, and confirm
4. Click "Change Password"

## Roles

Two roles are supported:

| Role | Access |
|------|--------|
| admin | Full access — all pages, settings, data modification |
| viewer | (Future) Read-only access — view data but can't modify |

Currently only admin role is implemented. Viewer role is reserved for future use.

## Security Details

- Passwords are hashed with SHA-256 + random salt (never stored in plain text)
- Sessions are stored in NiceGUI's encrypted user storage
- The login page does not reveal whether a username exists (generic error message)
- No rate limiting on login attempts (home lab context — not exposed to internet)

## Disabling Authentication

To disable auth and go back to open access:

```bash
# Connect to your database and delete all users
sqlite3 /opt/HomeLabManager/home_lab_manager.db "DELETE FROM users;"
```

Or from the app: if you have access, you could run this via a Python script. With no users in the database, auth is automatically disabled.

## Tips

- Set up auth if your app is accessible beyond your immediate workstation
- The logout button shows your username in its tooltip
- If you forget your password, delete the users table in SQLite and create a new account
- Auth protects the UI only — there's no REST API to secure separately
