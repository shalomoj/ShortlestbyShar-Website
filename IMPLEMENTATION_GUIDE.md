# ShortletsbyShar - Implementation Guide

## Quick Start Guide

This guide provides step-by-step instructions and code examples for implementing the ShortletsbyShar booking platform.

---

## 📁 Project Structure

```
shortletsbyshar/
├── frontend/                    # React frontend application
│   ├── public/
│   │   ├── index.html
│   │   ├── favicon.ico
│   │   └── images/
│   ├── src/
│   │   ├── components/         # Reusable components
│   │   │   ├── common/         # Shared components
│   │   │   │   ├── Navbar.jsx
│   │   │   │   ├── Footer.jsx
│   │   │   │   ├── Button.jsx
│   │   │   │   └── LoadingSpinner.jsx
│   │   │   ├── apartments/     # Apartment-related components
│   │   │   │   ├── ApartmentCard.jsx
│   │   │   │   ├── ApartmentGrid.jsx
│   │   │   │   ├── ApartmentDetails.jsx
│   │   │   │   ├── ImageGallery.jsx
│   │   │   │   └── FilterSidebar.jsx
│   │   │   ├── booking/        # Booking components
│   │   │   │   ├── BookingForm.jsx
│   │   │   │   ├── DateRangePicker.jsx
│   │   │   │   ├── PricingCalculator.jsx
│   │   │   │   └── BookingConfirmation.jsx
│   │   │   ├── user/           # User components
│   │   │   │   ├── LoginForm.jsx
│   │   │   │   ├── SignupForm.jsx
│   │   │   │   ├── UserProfile.jsx
│   │   │   │   └── BookingHistory.jsx
│   │   │   ├── admin/          # Admin components
│   │   │   │   ├── AdminSidebar.jsx
│   │   │   │   ├── ApartmentForm.jsx
│   │   │   │   ├── BookingTable.jsx
│   │   │   │   └── Dashboard.jsx
│   │   │   └── reviews/        # Review components
│   │   │       ├── ReviewCard.jsx
│   │   │       ├── ReviewForm.jsx
│   │   │       └── ReviewList.jsx
│   │   ├── pages/              # Page components
│   │   │   ├── Home.jsx
│   │   │   ├── Apartments.jsx
│   │   │   ├── ApartmentDetail.jsx
│   │   │   ├── Booking.jsx
│   │   │   ├── Login.jsx
│   │   │   ├── Signup.jsx
│   │   │   ├── Profile.jsx
│   │   │   ├── MyBookings.jsx
│   │   │   ├── Admin.jsx
│   │   │   ├── About.jsx
│   │   │   └── Contact.jsx
│   │   ├── redux/              # Redux store
│   │   │   ├── store.js
│   │   │   ├── slices/
│   │   │   │   ├── authSlice.js
│   │   │   │   ├── apartmentSlice.js
│   │   │   │   └── bookingSlice.js
│   │   ├── services/           # API services
│   │   │   ├── api.js
│   │   │   ├── authService.js
│   │   │   ├── apartmentService.js
│   │   │   ├── bookingService.js
│   │   │   └── paymentService.js
│   │   ├── utils/              # Utility functions
│   │   │   ├── dateUtils.js
│   │   │   ├── priceUtils.js
│   │   │   └── validators.js
│   │   ├── hooks/              # Custom hooks
│   │   │   ├── useAuth.js
│   │   │   ├── useBooking.js
│   │   │   └── useApartments.js
│   │   ├── App.jsx
│   │   ├── index.js
│   │   └── index.css
│   ├── package.json
│   ├── tailwind.config.js
│   └── .env
│
├── backend/                     # Node.js backend application
│   ├── src/
│   │   ├── config/             # Configuration files
│   │   │   ├── database.js
│   │   │   ├── cloudinary.js
│   │   │   └── paystack.js
│   │   ├── models/             # Mongoose models
│   │   │   ├── User.js
│   │   │   ├── Apartment.js
│   │   │   ├── Booking.js
│   │   │   ├── Review.js
│   │   │   └── Inquiry.js
│   │   ├── controllers/        # Route controllers
│   │   │   ├── authController.js
│   │   │   ├── apartmentController.js
│   │   │   ├── bookingController.js
│   │   │   ├── paymentController.js
│   │   │   ├── reviewController.js
│   │   │   └── adminController.js
│   │   ├── routes/             # API routes
│   │   │   ├── authRoutes.js
│   │   │   ├── apartmentRoutes.js
│   │   │   ├── bookingRoutes.js
│   │   │   ├── paymentRoutes.js
│   │   │   ├── reviewRoutes.js
│   │   │   └── adminRoutes.js
│   │   ├── middleware/         # Custom middleware
│   │   │   ├── auth.js
│   │   │   ├── admin.js
│   │   │   ├── errorHandler.js
│   │   │   ├── validator.js
│   │   │   └── upload.js
│   │   ├── services/           # Business logic
│   │   │   ├── emailService.js
│   │   │   ├── whatsappService.js
│   │   │   ├── bookingService.js
│   │   │   └── paymentService.js
│   │   ├── utils/              # Utility functions
│   │   │   ├── generateReference.js
│   │   │   ├── dateHelpers.js
│   │   │   └── priceCalculator.js
│   │   ├── app.js              # Express app setup
│   │   └── server.js           # Server entry point
│   ├── package.json
│   └── .env
│
├── docs/                        # Documentation
│   ├── API.md
│   ├── DEPLOYMENT.md
│   └── USER_GUIDE.md
│
└── README.md
```

