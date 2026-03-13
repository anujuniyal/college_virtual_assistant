# College Virtual Assistant Bot

A comprehensive Telegram bot for college information services with visitor and student modes.

## 🚀 Features

### 📋 Visitor Service Mode
- **Admission Process**: Complete admission information with eligibility, process, documents, and important dates
- **Courses & Fees**: Detailed course information with fee structure for all programs
- **Faculty Directory**: Faculty information with department, email, and consultation timings
- **Facilities**: Complete campus facilities information
- **Contact Information**: Reception and department contact details
- **Help Menu**: Interactive help with numbered options

### 🎓 Student Mode (After Verification)
- **Academic Services**: View results and check notices
- **Fee Services**: Check fee status and payment details
- **Faculty Search**: Search faculty information
- **Complaint System**: File anti-ragging and other complaints
- **Session Management**: Secure login/logout functionality
- **Daily View Limits**: Rate limiting for result and fee queries

### 🔐 Student Verification System
- **Two-Step Verification**: Phone number + Roll number verification
- **Phone Sharing**: Secure phone number sharing via Telegram button
- **Database Matching**: Automatic verification against student records
- **Telegram Mapping**: Map Telegram user ID to student record
- **Session Management**: Secure session handling

### 📊 Database Integration
- **Visitor Query Tracking**: Track all visitor queries for analysis
- **Student Records**: Complete student information management
- **Faculty Database**: Faculty directory with contact information
- **Results Management**: Academic results with visibility periods
- **Fee Records**: Comprehensive fee tracking
- **Notices**: Digital notice board with expiration
- **Complaint System**: Anti-ragging complaint management

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- Telegram Bot Token
- SQLite (default) or other database

### Setup Steps

1. **Clone and Setup**
   ```bash
   cd college_virtual_assistant
   pip install -r requirements.txt
   ```

2. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your Telegram bot token
   ```

3. **Database Setup**
   ```bash
   python setup_database_complete.py
   ```

4. **Run Tests**
   ```bash
   python test_bot_functionality.py
   ```

5. **Start the Bot**
   ```bash
   python run_telegram_bot_polling.py
   ```

## 📱 Bot Usage

### For Visitors
1. Start the bot on Telegram
2. The bot greets you in **Visitor Service Mode**
3. Use numbered options (1-6) or keywords:
   - `1` or `admission` - Admission process
   - `2` or `courses` - Courses and fees
   - `3` or `faculty` - Faculty directory
   - `4` or `facilities` - Campus facilities
   - `5` or `contact` - Contact information
   - `6` or `help` - Help menu

### For Students
1. **Verification Process**:
   - Type `register YOUR_ROLL_NUMBER`
   - Share your phone number using the button
   - Bot verifies both roll number and phone number

2. **Student Services** (after verification):
   - `1` or `results` - View your academic results
   - `2` or `notices` - Check latest notifications
   - `3` or `fee` - Check fee status
   - `4` or `faculty` - Search faculty
   - `5` or `complaint` - File complaints
   - `6` or `logout` - End session

## 🗃️ Database Schema

### Core Tables
- **students**: Student records with Telegram integration
- **faculty**: Faculty directory
- **admins**: Admin users (admin, faculty, accounts roles)
- **notifications**: Digital notice board
- **results**: Academic results with visibility periods
- **fee_records**: Fee tracking
- **complaints**: Anti-ragging complaints
- **visitor_queries**: Visitor query tracking
- **telegram_user_mappings**: Telegram user ID mappings

### Sample Data
The setup script creates sample data including:
- 3 Admin users
- 5 Faculty members
- 5 Students with roll numbers EDU20240001-EDU20240005
- Fee records, results, and notices
- Faculty directory and contact information

## 🔧 Configuration

### Environment Variables
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
DATABASE_URL=sqlite:///college_assistant.db
SECRET_KEY=your_secret_key_here
```

### Rate Limiting
- **Results**: 1 view per day per student
- **Fee Status**: 1 view per day per student
- Configurable via `Config.RATE_LIMIT_RESULT_QUERIES` and `Config.RATE_LIMIT_FEE_QUERIES`

## 🧪 Testing

Run the comprehensive test suite:
```bash
python test_bot_functionality.py
```

Tests cover:
- Visitor mode functionality
- Student verification process
- Student mode services
- Database integration
- Telegram service integration

## 📊 Sample Student Credentials

For testing purposes, use these sample student records:

| Roll Number | Name | Phone Number | Department |
|-------------|------|--------------|------------|
| EDU20240001 | Anuj Kumar | 9876543201 | Computer Science |
| EDU20240002 | Priya Singh | 9876543202 | Electronics |
| EDU20240003 | Rahul Sharma | 9876543203 | Mechanical |

## 🔐 Security Features

- **Phone Verification**: Secure phone number sharing via Telegram
- **Roll Number Matching**: Verification against database records
- **Session Management**: Secure session handling with timeout
- **Rate Limiting**: Prevent abuse of sensitive information
- **Input Validation**: Comprehensive input sanitization
- **Error Handling**: Secure error messages and logging

## 📞 Support & Contact

For any issues or queries:
- **Bot Issues**: Check logs and ensure database is properly set up
- **Database Issues**: Run setup script again
- **Telegram Issues**: Verify bot token and permissions

## 🚀 Deployment

### Local Development
```bash
python run_telegram_bot_polling.py
```

### Production
- Use webhook mode for production
- Configure proper database (PostgreSQL/MySQL)
- Set up monitoring and logging
- Use environment variables for configuration

## 📝 Features Implemented

✅ **Visitor Service Mode**
- Complete college information system
- Interactive numbered menu system
- Detailed admission, course, and contact information

✅ **Student Verification**
- Two-factor authentication (phone + roll number)
- Secure Telegram integration
- Database-backed verification

✅ **Student Services**
- Personalized result viewing
- Fee status checking
- Notice board access
- Faculty directory search
- Complaint filing system

✅ **Database Integration**
- Complete ORM models
- Query tracking and analytics
- Sample data population

✅ **Security & Performance**
- Input validation and sanitization
- Rate limiting for sensitive data
- Session management
- Error handling and logging

## 🎯 Bot Flow Summary

1. **Bot Starts** → Greets in Visitor Service Mode
2. **Visitor Interactions** → Provides college information
3. **Student Verification** → Phone sharing + roll number entry
4. **Student Mode** → Personalized services access
5. **Session Management** → Secure logout and re-verification

The bot is now fully functional and ready for deployment! 🎉
