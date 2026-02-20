# Setup Guide -- The Launchpad Incubator Coaching System

You are about to set up a personal AI coaching system that will transform how you support your program members. Once this guide is complete, you will have a fully operational system that sends personalized check-in emails to your members, reads their replies, generates coaching responses in your voice using OpenAI GPT-4o or Anthropic Claude (your choice of AI provider), and lets you review and approve everything from a clean web dashboard -- all running on autopilot.

This is a one-time setup. Once everything is in place, the system runs itself. Your daily involvement is simply reviewing and approving coaching responses from your dashboard.

The system uses five services that work together seamlessly:

- **OpenAI GPT-4o** -- the default AI engine that generates coaching responses grounded in your program content. Even when using Claude as the primary AI provider, OpenAI is still used for embeddings (vector search) and response evaluation.
- **Anthropic Claude** *(optional)* -- an alternative AI provider for generating coaching responses. If you prefer Claude's coaching style, you can select it as the primary provider in Settings. Requires an Anthropic API key.
- **Gmail (IMAP/SMTP)** -- sends and receives all coaching emails through your existing email address
- **Supabase (PostgreSQL)** -- the database that stores users, conversations, settings, and the AI's learning history
- **Streamlit** -- provides the web dashboard where you manage users, review responses, and monitor the system
- **GitHub Actions** -- runs automated workflows on a schedule so the system operates 24/7 without your intervention

**Total setup time:** approximately 60--90 minutes if you follow every step carefully. You only do this once.

---

## Prerequisites

Before you begin, make sure you have:

- **A Google account** -- either an existing Gmail address or a Google Workspace account. This will be the "from" address on all coaching emails (for example, `coachwes@thelaunchpadincubator.com` or `yourname@gmail.com`).
- **A GitHub account** -- free tier is fine. GitHub Actions provides 2,000 free minutes per month, which is more than enough for the coaching system.
- **A credit card** -- needed for OpenAI billing. Typical usage costs $5--20 per month depending on how many members you have. You will set a spending cap so there are no surprises.
- **Your program content files** -- lectures, book chapters, or other educational materials in PDF or text format. These get uploaded to OpenAI so the AI can reference specific content when crafting coaching responses. This is what makes the coaching contextual to your curriculum rather than generic.
- **A modern web browser** -- Chrome, Firefox, Safari, or Edge all work.

You do **not** need to install Python, Node.js, or any programming tools if you use Streamlit Community Cloud for the dashboard (recommended). If you prefer to run the dashboard locally, you will need Python 3.9 or newer.

---

## Part 1: OpenAI Setup

OpenAI provides the AI engine that powers everything. GPT-4o generates your coaching responses, drawing from your uploaded program content to give advice that is specific to your curriculum -- not generic business platitudes. You need three things from OpenAI: an API key, a funded account, and a vector store containing your program materials.

### Step 1.1: Create an OpenAI Account

1. Open your browser and go to **https://platform.openai.com**
2. Click **"Sign up"** in the top-right corner of the page
3. You can sign up with your email address, or use "Continue with Google," "Continue with Microsoft," or "Continue with Apple"
4. If you use email, you will need to verify your email address -- check your inbox for a verification link and click it
5. Complete the registration form with your name and organization name (your program name works fine here)
6. Once registered, you will land on the OpenAI Platform dashboard -- this is your control center for managing API keys, billing, and uploaded content

### Step 1.2: Add Billing and Set a Spending Limit

The coaching system uses the OpenAI API, which is pay-per-use. You need to add a payment method before the API will work. The cost is very low -- a typical coaching exchange costs about $0.01--0.05 in API usage, so even a busy program with dozens of members rarely exceeds $20 per month.

1. Go to **https://platform.openai.com/settings/organization/billing/overview**
   - Or from the dashboard: click your **profile icon** (top right) -> **"Settings"** -> **"Billing"** in the left sidebar
2. Click **"Add payment details"**
3. Choose **"Individual"** or **"Company"** depending on your situation
4. Enter your credit card number, expiration date, and billing address
5. Click **"Continue"**
6. **Set a usage limit** (this is important for peace of mind):
   - On the billing page, look for **"Usage limits"**
   - Set your **monthly budget** to **$20** to start. This is more than enough for most programs. You can always increase it later if needed.
   - You can also set a **notification threshold** (for example, $15) so you get an email before hitting the cap
7. Click **"Save"**

### Step 1.3: Generate Your API Key

The API key is what allows the coaching system to communicate with OpenAI. Think of it as a secure password that connects your system to the AI. Treat it like a password -- do not share it publicly or include it in any files that others can see.

1. Go to **https://platform.openai.com/api-keys**
   - Or from the dashboard: click **"API keys"** in the left sidebar
2. Click **"+ Create new secret key"**
3. In the dialog that appears:
   - **Name:** Enter `Coaching System` (this is just a label for your reference)
   - **Project:** Leave as "Default project" unless you have a reason to change it
   - **Permissions:** Select **"All"** (the system needs to create assistants, use chat completions, and access vector stores)
4. Click **"Create secret key"**
5. **CRITICAL:** A dialog will appear showing your key. It starts with `sk-proj-...`. **Copy it immediately and save it somewhere safe.** You will never be able to see this key again after closing the dialog. A password manager (like 1Password, Bitwarden, or Apple Keychain) is the ideal place to store it.
6. You will need this key in several places later during setup.

If you accidentally close the dialog without copying the key, do not worry -- just delete that key and create a new one. No harm done.

### Step 1.4: Create a Vector Store for Your Program Content

This is what makes the coaching truly yours. A vector store is where you upload your program materials -- lectures, book chapters, frameworks, worksheets -- so the AI can search through them when crafting coaching responses. Instead of giving generic advice, the AI will reference your specific content: "Lecture 7 walks through exactly this" or "Chapter 3 of the Launch System has a great framework for this."

1. Go to **https://platform.openai.com/storage/vector_stores**
   - Or from the dashboard: click **"Storage"** in the left sidebar, then **"Vector stores"**
2. Click **"+ Create"** in the top-right area
3. In the creation form:
   - **Name:** Enter `Coaching Program Content` (or any descriptive name you prefer)