---

## 🚀 Step-by-Step Implementation

### Step 1: Initialize Projects

#### Backend Setup
```bash
# Create backend directory
mkdir backend && cd backend

# Initialize Node.js project
npm init -y

# Install dependencies
npm install express mongoose dotenv bcryptjs jsonwebtoken cors
npm install express-validator multer cloudinary axios nodemailer
npm install --save-dev nodemon

# Create basic structure
mkdir -p src/{config,models,controllers,routes,middleware,services,utils}
touch src/app.js src/server.js .env
```

#### Frontend Setup
```bash
# Create React app with TypeScript
npx create-react-app frontend --template typescript
cd frontend

# Install dependencies
npm install react-router-dom @reduxjs/toolkit react-redux
npm install axios react-hook-form zod @hookform/resolvers
npm install tailwindcss postcss autoprefixer
npm install lucide-react react-datepicker react-image-gallery
npm install @headlessui/react

# Initialize Tailwind CSS
npx tailwindcss init -p
```

---

### Step 2: Backend Implementation

#### Database Configuration (`backend/src/config/database.js`)
```javascript
const mongoose = require('mongoose');

const connectDB = async () => {
  try {
    const conn = await mongoose.connect(process.env.MONGODB_URI, {
      useNewUrlParser: true,
      useUnifiedTopology: true,
    });
    
    console.log(`MongoDB Connected: ${conn.connection.host}`);
  } catch (error) {
    console.error(`Error: ${error.message}`);
    process.exit(1);
  }
};

module.exports = connectDB;
```

