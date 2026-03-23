from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import make_password, check_password
from test2.models import DeliveryBoy, Vendor, Order,Area #
from django.contrib import messages
import os

# --- 1. REGISTRATION (Redirects to Login) ---
def delivery_register(request):
    vendors = Vendor.objects.all()
    areas = Area.objects.all()

    if request.method == "POST":
        v_id = request.POST.get('vendor_id')
        a_id = request.POST.get('area_id')
        name = request.POST.get('deliveryboy_name')
        email = request.POST.get('email')
        contact = request.POST.get('contact')
        password = request.POST.get('password')
        profile_img = request.FILES.get('deliveryboy_profile')

        if DeliveryBoy.objects.filter(email=email).exists():
            messages.error(request, "This email is already registered!",extra_tags='del_reg')
            return render(request, 'registration.html', {'vendors': vendors})

        try:

            vendor_obj = Vendor.objects.get(vendor_id=v_id)
            area_obj = Area.objects.get(area_id=a_id)
        
            new_boy = DeliveryBoy(
                vendor_id=vendor_obj,
                area_id=area_obj,
                deliveryboy_name=name,
                email=email,
                contact=contact,
                password=make_password(password),
                status=0       # Default 0 (Vendor approve karega)
            )
            if profile_img:
                new_boy.deliveryboy_profile = profile_img
            
            new_boy.save()
            messages.success(request, "Registration successful! Please wait for Vendor approval before login.",extra_tags='delivery_login')
            return redirect('delivery_login') # Dashboard ki jagah login par redirect

        except Exception as e:
            messages.error(request, f"Registration failed: {e}",extra_tags='del_reg')
            return render(request, 'registration.html', {'vendors': vendors, 'areas': areas})
        
    return render(request, 'registration.html', {'vendors': vendors,'areas': areas})

