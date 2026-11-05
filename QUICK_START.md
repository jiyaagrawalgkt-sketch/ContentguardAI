# ContentGuard AI — Quick Start Guide (Windows)

> **Fastest path to run ContentGuard AI on any Windows PC in under 3 minutes.**

---

## 1. Prerequisites (Check Before Running)

Ensure you have these two free tools installed on your Windows machine:
1. **Python 3.11 or newer**: [python.org/downloads](https://www.python.org/downloads/)  
   *(CRITICAL: Check the box **"Add python.exe to PATH"** during installation!)*
2. **Node.js 18 or newer (LTS)**: [nodejs.org](https://nodejs.org/)

---

## 2. Fast 3-Step Setup

### Step 1: Open PowerShell in the Extracted Folder
1. Right-click the extracted `ContentGuardAI` folder.
2. Select **"Open in Terminal"** or open PowerShell and navigate to the folder:
   ```powershell
   cd C:\Path\To\ContentGuardAI
   ```

### Step 2: Run the Automatic Setup Script
Run the setup script:
```powershell
.\setup.ps1
```
*(If Windows blocks script execution, run with bypass:)*
```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```
- The script checks Python and Node.js versions.
- It sets up your virtual environment, installs backend and frontend packages.
- It auto-creates your environment files (`.env` and `.env.local`).
- It provisions the database and asks if you want to seed demo accounts (choose **Y**).

### Step 3: Start the Application
Run:
```powershell
.\start.ps1
```
*(If Windows blocks execution: `powershell -ExecutionPolicy Bypass -File .\start.ps1`)*

Two PowerShell windows will pop up:
1. **Backend Server**: Running FastAPI on `http://127.0.0.1:8000`
2. **Frontend Server**: Running Next.js on `http://localhost:3000`

---

## 3. Open in Browser & Sign In

Open your browser to:
👉 **[http://localhost:3000](http://localhost:3000)**

Click **Sign In**. Use the 1-click demo buttons or type credentials manually:

| Role | Email | Password | What You Can Test |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@contentguard.demo` | `Demo@123` | View live metrics, manage users, modify roles, monitor database health (`/admin`) |
| **Creator** | `creator@contentguard.demo` | `Demo@123` | Load sample drafts, run AI compliance check, 1-click fix violations, submit for review (`/creator`) |
| **Reviewer** | `reviewer@contentguard.demo` | `Demo@123` | Inspect diffs, test conflict-of-interest guard, approve & publish content (`/reviewer`) |

---

## 4. Interactive 2-Minute Demo Workflow

1. **Sign in as Creator** (`creator@contentguard.demo` / `Demo@123`).
2. In **Creator Studio**, scroll to the **Sample Content Library** and click **"Load Into Studio"** on *Consumer Tech Instagram Advertisement*.
3. Click **"Run Brand Compliance Analysis"** — observe the low compliance score (53/100) and flagged violations (unauthorized 100% risk-free guarantees).
4. Click **"Apply Fix"** on detected issues — watch the text automatically update to brand-approved language.
5. Click **"Re-Analyze Content"** — score jumps to **100/100**. Click **"Submit for Review"**.
6. Sign out, sign in as **Reviewer** (`reviewer@contentguard.demo` / `Demo@123`).
7. Open the pending submission in **Reviewer Station**, inspect the side-by-side diff, and click **"Approve & Certify"**.
8. Click **"View Public Certificate"** to view the tamper-evident cryptographic publication certificate!

---

## 5. Stop the Application

When finished, stop all background servers safely with:
```powershell
.\stop.ps1
```