4. Click **"Create"**
5. You will now see your empty vector store. Click **"+ Add files"** (or drag and drop files directly into the window)
6. Upload your program materials:
   - **Supported formats:** PDF, TXT, DOCX, MD, and others
   - Upload lecture transcripts, book chapters, course outlines, key frameworks -- anything you want the AI to be able to reference when coaching your members
   - You can upload multiple files at once
   - Each file will be processed and indexed (this may take a minute or two per file -- you will see a progress indicator)
   - **Tip:** The more content you upload, the richer and more specific the AI's coaching references will be. Do not hold back -- upload everything relevant.
7. After uploading, look at the top of the page for the **Vector Store ID**. It looks like `vs_` followed by a long string of letters and numbers (for example, `vs_6985fa853f84819196e012018b0defca`). **Copy this ID** and save it alongside your API key.

You can always come back later to add more files, remove files, or create additional vector stores. As your program evolves and you create new content, just upload it here and the AI will start referencing it immediately.

**Note on AI providers and knowledge storage:** The OpenAI vector store described above is used when OpenAI is selected as your AI provider (the default). When Claude is selected as the AI provider, the system uses a **local knowledge base** stored directly in your Supabase database instead. This local knowledge base is set up automatically when you run the database migrations (specifically `migration_v5.sql` in Step 3.4) -- there is no extra configuration required. To populate it with your program content, you run a one-time ingestion script (`scripts/ingest_knowledge_base.py`) that chunks your materials and stores them as searchable embeddings. You can also manage the knowledge base from the **Knowledge Base** page in the dashboard. Either way -- OpenAI vector store or local knowledge base -- the AI references your specific program content when coaching.

---

## Part 2: Gmail Setup

The coaching system sends and receives emails through Gmail using standard email protocols: IMAP for reading incoming emails and SMTP for sending outgoing emails. Your members never know the difference -- emails come from your address, in your name, threaded naturally in their inbox. You need to create an App Password, which requires 2-Factor Authentication to be enabled first.

### Step 2.1: Choose or Create Your Gmail Account

You can use any Gmail or Google Workspace account. This will be the "from" address on all coaching emails -- what your members see when they receive a check-in or coaching response.

- If you have a **Google Workspace domain** (like `coachwes@thelaunchpadincubator.com`), use that -- it looks more professional
- If not, you can use a **regular Gmail address** (like `yourcoaching@gmail.com`)
- **Recommendation:** Use a dedicated address for coaching rather than your personal email, so that coaching emails do not get mixed in with your other mail. This keeps things clean and organized.

### Step 2.2: Enable 2-Factor Authentication (2FA)

App Passwords (which you need in the next step) only work when 2FA is turned on. If you already have 2FA enabled on this Google account, skip to Step 2.3.

1. Go to **https://myaccount.google.com/security**
   - Or: open Gmail -> click your **profile photo** (top right) -> **"Manage your Google Account"** -> **"Security"** tab on the left
2. Scroll down to the section labeled **"How you sign in to Google"**
3. Click on **"2-Step Verification"**
4. Click **"Get started"**
5. Google will ask you to sign in again -- enter your password
6. Choose your verification method:
   - **Phone number (recommended for simplicity):** Enter your phone number, choose "Text message" or "Phone call," and click "Next." Enter the verification code you receive and click "Next."
   - **Google Authenticator app:** If you prefer, you can set up an authenticator app instead
7. Click **"Turn on"** to finalize
8. You should now see **"2-Step Verification is ON"** on the security page

### Step 2.3: Generate a Gmail App Password

An App Password is a special 16-character password that lets the coaching system access your Gmail securely without needing your actual password or 2FA codes. It is like giving the system its own secure key to your mailbox.

1. Go to **https://myaccount.google.com/apppasswords**
   - Or: from the Security page, scroll down to "2-Step Verification," click on it, then scroll to the bottom and look for **"App passwords"**
   - **Note:** If you do not see "App passwords," make sure 2FA is fully enabled (sometimes it takes a few minutes to appear after enabling 2FA)
2. On the App Passwords page:
   - In the **"App name"** field, type `Coaching System`
   - Click **"Create"**
3. Google will display a **16-character password** in a yellow box (formatted as four groups of four letters, like `abcd efgh ijkl mnop`)
4. **Copy this password immediately.** Remove the spaces -- you want it as one continuous string (like `abcdefghijklmnop`). This is your `GMAIL_APP_PASSWORD`.
5. Save this password alongside your OpenAI API key. You will need it in several places later.

**Important notes:**
- This App Password is shown only once. If you lose it, you will need to generate a new one (which is easy -- just repeat this step).
- If your Google account is managed by an organization (Google Workspace), your administrator may need to enable "Less secure app access" or "App passwords" for your account.
- The App Password is completely separate from your regular Gmail password. Your regular password is never stored anywhere in this system.

### Step 2.4: Verify IMAP Is Enabled

IMAP must be enabled for the system to read incoming emails from your members.

