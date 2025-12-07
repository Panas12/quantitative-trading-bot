# Capital.com API Setup & Troubleshooting Guide

## Authentication Error: "error.invalid.details"

If you're seeing a **401 authentication error**, it's likely because:
1. The API key hasn't been generated yet from Capital.com dashboard
2. Two-Factor Authentication (2FA) isn't enabled (required before API key generation)
3. The API key or password is incorrect

---

## How to Generate Capital.com API Key

### Step 1: Enable Two-Factor Authentication (2FA)
**IMPORTANT**: You MUST enable 2FA before you can generate an API key.

1. Log in to your Capital.com account at https://capital.com
2. Go to **Settings** (gear icon)
3. Navigate to **Security** section
4. Enable **Two-Factor Authentication (2FA)**
   - Download an authenticator app (Google Authenticator, Authy, etc.)
   - Scan the QR code with your authenticator app
   - Enter the 6-digit code to verify
   - Save your backup codes in a secure location

### Step 2: Generate API Key
After 2FA is enabled:

1. Go to **Settings** in your Capital.com account
2. Click on **API Integrations** (or "API" section)
3. Click **"Generate new key"**
4. Fill in the form:
   - **Label**: Give it a name (e.g., "Trading Bot")
   - **Custom Password**: Create a strong password (this is NOT your account password)
   - **Validity**: Choose expiration (1 year default)
   - **2FA Code**: Enter the 6-digit code from your authenticator app
5. Click **Generate**
6. **IMPORTANT**: Copy the API key immediately - it will only be shown once!

### Step 3: Update Your .env File
Edit the `.env` file with the correct values:

```env
# The API key shown after generation (starts with letters/numbers)
CAPITAL_API_KEY=YOUR_ACTUAL_API_KEY_HERE

# The custom password you set during API key generation
CAPITAL_API_PASSWORD=YOUR_CUSTOM_PASSWORD_HERE

# Your Capital.com account email (for reference)
CAPITAL_EMAIL=panayiotischristofides@gmail.com

# Environment
CAPITAL_ENVIRONMENT=DEMO
```

---

## Testing the Connection

After updating the .env file, run:

```bash
python capital_com_api.py
```

Expected output:
```
Initialized Capital.com API in DEMO mode
Authenticating with Capital.com API...
✓ Authentication successful
Account ID: XXXXX
```

---

## Common Issues

### Issue 1: "API key not found in .env"
- **Solution**: Make sure `.env` file exists in the project root
- Verify the variable names match exactly: `CAPITAL_API_KEY` and `CAPITAL_API_PASSWORD`

### Issue 2: "401 - error.invalid.details"
- **Solution**: API key or password is incorrect
- Regenerate a new API key from Capital.com dashboard
- Copy the key carefully (no extra spaces)
- Ensure you're using the CUSTOM password, not your account password

### Issue 3: "Cannot generate API key"
- **Solution**: Enable 2FA first (see Step 1 above)
- Make sure your Capital.com account is verified

### Issue 4: "Session expired" during trading
- **Solution**: Normal behavior - sessions expire after 10 minutes of inactivity
- The API automatically creates a new session with the next request
- For long-running bots, implement periodic session refresh

---

## API Key Security Best Practices

✓ **DO**:
- Store API keys in `.env` file (gitignored automatically)
- Use DEMO environment for testing
- Set API key expiration (renew yearly)
- Use strong, unique custom passwords
- Keep 2FA backup codes secure

✗ **DON'T**:
- Never commit `.env` to version control
- Don't share API keys publicly
- Don't use your account password as the custom password
- Don't store keys in plain text outside `.env`

---

## Next Steps

Once authentication is working:

1. **Test with demo script**:
   ```bash
   python capital_com_api.py
   ```

2. **Run full integration example**:
   ```bash
   python broker_integration_example.py
   ```

3. **Integrate with your trading strategy**:
   - The API connector is ready to use in `capital_com_api.py`
   - Example: `from capital_com_api import CapitalComAPI`
   - See `broker_integration_example.py` for usage patterns

---

## TradingView Monitoring (Optional)

To monitor your bot's trades visually in TradingView:

1. Visit https://tradingview.capital.com
2. Log in with your Capital.com credentials
3. Your positions from the API will appear automatically
4. Use TradingView's charts for manual analysis while bot trades automatically

This is completely optional - the bot works independently of TradingView.
