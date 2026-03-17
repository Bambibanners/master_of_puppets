# Your First Job

Jobs are Python scripts signed with an Ed25519 private key. The node verifies the signature before executing. This guide walks through generating a signing key, registering the public key, and dispatching your first job via the dashboard.

---

## Step 1: Generate a signing keypair

```bash
openssl genpkey -algorithm ed25519 -out signing.key
openssl pkey -in signing.key -pubout -out verification.key
```

!!! warning "Keep your private key safe"
    Never commit `signing.key` to git. Add it to `.gitignore` immediately. In production, store it in a secrets manager (Vault, AWS Secrets Manager, etc.) rather than on disk.

---

## Step 2: Register the public key in the dashboard

1. Go to **Signatures** in the dashboard sidebar
2. Click **Add Signature Key**
3. Paste the contents of `verification.key` into the field
4. Give it a descriptive name (e.g., `dev-operator-key`)
5. Click **Save**
6. Note the **Key ID** displayed — you will need to select this key when submitting jobs

!!! danger "Register before dispatching"
    Job creation fails with a `422` signature validation error if no public key is registered. **You must complete this step before proceeding to job dispatch.**

---

## Step 3: Write and sign a test script

Create `hello.py`:

```python
print("Hello from Master of Puppets!")
import platform
print(f"Running on {platform.node()} ({platform.system()})")
```

Sign it with your private key and base64-encode the signature:

```bash
# Sign the script
openssl pkeyutl -sign -inkey signing.key -out hello.py.sig -rawin -in hello.py

# Base64-encode the signature for the dashboard form
base64 -w0 hello.py.sig > hello.py.sig.b64
```

!!! tip "mop-push automates this"
    The `mop-push` CLI handles signing and submission in one command — no manual openssl steps required. See the [mop-push CLI guide](../feature-guides/mop-push.md) for details. The manual method is shown here to make the signing mechanics visible.

---

## Step 4: Dispatch the job via the dashboard

1. Go to **Jobs** in the dashboard sidebar
2. Click **New Job**
3. Fill in the form:
    - **Script**: paste the full contents of `hello.py`
    - **Signature**: paste the base64 string from `hello.py.sig.b64`
    - **Signature Key**: select the key you registered in Step 2
    - **Target tags**: leave blank to target any available node, or enter `general` to match the default node tag
4. Click **Dispatch**

---

## Step 5: Verify the result

The job appears in the Jobs list and transitions through statuses:

```
PENDING → ASSIGNED → COMPLETED
```

Click the job row to expand the result. The output should show:

```
Hello from Master of Puppets!
Running on <node-hostname> (Linux)
```

!!! success "You've completed the Getting Started guide"
    Your node is enrolled, jobs are running, and results are captured in the dashboard.

    **What to explore next:**

    - [Foundry](../feature-guides/foundry.md) — build custom node images with pre-installed runtimes and packages
    - [mop-push CLI](../feature-guides/mop-push.md) — sign and submit jobs from the command line in one step
