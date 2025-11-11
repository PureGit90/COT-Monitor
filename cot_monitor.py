#!/usr/bin/env python3
"""
COT Smart Money Monitor
Fetches Commitment of Traders data, detects divergences and extremes,
sends weekly reports via n8n webhook.

Based on: Swing Trading Strategy Framework (Verified Traders Roundtable)
"""

import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sys

# ============================================================================
# CONFIGURATION
# ============================================================================

CONFIG_FILE = "config.json"

# Default configuration (override with config.json)
DEFAULT_CONFIG = {
    "n8n_webhook_url": "https://your-n8n-instance.com/webhook/cot-report",
    "assets": {
        "NQ": {
            "name": "Nasdaq 100",
            "contract_name": "NASDAQ MINI",
            "cftc_code": "209742"
        },
        "SPX": {
            "name": "S&P 500",
            "contract_name": "E-MINI S&P 500",
            "cftc_code": "13874A"
        },
        "BTC": {
            "name": "Bitcoin",
            "contract_name": "BITCOIN",
            "cftc_code": "133741"
        },
        "ETH": {
            "name": "Ethereum",
            "contract_name": "ETHER CASH SETTLED",
            "cftc_code": "ETH"
        },
        "EUR": {
            "name": "Euro FX",
            "contract_name": "EURO FX",
            "cftc_code": "099741"
        },
        "USD": {
            "name": "US Dollar Index",
            "contract_name": "USD INDEX",
            "cftc_code": "098662"
        }
    },
    "lookback": {
        "divergence_weeks": 52,
        "extreme_weeks": 156
    }
}