#### User Model (`backend/src/models/User.js`)
```javascript
const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');

const userSchema = new mongoose.Schema({
  email: {
    type: String,
    required: [true, 'Email is required'],
    unique: true,
    lowercase: true,
    trim: true,
    match: [/^\S+@\S+\.\S+$/, 'Please provide a valid email']
  },
  password: {
    type: String,
    required: [true, 'Password is required'],
    minlength: 8,
    select: false
  },
  firstName: {
    type: String,
    required: [true, 'First name is required'],
    trim: true
  },
  lastName: {
    type: String,
    required: [true, 'Last name is required'],
    trim: true
  },
  phone: {
    type: String,
    required: [true, 'Phone number is required'],
    trim: true
  },
  role: {
    type: String,
    enum: ['customer', 'admin'],
    default: 'customer'
  },
  idType: {
    type: String,
    enum: ['passport', 'drivers_license', 'national_id']
  },
  idNumber: String,
  idDocument: String,
  profileImage: String,
  verified: {
    type: Boolean,
    default: false
  }
}, {
  timestamps: true
});

// Hash password before saving
userSchema.pre('save', async function(next) {
  if (!this.isModified('password')) return next();
  
  const salt = await bcrypt.genSalt(10);
  this.password = await bcrypt.hash(this.password, salt);
  next();
});

// Compare password method
userSchema.methods.comparePassword = async function(candidatePassword) {
  return await bcrypt.compare(candidatePassword, this.password);
};

// Get full name
userSchema.virtual('fullName').get(function() {
  return `${this.firstName} ${this.lastName}`;
});

module.exports = mongoose.model('User', userSchema);
```

#### Apartment Model (`backend/src/models/Apartment.js`)
```javascript
const mongoose = require('mongoose');
const slugify = require('slugify');

const apartmentSchema = new mongoose.Schema({
  name: {
    type: String,
    required: [true, 'Apartment name is required'],
    trim: true
  },
  slug: {
    type: String,
    unique: true
  },
  description: {
    type: String,
    required: [true, 'Description is required']
  },
  location: {
    city: {
      type: String,
      required: true,
      enum: ['Lagos', 'Abuja']
    },
    area: {
      type: String,
      required: true
    },
    address: {
      type: String,
      required: true
    },
    coordinates: {
      lat: Number,
      lng: Number
    }
  },
  bedrooms: {
    type: Number,
    required: [true, 'Number of bedrooms is required'],
    min: 1
  },
  bathrooms: {
    type: Number,
    required: [true, 'Number of bathrooms is required'],
    min: 1
  },
  maxGuests: {
    type: Number,
    required: [true, 'Maximum guests is required'],
    min: 1
  },
  amenities: [String],
  images: [{
    url: {
      type: String,
      required: true
    },
    caption: String,
    isPrimary: {
      type: Boolean,
      default: false
    }
  }],
  pricing: {
    basePrice: {
      type: Number,
      required: [true, 'Base price is required'],
      min: 0
    },
    weekendPrice: Number,
    weeklyDiscount: {
      type: Number,
      min: 0,
      max: 100
    },
    monthlyDiscount: {
      type: Number,
      min: 0,
      max: 100
    },
    cleaningFee: {
      type: Number,
      default: 0
    },
    securityDeposit: {
      type: Number,
      default: 0
    }
  },
  availability: {
    status: {
      type: String,
      enum: ['available', 'unavailable'],
      default: 'available'
    },
    blockedDates: [Date]
  },
  features: {
    wifi: { type: Boolean, default: false },
    parking: { type: Boolean, default: false },
    kitchen: { type: Boolean, default: false },
    airConditioning: { type: Boolean, default: false },
    tv: { type: Boolean, default: false },
    washer: { type: Boolean, default: false },
    securitySystem: { type: Boolean, default: false },
    generator: { type: Boolean, default: false }
  },
  rules: [String],
  rating: {
    average: {
      type: Number,
      default: 0,
      min: 0,
      max: 5
    },
    count: {
      type: Number,
      default: 0
    }
  },
  featured: {
    type: Boolean,
    default: false
  },
  active: {
    type: Boolean,
    default: true
  }
}, {
  timestamps: true,
  toJSON: { virtuals: true },
  toObject: { virtuals: true }
});

// Create slug before saving
apartmentSchema.pre('save', function(next) {
  if (this.isModified('name')) {
    this.slug = slugify(this.name, { lower: true, strict: true });
  }
  next();
});

// Virtual for primary image
apartmentSchema.virtual('primaryImage').get(function() {
  const primary = this.images.find(img => img.isPrimary);
  return primary ? primary.url : (this.images[0]?.url || null);
});

module.exports = mongoose.model('Apartment', apartmentSchema);
```

