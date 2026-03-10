from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import make_password, check_password
from test2.models import DeliveryBoy, Vendor, Order #
from django.contrib import messages
import os

# --- 1. REGISTRATION (Redirects to Login) ---
def delivery_register(request):
    vendors = Vendor.objects.all()
    if request.method == "POST":
        v_id = request.POST.get('vendor_id')
        name = request.POST.get('deliveryboy_name')
        email = request.POST.get('email')
        contact = request.POST.get('contact')
        password = request.POST.get('password')
        profile_img = request.FILES.get('deliveryboy_profile')

        if DeliveryBoy.objects.filter(email=email).exists():
            messages.error(request, "Email already registered!")
            return render(request, 'registration.html', {'vendors': vendors})

        vendor_obj = Vendor.objects.get(vendor_id=v_id)
        
        new_boy = DeliveryBoy(
            vendor_id=vendor_obj,
            deliveryboy_name=name,
            email=email,
            contact=contact,
            password=make_password(password)
        )
        if profile_img:
            new_boy.deliveryboy_profile = profile_img
            
        new_boy.save()
        messages.success(request, "Registration successful! Please login to continue.")
        return redirect('delivery_login') # Dashboard ki jagah login par redirect

    return render(request, 'registration.html', {'vendors': vendors})

# --- 2. LOGIN ---
def delivery_login(request):
    if 'delivery_id' in request.session:
        return redirect('delivery_dashboard')

    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            agent = DeliveryBoy.objects.get(email=email)
            if check_password(password, agent.password):
                request.session['delivery_id'] = agent.deliveryboy_id
                request.session['delivery_name'] = agent.deliveryboy_name
                messages.success(request, f"Welcome back, {agent.deliveryboy_name}!")
                return redirect('delivery_dashboard')
            else:
                messages.error(request, "Invalid password. Please try again.")
        except DeliveryBoy.DoesNotExist:
            messages.error(request, "Email not found in our records.")

    return render(request, 'dlogin.html')

# --- 3. DASHBOARD ---
def delivery_dashboard(request):
    if 'delivery_id' not in request.session:
        return redirect('delivery_login')

    delivery_id = request.session['delivery_id']
    agent = get_object_or_404(DeliveryBoy, pk=delivery_id)
    
    # Active vs Completed logic
    active_tasks = Order.objects.filter(deliveryboy_id=agent, order_status__in=[0, 1])
    completed_count = Order.objects.filter(deliveryboy_id=agent, order_status=2).count()

    context = {
        'agent': agent,
        'active_tasks': active_tasks,
        'completed_count': completed_count,
    }
    return render(request, 'delivery_dashboard.html', context)

# --- 4. FULL EDIT PROFILE (With Photo Remove Logic) ---
def edit_profile(request):
    if 'delivery_id' not in request.session:
        return redirect('delivery_login')
        
    agent = DeliveryBoy.objects.get(pk=request.session['delivery_id'])
    
    if request.method == 'POST':
        # Sirf wahi fields uthao jo form mein hain
        name = request.POST.get('deliveryboy_name')
        contact = request.POST.get('contact')
        
        if name and contact:
            agent.deliveryboy_name = name
            agent.contact = contact
            
            # Photo Logic: Change or Remove
            if 'profile_photo' in request.FILES:
                # Nayi photo upload ho rahi hai
                agent.deliveryboy_profile = request.FILES['profile_photo']
            elif request.POST.get('remove_photo'):
                # Agar user ne 'Remove' checkbox tick kiya hai
                agent.deliveryboy_profile = None
                
            agent.save()
            request.session['delivery_name'] = agent.deliveryboy_name
            messages.success(request, "Profile updated successfully! 🐾")
        else:
            messages.error(request, "All fields are required!")
            
    return redirect('delivery_dashboard')

# --- 5. TOGGLE STATUS & ORDER UPDATES ---
def toggle_status(request):
    if 'delivery_id' in request.session:
        agent = DeliveryBoy.objects.get(pk=request.session['delivery_id'])
        agent.is_available = 0 if agent.is_available == 1 else 1
        agent.save()
        messages.success(request, f"Status set to {'Online' if agent.is_available == 1 else 'Offline'}.")
    return redirect('delivery_dashboard')

def deliver_order(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    order.order_status = 2 # Delivered status
    order.save()
    messages.success(request, f"Order #ORD-{order_id} has been delivered.")
    return redirect('delivery_dashboard')

# --- 6. LOGOUT ---
def delivery_logout(request):
    if 'delivery_id' in request.session:
        del request.session['delivery_id']
    if 'delivery_name' in request.session:
        del request.session['delivery_name']
    messages.info(request, "Logged out successfully.")
    return redirect('delivery_login')