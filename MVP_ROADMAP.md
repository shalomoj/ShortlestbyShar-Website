# ShortletsbyShar - MVP Roadmap

## 🎯 MVP Strategy

Build a functional booking platform with essential features first, then add advanced features in Phase 2.

---

## 📋 MVP Features (Phase 1)

### What's Included in MVP

#### Frontend Features
✅ **Homepage**
- Hero section with search
- Featured apartments showcase
- About section
- Contact information

✅ **Apartment Catalog**
- Grid view of all apartments
- Basic filters (location, bedrooms, price range)
- Search functionality
- Sorting options

✅ **Apartment Details**
- Image gallery
- Full description
- Amenities list
- Location information
- Pricing details
- Booking inquiry form

✅ **Booking Inquiry Form**
- Guest information collection
- Date selection
- Number of guests
- Special requests
- Submit inquiry (no payment yet)

✅ **Contact Page**
- Contact form
- Business information
- WhatsApp link (manual)
- Email and phone

✅ **Basic Admin Panel**
- Login for admin
- View all apartments
- Add new apartment
- Edit apartment details
- Upload images
- View booking inquiries
- Mark inquiries as processed

#### Backend Features
✅ **API Endpoints**
- GET /api/apartments (list with filters)
- GET /api/apartments/:slug (single apartment)
- POST /api/apartments (admin only)
- PUT /api/apartments/:id (admin only)
- DELETE /api/apartments/:id (admin only)
- POST /api/inquiries (submit booking inquiry)
- GET /api/inquiries (admin only)
- POST /api/admin/login (admin authentication)

✅ **Database Models**
- Apartment model
- Inquiry model
- Admin user model (simple)

✅ **Core Functionality**
- CRUD operations for apartments
- Image upload to Cloudinary
- Basic admin authentication
- Inquiry submission and management
- Data validation

### What's NOT in MVP (Phase 2)
❌ Customer user accounts
❌ Online payment processing
❌ Automated email notifications
❌ WhatsApp API integration (manual link only)
❌ Review and rating system
❌ Booking calendar with conflicts
❌ Advanced admin dashboard
❌ Analytics and reporting
❌ Multi-language support

---

## 🏗️ Simplified Architecture

```
Frontend (React)
    ↓
Backend API (Express)
    ↓
MongoDB Database
    ↓
Cloudinary (Images)
```

---

## 📊 MVP Database Schema

### 1. Apartments Collection
```javascript
{
  _id: ObjectId,
  name: String,
  slug: String,
  description: String,
  location: {
    city: String, // Lagos or Abuja
    area: String,
    address: String
  },
  bedrooms: Number,
  bathrooms: Number,
  maxGuests: Number,
  amenities: [String],
  images: [String], // Cloudinary URLs
  pricing: {
    basePrice: Number,
    cleaningFee: Number
  },
  features: {
    wifi: Boolean,
    parking: Boolean,
    kitchen: Boolean,
    airConditioning: Boolean,
    tv: Boolean,
    washer: Boolean
  },
  active: Boolean,
  createdAt: Date,
  updatedAt: Date
}
```

### 2. Inquiries Collection
```javascript
{
  _id: ObjectId,
  apartment: ObjectId, // Reference to apartment
  guestName: String,
  email: String,
  phone: String,
  checkIn: Date,
  checkOut: Date,
  adults: Number,
  children: Number,
  message: String,
  status: String, // 'new', 'contacted', 'booked', 'cancelled'
  createdAt: Date
}
```

### 3. Admins Collection (Simple)
```javascript
{
  _id: ObjectId,
  username: String,
  password: String, // Hashed
  email: String,
  createdAt: Date
}
```

---

## 🎨 MVP Design

### Pages
1. **Home** (`/`)
2. **Apartments** (`/apartments`)
3. **Apartment Details** (`/apartments/:slug`)
4. **Contact** (`/contact`)
5. **Admin Login** (`/admin/login`)
6. **Admin Dashboard** (`/admin`)
7. **Admin Apartments** (`/admin/apartments`)
8. **Admin Inquiries** (`/admin/inquiries`)

### Color Scheme
- Primary: #2563eb (Blue)
- Secondary: #f59e0b (Amber)
- Success: #10b981 (Green)
- Background: #f8fafc (Light gray)

---

## 🚀 MVP Development Timeline

### Week 1: Backend Foundation
- [x] Day 1-2: Project setup, database models
- [ ] Day 3-4: API endpoints for apartments
- [ ] Day 5-6: Admin authentication
- [ ] Day 7: Image upload integration

