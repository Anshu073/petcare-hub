from django.shortcuts import render, redirect, get_object_or_404
from test2.models import Area,Customer,Product,ProductCategory,Gallery,Feedback,Vet, Appointment, Cart, Wishlist, VetSchedule
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth import logout
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from django.db.models import Avg, Count, Sum, Q
from django.http import JsonResponse
from datetime import datetime, timedelta, date
import re

# Create your views here.
from django.db.models import Avg, Count # Ye do cheezein import karna mat bhoolna

def show(request):
    # Annotate se har doctor ke liye average rating aur total reviews calculate honge
    vets = Vet.objects.filter(status=1).annotate(
        avg_rating=Avg('feedback__rating'), # Feedback table se rating ka average
        review_count=Count('feedback')      # Total kitne feedbacks hain
    )[:4]
    
    total_vets = Vet.objects.filter(status=1).count()
    total_products = Product.objects.count()
    
    context = {
        'vets': vets,
        'total_vets': total_vets,
        'total_products': total_products,
    }
    return render(request, 'index.html', context)

def register(request):
    # Fetching all areas to populate the dropdown for GET requests
    areas = Area.objects.all()
    
    if request.method == "POST":
        # Extracting user data from the registration form
        name = request.POST.get('cust_name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password')
        contact = request.POST.get('contact', '').strip()
        address = request.POST.get('address', '').strip()
        area_id = request.POST.get('area_id')

        # --- SERVER-SIDE VALIDATION START ---
        
        email_pattern = r'^[a-zA-Z][a-zA-Z0-9._%+-]*@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            messages.error(request, "Invalid Email: Must start with a letter and follow standard format (e.g., petcarehub@gmail.com).")
            return render(request, 'register.html', {'areas': areas}) # redirect ki jagah render taaki user wahi rahe
        
        # 1. Name Validation: Check if it contains only letters and spaces
        if not re.match(r'^[a-zA-Z\s]+$', name):
            messages.error(request, "Invalid Name: Please use alphabets only.")
            return render(request, 'register.html', {'areas': areas})

        # 2. Duplicate Email Check: Prevent multiple accounts with the same email address
        if Customer.objects.filter(email=email).exists():
            messages.error(request, "This email is already registered. Please login.")
            return render(request, 'register.html', {'areas': areas})
        
        # 3. Duplicate Contact Check (NEW)
        if Customer.objects.filter(contact=contact).exists():
            messages.error(request, "This mobile number is already registered. Please use a different one.")
            return render(request, 'register.html', {'areas': areas})
        
      # 3. Contact Validation: Exactly 10 digits and starts with 6-9
        if not re.match(r'^[6-9]\d{9}$', contact):
            messages.error(request, "Invalid Contact: Mobile number must be 10 digits and start with 6, 7, 8, or 9.")
            return render(request, 'register.html', {'areas': areas})
        
        # --- PASSWORD VALIDATION (New) ---
        password_pattern = r'^(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{8,16}$'
        if not re.match(password_pattern, password):
            messages.error(request, "Password must be 8-16 characters long and include at least one uppercase letter, one lowercase letter, and one number.")
            return render(request, 'register.html', {'areas': areas})
        
        
        # --- DATABASE INSERTION ---
        try:
            area_obj = Area.objects.get(area_id=area_id)
            hashed_p = make_password(password)

            Customer.objects.create(
                cust_name=name,
                email=email,
                password=hashed_p, 
                contact=contact,
                address=address,
                area_id=area_obj,
                is_admin=0 
            )
            
            messages.success(request, "Registration successful! You can now log in to your account. 🐾")
            return redirect('login1')

        except Exception as e:
            messages.error(request, f"Registration failed: {str(e)}")
            return render(request, 'register.html', {'areas': areas})
    
    return render(request, 'register.html', {'areas': areas})