#### Booking Model (`backend/src/models/Booking.js`)
```javascript
const mongoose = require('mongoose');

const bookingSchema = new mongoose.Schema({
  bookingReference: {
    type: String,
    unique: true,
    required: true
  },
  user: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true
  },
  apartment: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Apartment',
    required: true
  },
  checkIn: {
    type: Date,
    required: [true, 'Check-in date is required']
  },
  checkOut: {
    type: Date,
    required: [true, 'Check-out date is required']
  },
  numberOfNights: {
    type: Number,
    required: true
  },
  guests: {
    adults: {
      type: Number,
      required: true,
      min: 1
    },
    children: {
      type: Number,
      default: 0,
      min: 0
    }
  },
  guestDetails: {
    fullName: {
      type: String,
      required: true
    },
    email: {
      type: String,
      required: true
    },
    phone: {
      type: String,
      required: true
    },
    idType: {
      type: String,
      required: true
    },
    idNumber: {
      type: String,
      required: true
    }
  },
  pricing: {
    baseAmount: Number,
    cleaningFee: Number,
    securityDeposit: Number,
    discount: Number,
    totalAmount: {
      type: Number,
      required: true
    }
  },
  payment: {
    status: {
      type: String,
      enum: ['pending', 'paid', 'failed', 'refunded'],
      default: 'pending'
    },
    method: {
      type: String,
      enum: ['paystack', 'bank_transfer', 'cash']
    },
    transactionId: String,
    paidAt: Date,
    refundedAt: Date
  },
  status: {
    type: String,
    enum: ['pending', 'confirmed', 'checked_in', 'checked_out', 'cancelled'],
    default: 'pending'
  },
  specialRequests: String,
  cancellationReason: String,
  cancelledAt: Date
}, {
  timestamps: true
});

// Generate booking reference before saving
bookingSchema.pre('save', async function(next) {
  if (!this.bookingReference) {
    const timestamp = Date.now().toString(36).toUpperCase();
    const random = Math.random().toString(36).substring(2, 6).toUpperCase();
    this.bookingReference = `SBS-${timestamp}-${random}`;
  }
  next();
});

// Calculate number of nights
bookingSchema.pre('save', function(next) {
  if (this.checkIn && this.checkOut) {
    const diffTime = Math.abs(this.checkOut - this.checkIn);
    this.numberOfNights = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  }
  next();
});

module.exports = mongoose.model('Booking', bookingSchema);
```

#### Auth Controller (`backend/src/controllers/authController.js`)
```javascript
const User = require('../models/User');
const jwt = require('jsonwebtoken');

// Generate JWT token
const generateToken = (id) => {
  return jwt.sign({ id }, process.env.JWT_SECRET, {
    expiresIn: process.env.JWT_EXPIRE || '7d'
  });
};

// @desc    Register user
// @route   POST /api/auth/register
// @access  Public
exports.register = async (req, res) => {
  try {
    const { email, password, firstName, lastName, phone } = req.body;

    // Check if user exists
    const userExists = await User.findOne({ email });
    if (userExists) {
      return res.status(400).json({
        success: false,
        message: 'User already exists with this email'
      });
    }

    // Create user
    const user = await User.create({
      email,
      password,
      firstName,
      lastName,
      phone
    });

    // Generate token
    const token = generateToken(user._id);

    res.status(201).json({
      success: true,
      data: {
        user: {
          id: user._id,
          email: user.email,
          firstName: user.firstName,
          lastName: user.lastName,
          role: user.role
        },
        token
      }
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message
    });
  }
};

// @desc    Login user
// @route   POST /api/auth/login
// @access  Public
exports.login = async (req, res) => {
  try {
    const { email, password } = req.body;

    // Validate input
    if (!email || !password) {
      return res.status(400).json({
        success: false,
        message: 'Please provide email and password'
      });
    }

    // Find user and include password
    const user = await User.findOne({ email }).select('+password');
    if (!user) {
      return res.status(401).json({
        success: false,
        message: 'Invalid credentials'
      });
    }

    // Check password
    const isMatch = await user.comparePassword(password);
    if (!isMatch) {
      return res.status(401).json({
        success: false,
        message: 'Invalid credentials'
      });
    }

    // Generate token
    const token = generateToken(user._id);

    res.json({
      success: true,
      data: {
        user: {
          id: user._id,
          email: user.email,
          firstName: user.firstName,
          lastName: user.lastName,
          role: user.role
        },
        token
      }
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message
    });
  }
};

// @desc    Get current user
// @route   GET /api/auth/me
// @access  Private
exports.getMe = async (req, res) => {
  try {
    const user = await User.findById(req.user.id);
    
    res.json({
      success: true,
      data: user
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message
    });
  }
};
```