# --- 2. LOGIN ---
def delivery_login(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        try:
            agent = DeliveryBoy.objects.get(email=email)
            if check_password(password, agent.password):
                # Status checks
                if agent.status == 0:
                    messages.error(request, "Pending Approval: Wait for vendor to approve.", extra_tags='delivery_login')
                    return render(request, 'dlogin.html')
                elif agent.status == 2:
                    messages.error(request, "Rejected: Your account was denied.", extra_tags='delivery_login')
                    return render(request, 'dlogin.html')
                elif agent.status == 3:
                    messages.error(request, "Restricted: Account is blocked.", extra_tags='delivery_login')
                    return render(request, 'dlogin.html')

                # Login Success
                request.session['delivery_id'] = agent.deliveryboy_id
                messages.success(request, f"Welcome back, {agent.deliveryboy_name}!", extra_tags='delivery_login')
                return redirect('delivery_dashboard')
            else:
                messages.error(request, "Invalid Password!", extra_tags='delivery_login')
        except DeliveryBoy.DoesNotExist:
            messages.error(request, "Account not found!", extra_tags='delivery_login')
    return render(request, 'dlogin.html')

# --- 3. DASHBOARD ---
def delivery_dashboard(request):
    if 'delivery_id' not in request.session:
        return redirect('delivery_login')

    delivery_id = request.session['delivery_id']
    agent = get_object_or_404(DeliveryBoy, pk=delivery_id)

    # Status check
    if agent.status != 1:
        del request.session['delivery_id']
        if 'delivery_name' in request.session:
            del request.session['delivery_name']
        messages.error(request, "Access Denied: Your account is no longer active. 🚫", extra_tags='danger')
        return redirect('delivery_login')

    from test2.models import OrderDetail

    # Sirf is delivery boy ke assigned orders ke OrderDetails fetch karo
    # detail_status=1 (Assigned) ya 2 (Out for Delivery) wale active tasks hain
    active_details = OrderDetail.objects.filter(
        order_id__deliveryboy_id=agent,   # Is delivery boy ke assigned orders
        vendor_id=agent.vendor_id,        # Sirf apne vendor ke products
        detail_status__in=[1, 2]
    ).select_related(
        'order_id',
        'prod_id',
        'order_id__cust_id',
        'order_id__cust_id__area_id'
    ).order_by('order_id__order_id')

    # Order-wise group karo (ek order ke saare products ek saath)
    from collections import OrderedDict
    order_groups = OrderedDict()
    for detail in active_details:
        oid = detail.order_id.order_id
        if oid not in order_groups:
            order_groups[oid] = {
                'order': detail.order_id,
                'products': [],
                'detail_status': detail.detail_status  # Pehle product ka status
            }
        order_groups[oid]['products'].append({
            'detail': detail,
            'subtotal': detail.price * detail.quantity
        })

    # Completed orders fetch karo (detail_status=3)
    completed_details = OrderDetail.objects.filter(
        order_id__deliveryboy_id=agent,
        vendor_id=agent.vendor_id,        # Sirf apne vendor ke products
        detail_status=3
    ).select_related(
        'order_id',
        'prod_id',
        'order_id__cust_id',
        'order_id__cust_id__area_id',
        'vendor_id'
    ).order_by('-order_id__order_id')

    # Completed orders bhi group karo
    completed_groups = OrderedDict()
    for detail in completed_details:
        oid = detail.order_id.order_id
        if oid not in completed_groups:
            completed_groups[oid] = {
                'order': detail.order_id,
                'products': [],
                'detail_status': detail.detail_status
            }
        completed_groups[oid]['products'].append({
            'detail': detail,
            'subtotal': detail.price * detail.quantity
        })

    completed_count = len(completed_groups)

    context = {
        'agent': agent,
        'order_groups': list(order_groups.values()),        # Active orders
        'completed_groups': list(completed_groups.values()), # Completed orders
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

# --- 6. LOGOUT ---
def delivery_logout(request):
    if 'delivery_id' in request.session:
        del request.session['delivery_id']
    if 'delivery_name' in request.session:
        del request.session['delivery_name']
    messages.info(request, "Logged out successfully.")
    return redirect('delivery_login')

def update_delivery_status(request, order_id, new_status):
    if 'delivery_id' not in request.session:
        return redirect('delivery_login')

    from test2.models import OrderDetail
    
    agent = get_object_or_404(DeliveryBoy, pk=request.session['delivery_id'])
    order = get_object_or_404(Order, pk=order_id, deliveryboy_id=agent)

    # Logical check: Status sirf aage badh sakta hai
    # 1 (Assigned) → 2 (Out for Delivery) → 3 (Delivered)
    # Sirf is delivery boy ke vendor ke products update karo
    current_details = OrderDetail.objects.filter(
        order_id=order,
        order_id__deliveryboy_id=agent,
        vendor_id=agent.vendor_id         # Sirf apne vendor ke products
    )

    current_status = current_details.first().detail_status if current_details.exists() else 0

    if new_status == 2 and current_status != 1:
        messages.error(request, "Pehle order pick-up karna zaroori hai!")
        return redirect('delivery_dashboard')

    if new_status == 3 and current_status != 2:
        messages.error(request, "Pehle Out for Delivery karna zaroori hai!")
        return redirect('delivery_dashboard')

    # STEP 1: Is delivery boy ke is order ke saare OrderDetails update karo
    current_details.update(detail_status=new_status)

    # STEP 2: Order.order_status auto-calculate karo
    all_details = OrderDetail.objects.filter(order_id=order)
    all_statuses = list(all_details.values_list('detail_status', flat=True))

    if all(s == 3 for s in all_statuses):
        order.order_status = 3
    elif all(s >= 2 for s in all_statuses):
        order.order_status = 2
    elif all(s >= 1 for s in all_statuses):
        order.order_status = 1
    else:
        order.order_status = 0

    order.save()
    messages.success(request, "Status Updated! 🐾")
    return redirect('delivery_dashboard')