# client_views.py
def login(request):
    if request.method == "POST":
        email_val = request.POST.get('email', '').strip()
        password_val = request.POST.get('password')

        try:
            customer = Customer.objects.get(email=email_val)
            
            if check_password(password_val, customer.password):
                # Basic session data
                request.session['cust_id'] = customer.cust_id
                request.session['cust_name'] = customer.cust_name
                request.session['is_admin'] = customer.is_admin
                
                # PROFILE PHOTO RESTORE: Permanent path database se uthana
                if customer.user_profile:
                    # Database se asli URL (e.g., /media/customer_profiles/abc.jpg)
                    request.session['cust_profile'] = customer.user_profile.url
                else:
                    # Default photo agar upload nahi ki hai
                    request.session['cust_profile'] = "/static/assets/img/users/default.png"
                
                messages.success(request, f"Welcome back, {customer.cust_name}! 🐾", extra_tags='login_home')
                return redirect('home') 
            else:
                messages.error(request, "Invalid Password. Please try again.")
                return redirect('login1')
                
        except Customer.DoesNotExist:
            messages.error(request, "This email is not registered. Please sign up first.")
            return redirect('login1')

    return render(request, 'login1.html')

def product(request):
    categories = ProductCategory.objects.all()
    cat_id = request.GET.get('category')
    sort_by = request.GET.get('sort') 
    page_number = request.GET.get('page')
    
    if cat_id:
        product_list = Product.objects.filter(category_id=cat_id)
    else:
        product_list = Product.objects.all()

    if sort_by == 'name_asc':
        product_list = product_list.order_by('prod_name')
    elif sort_by == 'name_desc':
        product_list = product_list.order_by('-prod_name')
    elif sort_by == 'price_asc':
        product_list = product_list.order_by('price')
    elif sort_by == 'price_desc':
        product_list = product_list.order_by('-price')
    else:
        product_list = product_list.order_by('prod_id')
        
    paginator = Paginator(product_list, 15)
    products = paginator.get_page(page_number)
        
    return render(request, 'product.html', {
        'products': products, 
        'categories': categories,
        'selected_cat': cat_id,
        'selected_sort': sort_by 
    })
            
def product_details(request, pk):
    product = get_object_or_404(Product, prod_id=pk)
    gallery = Gallery.objects.filter(prod_id=product)
    related_products = Product.objects.filter(category_id=product.category_id).exclude(prod_id=pk)[:10]
    
    reviews = Feedback.objects.filter(prod_id=product).select_related('cust_id').order_by('-feedback_date')
    
    avg_rating_data = reviews.aggregate(avg_rating=Avg('rating'))
    avg_rating = avg_rating_data['avg_rating'] or 0
    display_rating = round(avg_rating, 1)
    
    full_stars = range(int(avg_rating))
    empty_stars = range(5 - int(avg_rating))
    
    current_user = None
    cust_id = request.session.get('cust_id')
    if cust_id:
        try:
            current_user = Customer.objects.get(cust_id=cust_id)
        except Customer.DoesNotExist:
            current_user = None

    context = {
        'product': product,
        'gallery': gallery,
        'related_products': related_products,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'display_rating': display_rating,
        'full_stars': full_stars,
        'empty_stars': empty_stars,
        'current_user': current_user,
    }
    
    return render(request, 'product-details.html', context)

def submit_review(request, prod_id):
    if request.method == "POST":
        cust_id = request.session.get('cust_id')
        if not cust_id:
            messages.warning(request, "Please login to write a review! 🐾")
            return redirect('login1')

        product = get_object_or_404(Product, prod_id=prod_id)
        customer = get_object_or_404(Customer, cust_id=cust_id)
        
        rating = request.POST.get('rating')
        comments = request.POST.get('comments')

        Feedback.objects.create(
            cust_id=customer,
            prod_id=product,
            rating=rating,
            comments=comments
        )
        
        messages.success(request, "Thank you for your review! ❤️")
        return redirect('product_details', pk=prod_id)
    
def add_to_cart(request, prod_id):
    cust_id = request.session.get('cust_id')
    
    if not cust_id:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'login_required'}, status=401)
        messages.warning(request, "Please login first!")
        return redirect('login1')

    if request.method == "POST":
        product = get_object_or_404(Product, prod_id=prod_id)
        customer = get_object_or_404(Customer, cust_id=cust_id)
        qty = int(request.POST.get('quantity', 1))

        cart_item, created = Cart.objects.get_or_create(
            cust_id=customer, prod_id=product, status=1,
            defaults={'quantity': qty, 'price': product.price, 'total_price': product.price * qty}
        )
        if not created:
            cart_item.quantity += qty
            cart_item.total_price = cart_item.quantity * product.price
            cart_item.save()

        Wishlist.objects.filter(cust_id=customer, prod_id=product).delete()

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'message': f'{product.prod_name} added to cart! 🛒'})

        messages.success(request, f"{product.prod_name} added to cart! 🛒")
        return redirect(request.META.get('HTTP_REFERER', 'product'))
    
