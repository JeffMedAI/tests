# Meta WhatsApp Business API — Setup Guide
**For:** Saeed (Avamed)  
**Purpose:** Get the API credentials needed to connect JeffLocal to WhatsApp  
**Time required:** 30–60 minutes  
**Cost:** Free (test tier) → ~£3–5/month for a real UK number  

---

## BEFORE YOU START — What you'll need

- [ ] A Facebook account (personal is fine — you'll create a business account)
- [ ] A phone number for WhatsApp Business (see options in Step 3)
- [ ] Access to that phone number to receive a verification SMS/call

---

## STEP 1 — Create a Meta Business Account

1. Go to: **https://business.facebook.com**
2. Click **"Create Account"**
3. Enter:
   - Business name: `Avamed` (or `Churchtown Medical Centre`)
   - Your name and email: 5256863@gmail.com
4. Verify your email address when prompted
5. Complete any identity verification Meta asks for

> ✅ You'll land on the Meta Business Suite dashboard.

---

## STEP 2 — Create a Meta Developer App

1. Go to: **https://developers.facebook.com**
2. Click **"My Apps"** (top right) → **"Create App"**
3. Select **"Business"** as the app type → click Next
4. Fill in:
   - **App name:** `JeffLocal WhatsApp`
   - **App contact email:** 5256863@gmail.com
   - **Business Account:** Select `Avamed` (from Step 1)
5. Click **"Create App"**

> ✅ You now have a developer app. You'll be taken to the app dashboard.

---

## STEP 3 — Add WhatsApp to Your App

1. On the app dashboard, find **"Add a product"**
2. Find **"WhatsApp"** and click **"Set Up"**
3. You'll be asked to link a WhatsApp Business Account (WABA):
   - Click **"Create a new WhatsApp Business Account"**
   - Name it: `Avamed JeffLocal`
   - Set timezone: `Europe/London`
   - Currency: `GBP`
4. Click **"Continue"**

> ✅ WhatsApp is now added to your app.

---

## STEP 4 — Add a Phone Number

You have two options:

### Option A — Use the Free Meta Test Number (fastest, for testing only)
Meta provides a free test number. Good for testing before you have a real number.
- On the WhatsApp setup page, look for **"From"** — there will be a test number pre-populated
- Note it down — this is your test Phone Number ID
- You can send test messages to up to 5 registered recipient numbers

### Option B — Register a Real UK Number (for pilot go-live)
You need a phone number that:
- Is **NOT** currently registered on personal WhatsApp (if it is, you must delete the personal account first — WhatsApp will prompt you)
- Is a valid UK mobile or landline

**Recommended:** Get a virtual UK mobile number (~£3–5/month):
- **Vonage (Nexmo):** https://www.vonage.co.uk/communications-apis/sms/
- **Twilio:** https://www.twilio.com/en-us/phone-numbers (search for UK numbers)
- **simwood / 46elks:** UK VoIP providers

Once you have the number:
1. On the WhatsApp Business setup page → click **"Add phone number"**
2. Enter the number → choose verification by SMS or call
3. Enter the code received

> ✅ Phone number registered. Note down the **Phone Number ID** shown on this page.

---

## STEP 5 — Get Your WhatsApp Business Account ID

1. In the Meta Developer console, go to **WhatsApp → Getting Started**
2. You'll see a panel with:
   - **Phone Number ID** — looks like: `123456789012345`
   - **WhatsApp Business Account ID** — looks like: `987654321098765`
3. Copy both of these

---

## STEP 6 — Generate a Permanent Access Token

The temporary test token expires. You need a permanent one.

1. Go to: **https://business.facebook.com/settings**
2. Left sidebar → **"System Users"**
3. Click **"Add"**
   - Name: `JeffLocal API`
   - Role: **Admin**
4. Click **"Generate New Token"**
   - Select your app: `JeffLocal WhatsApp`
   - Permissions to add:
     - `whatsapp_business_messaging` ✅
     - `whatsapp_business_management` ✅
5. Click **"Generate Token"** → **copy it immediately** (it won't be shown again)

> ✅ This is your permanent **Access Token**.

---

## STEP 7 — Choose Your Webhook Verify Token

This is a secret string YOU choose — it can be anything random. Meta uses it to verify that the webhook URL belongs to you.

Example (generate your own): `jefflocal_wa_verify_2026`

Just pick something and remember it — you'll give it to Claude and also enter it in the Meta console.

---

## STEP 8 — Send Everything to Claude

**Do NOT paste credentials in chat.** Instead, open a text file and note:

```
PHONE_NUMBER_ID     = [from Step 5]
WABA_ID             = [from Step 5]
ACCESS_TOKEN        = [from Step 6]  
WEBHOOK_VERIFY_TOKEN = [your choice from Step 7]
```

Then save this file as: `C:\JeffLocal\.env.whatsapp` (already in .gitignore)

Tell Claude: "I've saved the credentials to .env.whatsapp — please configure the system."

---

## STEP 9 — Configure the Webhook in Meta (Claude will tell you when to do this)

This step connects Meta to your server. You'll do this AFTER Claude has set up the endpoint.

1. Meta Developer console → **WhatsApp → Configuration** → **Webhook**
2. Click **"Edit"**
3. Enter:
   - **Callback URL:** `https://dashboard.app-avamed.uk/webhook/whatsapp`
   - **Verify token:** (same as Step 7)
4. Click **"Verify and Save"**
5. Under **"Webhook fields"** → subscribe to: `messages` ✅
6. Click **"Done"**

> ✅ Meta will now send all incoming WhatsApp messages to JeffLocal.

---

## ESTIMATED TIMELINE

| Step | Time | Who |
|------|------|-----|
| Steps 1–3 (account + app) | 15 min | Saeed |
| Step 4 (phone number) | 10–20 min | Saeed |
| Steps 5–7 (IDs + token) | 10 min | Saeed |
| Save .env.whatsapp file | 5 min | Saeed |
| Claude configures everything | 30 min | Claude |
| Step 9 (webhook config) | 5 min | Saeed |
| End-to-end test | 15 min | Together |

**Total: ~90 minutes across 2 sessions**

---

## TROUBLESHOOTING

**"Phone number already on WhatsApp"**  
You must delete the personal WhatsApp account on that number first. Open WhatsApp on that phone → Settings → Account → Delete My Account. Then try again.

**"App review required"**  
For testing, you don't need app review. For sending messages to numbers outside your test list, you'll need to submit for review. For the pilot, the 5-number test limit is sufficient to start.

**"Webhook verification failed"**  
Check that the Verify Token you entered in Meta matches exactly what's in your `.env.whatsapp` file. Claude will confirm the endpoint is live before you do Step 9.

---

*Document: Meta_WhatsApp_Setup_Guide.md | Created: 2026-06-02 | Avamed JeffLocal*
