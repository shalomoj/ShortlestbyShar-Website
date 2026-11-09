// Sample apartment data
const apartments = [
    {
        id: 1,
        name: "Luxury 3-Bedroom Apartment in Lekki",
        location: { city: "Lagos", area: "Lekki Phase 1" },
        bedrooms: 3,
        bathrooms: 3,
        maxGuests: 6,
        price: 85000,
        image: "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=800",
        amenities: ["WiFi", "Parking", "Kitchen", "AC", "TV", "Security"],
        description: "Beautiful 3-bedroom apartment in the heart of Lekki with modern amenities and 24/7 security."
    },
    {
        id: 2,
        name: "Cozy 2-Bedroom in Victoria Island",
        location: { city: "Lagos", area: "Victoria Island" },
        bedrooms: 2,
        bathrooms: 2,
        maxGuests: 4,
        price: 120000,
        image: "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800",
        amenities: ["WiFi", "Parking", "Kitchen", "AC", "TV", "Pool"],
        description: "Premium 2-bedroom apartment in VI with stunning views and access to swimming pool."
    },
    {
        id: 3,
        name: "Modern 1-Bedroom Studio in Ikeja",
        location: { city: "Lagos", area: "Ikeja GRA" },
        bedrooms: 1,
        bathrooms: 1,
        maxGuests: 2,
        price: 45000,
        image: "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800",
        amenities: ["WiFi", "Kitchen", "AC", "TV", "Security"],
        description: "Compact and modern studio apartment perfect for business travelers in Ikeja."
    },
    {
        id: 4,
        name: "Spacious 4-Bedroom Duplex in Maitama",
        location: { city: "Abuja", area: "Maitama" },
        bedrooms: 4,
        bathrooms: 4,
        maxGuests: 8,
        price: 150000,
        image: "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800",
        amenities: ["WiFi", "Parking", "Kitchen", "AC", "TV", "Generator", "Security"],
        description: "Luxurious 4-bedroom duplex in prestigious Maitama with all modern conveniences."
    },
    {
        id: 5,
        name: "Elegant 2-Bedroom in Wuse 2",
        location: { city: "Abuja", area: "Wuse 2" },
        bedrooms: 2,
        bathrooms: 2,
        maxGuests: 4,
        price: 75000,
        image: "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800",
        amenities: ["WiFi", "Parking", "Kitchen", "AC", "TV", "Security"],
        description: "Elegant apartment in the heart of Abuja's business district with easy access to amenities."
    },
    {
        id: 6,
        name: "Charming 3-Bedroom in Asokoro",
        location: { city: "Abuja", area: "Asokoro" },
        bedrooms: 3,
        bathrooms: 3,
        maxGuests: 6,
        price: 95000,
        image: "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=800",
        amenities: ["WiFi", "Parking", "Kitchen", "AC", "TV", "Generator", "Security"],
        description: "Charming 3-bedroom apartment in exclusive Asokoro neighborhood with serene environment."
    },
    {
        id: 7,
        name: "Beachfront 2-Bedroom in Ikoyi",
        location: { city: "Lagos", area: "Ikoyi" },
        bedrooms: 2,
        bathrooms: 2,
        maxGuests: 4,
        price: 110000,
        image: "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800",
        amenities: ["WiFi", "Parking", "Kitchen", "AC", "TV", "Pool", "Gym"],
        description: "Stunning beachfront apartment in Ikoyi with access to gym and swimming pool."
    },
    {
        id: 8,
        name: "Budget-Friendly 1-Bedroom in Yaba",
        location: { city: "Lagos", area: "Yaba" },
        bedrooms: 1,
        bathrooms: 1,
        maxGuests: 2,
        price: 35000,
        image: "https://images.unsplash.com/photo-1600607687644-c7171b42498b?w=800",
        amenities: ["WiFi", "Kitchen", "AC", "Security"],
        description: "Affordable and comfortable 1-bedroom apartment in vibrant Yaba neighborhood."
    }
];

let filteredApartments = [...apartments];
let currentApartment = null;

// Load apartments on page load
document.addEventListener('DOMContentLoaded', function() {
    displayApartments(apartments);
    setMinDate();
});

// Display apartments in grid
function displayApartments(apartmentsToDisplay) {
    const grid = document.getElementById('apartmentsGrid');
    
    if (apartmentsToDisplay.length === 0) {
        grid.innerHTML = '<p style="grid-column: 1/-1; text-align: center; padding: 2rem;">No apartments found matching your criteria.</p>';
        return;
    }
    
    grid.innerHTML = apartmentsToDisplay.map(apt => `
        <div class="apartment-card" onclick="openBookingModal(${apt.id})">
            <img src="${apt.image}" alt="${apt.name}" class="apartment-image">
            <div class="apartment-info">
                <h3 class="apartment-title">${apt.name}</h3>
                <p class="apartment-location">📍 ${apt.location.area}, ${apt.location.city}</p>
                <div class="apartment-features">
                    <span>🛏️ ${apt.bedrooms} Bed${apt.bedrooms > 1 ? 's' : ''}</span>
                    <span>🚿 ${apt.bathrooms} Bath${apt.bathrooms > 1 ? 's' : ''}</span>
                    <span>👥 ${apt.maxGuests} Guests</span>
                </div>
                <div class="apartment-amenities">
                    ${apt.amenities.slice(0, 4).map(amenity => 
                        `<span class="amenity-tag">${amenity}</span>`
                    ).join('')}
                    ${apt.amenities.length > 4 ? `<span class="amenity-tag">+${apt.amenities.length - 4} more</span>` : ''}
                </div>
                <p class="apartment-price">₦${apt.price.toLocaleString()} <span>/ night</span></p>
            </div>
        </div>
    `).join('');
}