def cart_view(request):
    cust_id = request.session.get('cust_id')
    if not cust_id:
        return redirect('login1')
    
    cart_items = Cart.objects.filter(cust_id=cust_id, status=1)
    grand_total = sum(item.total_price for item in cart_items)
    
    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'grand_total': grand_total
    })
    
def update_cart(request, cart_id, action):
    item = get_object_or_404(Cart, cart_id=cart_id)
    
    if action == 'plus':
        item.quantity += 1
    elif action == 'minus':
        if item.quantity > 1:
            item.quantity -= 1
        else:
            item.delete() 
            return redirect('cart')
            
    item.total_price = item.quantity * item.price
    item.save()
    return redirect('cart')

def remove_cart(request, cart_id):
    item = get_object_or_404(Cart, cart_id=cart_id)
    item.delete()
    return redirect('cart')

def cart_count(request):
    cust_id = request.session.get('cust_id')
    if cust_id:
        count = Cart.objects.filter(cust_id=cust_id, status=1).count()
        return {'cart_item_count': count}
    return {'cart_item_count': 0}

def logout_view(request):
    logout(request) 
    request.session.flush() 
    messages.success(request, "Logged out successfully! Come back soon. 🐾", extra_tags='client_logout_succ')
    return redirect('home')

def checkout(request, prod_id=None):
    cust_id = request.session.get('cust_id')
    if not cust_id:
        return redirect('login1')
    
    customer = get_object_or_404(Customer, cust_id=cust_id)
    checkout_items = []
    grand_total = 0

    if prod_id:
        product = get_object_or_404(Product, prod_id=prod_id)
        qty = int(request.GET.get('qty', 1))
        total = product.price * qty
        checkout_items.append({
            'product': product,
            'quantity': qty,
            'total_price': total
        })
        grand_total = total
    else:
        items = Cart.objects.filter(cust_id=customer, status=1)
        for item in items:
            checkout_items.append({
                'product': item.prod_id,
                'quantity': item.quantity,
                'total_price': item.total_price
            })
        grand_total = items.aggregate(Sum('total_price'))['total_price__sum'] or 0

    return render(request, 'checkout.html', {
        'checkout_items': checkout_items,
        'grand_total': grand_total,
        'customer': customer
    })

def add_to_wishlist(request, prod_id):
    cust_id = request.session.get('cust_id')
    if not cust_id:
        messages.warning(request, "Please login to manage your wishlist! 🐾")
        return redirect('login1')

    product = get_object_or_404(Product, prod_id=prod_id)
    customer = get_object_or_404(Customer, cust_id=cust_id)
    
    wish_item = Wishlist.objects.filter(cust_id=customer, prod_id=product).first()
    
    if wish_item:
        wish_item.delete()
        messages.info(request, f"'{product.prod_name}' has been removed from wishlist.")
    else:
        Wishlist.objects.create(cust_id=customer, prod_id=product)
        messages.success(request, f"Item is wishlisted! ❤️") 

    return redirect(request.META.get('HTTP_REFERER', 'product'))

def wishlist_view(request):
    cust_id = request.session.get('cust_id')
    if not cust_id:
        return redirect('login1')
    
    items = Wishlist.objects.filter(cust_id=cust_id).select_related('prod_id')
    return render(request, 'wishlist.html', {'items': items})    

def team(request):
    vets = Vet.objects.filter(status=1).select_related('area_id').annotate(
        avg_rating=Avg('feedback__rating'),
        review_count=Count('feedback')    
    )
    return render(request, 'team.html', {'vets': vets})

import re  # Top par regex import karna mat bhulna
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib import messages
from test2.models import Vet, VetSchedule, Appointment, Customer, Feedback

