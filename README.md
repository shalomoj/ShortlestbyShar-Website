# ShortletsbyShar - Booking Website

## 🚀 How to Run Your Website

### Super Simple - No Installation Required!

1. **Locate the `index.html` file** in this folder
2. **Double-click on `index.html`** - It will open in your default web browser
3. **That's it!** Your website is now running

### Alternative Methods:

#### Method 1: Right-click and Open
- Right-click on `index.html`
- Select "Open with" → Choose your preferred browser (Chrome, Edge, Firefox, etc.)

#### Method 2: Drag and Drop
- Open your web browser
- Drag the `index.html` file into the browser window

#### Method 3: From VS Code
- Right-click on `index.html` in VS Code
- Select "Open with Live Server" (if you have the Live Server extension)
- OR select "Reveal in File Explorer" → then double-click the file

---

## 📁 Files in This Project

- **index.html** - Main website file (THIS IS THE FILE YOU OPEN)
- **styles.css** - Styling and design
- **script.js** - Functionality and apartment data
- **README.md** - This instruction file

---

## ✨ Features

### Current Features (Working Now!)
✅ **Homepage** with hero section and search
✅ **8 Sample Apartments** (Lagos & Abuja)
✅ **Filter by Location** (Lagos/Abuja)
✅ **Filter by Bedrooms** (1-4+)
✅ **Filter by Price Range**
✅ **Booking Form** with date selection
✅ **Contact Form**
✅ **Mobile Responsive** - works on phones and tablets
✅ **Beautiful Design** with modern UI

### How It Works
1. Customers browse apartments
2. Click on any apartment to see details
3. Fill out booking form with dates and guest info
4. Submit booking request
5. You receive the inquiry and contact them via phone/WhatsApp

---

## 📝 Customizing Your Website

### Update Your Contact Information

Open `index.html` and find these sections to update:

#### Phone Number (Line ~185)
```html
<p>+234 XXX XXX XXXX</p>
```
Change to your actual phone number

#### Email (Line ~189)
```html
<p>info@shortletsbyshar.com</p>
```
Change to your actual email

#### WhatsApp Link (Line ~193)
```html
<a href="https://wa.me/234XXXXXXXXXX" target="_blank">
```
Replace `234XXXXXXXXXX` with your WhatsApp number (include country code, no + or spaces)
Example: `https://wa.me/2348012345678`

### Add Your Own Apartments

Open `script.js` and find the `apartments` array (starts at line 2). Add new apartments following this format:

```javascript
{
    id: 9,  // Unique number
    name: "Your Apartment Name",
    location: { city: "Lagos", area: "Your Area" },  // Lagos or Abuja
    bedrooms: 2,
    bathrooms: 2,
    maxGuests: 4,
    price: 75000,  // Price per night in Naira
    image: "https://your-image-url.com/image.jpg",
    amenities: ["WiFi", "Parking", "Kitchen", "AC", "TV"],
    description: "Your apartment description here"
}
```

### Change Images

Replace the image URLs in `script.js` with your own apartment photos:
- Upload photos to a free image hosting service (like Imgur, Cloudinary, or Google Drive)
- Get the direct image link
- Replace the `image:` URL in the apartment data

---

## 🎨 Customizing Colors

Open `styles.css` to change colors:

- **Primary Blue**: Search for `#2563eb` and replace with your color
- **Secondary Orange**: Search for `#f59e0b` and replace with your color
- **Success Green**: Search for `#10b981` and replace with your color

---

## 📱 Testing on Mobile

1. Open the website on your computer
2. Press `F12` to open Developer Tools
3. Click the mobile/tablet icon (or press `Ctrl+Shift+M`)
4. Select different device sizes to test

---

## 🌐 Publishing Your Website Online

### Option 1: Free Hosting (Netlify)
1. Go to [netlify.com](https://netlify.com)
2. Sign up for free
3. Drag and drop your folder (with all 3 files)
4. Get your free website URL: `yoursite.netlify.app`

### Option 2: Free Hosting (GitHub Pages)
1. Create account on [github.com](https://github.com)
2. Create new repository
3. Upload your files
4. Enable GitHub Pages in settings
5. Get URL: `yourusername.github.io/repository-name`

### Option 3: Free Hosting (Vercel)
1. Go to [vercel.com](https://vercel.com)
2. Sign up for free
3. Import your project
4. Deploy with one click

---

## 💡 Tips

### For Best Results:
- Use high-quality apartment photos (at least 1200x800 pixels)
- Keep descriptions clear and concise
- Update prices regularly
- Respond to inquiries quickly
- Test on mobile devices

### Getting Apartment Photos:
- Take professional photos of your apartments
- Use good lighting
- Show different angles
- Include amenities (kitchen, bathroom, living room)

---

## 🔄 Next Steps (Future Enhancements)

When you're ready to add more features:
1. **Online Payments** - Integrate Paystack
2. **User Accounts** - Let customers create accounts
3. **Admin Panel** - Manage apartments from a dashboard
4. **Email Notifications** - Automatic booking confirmations
5. **WhatsApp Integration** - Automated messages
6. **Reviews** - Customer feedback system
7. **Availability Calendar** - Real-time booking management

All these features are planned in the technical documents!

---

## 📞 Need Help?

If you need help customizing or have questions:
1. Check the technical documentation files
2. The website works offline - no internet needed to test
3. All changes are instant - just refresh the browser

---

## ✅ Quick Checklist

Before sharing your website:
- [ ] Updated phone number
- [ ] Updated email address
- [ ] Updated WhatsApp link
- [ ] Added your apartment photos
- [ ] Updated apartment details
- [ ] Tested on mobile
- [ ] Tested booking form
- [ ] Tested contact form

---

**Your website is ready to use! Just open `index.html` in any web browser.** 🎉