#### Price Calculator Utility (`backend/src/utils/priceCalculator.js`)
```javascript
const calculateBookingPrice = (apartment, checkIn, checkOut) => {
  const checkInDate = new Date(checkIn);
  const checkOutDate = new Date(checkOut);
  
  // Calculate number of nights
  const diffTime = Math.abs(checkOutDate - checkInDate);
  const nights = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  
  if (nights < 1) {
    throw new Error('Check-out must be at least 1 day after check-in');
  }
  
  let baseAmount = 0;
  let currentDate = new Date(checkInDate);
  
  // Calculate price for each night
  for (let i = 0; i < nights; i++) {
    const dayOfWeek = currentDate.getDay();
    const isWeekend = dayOfWeek === 5 || dayOfWeek === 6 || dayOfWeek === 0; // Fri, Sat, Sun
    
    if (isWeekend && apartment.pricing.weekendPrice) {
      baseAmount += apartment.pricing.weekendPrice;
    } else {
      baseAmount += apartment.pricing.basePrice;
    }
    
    currentDate.setDate(currentDate.getDate() + 1);
  }
  
  // Apply weekly discount (7+ nights)
  let discount = 0;
  if (nights >= 7 && apartment.pricing.weeklyDiscount) {
    discount = baseAmount * (apartment.pricing.weeklyDiscount / 100);
  }
  
  // Apply monthly discount (30+ nights)
  if (nights >= 30 && apartment.pricing.monthlyDiscount) {
    discount = baseAmount * (apartment.pricing.monthlyDiscount / 100);
  }
  
  const discountedAmount = baseAmount - discount;
  const cleaningFee = apartment.pricing.cleaningFee || 0;
  const securityDeposit = apartment.pricing.securityDeposit || 0;
  const totalAmount = discountedAmount + cleaningFee + securityDeposit;
  
  return {
    nights,
    baseAmount,
    discount,
    discountedAmount,
    cleaningFee,
    securityDeposit,
    totalAmount
  };
};

module.exports = { calculateBookingPrice };
```

---

### Step 3: Frontend Implementation

#### API Service (`frontend/src/services/api.js`)
```javascript
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Handle response errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
```