def vet_details(request, pk):
    # 1. Basic Setup & Data Fetching
    vet = get_object_or_404(Vet, vet_id=pk)
    cust_id = request.session.get('cust_id')
    current_customer = Customer.objects.filter(pk=cust_id).first() if cust_id else None

    # FEEDBACK FETCHING
    feedbacks = Feedback.objects.filter(vet_id=vet).select_related('cust_id').order_by('-feedback_date')

    now_aware = timezone.now()
    today_obj = now_aware.date()
    is_vet_vacation = (vet.availability_status == 0)

    # 2. Helper function to get available slots
    def get_slots_for_date(target_date):
        if is_vet_vacation: 
            return []
            
        day_index = target_date.weekday()
        schedule = VetSchedule.objects.filter(vet_id=vet, day_of_week=day_index).first()
        slots_list = []
        
        if schedule:
            d_start = timezone.make_aware(datetime.combine(target_date, datetime.min.time()))
            d_end = timezone.make_aware(datetime.combine(target_date, datetime.max.time()))

            booked_appointments = Appointment.objects.filter(
                vet_id=vet,
                appointment_date__range=(d_start, d_end),
                appointment_status__in=[0, 1, 3, 6] 
            ).values_list('appointment_date', flat=True)
            
            booked_times = [timezone.localtime(dt).strftime("%I:%M %p") for dt in booked_appointments]

            current_slot = timezone.make_aware(datetime.combine(target_date, schedule.open_time))
            end_time = timezone.make_aware(datetime.combine(target_date, schedule.close_time))
            
            check_limit = now_aware + timedelta(minutes=15) if target_date == today_obj else current_slot
            
            while current_slot < end_time:
                slot_str = current_slot.strftime("%I:%M %p")
                if current_slot >= check_limit: 
                    if slot_str not in booked_times:
                        slots_list.append(slot_str)
                current_slot += timedelta(hours=1)
        return slots_list

    # 3. POST Method: Booking Logic
    if request.method == "POST" and 'book_appointment' in request.POST:
        if not current_customer: 
            messages.error(request, "Please login to book an appointment.")
            return redirect('login1')
        
        if is_vet_vacation:
            messages.error(request, "Sorry, this Vet is currently on vacation.")
            return redirect('vet_details', pk=pk)

        # --- DESCRIPTION VALIDATION START ---
        raw_description = request.POST.get('description', '').strip()
        
        # Validation: Khali nahi hona chahiye, sirf spaces nahi, sirf dots nahi.
        # Kam se kam ek letter ya number hona chahiye.
        if not raw_description or not re.search(r'[a-zA-Z0-9]', raw_description):
            messages.error(request, "Description cannot be empty or contain only symbols/dots. Please explain the issue.")
            return redirect('vet_details', pk=pk)
        # --- DESCRIPTION VALIDATION END ---
            
        app_date = request.POST.get('app_date')
        app_slot = request.POST.get('app_slot')
        
        if not app_slot or "No slots" in app_slot:
            messages.error(request, "Please select a valid time slot.")
            return redirect('vet_details', pk=pk)

        try:
            naive_dt = datetime.strptime(f"{app_date} {app_slot}", "%Y-%m-%d %I:%M %p")
            check_datetime = timezone.make_aware(naive_dt)
            c_date = check_datetime.date()
            c_start = timezone.make_aware(datetime.combine(c_date, datetime.min.time()))
            c_end = timezone.make_aware(datetime.combine(c_date, datetime.max.time()))
        except ValueError:
            messages.error(request, "Invalid date/time format.")
            return redirect('vet_details', pk=pk)
        
        exists = Appointment.objects.filter(
            vet_id=vet, 
            appointment_date=check_datetime, 
            appointment_status__in=[0, 1, 3, 6]
        ).exists()
        
        if exists:
            messages.error(request, "Sorry, this slot was just booked. Please pick another.")
            return redirect('vet_details', pk=pk)

        already_booked_today = Appointment.objects.filter(
            cust_id=current_customer,
            vet_id=vet,
            appointment_date__range=(c_start, c_end),
            appointment_status__in=[0, 1, 3, 6]
        ).exists()

        if already_booked_today:
            messages.error(request, f"You already have an appointment on this date.")
            return redirect('vet_details', pk=pk)

        Appointment.objects.create(
            cust_id=current_customer,
            vet_id=vet,
            app_for=request.POST.get('app_for'),
            description=raw_description, # Cleaned description
            appointment_date=check_datetime,
            appointment_status=0
        )
        
        # Photo wala message hatane ke liye is line ko comment kar diya hai:
        # messages.success(request, "Appointment request sent successfully! 🚀")
        
        return redirect('my_appointments')

    # 4. GET Method: Display Logic
    available_days = VetSchedule.objects.filter(vet_id=vet).values_list('day_of_week', flat=True)
    booking_range = []
    all_slots_dict = {}
    
    for i in range(15):
        temp_date = today_obj + timedelta(days=i)
        if temp_date.weekday() in available_days:
            date_str = temp_date.strftime('%Y-%m-%d')
            
            if is_vet_vacation:
                all_slots_dict[date_str] = ["VET_ON_VACATION"]
                booking_range.append(temp_date)
                continue

            t_start = timezone.make_aware(datetime.combine(temp_date, datetime.min.time()))
            t_end = timezone.make_aware(datetime.combine(temp_date, datetime.max.time()))

            has_appt = Appointment.objects.filter(
                cust_id=current_customer,
                vet_id=vet,
                appointment_date__range=(t_start, t_end),
                appointment_status__in=[0, 1, 3, 6]
            ).exists() if current_customer else False

            if has_appt:
                all_slots_dict[date_str] = ["ALREADY_BOOKED"]
                booking_range.append(temp_date)
            else:
                day_slots = get_slots_for_date(temp_date)
                if day_slots:
                    booking_range.append(temp_date)
                    all_slots_dict[date_str] = day_slots

    context = {
        'vet': vet,
        'customer': current_customer,
        'feedbacks': feedbacks,
        'booking_range': booking_range,
        'today': today_obj.strftime('%Y-%m-%d'),
        'all_slots_data': all_slots_dict,
        'is_on_vacation': is_vet_vacation,
    }
    return render(request, 'vet_details.html', context)

