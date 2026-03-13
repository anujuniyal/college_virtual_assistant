#!/usr/bin/env python3
"""
Test Bot Activation Process
"""
import os
import sys
import subprocess
import time

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

def test_bot_activation():
    """Test the bot activation process exactly as the dashboard does"""
    print("🧪 Testing Bot Activation Process")
    print("=" * 40)
    
    # Check if bot is already running
    print("1. Checking if bot is already running...")
    try:
        import psutil
        bot_already_running = False
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            if proc.info['name'] in ['python', 'python.exe']:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if any(script in cmdline for script in ['run_telegram_bot_simple.py', 'run_telegram_bot_polling.py', 'run_telegram_bot.py', 'activate_telegram_bot.py', 'simple_telegram_bot.py']):
                    bot_already_running = True
                    print(f"   Bot already running with PID: {proc.info['pid']}")
                    break
        
        if bot_already_running:
            print("   ✅ Bot is already running")
            return True
    except Exception as e:
        print(f"   ❌ Error checking running processes: {str(e)}")
        return False
    
    # Find bot script
    print("2. Finding bot script...")
    bot_scripts = ['run_telegram_bot_simple.py', 'run_telegram_bot_polling.py', 'run_telegram_bot.py', 'activate_telegram_bot.py', 'simple_telegram_bot.py']
    bot_script_path = None
    
    for script in bot_scripts:
        script_path = os.path.join(os.getcwd(), script)
        if os.path.exists(script_path):
            bot_script_path = script_path
            print(f"   Found bot script: {script_path}")
            break
    
    if not bot_script_path:
        print("   ❌ No bot runner script found")
        return False
    
    # Start bot process
    print("3. Starting bot process...")
    try:
        env = os.environ.copy()
        env['PYTHONPATH'] = os.getcwd()
        
        process = subprocess.Popen([
            'python', bot_script_path
        ], 
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=os.getcwd(),
        env=env,
        text=True,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        )
        
        print(f"   Process started with PID: {process.pid}")
        
        # Wait a moment to check if it starts successfully
        print("4. Checking if process stays alive...")
        time.sleep(3)
        
        if process.poll() is None:
            print(f"   ✅ Bot started successfully with PID: {process.pid}")
            
            # Verify with status check
            print("5. Verifying with status check...")
            time.sleep(2)
            
            # Check if the process is still running
            still_running = False
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if proc.info['pid'] == process.pid:
                    still_running = True
                    break
            
            if still_running:
                print("   ✅ Bot process is confirmed running")
                return True
            else:
                print("   ❌ Bot process disappeared")
                return False
        else:
            exit_code = process.poll()
            print(f"   ❌ Bot failed to start. Exit code: {exit_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Exception starting bot: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_bot_activation()
    
    if success:
        print("\n✅ Bot activation test PASSED!")
    else:
        print("\n❌ Bot activation test FAILED!")
        print("Check the logs for more details.")
