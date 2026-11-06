# Share the demo with a public link (free)

You'll get a permanent link like `https://small-shop-review-responder.streamlit.app` that anyone can open, even when your laptop is off.

**Keep the public link demo-only. Do not add API keys to it.** Anyone with the link could use your keys. Without keys, the app opens straight into Demo mode, which works fully.

---

## Step 1: Put the project on GitHub (about 5 min)

The project is already a git repository with everything committed. `.env` and your keys are excluded by `.gitignore`.

### Option A: with the GitHub CLI (fastest)

In Terminal:

```bash
cd ~/Desktop/CMU/HCI/small-shop-review-responder
gh auth login                    # only the first time; follow the prompts and choose GitHub.com, then HTTPS
gh repo create small-shop-review-responder --public --source=. --push
```

### Option B: in the browser

1. Go to <https://github.com/new>.
2. Repository name: `small-shop-review-responder`. Visibility: **Public**. Do **not** add a README, .gitignore or license, because the project already has them.
3. Click **Create repository**, then run the two commands GitHub shows under *"…or push an existing repository from the command line"*. They look like this:

```bash
cd ~/Desktop/CMU/HCI/small-shop-review-responder
git remote add origin https://github.com/YOUR-USERNAME/small-shop-review-responder.git
git push -u origin main
```

## Step 2: Deploy on Streamlit Community Cloud (about 5 min)

1. Go to <https://share.streamlit.io> and **Continue with GitHub**.
2. Click **Create app**, then choose **Deploy a public app from GitHub**.
3. Fill in:
   - **Repository:** `YOUR-USERNAME/small-shop-review-responder`
   - **Branch:** `main`
   - **Main file path:** `app.py`
   - **App URL:** choose a name, e.g. `small-shop-review-responder`
4. Open **Advanced settings**, set **Python version: 3.11**, and leave **Secrets empty**.
5. Click **Deploy**. The first build takes a few minutes.

Share the link it gives you: `https://<your-app-name>.streamlit.app`.

## Updating the live link later

Any change you push to GitHub redeploys the app automatically:

```bash
git add -A
git commit -m "Describe your change"
git push
```

## Good to know

- **The app sleeps.** If nobody opens it for a while, Streamlit puts it to sleep. The next visitor sees a "wake up" button and waits about 30 seconds. **Open the link yourself a few minutes before the pitch.**
- **Each visitor gets their own copy.** Drafts and approvals aren't shared between people, and they're cleared when the browser tab closes.
- **If you ever want live features on a private version,** add keys in Streamlit's **App settings → Secrets** like this, and share that app only with people you trust:

  ```toml
  GOOGLE_MAPS_API_KEY = "..."
  OPENAI_API_KEY = "..."
  OPENAI_MODEL = "gpt-5.4"
  ```
