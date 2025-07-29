# 🏰 Logo Setup Instructions

## 📁 **Logo Location**
Place your logo file at: `static/logo.png`

## 🎨 **Logo Specifications**

### **Recommended Format**
- **File Format**: PNG (preferred) or JPG
- **Size**: 200x200 pixels or larger (will be scaled automatically)
- **Background**: Transparent or white background works best
- **File Name**: `logo.png`

### **File Path**
```
reservation system/
├── static/
│   ├── logo.png          ← Place your logo here
│   ├── index.html
│   ├── styles.css
│   └── script.js
```

## 🔧 **What's Already Configured**

The system is already set up to use your logo in:

### **1. Navigation Bar**
- Logo appears in the top navigation
- Size: 40px height, auto width
- Styled with rounded corners

### **2. Hero Section**
- Logo appears in the main hero area
- Size: 200px width, auto height
- Styled with shadow and rounded corners

### **3. PDF Reservation Slips** ⭐
- Logo appears in the header of all printed reservation slips
- Size: 60px x 60px
- Embedded as base64 data for reliable printing
- Works for both daily reports and individual reservation slips

## 📝 **How to Add Your Logo**

### **Step 1: Prepare Your Logo**
1. Save your logo as `logo.png`
2. Ensure it's high quality (200x200px or larger)
3. Use transparent background if possible

### **Step 2: Add to Project**
1. Copy your `logo.png` file
2. Paste it into the `static/` folder
3. Ensure the file is named exactly `logo.png`

### **Step 3: Test Locally**
```bash
# Start the application
python start_system.py

# Open in browser
http://localhost:8000
```

### **Step 4: Deploy to Railway**
```bash
# Commit and push changes
git add static/logo.png
git commit -m "Add Castle Pub logo"
git push origin main
```

## 🎯 **Logo Display Locations**

Your logo will appear in:

1. **Navigation Bar** (top left)
   - Small version (40px height)
   - Next to "The Castle Pub" text

2. **Hero Section** (main page)
   - Large version (200px width)
   - Centered in the hero area
   - With floating animation

3. **PDF Reservation Slips** ⭐
   - Logo appears in the header of all printed reservation slips
   - Size: 60px x 60px
   - Embedded as base64 data for reliable printing
   - Works for both daily reports and individual reservation slips

4. **Admin Dashboard** (if configured)
   - Consistent branding throughout

## 🔍 **Troubleshooting**

### **Logo Not Showing**
- Check file name is exactly `logo.png`
- Ensure file is in `static/` folder
- Clear browser cache (Ctrl+F5)
- Check browser console for errors

### **Logo Too Big/Small**
- The CSS automatically scales the logo
- Navigation logo: 40px height
- Hero logo: 200px width
- PDF logo: 60px x 60px
- Adjust your source image if needed

### **Logo Looks Blurry**
- Use a higher resolution source image
- PNG format preserves quality better
- Minimum 200x200px recommended

## 🎨 **Customization**

If you want to adjust the logo styling, edit `static/styles.css`:

```css
/* Navigation logo */
.logo-image {
    height: 40px;  /* Adjust height */
    width: auto;
    border-radius: 4px;
}

/* Hero logo */
.hero-logo {
    width: 200px;  /* Adjust width */
    height: auto;
    border-radius: 8px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
}
```

## ✅ **Quick Checklist**

- [ ] Logo file saved as `logo.png`
- [ ] File placed in `static/` folder
- [ ] Logo appears in navigation
- [ ] Logo appears in hero section
- [ ] Logo appears in PDF reservation slips
- [ ] Tested locally
- [ ] Pushed to GitHub
- [ ] Deployed to Railway

## 📄 **PDF Features**

Your logo will automatically appear in:

### **Daily Reports**
- **Endpoint**: `/api/admin/reports/daily?report_date=2024-01-15`
- **Format**: HTML (can be printed to PDF)
- **Logo**: 60px x 60px in header

### **Individual Reservation Slips**
- **Endpoint**: `/api/admin/reservations/{id}/slip`
- **Format**: HTML (can be printed to PDF)
- **Logo**: 60px x 60px in header

### **How to Test PDF with Logo**
1. Add your logo to `static/logo.png`
2. Start the application
3. Go to admin dashboard
4. Generate a daily report or individual slip
5. The logo will appear in the header

Your logo will now be displayed throughout The Castle Pub reservation system, including all printed materials! 🎉 