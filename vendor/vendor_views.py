from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from test2.models import Vendor, Area  #

# - Is logic ko update karein
def vendor_register(request):
    # Registration form ke dropdown ke liye saare areas fetch karein
    areas = Area.objects.all() 
    
    if request.method == "POST":
        v_name = request.POST.get('vendor_name')
        v_email = request.POST.get('email')
        v_pass = request.POST.get('password')
        v_contact = request.POST.get('contact')
        v_address = request.POST.get('address')
        v_area = request.POST.get('area_id')
        v_profile = request.FILES.get('vendor_profile')

        # 1. Email check (Duplicate email nahi honi chahiye)
        if Vendor.objects.filter(email=v_email).exists():
            messages.error(request, "This email is already registered!")
            return render(request, 'vendor_register.html', {'areas': areas})

        try:
            # 2. Area object fetch karein
            area_obj = Area.objects.get(area_id=v_area)
            
            # 3. Vendor Entry with Status 0 (Pending)
            Vendor.objects.create(
                vendor_name=v_name,
                email=v_email,
                password=make_password(v_pass), 
                contact=v_contact,
                address=v_address,
                area_id=area_obj,
                vendor_profile=v_profile,
                status=0  
            )
            messages.success(request, "Registration successful! Login after Admin approval.")
            # YAHAN SE REDIRECT KARNA ZAROORI HAI TAAKI NICHE WALA CODE RUN NA HO
            return redirect('vendor_login') 

        except Exception as e:
            print("Error during vendor registration:", e)
            messages.error(request, "Registration failed! Please try again.")
            # Error ke case mein wapas isi page par redirect/render
            return render(request, 'vendor_register.html', {'areas': areas})

    # GET request ke liye
    return render(request, 'vendor_register.html', {'areas': areas})

from django.contrib.auth.hashers import check_password
def vendor_login(request):
    if request.method == "POST":
        v_email = request.POST.get('email')
        v_pass = request.POST.get('password')

        try:
            # Email se vendor ko dhundho
            vendor = Vendor.objects.get(email=v_email)

            # 1. Password check karo
            if check_password(v_pass, vendor.password):
                
                # 2. Status check karo (Sirf Approved vendor hi login kar sakega)
                if vendor.status == 1:
                    request.session['vendor_id'] = vendor.vendor_id
                    request.session['vendor_name'] = vendor.vendor_name
                    messages.success(request, f"Welcome back, {vendor.vendor_name}!")
                    return redirect('vendor_dashboard') # Apne dashboard ka naam check kar lena
                
                elif vendor.status == 0:
                    messages.error(request, "Your account is pending for Admin approval.")
                elif vendor.status == 2:
                    messages.error(request, "Your registration request was rejected.")
                elif vendor.status == 3:
                    messages.error(request, "Your account has been restricted by Admin.")
                
            else:
                messages.error(request, "Invalid Password!")
        
        except Vendor.DoesNotExist:
            messages.error(request, "No account found with this email!")

    return render(request, 'vendor_login.html')

def vendor_dashboard(request):
    # Session check karo ki vendor logged in hai ya nahi
    if 'vendor_id' not in request.session:
        messages.error(request, "Please login first!")
        return redirect('vendor_login')

    vendor_id = request.session['vendor_id']
    vendor = Vendor.objects.get(vendor_id=vendor_id)
    
    # Dashboard render karte waqt vendor ka pura data bhej rahe hain
    return render(request, 'vendor_dashboard.html', {'vendor': vendor})