// Filter apartments
function filterApartments() {
    const location = document.getElementById('filterLocation').value.toLowerCase();
    const bedrooms = document.getElementById('filterBedrooms').value;
    const priceRange = document.getElementById('filterPrice').value;
    
    filteredApartments = apartments.filter(apt => {
        // Location filter
        if (location && apt.location.city.toLowerCase() !== location) {
            return false;
        }
        
        // Bedrooms filter
        if (bedrooms) {
            const bedroomNum = parseInt(bedrooms);
            if (bedroomNum === 4) {
                if (apt.bedrooms < 4) return false;
            } else {
                if (apt.bedrooms !== bedroomNum) return false;
            }
        }
        
        // Price filter
        if (priceRange) {
            const [min, max] = priceRange.split('-').map(Number);
            if (apt.price < min || apt.price > max) {
                return false;
            }
        }
        
        return true;
    });
    
    displayApartments(filteredApartments);
}

// Search apartments from hero
function searchApartments() {
    const location = document.getElementById('heroLocation').value;
    const bedrooms = document.getElementById('heroBedrooms').value;
    
    if (location) {
        document.getElementById('filterLocation').value = location;
    }
    if (bedrooms) {
        document.getElementById('filterBedrooms').value = bedrooms;
    }
    
    filterApartments();
    
    // Scroll to apartments section
    document.getElementById('apartments').scrollIntoView({ behavior: 'smooth' });
}

// Open booking modal
function openBookingModal(apartmentId) {
    currentApartment = apartments.find(apt => apt.id === apartmentId);
    
    if (!currentApartment) return;
    
    const modal = document.getElementById('bookingModal');
    const modalInfo = document.getElementById('modalApartmentInfo');
    
    modalInfo.innerHTML = `
        <div style="margin-bottom: 1.5rem;">
            <img src="${currentApartment.image}" alt="${currentApartment.name}" style="width: 100%; height: 200px; object-fit: cover; border-radius: 8px; margin-bottom: 1rem;">
            <h3 style="color: #1e293b; margin-bottom: 0.5rem;">${currentApartment.name}</h3>
            <p style="color: #64748b; margin-bottom: 0.5rem;">📍 ${currentApartment.location.area}, ${currentApartment.location.city}</p>
            <p style="color: #2563eb; font-size: 1.5rem; font-weight: 700;">₦${currentApartment.price.toLocaleString()} <span style="font-size: 1rem; font-weight: 400; color: #64748b;">/ night</span></p>
            <div style="margin-top: 1rem;">
                <p style="color: #64748b; margin-bottom: 0.5rem;"><strong>Features:</strong></p>
                <p style="color: #64748b;">🛏️ ${currentApartment.bedrooms} Bedrooms • 🚿 ${currentApartment.bathrooms} Bathrooms • 👥 Up to ${currentApartment.maxGuests} guests</p>
            </div>
            <div style="margin-top: 1rem;">
                <p style="color: #64748b; margin-bottom: 0.5rem;"><strong>Amenities:</strong></p>
                <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                    ${currentApartment.amenities.map(amenity => 
                        `<span style="background: #e0f2fe; color: #0369a1; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.85rem;">${amenity}</span>`
                    ).join('')}
                </div>
            </div>
        </div>
    `;
    
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

// Close booking modal
function closeBookingModal() {
    const modal = document.getElementById('bookingModal');
    modal.classList.remove('active');
    document.body.style.overflow = 'auto';
}

// Handle booking form submission
function handleBookingSubmit(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const checkIn = document.getElementById('checkIn').value;
    const checkOut = document.getElementById('checkOut').value;
    
    // Calculate number of nights
    const checkInDate = new Date(checkIn);
    const checkOutDate = new Date(checkOut);
    const nights = Math.ceil((checkOutDate - checkInDate) / (1000 * 60 * 60 * 24));
    const totalPrice = currentApartment.price * nights;
    
    // Show success message
    alert(`Booking Request Submitted Successfully!

Apartment: ${currentApartment.name}
Location: ${currentApartment.location.area}, ${currentApartment.location.city}
Check-in: ${checkIn}
Check-out: ${checkOut}
Nights: ${nights}
Total: ₦${totalPrice.toLocaleString()}

We will contact you shortly via phone or WhatsApp to confirm your booking and arrange payment.

Thank you for choosing ShortletsbyShar!`);
    
    closeBookingModal();
    event.target.reset();
}

// Handle contact form submission
function handleContactSubmit(event) {
    event.preventDefault();
    
    alert('Thank you for contacting us! We will get back to you within 24 hours.');
    event.target.reset();
}

// Toggle mobile menu
function toggleMobileMenu() {
    const mobileMenu = document.getElementById('mobileMenu');
    mobileMenu.classList.toggle('active');
}

// Set minimum date for check-in (today)
function setMinDate() {
    const today = new Date().toISOString().split('T')[0];
    const checkInInput = document.getElementById('checkIn');
    const checkOutInput = document.getElementById('checkOut');
    
    if (checkInInput) {
        checkInInput.setAttribute('min', today);
        checkInInput.addEventListener('change', function() {
            const checkInDate = new Date(this.value);
            checkInDate.setDate(checkInDate.getDate() + 1);
            const minCheckOut = checkInDate.toISOString().split('T')[0];
            checkOutInput.setAttribute('min', minCheckOut);
        });
    }
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('bookingModal');
    if (event.target === modal) {
        closeBookingModal();
    }
}

// Smooth scroll for navigation links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Made with Bob
