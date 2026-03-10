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
        
    if request.method == "POST":
        agent = DeliveryBoy.objects.get(pk=request.session['delivery_id'])
        
        agent.deliveryboy_name = request.POST.get('name')
        agent.contact = request.POST.get('contact')
        agent.email = request.POST.get('email')
        
        # Photo handling: Update or Remove
        # Updated Photo Handling inside edit_profile function
        if 'remove_photo' in request.POST:
            if agent.deliveryboy_profile:
                # Physical file delete karna
                if os.path.exists(agent.deliveryboy_profile.path):
                    os.remove(agent.deliveryboy_profile.path)
                agent.deliveryboy_profile = None 
        else:
            new_photo = request.FILES.get('profile_photo')
            if new_photo:
                # Purani hatao aur nayi lagao
                if agent.deliveryboy_profile and os.path.exists(agent.deliveryboy_profile.path):
                    os.remove(agent.deliveryboy_profile.path)
                agent.deliveryboy_profile = new_photo
            
        agent.save()
        messages.success(request, "Profile details updated successfully.")
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