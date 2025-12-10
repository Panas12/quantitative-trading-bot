"""
Automated Scheduler for Live Trading Bot

Runs the trading bot daily at specified times and sends email alerts.

Setup:
1. Install: pip install schedule
2. Configure email settings in .env
3. Run: python scheduler.py

Will check signals at:
- 9:00 AM EST (pre-market)
- 9:35 AM EST (post open)
- 12:00 PM EST (midday)
- 3:55 PM EST (before close)
"""

import schedule
import time
import logging
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

from live_trading import LiveTradingExecutor

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TradingScheduler:
    """
    Automated scheduler for trading bot with email alerts.
    """
    
    def __init__(self):
        self.executor = LiveTradingExecutor(
            capital=float(os.getenv('TRADING_CAPITAL', '111.55')),
            dry_run=os.getenv('DRY_RUN', 'True').lower() == 'true'
        )
        
        # Email configuration
        self.email_enabled = os.getenv('EMAIL_ALERTS', 'False').lower() == 'true'
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.sender_email = os.getenv('SENDER_EMAIL', '')
        self.sender_password = os.getenv('SENDER_PASSWORD', '')
        self.recipient_email = os.getenv('RECIPIENT_EMAIL', '')
        
        logger.info("Trading Scheduler initialized")
        logger.info(f"Dry run mode: {self.executor.dry_run}")
        logger.info(f"Email alerts: {self.email_enabled}")
    
    def send_email(self, subject: str, body: str):
        """
        Send email alert.
        
        Args:
            subject: Email subject
            body: Email body text
        """
        if not self.email_enabled:
            logger.info(f"Email disabled. Would send: {subject}")
            return
        
        if not all([self.sender_email, self.sender_password, self.recipient_email]):
            logger.warning("Email credentials not configured")
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            logger.info(f"Email sent: {subject}")
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
    
    def check_signals_job(self):
        """Scheduled job to check trading signals"""
        logger.info("="*70)
        logger.info("SCHEDULED SIGNAL CHECK")
        logger.info("="*70)
        
        try:
            # Initialize portfolio
            self.executor.connect_broker()
            self.executor.initialize_portfolio()
            
            # Get signals
            signals_df = self.executor.get_current_signals()
            
            # Check for actionable signals
            active_signals = signals_df[signals_df['signal'].isin(['LONG', 'SHORT', 'EXIT'])]
            
            if len(active_signals) > 0:
                # Send alert
                subject = f"🚨 Trading Signal Alert - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                body = f"Active trading signals detected:\n\n{signals_df.to_string(index=False)}\n\n"
                body += f"Dry run mode: {self.executor.dry_run}\n"
                
                if not self.executor.dry_run:
                    body += "\n⚠️  LIVE MODE - Signals will auto-execute if scheduled!\n"
                
                self.send_email(subject, body)
                logger.info(f"Active signals: {len(active_signals)}")
            else:
                logger.info("No active signals")
            
            logger.info(f"\n{signals_df.to_string(index=False)}\n")
            
        except Exception as e:
            logger.error(f"Error in signal check: {e}")
            self.send_email(
                "❌ Trading Bot Error",
                f"Error occurred during signal check:\n\n{str(e)}"
            )
    
    def execute_trades_job(self):
        """Scheduled job to execute trades (only if auto-execute enabled)"""
        auto_execute = os.getenv('AUTO_EXECUTE', 'False').lower() == 'true'
        
        if not auto_execute:
            logger.info("Auto-execute disabled, skipping trade execution")
            return
        
        if self.executor.dry_run:
            logger.info("Dry run mode, skipping real execution")
            return
        
        logger.info("="*70)
        logger.info("SCHEDULED TRADE EXECUTION")
        logger.info("="*70)
        
        try:
            self.executor.run(mode='execute')
            
            # Send execution summary
            self.send_email(
                "✅ Trades Executed",
                "Automated trade execution completed. Check logs for details."
            )
            
        except Exception as e:
            logger.error(f"Error executing trades: {e}")
            self.send_email(
                "❌ Trade Execution Failed",
                f"Error during automated execution:\n\n{str(e)}"
            )
    
    def monitor_positions_job(self):
        """Scheduled job to monitor open positions"""
        logger.info("="*70)
        logger.info("SCHEDULED POSITION MONITORING")
        logger.info("="*70)
        
        try:
            self.executor.run(mode='monitor')
        except Exception as e:
            logger.error(f"Error monitoring positions: {e}")
    
    def daily_summary_job(self):
        """Send daily summary at market close"""
        logger.info("Generating daily summary...")
        
        try:
            self.executor.connect_broker()
            self.executor.initialize_portfolio()
            
            signals_df = self.executor.get_current_signals()
            risk = self.executor.portfolio.check_portfolio_risk()
            
            subject = f"📊 Daily Trading Summary - {datetime.now().strftime('%Y-%m-%d')}"
            body = f"""
Daily Portfolio Summary
=======================

Current Signals:
{signals_df.to_string(index=False)}

Risk Metrics:
- Equity: ${risk['current_equity']:.2f}
- Drawdown: {risk['drawdown']:.1%}
- Leverage: {risk['leverage']:.2f}x
- Open Positions: {risk['num_positions']}

Mode: {'DRY RUN' if self.executor.dry_run else 'LIVE TRADING'}
"""
            
            self.send_email(subject, body)
            logger.info("Daily summary sent")
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
    
    def setup_schedule(self):
        """Setup trading schedule"""
        logger.info("Setting up schedule...")
        
        # Pre-market check (9:00 AM EST = 3:00 PM Amsterdam)
        schedule.every().day.at("15:00").do(self.check_signals_job)
        
        # Post-open check (9:35 AM EST = 3:35 PM Amsterdam)
        schedule.every().day.at("15:35").do(self.check_signals_job)
        
        # Midday check (12:00 PM EST = 6:00 PM Amsterdam)
        schedule.every().day.at("18:00").do(self.check_signals_job)
        
        # Pre-close check (3:55 PM EST = 9:55 PM Amsterdam)
        schedule.every().day.at("21:55").do(self.check_signals_job)
        
        # Position monitoring (every 2 hours during market hours)
        schedule.every(2).hours.do(self.monitor_positions_job)
        
        # Daily summary at close (4:05 PM EST = 10:05 PM Amsterdam)
        schedule.every().day.at("22:05").do(self.daily_summary_job)
        
        logger.info("Schedule configured (AMSTERDAM TIME):")
        logger.info("  - 15:00 (3:00 PM): Pre-market (9:00 AM EST)")
        logger.info("  - 15:35 (3:35 PM): Post-open (9:35 AM EST)")
        logger.info("  - 18:00 (6:00 PM): Midday (12:00 PM EST)")
        logger.info("  - 21:55 (9:55 PM): Pre-close (3:55 PM EST)")
        logger.info("  - Every 2 hours: Position monitoring")
        logger.info("  - 22:05 (10:05 PM): Daily summary (4:05 PM EST)")
    
    def run(self):
        """Start the scheduler"""
        self.setup_schedule()
        
        logger.info("\n" + "="*70)
        logger.info("TRADING BOT SCHEDULER STARTED")
        logger.info("="*70)
        logger.info("Running in background. Press Ctrl+C to stop.\n")
        
        # Send startup notification
        self.send_email(
            "🚀 Trading Bot Started",
            f"Automated trading scheduler started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"Mode: {'DRY RUN' if self.executor.dry_run else 'LIVE TRADING'}\n"
            f"Email alerts: {self.email_enabled}"
        )
        
        # Run immediately on startup
        logger.info("Running initial signal check...")
        self.check_signals_job()
        
        # Main loop
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("\n\nScheduler stopped by user")
            self.send_email(
                "⏸️  Trading Bot Stopped",
                f"Trading scheduler stopped at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )


if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════════════════════════╗
║           AUTOMATED TRADING BOT SCHEDULER                        ║
╚══════════════════════════════════════════════════════════════════╝

This scheduler will run signal checks at (AMSTERDAM TIME):
  - 3:00 PM  (15:00) - Pre-market   (9:00 AM EST)
  - 3:35 PM  (15:35) - Post-open    (9:35 AM EST)
  - 6:00 PM  (18:00) - Midday       (12:00 PM EST)
  - 9:55 PM  (21:55) - Pre-close    (3:55 PM EST)
  - Every 2 hours    - Position monitoring
  - 10:05 PM (22:05) - Daily summary (4:05 PM EST)

US Market hours: 3:30 PM - 10:00 PM Amsterdam

Configure .env file with:
  TRADING_CAPITAL=111.55
  DRY_RUN=True  (or False for live trading)
  EMAIL_ALERTS=True
  SMTP_SERVER=smtp.gmail.com
  SENDER_EMAIL=your@email.com
  SENDER_PASSWORD=your_app_password
  RECIPIENT_EMAIL=alerts@email.com
  AUTO_EXECUTE=False  (True to auto-execute trades - DANGEROUS!)

Press Ctrl+C to stop.
    """)
    
    scheduler = TradingScheduler()
    scheduler.run()
