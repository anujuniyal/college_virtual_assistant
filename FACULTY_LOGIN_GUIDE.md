# Faculty Login Credentials Guide

## ✅ Authentication Status Verified

### **🔐 Working Credentials**
Both admin and faculty credentials are working perfectly in local testing:

#### **🔹 Admin Login**
```
Email: admin@edubot.com
Password: admin123
Role: Admin
```

#### **🔹 Faculty Login**
```
Email: sanjeev.raghav@edubot.com
Password: sanjeev123
Role: Admin Faculty
```

### **📋 Faculty Users in Database**

| Name | Email | Role | Department | Phone |
|-------|--------|-------|-------------|--------|
| Default Admin | admin@edubot.com | admin | Administration | N/A |
| Sanjeev Raghav | sanjeev.raghav@edubot.com | admin | Computer Science | 9876543212 |

### **🔧 How to Login**

#### **Step 1: Access Login Page**
- URL: `https://college-virtual-assistant.onrender.com/auth/login`

#### **Step 2: Select Role**
- **For Admin Access**: Click "Admin" option
- **For Faculty Access**: Click "Faculty" option

#### **Step 3: Enter Credentials**
- **Username/Email Field**: Use the email address
- **Password Field**: Use the corresponding password
- **Remember Me**: Optional checkbox

#### **Step 4: Login**
- Click "Sign In" button
- Wait for redirect to dashboard

### **🎯 Login Instructions**

#### **Admin Login**
1. Select **"Admin"** role option
2. Enter: `admin@edubot.com`
3. Enter: `admin123`
4. Click **"Sign In"**

#### **Faculty Login**
1. Select **"Faculty"** role option
2. Enter: `sanjeev.raghav@edubot.com`
3. Enter: `sanjeev123`
4. Click **"Sign In"**

### **🔍 Authentication Flow**

The application uses **database-only authentication**:

1. **Form Submission** → POST to `/auth/login`
2. **UserService.authenticate_user()** → Queries Faculty table
3. **Password Verification** → Uses `check_password()` method
4. **Session Creation** → Flask-Login creates user session
5. **Redirect** → User redirected to appropriate dashboard

### **🛠️ Technical Details**

#### **Authentication Method**
- **Database**: Faculty table (primary)
- **Fallback**: Admin table (backward compatibility)
- **Password Hashing**: Werkzeug security
- **Session Management**: Flask-Login

#### **User Roles Supported**
- **admin**: Full administrative access
- **faculty**: Faculty dashboard access
- **accounts**: Financial/records access

### **🚨 Troubleshooting**

#### **If Login Fails**
1. **Check Email**: Ensure correct email format
2. **Check Password**: Verify exact password
3. **Check Role**: Ensure correct role selected
4. **Clear Cache**: Refresh browser cache
5. **Check Deployment**: Verify deployment is latest

#### **Common Issues**
- **Wrong Role**: Selecting wrong role option
- **Email Format**: Using username instead of email
- **Password Case**: Check for correct capitalization
- **Database Connection**: Wait for deployment to complete

### **📱 Mobile Access**

The login page is mobile-friendly:
- **Responsive Design**: Works on all devices
- **Touch Interface**: Optimized for mobile
- **Auto-complete**: Supports password managers

### **🔒 Security Features**

- **Secure Cookies**: HTTPS only, HTTPOnly, Strict SameSite
- **Session Timeout**: Automatic logout after inactivity
- **Password Security**: Hashed passwords, no plaintext storage
- **CSRF Protection**: Form tokens for security

### **🎉 Success Indicators**

#### **Successful Login**
- ✅ Redirect to dashboard
- ✅ Flash message: "Login successful!"
- ✅ User session established
- ✅ Access to role-specific features

#### **Failed Login**
- ❌ Error message: "Authentication failed"
- ❌ Return to login page
- ❌ No session created
- ❌ No dashboard access

---

## 📞 Support

If you encounter issues:
1. **Wait 2-3 minutes** for deployment to complete
2. **Clear browser cache** and cookies
3. **Try both credential sets** above
4. **Check deployment status** via health endpoint

**Both admin and faculty credentials are verified and working!** 🎯