#### Apartment Card Component (`frontend/src/components/apartments/ApartmentCard.jsx`)
```jsx
import React from 'react';
import { Link } from 'react-router-dom';
import { MapPin, Users, Bed, Star } from 'lucide-react';

const ApartmentCard = ({ apartment }) => {
  return (
    <Link 
      to={`/apartments/${apartment.slug}`}
      className="block bg-white rounded-lg shadow-md overflow-hidden hover:shadow-xl transition-shadow duration-300"
    >
      {/* Image */}
      <div className="relative h-48 overflow-hidden">
        <img
          src={apartment.primaryImage || apartment.images[0]?.url}
          alt={apartment.name}
          className="w-full h-full object-cover hover:scale-110 transition-transform duration-300"
        />
        {apartment.featured && (
          <span className="absolute top-2 right-2 bg-amber-500 text-white px-3 py-1 rounded-full text-sm font-semibold">
            Featured
          </span>
        )}
      </div>

      {/* Content */}
      <div className="p-4">
        {/* Title */}
        <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-1">
          {apartment.name}
        </h3>

        {/* Location */}
        <div className="flex items-center text-gray-600 mb-3">
          <MapPin className="w-4 h-4 mr-1" />
          <span className="text-sm">{apartment.location.area}, {apartment.location.city}</span>
        </div>

        {/* Features */}
        <div className="flex items-center gap-4 text-sm text-gray-600 mb-3">
          <div className="flex items-center">
            <Bed className="w-4 h-4 mr-1" />
            <span>{apartment.bedrooms} Bed{apartment.bedrooms > 1 ? 's' : ''}</span>
          </div>
          <div className="flex items-center">
            <Users className="w-4 h-4 mr-1" />
            <span>Up to {apartment.maxGuests} guests</span>
          </div>
        </div>

        {/* Rating */}
        {apartment.rating.count > 0 && (
          <div className="flex items-center mb-3">
            <Star className="w-4 h-4 text-amber-500 fill-current mr-1" />
            <span className="text-sm font-semibold">{apartment.rating.average.toFixed(1)}</span>
            <span className="text-sm text-gray-600 ml-1">({apartment.rating.count} reviews)</span>
          </div>
        )}

        {/* Price */}
        <div className="flex items-baseline justify-between">
          <div>
            <span className="text-2xl font-bold text-blue-600">
              ₦{apartment.pricing.basePrice.toLocaleString()}
            </span>
            <span className="text-sm text-gray-600 ml-1">/ night</span>
          </div>
        </div>
      </div>
    </Link>
  );
};

export default ApartmentCard;
```

