# How to Test Sandbox Dashboard Before Approving
**Purpose:** Verify the CSS fix works before approving for production  
**Time:** 5-10 minutes  
**Difficulty:** Easy (just run the app)

---

## Quick Start (3 Steps)

### Step 1: Open PowerShell
```
Windows Key → Type "PowerShell" → Click "Windows PowerShell"
```

### Step 2: Navigate to Sandbox Dashboard
```powershell
cd "C:\JeffLocal-Sandbox\dashboard"
```

### Step 3: Run the Dashboard
```powershell
.\run_dashboard.ps1
```

**Wait for:** "Running on http://127.0.0.1:5000" message

---

## View the Dashboard

### On This Computer
1. Open browser: Chrome, Firefox, or Edge
2. Go to: `http://127.0.0.1:5000`
3. You'll see the JeffLocal dashboard

### On Your Phone
1. Find your computer's IP address (see instructions below)
2. On phone browser: `http://YOUR_IP:5000`
3. Test responsive design

---

## What To Test

### Test 1: Toggle Button Visibility ✅
**What to do:**
1. Look at top-left of dashboard
2. Find the "☰" (hamburger/toggle) button
3. It should be **clearly visible** with a border

**Before fix:** Button is invisible (can't see it)  
**After fix:** Button is visible with dark border + white background

### Test 2: Click Toggle Button ✅
**What to do:**
1. Click the toggle button
2. Side panel should slide out/in smoothly
3. Click again to toggle back

**Expected:** Smooth animation, clean transitions

### Test 3: Desktop (Wide Screen) ✅
**What to do:**
1. Maximize browser window (full width)
2. Sidebar should be 280px wide (unchanged)
3. Toggle button clearly visible
4. Main content takes up remaining space

**Expected:** Sidebar on left, content takes up most screen

### Test 4: Tablet Size ✅
**What to do:**
1. Right-click in browser → "Inspect" (F12)
2. Click device toggle (phone icon)
3. Select "iPad" or "Tablet" (768px width)
4. Sidebar should be narrower (240px)
5. Toggle button still visible

**Expected:** Responsive layout adapts to tablet size

### Test 5: Mobile Size ✅
**What to do:**
1. In DevTools, select mobile device (iPhone 12, etc.)
2. Width should be ~390px
3. Sidebar should overlay (full width)
4. Toggle button clearly visible
5. Click toggle to open/close

**Expected:** Sidebar slides in as overlay, doesn't push content

### Test 6: All 8 Pathways ✅
**What to do:**
1. Close DevTools (F12)
2. Look for patient list or intake queue
3. Try loading different pathways if available:
   - Prescription
   - Sick note
   - Referral
   - Test result
   - Appointment
   - Admin
   - Medication query
   - Unknown

**Expected:** All work normally, no broken links, no console errors

### Test 7: Browser Console (Check for Errors) ✅
**What to do:**
1. Press F12 to open DevTools
2. Click "Console" tab
3. Look for red error messages
4. Toggle sidebar a few times
5. Watch console for errors

**Expected:** No red errors, maybe warnings (OK to ignore)

---

## How to Find Your Computer's IP Address

**Windows (PowerShell):**
```powershell
ipconfig
```
Look for "IPv4 Address" (e.g., 192.168.1.100)

**Then on phone:**
- Open Chrome
- Type: `http://192.168.1.100:5000`
- You'll see dashboard on your phone

---

## Test Checklist

- [ ] Toggle button visible on desktop
- [ ] Toggle button visible on tablet (DevTools)
- [ ] Toggle button visible on mobile (DevTools)
- [ ] Click toggle works smoothly
- [ ] Sidebar width changes at breakpoints (desktop 280px, tablet 240px, mobile 100%)
- [ ] All 8 pathways still accessible
- [ ] No console errors (F12 → Console)
- [ ] Layout looks correct at all sizes
- [ ] Animations are smooth
- [ ] Everything responsive and clean

**All checks pass?** → Reply "approved" ✅

---

## Stop the Dashboard

**When done testing:**

Press: `Ctrl+C` in PowerShell (stop the server)

Or just close PowerShell.

---

## Troubleshooting

### Dashboard won't start
```powershell
# Make sure you're in the right folder
cd "C:\JeffLocal-Sandbox\dashboard"

# Try running Python directly
python -m flask run
```

### Can't access http://127.0.0.1:5000
- Wait 3-5 seconds after seeing "Running on" message
- Try refreshing (Ctrl+R or F5)
- Try different port: http://127.0.0.1:5001

### Can't see changes in browser
- Clear cache: Ctrl+Shift+Delete (Chrome)
- Hard refresh: Ctrl+Shift+R
- Close and reopen browser

### Phone can't access dashboard
- Check IP address is correct (run `ipconfig` again)
- Make sure phone is on same WiFi network
- Check firewall isn't blocking port 5000

---

## What You're Verifying

### For Issue #1 Fix:
1. ✅ Toggle button is now visible (was invisible before)
2. ✅ Sidebar width adapts to device size
3. ✅ Everything else still works (pathways, login, etc.)
4. ✅ No visual regressions or broken layouts

### This Confirms:
- ✅ Fix works as expected
- ✅ No unintended side effects
- ✅ All 8 pathways still functional
- ✅ Safe to deploy to production

**If everything looks good → Approve!**

---

## Pro Tips

1. **Test on actual phone if possible** — Better than DevTools simulation
2. **Test on multiple browsers** — Chrome, Firefox, Safari
3. **Resize browser manually** — Drag window edges to test responsiveness
4. **Watch the transition** — See the sidebar smoothly adapt
5. **Toggle button multiple times** — Verify animation is smooth

---

## Expected Results

### Before Fix (Current Production)
```
❌ Toggle button: INVISIBLE (can't see it)
❌ Sidebar: Always 280px (no responsive)
❌ Mobile: Sidebar blocks content (not usable)
```

### After Fix (What You're Testing)
```
✅ Toggle button: VISIBLE (dark border, white background)
✅ Sidebar: 280px desktop, 240px tablet, overlay mobile
✅ All sizes: Responsive, functional, clean
✅ All pathways: Working normally
```

---

## Next Steps After Testing

### If Everything Looks Good ✅
Reply in chat: **`approved`**

Then:
1. DX Agent deploys to production
2. Same changes go live
3. All users benefit from fix

### If Something Looks Wrong ❌
Reply: `hold - [describe issue]`

Then:
1. DX Agent investigates
2. Makes corrections
3. Resubmits for approval

---

## Time Estimate

- Start dashboard: 1 minute
- Run through tests: 5-10 minutes
- Verify all pathways: 3-5 minutes
- **Total: 10-15 minutes**

Then you can confidently approve!

---

## Questions While Testing?

Just ask in chat. DX Agent available for clarification.

---

**Ready to test? Open PowerShell and run `cd C:\JeffLocal-Sandbox\dashboard` then `.\run_dashboard.ps1`**

Happy testing! 🚀