1. Open **Gmail** in your browser (https://mail.google.com)
2. Click the **gear icon** in the top right -> **"See all settings"**
3. Click the **"Forwarding and POP/IMAP"** tab
4. In the **IMAP access** section, make sure **"Enable IMAP"** is selected
5. If you changed anything, scroll down and click **"Save Changes"**

For Google Workspace accounts, IMAP is usually enabled by default, but it is worth confirming.

---

## Part 3: Supabase Setup

Supabase provides the PostgreSQL database that stores everything the coaching system needs: users, conversations, AI responses, your corrections, system settings, workflow history, and more. Think of it as the system's memory -- it remembers every member, every exchange, and every correction you have ever made, so the coaching gets sharper over time. The free tier is generous and more than sufficient for most programs.

### Step 3.1: Create a Supabase Account

1. Go to **https://supabase.com**
2. Click **"Start your project"** (or "Sign in" if you already have an account)
3. You will be prompted to sign in. The easiest option is **"Continue with GitHub"** since you already have a GitHub account from the prerequisites. Click it and authorize Supabase to access your GitHub account.
   - Alternatively, you can sign up with email and password
4. If this is your first time, Supabase will ask you to create an organization. Enter your organization name (your program name works) and click **"Create organization"**

### Step 3.2: Create a New Project

1. From the Supabase dashboard, click **"New project"**
2. Fill in the project details:
   - **Organization:** Select the organization you just created (or your existing one)
   - **Project name:** Enter `coaching-system` (or any name you like)
   - **Database password:** Choose a strong password and **save it somewhere safe**. You will need this if you ever want to connect to the database directly. (The coaching system itself uses API keys, not this password, but keep it as a backup.)
   - **Region:** Choose the region closest to you geographically. For US-based programs, **"East US (Virginia)"** or **"West US (Oregon)"** are good choices.
   - **Pricing plan:** Free tier is fine to start
3. Click **"Create new project"**
4. Wait approximately 1--2 minutes while Supabase provisions your database. You will see a progress indicator.

### Step 3.3: Get Your Supabase Credentials

You need two values from Supabase: the Project URL and the Service Role Key.

1. Once your project is ready, click **"Project Settings"** in the left sidebar (the gear icon near the bottom)
2. Click **"API"** in the left sidebar under "Configuration"
3. You will see several values on this page:
   - **Project URL:** Copy this value. It looks like `https://abcdefghijkl.supabase.co`. This is your `SUPABASE_URL`.
   - **API Keys:** You will see two keys:
     - `anon` `public` -- this is the public key. **Do not use this one.**
     - `service_role` `secret` -- **this is the one you need.** Click the eye icon or "Reveal" to see the full key, then copy it. This is your `SUPABASE_KEY`.
4. Save both values alongside your other credentials.

**Why the service_role key?** The coaching system runs server-side (from GitHub Actions and your dashboard), not from a browser. The service_role key gives it full access to read and write all data. Never expose this key in client-side code or public repositories -- it is for server-side use only.

### Step 3.4: Run the Database Schema

Now you need to create the database tables that the coaching system uses. The system includes SQL files that set up everything automatically -- you just need to copy, paste, and run them.

1. In your Supabase project, click **"SQL Editor"** in the left sidebar (it looks like a terminal icon)
2. Click **"New query"** (or you may see a blank editor already open)
3. Open the file `db/setup.sql` from the coaching system code. You can find this in the GitHub repository, or open it in any text editor on your computer.
4. **Select all** the contents of `db/setup.sql` (Cmd+A on Mac, Ctrl+A on Windows) and **copy** it (Cmd+C / Ctrl+C)
5. **Paste** it into the Supabase SQL Editor (Cmd+V / Ctrl+V)
6. Click the green **"Run"** button (or press Cmd+Enter / Ctrl+Enter)
7. You should see **"Success. No rows returned"** -- this is normal and expected. The script creates tables and indexes, not data rows (except for the default settings).
8. Now open the file `db/migration_v2.sql`
9. Click **"New query"** again (or clear the editor with Cmd+A then Delete)
10. **Copy the entire contents** of `db/migration_v2.sql` and **paste it into the SQL Editor**
11. Click **"Run"**
12. Again, you should see **"Success. No rows returned"**
13. Repeat the same process for `db/migration_v3.sql`, `db/migration_v4.sql`, and `db/migration_v5.sql` -- open each file, copy its contents, paste into a new query, and click Run. Run them in order (v3, then v4, then v5). Migration v5 specifically creates the `knowledge_chunks` table used by the local knowledge base when Claude is the AI provider.
14. **Recommended:** Run `db/seed_model_responses.sql` to populate the model responses table with example coaching responses for each stage. These model responses teach the AI your coaching voice and approach from day one, resulting in better responses right out of the gate.

### Step 3.5: Verify the Database

Confirm that everything was created correctly. This takes less than a minute and saves you from debugging later.

1. Click **"Table Editor"** in the left sidebar
2. You should see these tables listed:
   - `users` -- stores your program members
   - `conversations` -- stores all email exchanges and AI responses
   - `corrected_responses` -- stores your corrections to AI responses (the system learns from these)
   - `model_responses` -- example coaching responses the AI uses as reference for tone and approach
   - `settings` -- system configuration (key-value pairs)
   - `resources` -- program content references (lectures, chapters) with stage and topic metadata
   - `knowledge_chunks` -- local knowledge base chunks with vector embeddings (used when Claude is the AI provider)
   - `workflow_runs` -- audit log of every automated workflow execution
3. Click on the **`settings`** table. You should see rows like:
   - `global_auto_approve_threshold` = `10`
   - `check_in_days` = `tue,fri`
   - `check_in_hour` = `9`
   - `default_checkin_days` = `tue,fri`
   - `max_thread_replies` = `4`
   - And several more
4. If you ran the model responses seed, click on **`model_responses`** and verify you see 20 rows covering Ideation, Early Validation, Late Validation, and Growth stages.

If any table is missing, go back to the SQL Editor and re-run the relevant SQL file. Check for error messages in the output panel below the editor.

---

## Part 4: GitHub Setup

GitHub hosts your code and runs the automated workflows that power the entire coaching system. GitHub Actions is the free CI/CD service that executes your workflows on a schedule -- checking for new emails, sending approved responses, delivering check-ins, and more. Once configured, it runs everything automatically so you never have to think about it.

### Step 4.1: Fork or Clone the Repository

1. Go to the coaching system repository on GitHub
2. Click the **"Fork"** button in the top-right corner
3. On the fork creation page:
   - **Owner:** Select your GitHub account
   - **Repository name:** `coaching-system` (or keep the default)
   - Make sure **"Copy the `main` branch only"** is checked
4. Click **"Create fork"**
5. Wait a few seconds. You now have your own copy of the repository under your GitHub account.

**Alternative -- create a new repository from scratch:**

If you already have the code on your computer and want to push it to a new repo instead:

1. Go to **https://github.com/new**
2. Name your repository `coaching-system`
3. Set it to **Private** (recommended -- this repo will contain references to your configuration)
4. Click **"Create repository"**
5. Follow the instructions shown to push your local code to the new repo

### Step 4.2: Set GitHub Secrets

GitHub Secrets are encrypted environment variables that your workflows use to connect to Supabase, OpenAI, and Gmail. They are never visible in logs or to anyone who can view the repository -- they are securely encrypted at rest.

1. Go to your repository on GitHub (for example, `https://github.com/yourusername/coaching-system`)
2. Click the **"Settings"** tab (near the top of the page, next to "Insights")
3. In the left sidebar, under "Security," click **"Secrets and variables"**
4. Click **"Actions"**
5. You will see a section for "Repository secrets." Click **"New repository secret"** to add each of the following six secrets:

**Secret 1: SUPABASE_URL**
- **Name:** `SUPABASE_URL`
- **Value:** Paste your Supabase Project URL (for example, `https://abcdefghijkl.supabase.co`)
- Click **"Add secret"**

**Secret 2: SUPABASE_KEY**
- **Name:** `SUPABASE_KEY`
- **Value:** Paste your Supabase service_role key (the long `eyJ...` string)
- Click **"Add secret"**

**Secret 3: OPENAI_API_KEY**
- **Name:** `OPENAI_API_KEY`
- **Value:** Paste your OpenAI API key (starts with `sk-proj-...`)
- Click **"Add secret"**

**Secret 4: VECTOR_STORE_ID**
- **Name:** `VECTOR_STORE_ID`
- **Value:** Paste your vector store ID (starts with `vs_`)
- Click **"Add secret"**

**Secret 5: GMAIL_ADDRESS**
- **Name:** `GMAIL_ADDRESS`
- **Value:** Your Gmail address (for example, `coachwes@thelaunchpadincubator.com`)
- Click **"Add secret"**

**Secret 6: GMAIL_APP_PASSWORD**
- **Name:** `GMAIL_APP_PASSWORD`
- **Value:** Your 16-character Gmail App Password (no spaces)
- Click **"Add secret"**

**Secret 7: ANTHROPIC_API_KEY** *(optional)*
- **Name:** `ANTHROPIC_API_KEY`
- **Value:** Your Anthropic API key (starts with `sk-ant-...`)
- Click **"Add secret"**
- **Only needed if you plan to use Claude as the AI provider.** If you are sticking with OpenAI GPT-4o for response generation, you can skip this secret entirely.
- **Where to get it:** Go to **https://console.anthropic.com**, sign in (or create an account), then navigate to **API Keys** in the left sidebar. Click **"Create Key"**, give it a name like `Coaching System`, and copy the key. Like OpenAI, you will need to add billing/credits to your Anthropic account before the API will work.

After adding all secrets, your secrets list should show:
```
ANTHROPIC_API_KEY          (optional -- only if using Claude)
GMAIL_ADDRESS
GMAIL_APP_PASSWORD
OPENAI_API_KEY
SUPABASE_KEY
SUPABASE_URL
VECTOR_STORE_ID
```

### Step 4.3: Verify GitHub Actions Are Enabled

1. Go to the **"Actions"** tab in your repository (next to "Pull requests")
2. If this is a forked repository, you may see a message saying "Workflows aren't being run on this forked repository." Click **"I understand my workflows, go ahead and enable them"**
3. In the left sidebar of the Actions page, you should see five workflows listed:
   - **Check In** -- sends check-in emails to users scheduled for today
   - **Cleanup** -- catches any emails that slipped through during the day
   - **Process Emails** -- reads incoming emails and generates AI responses
   - **Re-engagement** -- nudges users who have been silent for 10+ days
   - **Send Approved** -- sends coaching responses that have been approved

These five workflows are the engine that keeps the coaching system running automatically, day after day.

### Step 4.4: Test a Workflow Manually

Before relying on the automated schedule, verify that the system can connect to all services. This is the moment of truth -- you are confirming that OpenAI, Gmail, and Supabase are all wired up correctly.

1. In the Actions tab, click on **"Process Emails"** in the left sidebar
2. You will see a banner that says "This workflow has a workflow_dispatch trigger." Click **"Run workflow"**
3. A dropdown will appear. Make sure the branch is `main`, then click the green **"Run workflow"** button
4. A new workflow run will appear in the list. Click on it to watch the progress.
5. Click on the **"run"** job to see the detailed logs
6. Look for these indicators of success:
   - The `pip install -r requirements.txt` step should complete without errors
   - The `python run_workflow.py process_emails` step should complete. If there are no unread emails to process, it will finish quickly with "0 items processed" -- that is perfectly fine and expected for a fresh setup.
7. If you see errors, check the log messages:
   - **"SUPABASE_URL" environment variable not set** -- double-check your GitHub Secrets (Step 4.2). Make sure the secret names match exactly.
   - **Authentication failed** (Gmail-related) -- verify your app password and that IMAP is enabled (Step 2.3 and 2.4)
   - **OpenAI error / Invalid API key** -- verify your API key and that billing is set up (Step 1.2 and 1.3)

---

## Part 5: Streamlit Dashboard Setup

The dashboard is your command center. This is where you manage users, review AI-generated coaching responses, configure system settings, run workflows manually, and monitor the health of everything. It is a clean, intuitive web interface that puts everything you need within a few clicks.

You have two options for hosting the dashboard.

### Option A: Streamlit Community Cloud (Recommended -- Free)

Streamlit Community Cloud is a free hosting service from Streamlit. Your dashboard will be available at a URL like `https://yourapp.streamlit.app` that you can access from anywhere. This is the easiest option and requires no local setup, no servers to maintain, and no technical configuration beyond entering your credentials.

#### Step 5A.1: Sign In to Streamlit Community Cloud

1. Go to **https://share.streamlit.io**
2. Click **"Sign in with GitHub"**
3. Authorize Streamlit to access your GitHub account
4. You will land on the Streamlit Community Cloud dashboard

#### Step 5A.2: Deploy Your App

1. Click **"New app"** (or "Create app") in the top-right area
2. Fill in the deployment form:
   - **Repository:** Select your coaching system repository (for example, `yourusername/coaching-system`)
   - **Branch:** `main`
   - **Main file path:** `dashboard/app.py`
   - **App URL (optional):** You can customize the subdomain, for example `coach-wes` will give you `https://coach-wes.streamlit.app`
3. Before clicking Deploy, click **"Advanced settings"** to add your secrets.

#### Step 5A.3: Add Secrets

1. In the Advanced settings, you will see a text area for **Secrets**. This is where you provide your credentials in TOML format.
2. Paste the following, replacing each placeholder with your actual values:

```toml
SUPABASE_URL = "https://abcdefghijkl.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
OPENAI_API_KEY = "sk-proj-..."
VECTOR_STORE_ID = "vs_6985fa853f84819196e012018b0defca"
GMAIL_ADDRESS = "coachwes@thelaunchpadincubator.com"
GMAIL_APP_PASSWORD = "abcdefghijklmnop"
DASHBOARD_PASSWORD = "choose-a-strong-password-here"
ANTHROPIC_API_KEY = "sk-ant-..."  # Optional -- only needed if using Claude as AI provider
```

**About DASHBOARD_PASSWORD:** This password protects your dashboard from unauthorized access. Anyone who visits your dashboard URL will need to enter this password before they can see anything. Choose something strong but memorable. If you leave it out or set it to an empty string, the dashboard will not require a password (not recommended for production use).

3. Click **"Save"**
4. Click **"Deploy!"**
5. Streamlit will build and deploy your app. This typically takes 1--3 minutes. You will see a build log showing the progress.
6. When deployment is complete, your dashboard will load at its URL (for example, `https://coach-wes.streamlit.app`)

#### Step 5A.4: Verify the Dashboard

1. Visit your dashboard URL
2. Enter the `DASHBOARD_PASSWORD` you set and click "Log in"
3. You should see the home page with your coaching system name and quick stats (all zeros is normal and expected for a fresh setup)
4. Check the sidebar -- you should see these pages:
   - Pending Review
   - Flagged
   - Conversations
   - Users
   - Corrections
   - Settings
   - Run Workflows
   - Analytics
   - Knowledge Base
5. Click **Settings** and verify the Gmail connection shows **"Gmail connection: OK"** at the bottom of the page

If the dashboard shows a connection error, double-check that your secrets are entered correctly. Go to Streamlit Community Cloud -> your app -> three-dot menu -> "Settings" -> "Secrets" to edit them.

### Option B: Run Locally

If you prefer to run the dashboard on your own computer (useful for development, testing, or if you do not want it publicly accessible).

#### Step 5B.1: Install Python

1. Check if Python is installed by opening a terminal (Mac: Terminal app, Windows: Command Prompt or PowerShell) and typing:
   ```
   python3 --version
   ```
   You need version 3.9 or higher. If you do not have Python, download it from **https://www.python.org/downloads/** and install it.

#### Step 5B.2: Set Up the Project

1. Open a terminal and navigate to the coaching system folder:
   ```
   cd /path/to/coaching-system
   ```
2. (Recommended) Create a virtual environment to keep dependencies isolated:
   ```
   python3 -m venv venv
   source venv/bin/activate       # Mac/Linux
   # or
   venv\Scripts\activate          # Windows
   ```
3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

#### Step 5B.3: Create Your .env File

1. In the project root folder, copy the example file:
   ```
   cp .env.example .env
   ```
2. Open `.env` in a text editor and fill in your actual values:
   ```
   SUPABASE_URL=https://abcdefghijkl.supabase.co
   SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   OPENAI_API_KEY=sk-proj-...
   VECTOR_STORE_ID=vs_6985fa853f84819196e012018b0defca
   GMAIL_ADDRESS=coachwes@thelaunchpadincubator.com
   GMAIL_APP_PASSWORD=abcdefghijklmnop
   COACH_TIMEZONE=America/New_York
   ANTHROPIC_API_KEY=sk-ant-...          # Optional -- only if using Claude
   ```
   Note: No quotes around the values in `.env` files. No spaces around the `=` sign.

3. For the dashboard password (when running locally), create a file at `.streamlit/secrets.toml`:
   ```
   DASHBOARD_PASSWORD = "choose-a-strong-password-here"
   ```

#### Step 5B.4: Launch the Dashboard

1. From the project root, run:
   ```
   streamlit run dashboard/app.py
   ```
2. Streamlit will open your browser automatically to `http://localhost:8501`
3. Enter your dashboard password and verify everything loads correctly

To stop the dashboard, press `Ctrl+C` in the terminal.

---

## Part 6: First Run Verification

Now that everything is set up, walk through the complete coaching cycle to confirm every piece is working together. This end-to-end test takes about 15 minutes and confirms that emails flow in, AI responses are generated, you can review them, and approved responses reach your members. **Do not skip this step** -- it is the single best way to catch any configuration issues before your members start using the system.

### Step 6.1: Check System Status

1. Open your dashboard
2. Navigate to the **Run Workflows** page (in the sidebar)
3. Look at the **System Status** section at the top. You should see four green checkmarks:
   - **Database** -- Connected (confirms Supabase credentials are working)
   - **Gmail** -- Connected (confirms Gmail App Password and IMAP are working)
   - **Python** -- version 3.9+ (confirms the runtime environment is correct)
   - **Migration v2** -- Applied (confirms all database schema updates have been run)
4. If any item shows an error (red X), go back to the relevant setup section in this guide and troubleshoot

### Step 6.2: Review Default Settings

1. Navigate to the **Settings** page
2. Verify these defaults are in place (you can adjust them later once you are familiar with the system):
   - **Auto-Approve Threshold:** 10 (meaning nothing auto-approves -- you review every AI response manually, which is the right starting point)
   - **Default check-in days:** Tue, Fri
   - **Check-in hour:** 9 (9:00 AM Eastern)
   - **Max thread replies:** 4 (members can go back and forth up to 4 times per check-in cycle)
   - **Process interval:** 60 minutes
   - **Processing hours:** 8 AM to 9 PM
   - **Send hours:** 9, 13, 19 (9 AM, 1 PM, 7 PM)
   - **Re-engagement days:** 10 (silent users get a nudge after 10 days)
   - **Max response paragraphs:** 3 (keeps coaching responses focused and actionable)
   - **AI Model:** Check the Provider and Model selection. The default is OpenAI GPT-4o. If you have set up an Anthropic API key (Step 4.2, Secret 7), you can switch the provider to Anthropic and choose a Claude model. The system will use whichever provider and model you select here for generating coaching responses.
3. Confirm **Gmail Connection** shows **"OK"** at the bottom of the page

### Step 6.3: Add a Test User

1. Navigate to the **Users** page
2. Click **"Add new user"** to expand the form
3. Fill in:
   - **Email:** Your personal email address (not the coaching Gmail -- use a different email so you can receive test emails as if you were a member)
   - **First name:** Your first name (or "Test")
   - **Stage:** Ideation (or whichever stage you want to test)
   - **Business idea:** "Testing the coaching system" (or any placeholder text)
   - **Check-in days:** Leave empty to use the system default (Tuesday and Friday), or pick specific days
4. Click **"Add User"**
5. Verify the user appears in the list below with a green dot (Active status)

### Step 6.4: Send a Test Check-In

1. Navigate to the **Run Workflows** page
2. Click the **"Check In"** button under Manual Triggers
3. Wait for the spinner to finish. You should see a success message like "Check-ins sent!"
4. **Check your test email inbox** (the personal email you used for the test user). Within a minute or two, you should receive a check-in email from the coaching Gmail address.
   - If you do not see it, check your spam/junk folder -- new sending addresses sometimes get filtered
   - The email will ask about what you accomplished, what you are focused on, your next step, and your approach

### Step 6.5: Reply to the Check-In

1. Open the check-in email in your personal inbox
2. Reply to it with a test message. For a realistic test, write something like:
   ```
   Accomplished: Had 3 conversations with potential customers this week
   about their scheduling problems.

   Current Focus: Trying to understand if this is a real pain point
   or just a mild annoyance.

   Next Step: Talk to 5 more people and ask specifically about what
   they've tried before.

   Approach: Reaching out through LinkedIn and asking friends
   for introductions.
   ```
3. Send the reply

### Step 6.6: Process the Incoming Email

1. Wait 1--2 minutes for the email to arrive in Gmail's inbox
2. Go back to your dashboard -> **Run Workflows**
3. Click **"Process Emails"**
4. Wait for it to finish. You should see a success message like "Emails processed!"
5. Behind the scenes, the workflow just:
   - Connected to Gmail and found your unread reply
   - Parsed the email content (stripped signatures, quoted text, and boilerplate)
   - Sent it to GPT-4o to generate a personalized coaching response, pulling relevant content from your vector store
   - Had GPT-4o-mini evaluate the response for quality (confidence score, flag checks, stage detection)
   - Saved everything to the database
   - Marked the email as read in Gmail

### Step 6.7: Review the AI Response

1. Navigate to the **Pending Review** page
2. You should see the AI-generated coaching response waiting for your review
3. For each pending response, you will see:
   - The user's name and confidence score (1--10)
   - The user's original message
   - The AI's drafted response (in an editable text area)
   - An expandable "View user context" section with the user's business idea, journey summary, and recent exchanges
4. **Read the AI response carefully.** This is your first look at what the AI produces. Ask yourself: Does this sound like good coaching? Is it specific to what the user wrote? Does it end with a question?
5. If it needs changes, edit it directly in the text area. When you edit before approving, a **correction record** is automatically saved -- the system literally learns from your edits.
6. Click **"Approve"** to approve the response
   - Or click **"Reject"** to discard it, or **"Flag"** to mark it for special attention

### Step 6.8: Send the Approved Response

1. Navigate to **Run Workflows**
2. Click **"Send Approved"**
3. Wait for it to finish. You should see "Approved responses sent!"
4. **Check your test email inbox** again. You should receive the coaching response, sent as a reply in the same email thread as the original check-in. It will appear as a natural conversation -- your member will see the check-in and the coaching response threaded together.

### Step 6.9: Verify the Full Cycle

1. Navigate to the **Conversations** page. You should see the complete exchange: the check-in, the user's reply, and the coaching response -- all linked together.
2. Navigate to **Users** and look at your test user. You should see the "Last response" date updated to now.
3. Navigate to **Run Workflows** and check the **Workflow Run History** at the bottom. You should see successful runs for check_in, process_emails, and send_approved.

**Congratulations -- your coaching system is fully operational.** Everything from here on runs automatically. Check-ins go out on schedule, emails are processed hourly, and approved responses are sent three times daily. Your only daily task is reviewing responses on the Pending Review page.

---

## Part 7: Automated Schedule Reference

Once everything is verified, the GitHub Actions workflows run on autopilot. Here is the complete schedule so you know exactly what happens and when. All times are Eastern US.

| Workflow | What It Does | Schedule |
|---|---|---|
| **Process Emails** | Reads unread emails from Gmail, parses them, generates AI coaching responses, evaluates quality, and routes to Pending Review, Flagged, or Auto-Approved | Every hour from 8 AM to 9 PM |
| **Send Approved** | Sends all approved coaching responses via Gmail, with human-like threading and randomized timing delays -- each email gets a random delay of 1 to N minutes (configurable in Settings) before sending, so responses feel human rather than bot-like | 9 AM, 1 PM, and 7 PM |
| **Check In** | Sends personalized check-in emails to users whose schedule includes today | Daily at 9 AM |
| **Re-engagement** | Sends a friendly nudge to users who have not responded in 10+ days; marks users silent after 17+ days | Daily at 10 AM |
| **Cleanup** | Catches any emails that may have been missed during the day (a safety net) | Daily at 11 PM |

You can also trigger any workflow manually from the **Run Workflows** page in the dashboard, or from the GitHub Actions tab in your repository. Manual triggers are useful when you want to process a specific email immediately or send an approved response without waiting for the next send window.

**Note on timing:** GitHub Actions cron schedules run in UTC. The system is configured to account for the Eastern timezone offset. Check-in behavior is also filtered by each user's personal check-in days (configurable on the Users page), so even though the Check In workflow runs daily, only users scheduled for that day will receive a check-in. The system respects individual schedules.

---

## Part 8: Environment Variables Reference

Here is the complete list of every environment variable the system uses, where to find each value, and what it does.

| Variable | Required | Where to Find It | Description |
|---|---|---|---|
| `SUPABASE_URL` | Yes | Supabase -> Project Settings -> API -> Project URL | The base URL of your Supabase project |
| `SUPABASE_KEY` | Yes | Supabase -> Project Settings -> API -> service_role key | Server-side key that gives full database access |
| `OPENAI_API_KEY` | Yes | OpenAI Platform -> API Keys | Your OpenAI API key (starts with `sk-proj-`) |
| `VECTOR_STORE_ID` | Yes | OpenAI Platform -> Storage -> Vector Stores | ID of your program content vector store (starts with `vs_`) |
| `GMAIL_ADDRESS` | Yes | Your Gmail / Google Workspace email | The "from" address for all coaching emails |
| `GMAIL_APP_PASSWORD` | Yes | Google Account -> Security -> App passwords | 16-character app password (no spaces) |
| `COACH_TIMEZONE` | No | -- | Timezone for scheduling (default: `America/New_York`). Uses standard timezone names like `America/Chicago`, `America/Los_Angeles`, `Europe/London`. |
| `GMAIL_IMAP_HOST` | No | -- | IMAP server hostname (default: `imap.gmail.com`). Only change if using a non-Gmail provider. |
| `GMAIL_SMTP_HOST` | No | -- | SMTP server hostname (default: `smtp.gmail.com`). Only change if using a non-Gmail provider. |
| `GMAIL_SMTP_PORT` | No | -- | SMTP server port (default: `587`). Only change if using a non-Gmail provider. |
| `ANTHROPIC_API_KEY` | No | Anthropic Console -> API Keys | Your Anthropic API key (starts with `sk-ant-`). Only needed if using Claude as the AI provider for response generation. |
| `DASHBOARD_PASSWORD` | No | You choose this | Password to access the Streamlit dashboard. If not set, the dashboard is open to anyone with the URL. |

**Where each variable goes:**

The same credentials need to be entered in up to three places, depending on how you are running the system:

- **GitHub Secrets** (Settings -> Secrets -> Actions): `SUPABASE_URL`, `SUPABASE_KEY`, `OPENAI_API_KEY`, `VECTOR_STORE_ID`, `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`, and optionally `ANTHROPIC_API_KEY`. These are used by the automated workflows.
- **Streamlit Cloud Secrets** (Advanced settings on deploy): All of the above plus `DASHBOARD_PASSWORD`. These are used by the web dashboard.
- **Local `.env` file** (if running locally): All of the above except `DASHBOARD_PASSWORD` (which goes in `.streamlit/secrets.toml` instead).

---

## Part 9: Troubleshooting

### "Gmail connection failed"

**Symptoms:** The Settings page shows "Gmail connection failed" or workflow logs show IMAP authentication errors.

**Fixes:**
1. Double-check your `GMAIL_APP_PASSWORD`. It should be exactly 16 characters with no spaces.
2. Verify that 2-Factor Authentication is still enabled on your Google account. If you disabled it, App Passwords stop working immediately.
3. Confirm IMAP is enabled in Gmail settings (Settings -> Forwarding and POP/IMAP -> Enable IMAP).
4. If you recently changed your Google password, your App Password may have been revoked. Generate a new one by repeating Step 2.3.
5. For Google Workspace accounts, ask your admin to check that IMAP and "App passwords" are not blocked at the organization level.

### "Supabase connection failed"

**Symptoms:** Dashboard shows "Could not connect to Supabase" or workflows fail with Supabase errors.

**Fixes:**
1. Verify your `SUPABASE_URL` includes `https://` at the beginning and `.supabase.co` at the end.
2. Make sure you are using the `service_role` key, not the `anon` key. The service_role key is longer and starts with `eyJ`.
3. Check that your Supabase project is running -- go to the Supabase dashboard and make sure it has not been paused. Free-tier projects can be paused after 7 days of inactivity. If it was paused, click **"Restore project"** and wait a minute for it to come back online.
4. If tables are missing, re-run `db/setup.sql` and `db/migration_v2.sql` in the SQL Editor.

### "OpenAI error" or "Invalid API key"

**Symptoms:** Workflows fail when generating AI responses. Error messages mention authentication or quota.

**Fixes:**
1. Go to **https://platform.openai.com/api-keys** and verify your key is still active (not revoked or expired).
2. Go to **https://platform.openai.com/settings/organization/billing/overview** and verify you have credit remaining and have not hit your monthly limit. If you hit the limit, increase it or wait for the next billing cycle.
3. If you recently created your account, there may be a short delay before the API is fully activated. Wait 10--15 minutes and try again.
4. Make sure the key starts with `sk-proj-`. Older key formats (`sk-...` without `proj`) may not have the right permissions.

### Dashboard will not load or shows errors

**Symptoms:** Streamlit shows an error page, or the dashboard is stuck on "Please wait..."

**Fixes:**
1. **On Streamlit Community Cloud:** Go to your app's settings and verify all secrets are entered correctly. Even one missing secret will cause the app to crash. Check for typos, extra spaces, or missing quotes in the TOML format. All string values must be wrapped in double quotes.
2. **Locally:** Make sure your `.env` file exists in the project root and has all required variables. Make sure you activated the virtual environment (`source venv/bin/activate`) before running `streamlit run dashboard/app.py`.
3. Check the Streamlit logs (in the browser, look for "Show details" on error pages, or check the terminal output if running locally) for specific error messages.

### Workflows are not running on schedule

**Symptoms:** You see no recent workflow runs in the dashboard or GitHub Actions tab, even though hours have passed.

**Fixes:**
1. Go to your GitHub repo -> **Actions** tab. If you see a banner about enabling workflows, click it.
2. Check that your repository is not archived or that Actions are not disabled in Settings -> Actions -> General.
3. GitHub Actions cron schedules can be delayed by up to 15--20 minutes. This is normal and documented by GitHub. If runs are consistently missing, check the workflow YAML files for syntax errors.
4. Forked repositories sometimes have Actions disabled by default. You need to explicitly enable them (Step 4.3).

### Emails not being received by users

**Symptoms:** Workflows show "Check-ins sent!" or "Approved responses sent!" but the user never receives the email.

**Fixes:**
1. **Check the spam/junk folder** of the recipient. New sending addresses often get flagged initially. Have the recipient mark the email as "not spam" and add the coaching address to their contacts.
2. Verify the user's email address is correct on the Users page. Even a single character difference will cause delivery to the wrong address.
3. Check that the user's status is **Active** (not Paused, Silent, or Onboarding).
4. For check-ins specifically, verify that today's day of the week matches the user's check-in schedule. If the user has no custom schedule, it uses the system default (Tuesday and Friday by default).
5. Check Gmail's "Sent" folder to see if the email was actually sent by the system.

### AI responses are low quality or off-topic

**Symptoms:** The AI generates generic advice or does not reference your program content.

**Fixes:**
1. Verify your `VECTOR_STORE_ID` is correct and that files have been uploaded to the vector store. Go to OpenAI Platform -> Storage -> Vector Stores and confirm your files are there.
2. Upload more program content to the vector store -- the more material the AI has to reference, the more specific and grounded the responses will be.
3. Run `db/seed_model_responses.sql` if you have not already. These model responses teach the AI your coaching voice and approach, resulting in more natural and on-brand responses.
4. Over time, as you correct AI responses on the Pending Review page, the system saves those corrections and uses them as context for future responses. The more you correct, the better it gets. When you have 50 or more corrections, you can also use the fine-tuning export feature on the Run Workflows page to create a custom model that matches your voice even more closely.

### "Migration v2 -- Not applied"

**Symptoms:** The Run Workflows page shows a red indicator for Migration v2.

**Fixes:**
1. Go to Supabase -> SQL Editor
2. Run the contents of `db/migration_v2.sql`
3. Refresh the dashboard -- the indicator should turn green

---

## Part 10: Day-to-Day Operations

Once the system is running, your typical daily routine is simple and takes about 15--30 minutes:

1. **Open the dashboard** and check the home page. Scan the pending review count and recent workflow runs. If everything shows green checkmarks and the pending count is low, you are in good shape.

2. **Go to Flagged first** and handle any responses the AI flagged for safety, sensitivity, or uncertainty. These need your personal attention -- they may involve legal questions, mental health mentions, or ambiguous situations.

3. **Go to Pending Review** and review the AI-generated coaching responses.
   - Read the user's message and the AI's proposed response
   - Edit the response if needed (your corrections are saved automatically and help the AI improve)
   - Click Approve for good responses, Flag for questionable ones, Reject for unusable ones

4. **Approved responses get sent automatically** at the next send window (9 AM, 1 PM, or 7 PM Eastern), or you can click "Send Approved" on the Run Workflows page to send them immediately if something is time-sensitive.

5. **Check Analytics weekly** to see overall program engagement, confidence calibration, and correction trends. This helps you tune the system over time.

6. **Adjust Settings as needed** -- for example, lowering the auto-approve threshold once you trust the AI's responses, or changing check-in days to match your program schedule.

The system handles everything else automatically: sending check-ins on schedule, processing incoming emails hourly, nudging silent users, and logging all activity. You focus on the coaching quality. The system handles the logistics.

---

## Appendix: Project File Structure

For reference, here is how the project is organized:

```
coaching-system/
  dashboard/
    app.py                    # Main Streamlit dashboard entry point (Home page)
    pages/
      1_pending_review.py     # Review and approve AI responses
      2_flagged.py            # Flagged responses needing attention
      3_conversations.py      # All conversation history
      4_users.py              # User management
      5_corrections.py        # AI correction records
      6_settings.py           # System settings and Gmail status
      7_run_workflows.py      # Manual workflow triggers and system status
      8_analytics.py          # Engagement analytics and calibration
      9_knowledge_base.py     # Knowledge Base management page
  db/
    setup.sql                 # Initial database schema
    migration_v2.sql          # Feature enhancement migration
    migration_v3.sql          # Per-email send offsets and model selection
    migration_v4.sql          # Evaluation sub-scores and bulk approve
    migration_v5.sql          # Knowledge chunks table for local knowledge base
    seed_model_responses.sql  # Example coaching responses
    supabase_client.py        # Database access layer
  workflows/
    check_in.py               # Send check-in emails
    process_emails.py         # Read and process incoming emails
    send_approved.py          # Send approved responses
    re_engagement.py          # Nudge silent users
    cleanup.py                # Catch missed emails
  services/
    gmail_service.py          # Gmail IMAP/SMTP service
    openai_service.py         # OpenAI API service (GPT-4o, RAG, evaluation)
    anthropic_service.py      # Anthropic Claude API service
    ai_service.py             # AI provider router (OpenAI or Anthropic)
    embedding_service.py      # OpenAI embeddings for knowledge base vector search
    knowledge_service.py      # RAG retrieval and formatting for Claude
    coaching_service.py       # Core business logic and pipeline orchestration
  prompts/
    assistant_instructions.md # AI coaching persona, style, and rules
    evaluation_prompt.md      # Response quality evaluation criteria
    email-parsing-prompt.md   # Email parsing instructions
    summary-update-prompt.md  # Journey summary update instructions
  templates/
    emails/
      email-templates.md      # Email templates for check-ins, onboarding, etc.
    knowledge-chunks/
      chunking-guide.md       # Guide for chunking program content
    model-responses/
      all-model-responses.md  # Model response reference by stage
  scripts/
    setup_supabase.py         # Supabase setup helper
    export_finetune_data.py   # Fine-tuning dataset export
    ingest_knowledge_base.py  # One-time knowledge base ingestion script
  .github/workflows/
    check_in.yml              # GitHub Actions: daily check-ins
    process_emails.yml        # GitHub Actions: hourly email processing
    send_approved.yml         # GitHub Actions: send at 9am/1pm/7pm
    re_engagement.yml         # GitHub Actions: daily re-engagement
    cleanup.yml               # GitHub Actions: nightly cleanup
  tests/
    conftest.py               # Shared test fixtures and mocks
    test_process_emails.py    # Email processing tests
    test_evaluation.py        # Evaluation routing tests
    test_send_approved.py     # Send workflow tests
    test_proactive.py         # Proactive outreach tests
    test_edge_cases.py        # Edge case tests
    test_knowledge_base.py    # Knowledge base ingestion and retrieval tests
    test_ai_service.py        # AI provider routing tests
  config.py                   # Configuration and environment loading
  run_workflow.py             # CLI entry point for running workflows
  requirements.txt            # Python dependencies
  .env.example                # Template for local environment file
  .streamlit/config.toml      # Streamlit theme and settings
```

---

You are now fully set up. The coaching system is live and ready to support your program members with personalized, AI-assisted coaching through email. If you run into any issues not covered here, check the error messages carefully -- they almost always point to a misconfigured credential or a missing database migration. When in doubt, re-verify all six environment variables and re-run the database SQL files.

For detailed guides on specific topics, see the companion documents:
- **Quick Start Guide** -- a concise overview to share with your members
- **Admin Onboarding Guide** -- step-by-step instructions for adding new users
- **Operator's Guide** -- the complete operations manual for daily system management
- **Tech Stack Summary** -- detailed technical architecture for developers