def my_appointments(request):
    # 1. Session & Customer Validation
    cust_id = request.session.get('cust_id')
    if not cust_id: 
        return redirect('login1')
    
    customer = get_object_or_404(Customer, cust_id=cust_id)
    
    # --- AUTO-CANCEL EXPIRED SLOTS ---
    # GADBAD FIX: payment_timer_start__isnull=False add kiya hai 
    # taaki NULL values comparison mein crash na karein.
    expiry_limit = timezone.now() - timedelta(minutes=30)
    Appointment.objects.filter(
        cust_id=customer,
        appointment_status=1,
        payment_timer_start__isnull=False, 
        payment_timer_start__lt=expiry_limit
    ).update(appointment_status=2)

    # --- 2. POST Logic (Handling Actions) ---
    if request.method == "POST":
        
        # CASE A: Payment Confirmation (Status 1 -> 3)
        if 'confirm_payment' in request.POST:
            app_id = request.POST.get('app_id')
            mode = int(request.POST.get('payment_mode')) 
            appointment = get_object_or_404(Appointment, appointment_id=app_id, cust_id=customer)
            
            # GADBAD FIX: Server-side re-check for timer expiry before saving
            is_expired = False
            if appointment.payment_timer_start:
                if appointment.payment_timer_start < expiry_limit:
                    is_expired = True

            if appointment.appointment_status == 1 and not is_expired:
                if mode == 2 and customer.is_cash_blocked:
                    messages.error(request, "Cash payment is blocked due to previous no-shows.")
                else:
                    appointment.payment_mode = mode
                    appointment.appointment_status = 3 # Confirmed
                    appointment.save()
                    messages.success(request, "Appointment confirmed! See you at the clinic. 🐾")
            else:
                # Agar timer khatam ho gaya toh status update kar do manually
                appointment.appointment_status = 2
                appointment.save()
                messages.error(request, "Sorry, this payment window has expired.")

        # CASE B: Handle Reschedule (Status 6 -> 1 or 2)
        elif 'handle_reschedule' in request.POST:
            app_id = request.POST.get('app_id')
            action = request.POST.get('action') # 'accept' or 'reject'
            appointment = get_object_or_404(Appointment, appointment_id=app_id, cust_id=customer)

            if action == 'accept':
                appointment.appointment_status = 1  # Move to Payment Stage
                appointment.payment_timer_start = timezone.now() # Start NEW 30-min window
                appointment.save()
                messages.success(request, "Reschedule accepted! Please complete payment within 30 minutes.")
            else:
                appointment.appointment_status = 2  # Cancelled
                appointment.save()
                messages.warning(request, "Reschedule rejected. Appointment cancelled.")

        return redirect('my_appointments')

    # --- 3. GET Logic (Fetching Data) ---
    appointments = Appointment.objects.filter(cust_id=cust_id).order_by('-appointment_id')
    rated_app_ids = Feedback.objects.filter(cust_id=cust_id).values_list('appointment_id', flat=True)

    context = {
        'appointments': appointments,
        'customer': customer,
        'rated_app_ids': rated_app_ids,
        'now': timezone.now(), 
    }

    return render(request, 'my_appointments.html', context)
    
