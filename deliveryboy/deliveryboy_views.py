from django.shortcuts import render, redirect
from django.contrib.auth.hashers import make_password
from test2.models import DeliveryBoy, Vendor  # Aapke models se import
from django.contrib import messages

def delivery_register(request):
    # Dropdown ke liye saare vendors fetch karein
    vendors = Vendor.objects.all()

    if request.method == "POST":
        # Form se data nikalna
        v_id = request.POST.get('vendor_id')
        name = request.POST.get('deliveryboy_name')
        email = request.POST.get('email')
        contact = request.POST.get('contact')
        password = request.POST.get('password')
        
        # Image handle karna
        profile_img = request.FILES.get('deliveryboy_profile')

        # Validation: Email unique honi chahiye
        if DeliveryBoy.objects.filter(email=email).exists():
            messages.error(request, "Email already registered!")
            return render(request, 'delivery_register.html', {'vendors': vendors})

        try:
            # Foreign Key object fetch karna
            vendor_obj = Vendor.objects.get(vendor_id=v_id)

            # Naya DeliveryBoy create karna
            new_boy = DeliveryBoy(
                vendor_id=vendor_obj,
                deliveryboy_name=name,
                email=email,
                contact=contact,
                password=make_password(password), # Password ko hash karna
                deliveryboy_profile=profile_img, # Image path store hoga
                is_available=1 # Default: Available
            )
            new_boy.save()

            messages.success(request, "Registration successful! Please login.")
            return redirect('delivery_login') # Login page par bhejein

        except Exception as e:
            messages.error(request, f"Error: {e}")

    return render(request, 'registration.html', {'vendors': vendors})

from django.contrib.auth.hashers import check_password
def delivery_login(request):
    # Check if already logged in
    if 'delivery_id' in request.session:
        return redirect('delivery_dashboard')

    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            # Email se fetch karo
            agent = DeliveryBoy.objects.get(email=email)
            
            # Password verification
            if check_password(password, agent.password):
                # Specific session keys set karo
                request.session['delivery_id'] = agent.deliveryboy_id
                request.session['delivery_name'] = agent.deliveryboy_name
                
                messages.success(request, f"Login successful! Welcome {agent.deliveryboy_name}.")
                return redirect('delivery_dashboard')
            else:
                messages.error(request, "Invalid password. Please try again.")
        
        except DeliveryBoy.DoesNotExist:
            messages.error(request, "Email not found in our records.")

    return render(request, 'dlogin.html')