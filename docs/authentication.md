# Authentication

Home Lab Manager includes optional user authentication to protect your data and settings from unauthorized access.

## How It Works

- **Auth is optional** — if no user account exists, the app runs without login (open access)
- **To enable auth** → navigate to `/login` and create your first admin account
- **After setup** → all pages require login, redirecting to `/login` if not authenticated
- **Session-based** — login persists via NiceGUI's user storage (browser cookie)

## Enabling Authentication

Authentication is disabled by default. To enable it:

1. Navigate to `http://your-server:8080/login`
2. Since no users exist, you'll see the **Create Admin Account** screen
3. Choose a username and password
4. Click "Create Account"

From this point forward, all pages require login. The app remains open (no login) until you explicitly create the first user.

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
