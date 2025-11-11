# COT Smart Money Monitor

Automated Commitment of Traders (COT) analysis system that detects hedge fund positioning divergences and extreme levels, delivering weekly email reports via n8n.

**Based on:** Swing Trading Strategy Framework - Verified Traders Roundtable

---

## 📦 What's Included

- `cot_monitor.py` - Main Python script for COT analysis
- `requirements.txt` - Python dependencies
- `config.json` - Configuration file (assets, webhook URL)
- `n8n_cot_workflow.json` - Ready-to-import n8n workflow
- `README.md` - This file

---

## 🎯 What It Does

**Monitors 7 Assets:**
- NQ (Nasdaq 100)
- SPX (S&P 500)
- BTC (Bitcoin)
- ETH (Ethereum)
- EUR (Euro FX)
- USD (US Dollar Index)
- GOLD (Gold)

**Detects 4 Signal Types:**
1. **Bullish Divergence** - Price new low, hedge funds higher low
2. **Bearish Divergence** - Price new high, hedge funds lower high
3. **Extreme Bullish** - Hedge funds at 3-year max bearish (contrarian buy)
4. **Extreme Bearish** - Hedge funds at 3-year max bullish (contrarian sell)

**Delivers:**
- Beautiful HTML email every Sunday
- Summary of active signals
- Full positioning data for all assets
- Playbook guidance for each signal

---

## 🚀 Quick Start (Local Testing)

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up n8n Workflow

1. Open your n8n cloud instance
2. Click **Workflows** → **Import from File**
3. Upload `n8n_cot_workflow.json`
4. Open the **"Send Email"** node
5. Configure with your Gmail account (OAuth2)
6. Update the recipient email address
7. Click **"Webhook"** node to see your webhook URL
8. Copy the webhook URL (looks like: `https://your-n8n.app/webhook/cot-report`)
9. **Save & Activate** the workflow

### 3. Configure Python Script

Edit `config.json` and update:

```json
{
  "n8n_webhook_url": "https://your-n8n.app/webhook/cot-report",
  ...
}
```

### 4. Test Run

```bash
python3 cot_monitor.py
```

**Expected output:**
```
======================================================================
COT SMART MONEY MONITOR
======================================================================
Run time: 2025-11-11 11:30:00

✓ Loaded configuration from config.json

📊 Analyzing Nasdaq 100 (NQ)...
  Fetching NASDAQ-100 MINI...
  ✓ Retrieved 156 weeks of data
  Status: NEUTRAL
  HF Net: 15,234

[... continues for all assets ...]

======================================================================
SUMMARY
======================================================================
Assets analyzed: 7
Active signals: 2

🚨 ACTIVE SIGNALS:
  • Nasdaq 100 (NQ): 🔥 BULLISH DIVERGENCE
  • Gold (GOLD): ⚠️ EXTREME BULLISH

💾 Report saved: cot_report_20251111.json

📤 Sending to webhook: https://your-n8n.app/webhook/cot-report
✓ Webhook delivered successfully

✓ Analysis complete!
======================================================================
```

**Check your email!** You should receive the formatted COT report.

---

## ☁️ Deploy to Render.com (Free Tier)

### Why Render?
- ✅ 100% free tier with cron jobs
- ✅ Runs every Sunday automatically
- ✅ No server management
- ✅ Built-in monitoring

### Setup Instructions

1. **Create Render Account**
   - Go to https://render.com
   - Sign up (free)

2. **Create New Cron Job**
   - Dashboard → **"New +"** → **"Cron Job"**
   - **Name:** `cot-monitor`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Command:** `python cot_monitor.py`
   - **Schedule:** `0 17 * * 5` (Every Friday 5pm EST - when COT data drops)
   
3. **Connect Your Repository**
   
   **Option A: Upload via GitHub**
   - Create a private GitHub repo
   - Push all files (`cot_monitor.py`, `requirements.txt`, `config.json`)
   - Connect repo to Render
   
   **Option B: Upload Directly**
   - Zip all files
   - Upload to Render dashboard

4. **Set Environment Variables (Optional)**
   - In Render dashboard, go to **Environment**
   - Add: `N8N_WEBHOOK_URL` = your webhook URL
   - Update `cot_monitor.py` to read from env var instead of config.json

5. **Deploy**
   - Click **"Create Cron Job"**
   - Wait for first build (~1-2 minutes)
   - View logs to confirm success

---

## 📧 Email Preview

Your Sunday email will look like this:

```
📊 COT Smart Money Report
Week ending November 10, 2025

🚨 ACTIVE SIGNALS
• Nasdaq 100 (NQ): 🔥 BULLISH DIVERGENCE (Net: 15,234)
• Gold (GOLD): ⚠️ EXTREME BULLISH (Net: -45,678)

📈 All Assets Summary

Code  | Asset              | HF Net     | Status              | Guidance
------|--------------------|-----------|--------------------|-------------------
NQ    | Nasdaq 100         | +15,234   | 🔥 BULLISH DIV     | Wait for retracement
SPX   | S&P 500            | +45,123   | NEUTRAL            | Monitor
BTC   | Bitcoin            | -8,456    | NEUTRAL            | Monitor
ETH   | Ethereum           | -2,345    | NEUTRAL            | Monitor
EUR   | Euro FX            | +12,678   | NEUTRAL            | Monitor
USD   | US Dollar Index    | -5,432    | NEUTRAL            | Monitor
GOLD  | Gold               | -45,678   | ⚠️ EXTREME BULL    | Contrarian long zone

📚 Playbook Reminder
• Bullish Divergence: Price makes new low, but hedge funds make higher low
• Bearish Divergence: Price makes new high, but hedge funds make lower high
• Extreme Positioning: Hedge funds at 3-year max = contrarian opportunity
• Next Step: Use technical analysis to time entry on retracements
```

