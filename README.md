# ContentGuard AI — Enterprise AI-Powered Brand Governance & Content Compliance Platform

> **Tagline**: *Review it before it ships.*  
> **Category**: Enterprise AI Brand Governance, Regulatory Compliance & Content Certification  
> **Version**: 1.0.0 Portable Production Release  

---

## 1. What ContentGuard AI Does

**ContentGuard AI** is an intelligent brand governance platform that empowers marketing, communication, legal, and growth teams to systematically audit outward-facing business content prior to publication. 

Every piece of draft content—including social media campaigns, paid search ads, marketing email newsletters, corporate landing pages, thought leadership blogs, and press releases—is evaluated against the organization's official brand guidelines, factual knowledge vault, restricted terminology dictionary, and communication policies.

The platform provides a **Hybrid Compliance Engine** (deterministic relational rules + Google Gemini contextual AI) that flags violations with character-level precision, explains the legal and brand risk, generates 1-click verified corrections, and enforces human-in-the-loop review and approval workflows before publishing.

---

## 2. Key Platform Features

- **Multi-Format Content Analysis**: Natively analyzes LinkedIn posts, Meta/Google Ads, marketing emails, website hero pages, and corporate press releases.
- **Explainable Mathematical Scoring**: Compliance scores ($0-100$) are calculated deterministically from empirical violation weights—never fabricated:
  $$\text{Compliance Score} = \max\left(0, 100 - \sum (\text{SeverityWeight}_i \times \text{Count}_i)\right)$$
- **Interactive 1-Click Remediation**: Click **[Apply Fix]** on any detected violation to instantly replace prohibited phrases with officially sanctioned alternatives from the Brand Knowledge Vault.
- **Reviewer Governance Station & Conflict-of-Interest Guard**: Reviewers cannot approve or reject their own authored submissions (`HTTP 403 Forbidden`). Dedicated queue status tabs (`Pending Reviews`, `Changes Requested`, `Approved Content`, `All Submissions`).
- **Side-by-Side Version Diff Comparison**: Visual comparison between original draft (Version 1) and corrected draft (Version 2).
- **Tamper-Evident Certified Public Preview**: Approved content generates a cryptographic preview token (`/preview/[token]`) with verification stamps.
- **Admin Operations Console**: Live database aggregates (total users, active orgs, total submissions, pending reviews, approval rate, avg score), user management, dynamic role assignment, account activation/deactivation, and database engine health probes.
- **Multi-Tenant User Isolation**: Standalone user registrations provision an isolated workspace, preventing data sharing across accounts.
- **Real-World Sample Content Library**: 5 realistic industry drafts across high-risk, moderate-risk, and compliant scenarios with 1-click loading into the studio.

---

## 3. System Requirements

Before running the application on Windows, verify that your computer meets these requirements:

| Component | Minimum Requirement | Recommended |
| :--- | :--- | :--- |
| **Operating System** | Windows 10 (64-bit) or Windows 11 | Windows 11 (64-bit) |
| **Python** | Python 3.10+ | Python 3.11 or 3.12 (64-bit) |
| **Node.js** | Node.js 18.0.0+ | Node.js 20.x or 22.x LTS |
| **Memory (RAM)** | 4 GB | 8 GB or more |
| **Disk Space** | 1 GB free | 2 GB free |
| **Shell** | Windows PowerShell 5.1+ or PowerShell 7+ | PowerShell 7 or Windows Terminal |

---

## 4. Required Software Installation Links

If Python, Node.js, or VS Code are not already installed on your computer, install them using the official links below:

