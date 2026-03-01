# EduBot 24x7 Setup Guide

## 🚀 **24x7 AUTOMATIC MONITORING SETUP**

This setup will keep your EduBot running 24/7 with automatic recovery from errors and internet interruptions.

---

## 📋 **REQUIREMENTS**

### ✅ **Prerequisites**
- Python 3.8+ installed
- Internet connection (initial setup only)
- Windows computer that can stay on
- Admin privileges (for some operations)

### ✅ **Additional Python Packages**
```bash
pip install psutil requests
```

---

## 🎯 **QUICK START**

### ✅ **Method 1: Simple 24x7 Monitor**
1. **Double-click**: `start_24x7.bat`
2. **Wait**: Monitor will start automatically
3. **Done**: Bot will run 24/7 with automatic recovery

### ✅ **Method 2: Advanced Robust Server**
1. **Run**: `python robust_wsgi.py`
2. **Separate**: Start ngrok manually in another window
3. **Monitor**: Use `run_24x7.py` for monitoring

---

## 🔧 **DETAILED SETUP**

### ✅ **Step 1: Install Dependencies**
```bash
pip install psutil requests
```

### ✅ **Step 2: Start 24x7 Monitoring**
```bash
# Option 1: Use batch file (recommended)
start_24x7.bat

# Option 2: Use Python directly
python run_24x7.py
```

### ✅ **Step 3: Verify Everything is Working**
- Check logs in `logs/24x7_monitor.log`
- Bot should be running at `@edubot_assistant_bot`
- Webhook should be accessible via ngrok

---

## 🛡️ **FEATURES**

### ✅ **Automatic Recovery**
- **🔄 Server Restart**: Automatically restarts if Flask crashes
- **🌐 Ngrok Restart**: Automatically restarts if ngrok fails
- **🗄️ Database Recovery**: Automatically reconnects if database fails
- **📡 Health Checks**: Continuous monitoring of all services

### ✅ **Internet Interruption Handling**
- **🔄 Retry Logic**: Automatic retry with exponential backoff
- **📊 Status Logging**: Detailed logs of all recovery attempts
- **⏰ Graceful Degradation**: Services continue working during internet issues
- **🔄 Auto-Reconnect**: Automatically reconnects when internet returns

### ✅ **Error Handling**
- **📝 Comprehensive Logging**: All errors logged with timestamps
- **🔄 Maximum Retries**: Prevents infinite loops
- **⏱️ Timeout Protection**: Prevents hanging on network issues
- **📊 Health Monitoring**: Continuous health checks

---

## 📊 **MONITORING DASHBOARD**

### ✅ **Log Files**
- **📋 Main Log**: `logs/24x7_monitor.log`
- **🔄 Server Log**: `logs/robust_server.log`
- **🤖 Bot Log**: `logs/edubot.log`

### ✅ **Health Checks**
- **🤖 Bot Token**: Validates Telegram bot access
- **📡 Webhook**: Tests webhook endpoint
- **🗄️ Database**: Checks database connectivity
- **🌐 Ngrok**: Monitors tunnel status

---

## 🚨 **TROUBLESHOOTING**

### ✅ **Common Issues**

#### **🔄 Bot Not Responding**
1. **Check**: User needs to send `/start` first
2. **Solution**: Tell users to start conversation with bot
3. **Log**: Check `logs/edubot.log` for errors

#### **🌐 Ngrok Connection Issues**
1. **Check**: Internet connection
2. **Solution**: Monitor will restart ngrok automatically
3. **Manual**: Restart ngrok if needed

#### **🗄️ Database Issues**
1. **Check**: Database file permissions
2. **Solution**: Monitor will reconnect automatically
3. **Manual**: Restart Flask server if needed

---

## 📱 **BOT ACCESS INFORMATION**

### ✅ **Bot Details**
- **🤖 Username**: `@edubot_assistant_bot`
- **📱 Phone**: 9760387360 (Anuj Uniyal)
- **🎓 Roll Number**: EDU2025001
- **🔐 Verification**: `register EDU2025001`

### ✅ **Commands**
- **📋 Help**: `help`
- **🔐 Register**: `register EDU2025001`
- **📊 Results**: `1` or `result`
- **📢 Notices**: `2` or `notice`
- **💰 Fee**: `3` or `fee`
- **👨‍🏫 Faculty**: `4` or `faculty`
- **📝 Complaint**: `5` or `complaint`
- **📱 Logout**: `6` or `logout`

---

## 🎯 **PPT PRESENTATION TIPS**

### ✅ **What to Show**
1. **🤖 Live Bot**: Show bot responding to commands
2. **📊 Dashboard**: Show monitoring logs
3. **🔐 Verification**: Show phone verification working
4. **📱 Commands**: Show all available commands
5. **🛡️ Auto-Recovery**: Explain 24x7 monitoring

### ✅ **Demonstration Script**
```
1. "This is our EduBot running 24/7"
2. "Let me show you how it works..."
3. "Send /start to @edubot_assistant_bot"
4. "Now register EDU2025001"
5. "Bot verifies Anuj Uniyal automatically"
6. "All commands work: 1-6 or text commands"
7. "System monitors itself 24/7"
8. "Automatic recovery from any issues"
```

---

## 🎉 **SUCCESS INDICATORS**

### ✅ **Everything Working When**
- **🤖 Bot**: Responds to `/start` and `register EDU2025001`
- **📡 Webhook**: Returns HTTP 200 for test requests
- **🗄️ Database**: Shows Anuj Uniyal's data
- **📊 Logs**: No critical errors in log files
- **🔄 Monitor**: Running and checking services

---

## 📞 **SUPPORT**

### ✅ **If Issues Occur**
1. **📋 Check Logs**: Look in `logs/` directory
2. **🔄 Restart**: Stop and restart `start_24x7.bat`
3. **🌐 Internet**: Ensure internet is available
4. **📱 Bot**: Verify bot token is still valid

---

## 🎯 **FINAL CHECKLIST**

### ✅ **Before PPT**
- [ ] Bot running and responding
- [ ] 24x7 monitor active
- [ ] All logs clean
- [ ] Commands working
- [ ] Phone verification working
- [ ] Ngrok tunnel active

### ✅ **During PPT**
- [ ] Show live bot interaction
- [ ] Demonstrate auto-recovery
- [ ] Explain 24x7 monitoring
- [ ] Show error handling
- [ ] Answer questions

---

**🎉 Your EduBot is now ready for 24x7 operation and PPT presentation!**