### Week 2: Frontend Core
- [ ] Day 1-2: React setup, routing, homepage
- [ ] Day 3-4: Apartment catalog with filters
- [ ] Day 5-6: Apartment details page
- [ ] Day 7: Responsive design refinement

### Week 3: Forms & Admin
- [ ] Day 1-2: Booking inquiry form
- [ ] Day 3-4: Contact form
- [ ] Day 5-6: Admin panel (apartments)
- [ ] Day 7: Admin panel (inquiries)

### Week 4: Polish & Deploy
- [ ] Day 1-2: Testing and bug fixes
- [ ] Day 3-4: Sample data, documentation
- [ ] Day 5-6: Deployment setup
- [ ] Day 7: Final testing and launch

**Total MVP Timeline: 4 weeks**

---

## 💰 MVP Costs

### Development Phase
- Free (self-hosted development)

### Hosting (Monthly)
- Vercel (Frontend): Free tier
- Railway (Backend): $5/month
- MongoDB Atlas: Free tier (512MB)
- Cloudinary: Free tier (25GB)
- Domain: ~$1.25/month ($15/year)

**Total MVP Cost: ~$6-7/month**

---

## 📝 MVP User Flow

### Customer Journey
1. Visit homepage
2. Browse apartments or search
3. Click on apartment for details
4. View images, amenities, pricing
5. Fill booking inquiry form
6. Submit inquiry
7. Receive confirmation message
8. Admin contacts via phone/WhatsApp

### Admin Journey
1. Login to admin panel
2. View dashboard
3. Manage apartments (add/edit/delete)
4. Upload apartment images
5. View booking inquiries
6. Contact customers manually
7. Mark inquiries as processed

---

## 🎯 MVP Success Criteria

The MVP is successful when:
- ✅ Customers can browse all apartments
- ✅ Filters work correctly (location, bedrooms, price)
- ✅ Apartment details display properly
- ✅ Booking inquiry form submits successfully
- ✅ Admin can manage apartments
- ✅ Admin can view and process inquiries
- ✅ Site is mobile responsive
- ✅ Images load quickly
- ✅ No critical bugs

---

## 🔄 Phase 2 Features (After MVP)

Once MVP is validated with real users, add:

### Priority 1 (Next 2-3 weeks)
1. **User Authentication**
   - Customer accounts
   - Login/signup
   - Profile management

2. **Payment Integration**
   - Paystack integration
   - Secure checkout
   - Payment confirmation

3. **Email Notifications**
   - Booking confirmations
   - Admin notifications
   - Automated emails

### Priority 2 (Following 2-3 weeks)
4. **Booking Calendar**
   - Availability checking
   - Conflict prevention
   - Date blocking

5. **Review System**
   - Customer reviews
   - Rating system
   - Review moderation

6. **WhatsApp Integration**
   - Automated messages
   - Booking confirmations
   - Customer support

### Priority 3 (Future)
7. **Advanced Admin Features**
   - Analytics dashboard
   - Revenue reports
   - User management

8. **Enhanced Features**
   - Multi-language support
   - Currency converter
   - Virtual tours

---

## 🛠️ Technology Stack (MVP)

### Frontend
- React 18
- React Router
- Tailwind CSS
- Axios
- React Hook Form

### Backend
- Node.js
- Express.js
- MongoDB + Mongoose
- JWT (for admin auth)
- Multer + Cloudinary

### Tools
- Git/GitHub
- VS Code
- Postman (API testing)

---

## 📦 MVP Deliverables

1. **Functional Website**
   - Public-facing pages
   - Admin panel
   - Mobile responsive

2. **Documentation**
   - README with setup instructions
   - API documentation
   - Admin user guide

3. **Sample Data**
   - 5-10 sample apartments
   - Test inquiries

4. **Deployment**
   - Live website URL
   - Admin credentials
   - Database backup

---

## 🎓 Learning from MVP

### What to Measure
- Number of apartment views
- Inquiry submission rate
- Most viewed apartments
- Popular locations
- Common guest questions
- Admin workflow efficiency

### Feedback to Collect
- User experience feedback
- Booking process clarity
- Missing features
- Performance issues
- Mobile usability

---

## ✅ Next Steps

1. **Review this MVP plan** - Confirm features and timeline
2. **Start building** - Begin with backend setup
3. **Iterate quickly** - Build, test, improve
4. **Launch MVP** - Get it in front of real users
5. **Collect feedback** - Learn what users need
6. **Plan Phase 2** - Prioritize based on feedback

---

**Ready to start building the MVP? Let's create the project structure!** 🚀