1. **Python 3.11+ (Required)**:  
   👉 [Download Python for Windows](https://www.python.org/downloads/)  
   > ⚠️ **CRITICAL STEP DURING PYTHON INSTALLATION**:  
   > On the first installer screen, you **MUST check the box** that says:  
   > `[X] Add python.exe to PATH` (at the bottom of the installer window).  
   > If you forget this, PowerShell will not be able to find `python`.

2. **Node.js LTS (Required)**:  
   👉 [Download Node.js LTS](https://nodejs.org/)  
   > Run the installer and click Next through all default options. `npm` is included automatically.

3. **Visual Studio Code (Recommended Code Editor)**:  
   👉 [Download Visual Studio Code](https://code.visualstudio.com/Download)

4. **Git for Windows (Optional)**:  
   👉 [Download Git for Windows](https://git-scm.com/download/win)

---

## 5. How to Extract the ZIP File

1. Locate the downloaded `ContentGuardAI-Portable.zip` file in your **Downloads** folder.
2. Right-click the `.zip` file and select **"Extract All..."**.
3. Choose a convenient destination folder (for example: `C:\Projects\ContentGuardAI` or `D:\ContentGuardAI`).
4. Click **Extract**.

---

## 6. How to Open the Project in VS Code

1. Launch **Visual Studio Code**.
2. Click **File** -> **Open Folder...** (or press `Ctrl + K, Ctrl + O`).
3. Browse to the extracted `ContentGuardAI` directory and click **Select Folder**.
4. Press ``Ctrl + ` `` (backtick) or select **Terminal** -> **New Terminal** from the top menu to open an integrated PowerShell terminal.

---

## 7. How to Run `setup.ps1` (Automatic Environment Setup)

In your PowerShell terminal in the project root, run:

```powershell
.\setup.ps1
```

### If Windows Execution Policy Blocks the Script:
If Windows displays an error saying *`... execution of scripts is disabled on this system`*, run this command instead:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

### What `setup.ps1` Does Automatically:
1. Verifies that Python (3.10+) and Node.js (18+) are installed.
2. Automatically generates `backend\.env` from `backend\.env.example` (if not already present).
3. Automatically generates `frontend\.env.local` from `frontend\.env.example` (if not already present).
4. Creates the Python virtual environment at `backend\venv`.
5. Installs all required Python dependencies via `pip`.
6. Installs all required Node.js frontend dependencies via `npm`.
7. Initializes all 16 database tables in the relational database.
8. Prompts you to optionally seed demo accounts and sample brand guidelines (type `Y` and press Enter).

---

## 8. Database Configuration (Zero-Config SQLite vs PostgreSQL)

### Option A: Zero-Config SQLite (Default — Ready Out of the Box)
By default, ContentGuard AI is pre-configured to use SQLite. No database installation, configuration, or port forwarding is required. The database file is automatically created at:
`backend/contentguard.db`

All foreign keys, constraints, multi-tenant relationships, and transactions are enforced.

### Option B: PostgreSQL Setup (Optional for Production or Advanced Staging)
If you prefer to run with PostgreSQL:

1. **Install PostgreSQL on Windows**:
   - Download the PostgreSQL Windows installer from [enterprisedb.com/downloads/postgres-postgresql-downloads](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads).
   - During installation, set a master password (e.g. `postgres`).
2. **Create the Database**:
   - Open **pgAdmin** or run in PowerShell (with `psql` in PATH):
     ```powershell
     psql -U postgres -c "CREATE DATABASE contentguard_ai;"
     ```
3. **Configure `backend\.env`**:
   - Open `backend\.env` in your editor.
   - Update `DATABASE_URL`:
     ```env
     DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@localhost:5432/contentguard_ai"
     ```
4. **Initialize Tables**:
   - Re-run `.\setup.ps1` or run:
     ```powershell
     .\backend\venv\Scripts\python -c "from app.core.database import init_db; init_db(); print('Tables created.')"
     ```

---

## 9. How to Configure Google Gemini API (Optional)

ContentGuard AI features a hybrid architecture:
- **100% Deterministic Engine**: Always active out of the box with zero external dependencies or API keys. Fully detects tone drift, unverified multipliers, absolute guarantees, SLA discrepancies, and buzzwords.
- **Gemini Contextual AI**: Analyzes subtle linguistic nuances and brand guidelines when an API key is configured.

### Adding your Gemini API Key:
1. Get a free Google Gemini API key from Google AI Studio:  
   👉 [https://aistudio.google.com/](https://aistudio.google.com/)
2. Open `backend\.env` in VS Code or Notepad.
3. Locate the `GEMINI_API_KEY` line and paste your key inside the quotes:
   ```env
   GEMINI_API_KEY="AIzaSyYourActualKeyHere..."
   ```
4. Save the file. The backend automatically reloads when running!

> **Note**: If you do not have a Gemini key, leave `GEMINI_API_KEY=""`. The platform runs smoothly on the deterministic compliance engine without any crashes or warnings.

---

## 10. How to Start the Application

Once `setup.ps1` has finished, start the entire stack with a single command:

```powershell
.\start.ps1
```

*(Or with bypass: `powershell -ExecutionPolicy Bypass -File .\start.ps1`)*

This script automatically opens two designated PowerShell windows:
1. **Window 1 (Backend)**: Runs FastAPI server on `http://127.0.0.1:8000` with hot-reload.
2. **Window 2 (Frontend)**: Runs Next.js 14 server on `http://localhost:3000`.

---

## 11. Application Endpoints & URLs

| Service | URL | Description |
| :--- | :--- | :--- |
| **Web Application** | [http://localhost:3000](http://localhost:3000) | Main SaaS interface (Landing, Auth, Creator Studio, Reviewer Station, Admin Console) |
| **Backend API Root** | [http://127.0.0.1:8000](http://127.0.0.1:8000) | FastAPI JSON root endpoint |
| **Interactive Swagger API Docs** | [http://127.0.0.1:8000/api/v1/docs](http://127.0.0.1:8000/api/v1/docs) | Interactive Swagger UI testing all endpoints |
| **ReDoc API Documentation** | [http://127.0.0.1:8000/api/v1/redoc](http://127.0.0.1:8000/api/v1/redoc) | Alternate clean API documentation |

---

## 12. Pre-Configured Demo Accounts (Judge & Hackathon Evaluation)

ContentGuard AI provides a dedicated, pre-seeded Hackathon Demo Account displayed directly on the login page for instantaneous 1-click evaluation:

| Account Type | Email | Password | Landing Page & Capabilities |
| :--- | :--- | :--- | :--- |
| 🌟 **Demo Creator** | `demo@contentguard.ai` | `Demo@12345` | **`/creator`** — Seeded Creator Workspace with 1-click login on login page, brand guidelines, sample whitepapers, vector chunks, and brand assets |
| **Compliance Officer** | `compliance@contentguard.demo` | `Demo@123` | **`/compliance`** — Regulatory claim verification queue, certify/reject actions, and append-only audit trail logs |
| **Administrator** | `admin@contentguard.demo` | `Demo@123` | **`/admin`** — Platform overview KPIs, user management, role assignments, system health |
| **Reviewer** | `reviewer@contentguard.demo` | `Demo@123` | **`/reviewer`** — Queue status filters, side-by-side diffs, evidence verification graph, conflict guard, approve & publish |
| **Creator** | `creator@contentguard.demo` | `Demo@123` | **`/creator`** — Load sample drafts, run AI analysis, apply 1-click fixes, multimodal visual audits, submit for review |

---

## 13. Round 3 Enterprise Features

### Feature 1: Zero-Trust Brand Governance
- **Cryptographic Multi-Tenancy**: Organization-level isolation enforced at the database query layer (`org_id` scoping). Cross-tenant queries are blocked with `HTTP 403 Forbidden`.
- **Granular RBAC**: 4 distinct roles (`creator`, `reviewer`, `compliance_officer`, `admin`) enforced on both API routes and client interfaces.
- **JWT Access + Refresh Token Rotation**: Ephemeral 30-minute access tokens paired with secure 7-day refresh tokens stored as SHA-256 hashes in `refresh_tokens` table with cryptographic `jti` entropy. Instant token revocation on logout.
- **Enterprise Password Complexity**: Enforces $\ge 8$ characters, uppercase, lowercase, numerical digit, and special character.
- **TOTP Multi-Factor Authentication**: RFC 6238 time-based one-time passwords via `pyotp` (`/auth/mfa/setup` & `/auth/mfa/verify`).
- **Append-Only Audit Logging**: Dedicated `audit_logs` table recording timestamp, user, action, resource, IP address, and payload diffs for regulatory compliance inspections.

### Feature 2: Evidence Intelligence Graph
- **Multi-Format Ingestion**: Ingests PDF, DOCX, TXT, and Markdown whitepapers into the Knowledge Vault (`/knowledge-base`).
- **Sliding-Window Semantic Chunking**: Automatic document chunking with character overlap preserving context across boundaries.
- **Deterministic 64-D Vector Embeddings**: Cosine similarity search over normalized n-gram semantic embeddings running 100% offline with zero external network dependencies and zero hallucinations.
- **Automated Claim Extraction**: Regex and NLP pattern extraction identifying numerical metrics, performance multipliers, absolute guarantees, certifications, and supremacy claims.
- **5-State Fact Grounding**: Each claim is evaluated against ingested organizational evidence as `SUPPORTED`, `UNSUPPORTED`, `CONFLICTING`, `OUTDATED`, or `UNVERIFIED` with exact source document citations and similarity confidence scores.
- **Interactive Node-Link Topology Graph**: Cytoscape/SVG-style visual graph (`EvidenceGraph.tsx`) linking draft submissions to extracted claims and cited knowledge base chunks with real-time status filtering.

### Feature 3: Multimodal Brand Intelligence
- **Brand Asset Vault**: Centralized management of primary/secondary brand palettes, typography, and SVG/PNG logos (`/brand-knowledge/assets`).
- **Dominant Color Extraction & Palette Distance**: K-means/Euclidean color quantization extracting hex swatches from uploaded images and calculating $\Delta E$ Euclidean distance against approved corporate palette colors.
- **WCAG 2.1 Luminance & Contrast Ratio Calculator**: Computes relative luminance and precise foreground/background contrast ratios:
  $$\text{Contrast Ratio} = \frac{L_1 + 0.05}{L_2 + 0.05}$$
  Enforces WCAG AA ($\ge 4.5:1$) and AAA ($\ge 7:1$) accessibility compliance standards.
- **OCR Text Extraction**: Automated text detection and extraction (`pytesseract` with graceful fallback) scanning embedded visual banners for restricted slogans.
- **Alt-Text Accessibility Auditor**: Analyzes image `alt` descriptions for length, keyword stuffing, and descriptive context.

---

## 14. Google OAuth 2.0 Integration & Setup

ContentGuard AI supports single sign-on via Google OAuth 2.0 / OpenID Connect:

1. Create a project in [Google Cloud Console](https://console.cloud.google.com/).
2. Navigate to **APIs & Services** > **Credentials**.
3. Create an **OAuth 2.0 Client ID** (Web Application).
4. Add Authorized JavaScript Origins:
   - Development: `http://localhost:3000`
   - Production: `https://your-vercel-domain.vercel.app`
5. Configure environment variables in backend `.env`:
   ```env
   GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   ```
6. On the login/register screen, users can click **"Continue with Google"** for zero-friction sign-on with automatic organization provisioning.

---

## 15. Cloud Deployment Guide (Vercel & Render)

### Backend Deployment (Render)
1. In Render, create a new **Web Service** pointing to your repository.
2. Root Directory: `backend`
3. Environment: `Python 3`
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Set Environment Variables:
   - `DATABASE_URL`: Your PostgreSQL connection string or SQLite default.
   - `JWT_SECRET`: A secure random cryptographic key.
   - `GEMINI_API_KEY`: Your Google Gemini API key (optional; deterministic fallback active).

### Frontend Deployment (Vercel)
1. In Vercel, import your GitHub repository.
2. Root Directory: `frontend`
3. Framework Preset: `Next.js`
4. **Environment Variables**:
   - `NEXT_PUBLIC_API_URL`: Your Render backend URL (e.g. `https://contentguardai-backend.onrender.com`).
   > ℹ️ *Note*: The frontend automatically normalizes the URL to append `/api/v1` and includes cold-start resilience to prevent timeouts.

---

## 13. How to Register a New Independent Account

1. Open `http://localhost:3000/register`.
2. Fill in your details:
   - **Full Name**: e.g., `Jane Doe`
   - **Email Address**: e.g., `jane@acmecorp.com`
   - **Organization Name**: e.g., `Acme Innovations` *(Optional — if left blank, an isolated personal workspace is automatically generated)*
   - **Password**: Enter any password with at least 8 characters.
3. Click **"Create Workspace"**.
4. You will be logged into your private, isolated Creator Studio. You will not see drafts from any other organization.

---

## 14. How to Configure User Roles Securely

- **Via the Admin Dashboard (`/admin`)**:
  1. Sign in as Administrator (`admin@contentguard.demo`).
  2. Navigate to the **User Management** tab.
  3. Find the user you wish to modify.
  4. Click **"Change Role"** and select `creator`, `reviewer`, or `admin`.
  5. The change is saved immediately to the database.
- **Via Direct Database Creation**:
  - Administrators can also use the **"Create User"** modal in the Admin Console to provision new accounts with designated roles without sharing initial setup passwords.

---

## 15. Troubleshooting Common Windows Errors

### Error 1: `File ... cannot be loaded because running scripts is disabled on this system`
- **Cause**: Windows PowerShell security policy restricts unsigned script execution by default.
- **Solution**: Run PowerShell scripts with the `-ExecutionPolicy Bypass` flag:
  ```powershell
  powershell -ExecutionPolicy Bypass -File .\setup.ps1
  powershell -ExecutionPolicy Bypass -File .\start.ps1
  powershell -ExecutionPolicy Bypass -File .\stop.ps1
  ```
  Or permanently enable local script execution in your PowerShell:
  ```powershell
  Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
  ```

### Error 2: `'python' is not recognized as an internal or external command`
- **Cause**: Python was installed without enabling the "Add Python to PATH" option.
- **Solution**:
  1. Re-run the Python installer.
  2. Select **Modify**.
  3. Check the box **"Add Python to PATH"** and complete setup.
  4. Close all open PowerShell windows and re-open.

### Error 3: `Port 8000 or Port 3000 is already in use`
- **Cause**: A previous development server process was not stopped.
- **Solution**: Run the stop script to release both ports cleanly:
  ```powershell
  .\stop.ps1
  ```

### Error 4: `npm : The term 'npm' is not recognized`
- **Cause**: Node.js is not installed or the terminal has not refreshed its environment variables.
- **Solution**: Install Node.js LTS from [nodejs.org](https://nodejs.org/), then close and reopen your PowerShell terminal.

### Error 5: Backend integration test failure with `EPERM`
- **Cause**: On Windows, anti-virus or file locks can occasionally delay directory deletion in temp caches.
- **Solution**: Simply re-run `.\backend\venv\Scripts\python -m pytest backend/tests`.

---

## 16. How to Stop the Application

To stop all running backend and frontend servers cleanly without affecting any other programs on your machine, run:

```powershell
.\stop.ps1
```

*(Or: `powershell -ExecutionPolicy Bypass -File .\stop.ps1`)*

This script automatically terminates the background processes on port 8000 and port 3000 and clears the PID records.

---

## 17. How to Create a Clean Portable ZIP (For Sharing)

If you want to package the project into a fresh ZIP to send to another friend:

```powershell
.\package.ps1
```

This generates `ContentGuardAI-Portable.zip` in your project root (~140 KB), automatically excluding all `node_modules`, virtual environments, cache files, and private `.env` files. Your friend can extract it on their Windows PC and follow `QUICK_START.md` to get started in minutes!