---

## 🔧 Customization

### Change Assets

Edit `config.json`:

```json
"assets": {
  "YOUR_CODE": {
    "name": "Display Name",
    "contract_name": "EXACT CFTC CONTRACT NAME",
    "cftc_code": "CFTC_CODE"
  }
}
```

Find CFTC contract names: https://publicreporting.cftc.gov/

### Change Schedule

**Render Cron Syntax:**
- `0 17 * * 5` = Every Friday 5pm EST
- `0 9 * * 0` = Every Sunday 9am
- `0 */6 * * *` = Every 6 hours

**When does COT data update?**
- Released every Friday at 3:30pm EST
- Set cron for 5pm EST to ensure data is available

### Change Lookback Periods

Edit `config.json`:

```json
"lookback": {
  "divergence_weeks": 52,   // 1 year
  "extreme_weeks": 156       // 3 years
}
```

### Add More Alert Channels

Modify n8n workflow:
- Add **Telegram** node after "Format Email"
- Add **Discord** webhook node
- Add **Slack** notification node
- All nodes receive same data

---

## 🐛 Troubleshooting

### "No data returned from API"

**Cause:** CFTC contract name doesn't match API
**Fix:** Verify contract names at https://publicreporting.cftc.gov/resource/gpe5-46if.json

Example query:
```
https://publicreporting.cftc.gov/resource/gpe5-46if.json?$select=contract_market_name&$group=contract_market_name
```

### "Webhook failed"

**Cause:** Incorrect webhook URL or n8n workflow not activated
**Fix:** 
1. Check n8n workflow is **Activated** (toggle in top-right)
2. Copy webhook URL directly from n8n webhook node
3. Test webhook with curl:
   ```bash
   curl -X POST https://your-n8n.app/webhook/cot-report \
     -H "Content-Type: application/json" \
     -d '{"test": "data"}'
   ```

### "Gmail authentication failed"

**Fix:**
1. In n8n, re-authenticate Gmail node
2. Use OAuth2 (not SMTP)
3. Grant all required permissions

### "Script hangs or times out"

**Cause:** CFTC API slow or down
**Fix:** The script has 30-second timeouts. If CFTC is down, wait and retry later.

---

## 📊 Data Sources

**Primary:** CFTC Socrata API
- **Endpoint:** https://publicreporting.cftc.gov/resource/gpe5-46if.json
- **Report:** Traders in Financial Futures (TFF)
- **Update Schedule:** Every Friday 3:30pm EST
- **Rate Limit:** None (public API)
- **Cost:** 100% Free

**Alternative:** CFTC Legacy Reports
- If Socrata API unavailable, script can be modified to parse legacy text files
- Less reliable but backup option

---

## 🔐 Security Notes

- **config.json contains webhook URL** - Don't commit to public repos
- **Add to .gitignore:**
  ```
  config.json
  cot_report_*.json
  ```
- **Render Environment Variables** - Use for production webhook URL
- **n8n Webhook** - No authentication by default. Add basic auth if needed.

---

## 📈 Future Enhancements

**Phase 2: Price Integration**
- Fetch actual price data to improve divergence detection
- Currently uses HF positioning trends as proxy

**Phase 3: Backtesting**
- Historical signal performance
- Win rate analysis
- Optimal entry timing

**Phase 4: Altcoin Indicator (Arkham MCP)**
- On-chain whale wallet tracking
- Smart money accumulation for SOL, AVAX, HYPE
- Same divergence logic, blockchain data

---

## 📚 Resources

- **CFTC COT Reports:** https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm
- **Playbook Source:** Titans of Tomorrow Podcast - Verified Traders Roundtable
- **n8n Docs:** https://docs.n8n.io
- **Render Docs:** https://render.com/docs

---

## ✅ Checklist

- [ ] Python installed (3.8+)
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] n8n workflow imported and activated
- [ ] Gmail connected in n8n
- [ ] Webhook URL copied to config.json
- [ ] Test run successful (`python3 cot_monitor.py`)
- [ ] Email received
- [ ] Deployed to Render (optional)
- [ ] First automated run verified

---

## 💬 Support

**Issues?**
1. Check logs: `cot_report_YYYYMMDD.json`
2. Verify n8n workflow is active
3. Test webhook manually with curl
4. Confirm CFTC API is accessible

**Need Help?**
- Review troubleshooting section above
- Check CFTC API status
- Verify contract names match exactly

---

**Built with:**
- Python 3
- CFTC Socrata API
- n8n workflow automation
- Render.com hosting

**Last Updated:** November 11, 2025