def submit_vet_feedback(request):
    if request.method == "POST":
        # 1. Login Check
        cust_id = request.session.get('cust_id')
        if not cust_id:
            messages.error(request, "Please login to submit feedback.")
            return redirect('login1')

        # 2. Data Fetching from POST
        vet_id = request.POST.get('vet_id')
        app_id = request.POST.get('app_id')
        rating = request.POST.get('rating')
        comments = request.POST.get('comments', '').strip()

        try:
            # 3. Object Fetching (Database Safety)
            vet_obj = get_object_or_404(Vet, vet_id=vet_id)
            cust_obj = get_object_or_404(Customer, cust_id=cust_id)
            app_obj = get_object_or_404(Appointment, appointment_id=app_id)

            # 4. DUPLICATE CHECK: Ek appointment ka ek hi feedback hona chahiye
            existing_feedback = Feedback.objects.filter(appointment_id=app_obj).exists()
            if existing_feedback:
                messages.warning(request, "You have already submitted feedback for this appointment.")
                return redirect('my_appointments')

            # 5. CREATE FEEDBACK
            Feedback.objects.create(
                cust_id=cust_obj,
                vet_id=vet_obj,
                appointment_id=app_obj,
                rating=rating,
                comments=comments
            )

            messages.success(request, f"Your review for Dr. {vet_obj.vet_name} has been submitted! ⭐")
        
        except Exception as e:
            # Troubleshooting ke liye terminal mein error print karega
            print(f"--- FEEDBACK SUBMISSION ERROR: {e} ---")
            messages.error(request, "Something went wrong while submitting feedback.")

        return redirect('my_appointments')

    # Agar koi direct URL hit kare bina POST ke
    return redirect('my_appointments')
 
# done by vraj
# client_views.py
# client_views.py
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.conf import settings 
from test2.models import Customer 

def edit_profile(request):
    cust_id = request.session.get('cust_id')
    if not cust_id: 
        return redirect('login1')
        
    customer = get_object_or_404(Customer, cust_id=cust_id)
    
    if request.method == "POST":
        # Details update
        customer.cust_name = request.POST.get('name')
        customer.contact = request.POST.get('contact')
        customer.address = request.POST.get('address')
        
        # Photo Remove Logic
        if request.POST.get('remove_photo_flag') == "1":
            customer.user_profile = None 
        
        # Photo Upload (Isse file permanent folder mein save hogi)
        elif 'profile_pic' in request.FILES:
            customer.user_profile = request.FILES['profile_pic']
            
        # DATABASE MEIN SAVE: Ye line file ko media root mein move kar degi
        customer.save() 
        
        # Session Sync (Permanent URL uthane ke liye)
        request.session['cust_name'] = customer.cust_name 
        if customer.user_profile:
            request.session['cust_profile'] = customer.user_profile.url
        else:
            request.session['cust_profile'] = f"{settings.STATIC_URL}assets/img/users/default.png"
            
        messages.success(request, "Profile updated successfully! 🐾")
        return redirect('home')

    return render(request, 'edit_profile.html', {'customer': customer})

from test2.models import Order #
# 2. My Orders View (With Tracking Logic)
def my_orders(request):
    cust_id = request.session.get('cust_id')
    if not cust_id: return redirect('login1')

    # Latest orders top par dikhane ke liye order_by('-order_id')
    orders = Order.objects.filter(cust_id=cust_id).order_by('-order_id')
    return render(request, 'my_orders.html', {'orders': orders})

def order_success(request):
    return render(request, 'order_success.html')

def my_orders(request):
    if 'cust_id' not in request.session:
        return redirect('customer_login')
    
    # Session se customer id lekar uske orders filter karo
    customer_id = request.session['cust_id']
    user_orders = Order.objects.filter(cust_id=customer_id).order_by('-order_date')
    
    return render(request, 'my_orders.html', {'user_orders': user_orders})