#### Booking Form Component (`frontend/src/components/booking/BookingForm.jsx`)
```jsx
import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import { calculatePrice } from '../../utils/priceUtils';

const BookingForm = ({ apartment, onSubmit }) => {
  const { register, handleSubmit, formState: { errors }, watch } = useForm();
  const [checkIn, setCheckIn] = useState(null);
  const [checkOut, setCheckOut] = useState(null);
  const [pricing, setPricing] = useState(null);

  const adults = watch('adults', 1);
  const children = watch('children', 0);

  // Calculate price when dates change
  useEffect(() => {
    if (checkIn && checkOut && apartment) {
      const calculatedPrice = calculatePrice(apartment, checkIn, checkOut);
      setPricing(calculatedPrice);
    }
  }, [checkIn, checkOut, apartment]);

  const onFormSubmit = (data) => {
    if (!checkIn || !checkOut) {
      alert('Please select check-in and check-out dates');
      return;
    }

    const bookingData = {
      ...data,
      checkIn,
      checkOut,
      apartmentId: apartment._id,
      pricing
    };

    onSubmit(bookingData);
  };

  return (
    <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-6">
      {/* Dates */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Check-in Date
          </label>
          <DatePicker
            selected={checkIn}
            onChange={(date) => setCheckIn(date)}
            minDate={new Date()}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            placeholderText="Select check-in date"
            dateFormat="dd/MM/yyyy"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Check-out Date
          </label>
          <DatePicker
            selected={checkOut}
            onChange={(date) => setCheckOut(date)}
            minDate={checkIn || new Date()}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            placeholderText="Select check-out date"
            dateFormat="dd/MM/yyyy"
          />
        </div>
      </div>

      {/* Guests */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Adults
          </label>
          <input
            type="number"
            min="1"
            max={apartment.maxGuests}
            {...register('adults', { required: true, min: 1 })}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Children
          </label>
          <input
            type="number"
            min="0"
            {...register('children', { min: 0 })}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Guest Details */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Full Name
        </label>
        <input
          type="text"
          {...register('fullName', { required: 'Full name is required' })}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
        />
        {errors.fullName && (
          <p className="text-red-500 text-sm mt-1">{errors.fullName.message}</p>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Email
          </label>
          <input
            type="email"
            {...register('email', { required: 'Email is required' })}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          />
          {errors.email && (
            <p className="text-red-500 text-sm mt-1">{errors.email.message}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Phone Number
          </label>
          <input
            type="tel"
            {...register('phone', { required: 'Phone number is required' })}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          />
          {errors.phone && (
            <p className="text-red-500 text-sm mt-1">{errors.phone.message}</p>
          )}
        </div>
      </div>

      {/* ID Information */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            ID Type
          </label>
          <select
            {...register('idType', { required: 'ID type is required' })}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Select ID type</option>
            <option value="passport">Passport</option>
            <option value="drivers_license">Driver's License</option>
            <option value="national_id">National ID</option>
          </select>
          {errors.idType && (
            <p className="text-red-500 text-sm mt-1">{errors.idType.message}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            ID Number
          </label>
          <input
            type="text"
            {...register('idNumber', { required: 'ID number is required' })}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          />
          {errors.idNumber && (
            <p className="text-red-500 text-sm mt-1">{errors.idNumber.message}</p>
          )}
        </div>
      </div>

      {/* Special Requests */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Special Requests (Optional)
        </label>
        <textarea
          {...register('specialRequests')}
          rows="3"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          placeholder="Any special requests or requirements..."
        />
      </div>

      {/* Price Summary */}
      {pricing && (
        <div className="bg-gray-50 p-4 rounded-lg">
          <h3 className="font-semibold text-lg mb-3">Price Summary</h3>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span>₦{apartment.pricing.basePrice.toLocaleString()} x {pricing.nights} nights</span>
              <span>₦{pricing.baseAmount.toLocaleString()}</span>
            </div>
            {pricing.discount > 0 && (
              <div className="flex justify-between text-green-600">
                <span>Discount</span>
                <span>-₦{pricing.discount.toLocaleString()}</span>
              </div>
            )}
            {pricing.cleaningFee > 0 && (
              <div className="flex justify-between">
                <span>Cleaning fee</span>
                <span>₦{pricing.cleaningFee.toLocaleString()}</span>
              </div>
            )}
            {pricing.securityDeposit > 0 && (
              <div className="flex justify-between">
                <span>Security deposit</span>
                <span>₦{pricing.securityDeposit.toLocaleString()}</span>
              </div>
            )}
            <div className="border-t pt-2 flex justify-between font-bold text-lg">
              <span>Total</span>
              <span>₦{pricing.totalAmount.toLocaleString()}</span>
            </div>
          </div>
        </div>
      )}

      {/* Submit Button */}
      <button
        type="submit"
        className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors"
      >
        Proceed to Payment
      </button>
    </form>
  );
};

export default BookingForm;
```

---

## 🎨 Tailwind Configuration

```javascript
// tailwind.config.js
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#2563eb',
        secondary: '#f59e0b',
        accent: '#10b981',
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
```

---

## 🔐 Environment Variables

### Backend `.env`
```env
NODE_ENV=development
PORT=5000

# Database
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/shortletsbyshar

# JWT
JWT_SECRET=your-super-secret-jwt-key-change-this
JWT_EXPIRE=7d

# Paystack
PAYSTACK_SECRET_KEY=sk_test_your_secret_key
PAYSTACK_PUBLIC_KEY=pk_test_your_public_key

# Cloudinary
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# Email
EMAIL_SERVICE=gmail
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password

# Twilio WhatsApp
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+1234567890

# Frontend URL
FRONTEND_URL=http://localhost:3000
```

### Frontend `.env`
```env
REACT_APP_API_URL=http://localhost:5000/api
REACT_APP_PAYSTACK_PUBLIC_KEY=pk_test_your_public_key
```

---

## 📝 Next Steps

1. Review the technical plan and architecture
2. Set up development environment
3. Initialize both frontend and backend projects
4. Implement core features step by step
5. Test thoroughly
6. Deploy to production

This implementation guide provides the foundation for building ShortletsbyShar. Each component can be expanded with additional features as needed.