# CFTC Socrata API endpoint
CFTC_API_URL = "https://publicreporting.cftc.gov/resource/gpe5-46if.json"

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def load_config() -> Dict:
    """Load configuration from file or use defaults."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                print(f"✓ Loaded configuration from {CONFIG_FILE}")
                return config
        except Exception as e:
            print(f"⚠ Error loading config file: {e}")
            print("Using default configuration")
    else:
        print(f"⚠ Config file not found. Creating {CONFIG_FILE} with defaults...")
        with open(CONFIG_FILE, 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
        print(f"✓ Created {CONFIG_FILE}. Please update webhook URL.")
    
    return DEFAULT_CONFIG

def fetch_cot_data(contract_name: str, limit: int = 156) -> Optional[List[Dict]]:
    """
    Fetch COT data from CFTC Socrata API.
    Returns list of weekly records, newest first.
    """
    try:
        params = {
            "$select": "report_date_as_yyyy_mm_dd,contract_market_name,lev_money_positions_long,lev_money_positions_short,nonrept_positions_long_all,nonrept_positions_short_all",
            "$where": f"contract_market_name='{contract_name}'",
            "$order": "report_date_as_yyyy_mm_dd DESC",
            "$limit": limit
        }
        
        print(f"  Fetching {contract_name}...")
        response = requests.get(CFTC_API_URL, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        print(f"  ✓ Retrieved {len(data)} weeks of data")
        return data
        
    except Exception as e:
        print(f"  ✗ Error fetching {contract_name}: {e}")
        return None

def calculate_net_positions(data: List[Dict]) -> List[Dict]:
    """Calculate net hedge fund and retail positions."""
    processed = []
    
    for record in data:
        try:
            hf_long = float(record.get('lev_money_positions_long', 0))
            hf_short = float(record.get('lev_money_positions_short', 0))
            retail_long = float(record.get('nonrept_positions_long_all', 0))
            retail_short = float(record.get('nonrept_positions_short_all', 0))
            
            processed.append({
                'date': record['report_date_as_yyyy_mm_dd'],
                'hf_net': hf_long - hf_short,
                'retail_net': retail_long - retail_short,
                'hf_long': hf_long,
                'hf_short': hf_short
            })
        except (KeyError, ValueError) as e:
            continue
    
    return processed

def detect_signals(data: List[Dict], divergence_weeks: int = 52, extreme_weeks: int = 156) -> Dict:
    """
    Detect divergences and extreme positioning.
    
    Returns:
    {
        'current_net': float,
        'bullish_divergence': bool,
        'bearish_divergence': bool,
        'extreme_bullish': bool,
        'extreme_bearish': bool,
        'status': str
    }
    """
    if len(data) < 2:
        return {
            'current_net': 0,
            'bullish_divergence': False,
            'bearish_divergence': False,
            'extreme_bullish': False,
            'extreme_bearish': False,
            'status': 'INSUFFICIENT_DATA'
        }
    
    current = data[0]
    current_net = current['hf_net']
    
    # Get lookback periods
    divergence_data = data[:min(divergence_weeks, len(data))]
    extreme_data = data[:min(extreme_weeks, len(data))]
    
    # Calculate extremes
    hf_nets = [d['hf_net'] for d in extreme_data]
    extreme_low = min(hf_nets)
    extreme_high = max(hf_nets)
    
    extreme_bullish = current_net == extreme_low  # HF at max bearish = contrarian buy
    extreme_bearish = current_net == extreme_high  # HF at max bullish = contrarian sell
    
    # Detect divergences (simplified - would need price data for full implementation)
    # For now, detect if HF positioning is making higher lows or lower highs
    divergence_nets = [d['hf_net'] for d in divergence_data]
    
    # Bullish divergence: HF making higher low
    recent_low = min(divergence_nets[-26:])  # Last 6 months
    older_low = min(divergence_nets[-52:-26])  # Previous 6 months
    bullish_divergence = recent_low > older_low and current_net < divergence_nets[-1]
    
    # Bearish divergence: HF making lower high
    recent_high = max(divergence_nets[-26:])
    older_high = max(divergence_nets[-52:-26])
    bearish_divergence = recent_high < older_high and current_net > divergence_nets[-1]
    
    # Determine status
    if bullish_divergence:
        status = "🔥 BULLISH DIVERGENCE"
    elif bearish_divergence:
        status = "🔥 BEARISH DIVERGENCE"
    elif extreme_bullish:
        status = "⚠️ EXTREME BULLISH"
    elif extreme_bearish:
        status = "⚠️ EXTREME BEARISH"
    else:
        status = "NEUTRAL"
    
    return {
        'current_net': round(current_net, 2),
        'hf_long': round(current['hf_long'], 2),
        'hf_short': round(current['hf_short'], 2),
        'bullish_divergence': bullish_divergence,
        'bearish_divergence': bearish_divergence,
        'extreme_bullish': extreme_bullish,
        'extreme_bearish': extreme_bearish,
        'status': status,
        'date': current['date']
    }

def analyze_asset(asset_code: str, asset_config: Dict, lookback_config: Dict) -> Optional[Dict]:
    """Analyze single asset and return signals."""
    print(f"\n📊 Analyzing {asset_config['name']} ({asset_code})...")
    
    data = fetch_cot_data(
        asset_config['contract_name'],
        limit=lookback_config['extreme_weeks']
    )
    
    if not data:
        return None
    
    processed = calculate_net_positions(data)
    if not processed:
        print(f"  ✗ No valid data for {asset_code}")
        return None
    
    signals = detect_signals(
        processed,
        divergence_weeks=lookback_config['divergence_weeks'],
        extreme_weeks=lookback_config['extreme_weeks']
    )
    
    print(f"  Status: {signals['status']}")
    print(f"  HF Net: {signals['current_net']:,.0f}")
    
    return {
        'asset_code': asset_code,
        'asset_name': asset_config['name'],
        **signals
    }

def send_to_webhook(data: Dict, webhook_url: str) -> bool:
    """Send report data to n8n webhook."""
    try:
        print(f"\n📤 Sending to webhook: {webhook_url}")
        
        response = requests.post(
            webhook_url,
            json=data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        response.raise_for_status()
        
        print("✓ Webhook delivered successfully")
        return True
        
    except Exception as e:
        print(f"✗ Webhook failed: {e}")
        return False

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution flow."""
    print("=" * 70)
    print("COT SMART MONEY MONITOR")
    print("=" * 70)
    print(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Load configuration
    config = load_config()
    
    # Validate webhook URL
    webhook_url = config.get('n8n_webhook_url', '')
    if 'your-n8n-instance' in webhook_url:
        print("\n⚠️  WARNING: Please update webhook URL in config.json")
        print("Current URL is placeholder. Script will continue but webhook will fail.\n")
    
    # Analyze all assets
    results = []
    active_signals = []
    
    for asset_code, asset_config in config['assets'].items():
        analysis = analyze_asset(
            asset_code,
            asset_config,
            config['lookback']
        )
        
        if analysis:
            results.append(analysis)
            
            # Track active signals
            if analysis['status'] != 'NEUTRAL':
                active_signals.append({
                    'asset': f"{asset_config['name']} ({asset_code})",
                    'signal': analysis['status'],
                    'net_position': analysis['current_net']
                })
    
    # Prepare report payload
    report = {
        'timestamp': datetime.now().isoformat(),
        'week_ending': datetime.now().strftime('%Y-%m-%d'),
        'total_assets': len(results),
        'active_signals': len(active_signals),
        'signals': active_signals,
        'all_assets': results
    }
    
    # Print summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Assets analyzed: {len(results)}")
    print(f"Active signals: {len(active_signals)}")
    
    if active_signals:
        print("\n🚨 ACTIVE SIGNALS:")
        for signal in active_signals:
            print(f"  • {signal['asset']}: {signal['signal']}")
    else:
        print("\nNo active signals this week.")
    
    # Save report locally
    report_file = f"cot_report_{datetime.now().strftime('%Y%m%d')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"\n💾 Report saved: {report_file}")
    
    # Send to webhook
    if webhook_url and 'your-n8n-instance' not in webhook_url:
        send_to_webhook(report, webhook_url)
    else:
        print("\n⚠️  Skipping webhook (URL not configured)")
    
    print("\n✓ Analysis complete!")
    print("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
