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
            messages.error(request, "This email is already registered!", extra_tags='vendor_reg')
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
            messages.success(request, "Registration successful! Login after Admin approval.", extra_tags='vendor_reg')
            # YAHAN SE REDIRECT KARNA ZAROORI HAI TAAKI NICHE WALA CODE RUN NA HO
            return redirect('vendor_login') 

        except Exception as e:
            print("Error during vendor registration:", e)
            messages.error(request, f"Registration failed! {e}", extra_tags='vendor_reg')
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
                    messages.success(request, f"Welcome back, {vendor.vendor_name}!", extra_tags='vendor_login')
                    return redirect('vendor_dashboard') # Apne dashboard ka naam check kar lena
                
                # - vendor_login function ke andar ye update karein
                elif vendor.status == 0:
                    messages.error(request, "Your account is pending for Admin approval.", extra_tags='vendor_login')
                elif vendor.status == 2:
                    messages.error(request, "Your registration request was rejected.", extra_tags='vendor_login')
                elif vendor.status == 3:
                    messages.error(request, "Your account has been restricted by Admin.", extra_tags='vendor_login')
                
            else:
                messages.error(request, "Invalid Password!", extra_tags='vendor_login')
        
        except Vendor.DoesNotExist:
            messages.error(request, "No account found with this email!", extra_tags='vendor_login')

    return render(request, 'vendor_login.html')

from django.shortcuts import render, redirect, get_object_or_404
from test2.models import Vendor, Product, ProductCategory, Gallery,DeliveryBoy #

def vendor_dashboard(request):
    if 'vendor_id' not in request.session:
        messages.error(request, "Please login first!", extra_tags='vendor_login')
        return redirect('vendor_login')

    vendor = get_object_or_404(Vendor, vendor_id=request.session['vendor_id'])
    
    all_boys = DeliveryBoy.objects.filter(vendor_id=vendor)

    # Database se categories uthao dropdown ke liye
    categories = ProductCategory.objects.all()
    # Vendor ke purane products list karne ke liye
    my_products = Product.objects.filter(vendor_id=vendor).order_by('-prod_id')

    if request.method == "POST":
        # --- A. PRODUCT UPLOAD LOGIC ---
        if 'add_product' in request.POST:
            p_name = request.POST.get('p_name')
            p_cat_id = request.POST.get('p_category')
            p_price = request.POST.get('p_price')
            p_qty = request.POST.get('p_qty')
            p_desc = request.POST.get('p_desc')
            p_cover = request.FILES.get('p_cover') # Main Image
            p_gallery = request.FILES.getlist('p_gallery') # Multiple Gallery Images

            try:
                # Category object fetch karo
                cat_obj = ProductCategory.objects.get(category_id=p_cat_id)
                
                # 1. Product save karo
                new_prod = Product.objects.create(
                    vendor_id=vendor,
                    category_id=cat_obj,
                    prod_name=p_name,
                    price=p_price,
                    qty=p_qty,
                    description=p_desc,
                    cover_img_path=p_cover
                )

                # 2. Gallery images save karo
                for img in p_gallery:
                    Gallery.objects.create(prod_id=new_prod, image_path=img)

                messages.success(request, "Product listed successfully!", extra_tags='vendor_login')
                return redirect('vendor_dashboard')
            except Exception as e:
                messages.error(request, f"Upload failed: {e}")

        # --- B. PROFILE UPDATE LOGIC (Tera purana code) ---
        elif 'vendor_name' in request.POST:
            v_name = request.POST.get('vendor_name', '').strip()
            v_contact = request.POST.get('contact', '').strip()
            v_address = request.POST.get('address', '').strip()
            
            if 'vendor_profile' in request.FILES:
                vendor.vendor_profile = request.FILES['vendor_profile']
            
            vendor.vendor_name = v_name
            vendor.contact = v_contact
            vendor.address = v_address
            vendor.save()
            request.session['vendor_name'] = vendor.vendor_name
            messages.success(request, "Profile updated successfully!", extra_tags='vendor_login')
            return redirect('vendor_dashboard')

    return render(request, 'vendor_dashboard.html', {
        'vendor': vendor,
        'categories': categories,
        'products': my_products,
        'all_boys': all_boys,
    })

def update_db_status(request, db_id, new_status):
    if 'vendor_id' not in request.session:
        return redirect('vendor_login')
    
    boy = get_object_or_404(DeliveryBoy, deliveryboy_id=db_id)

    # STRICT LOGIC: Rejected (2) case closed hai, koi badlav nahi hoga
    if boy.status == 2:
        messages.error(request, f"Access Denied: {boy.deliveryboy_name} is already Rejected.", extra_tags='vendor_login')
        return redirect('vendor_dashboard')

    # Status update karo
    boy.status = new_status
    boy.save()
    
    # Sirf wahi messages rakhe hain jo actually trigger honge
    status_msgs = {
        1: f"{boy.deliveryboy_name} is now Active! ✅",
        2: f"{boy.deliveryboy_name} Registration Rejected. ❌",
        3: f"{boy.deliveryboy_name} is now Restricted. 🚫"
    }
    
    # Reactivate ke liye special message
    if new_status == 1 and boy.status == 3:
        msg = f"{boy.deliveryboy_name} Reactivated successfully! 🔄"
    else:
        msg = status_msgs.get(new_status, "Status Updated!")

    messages.success(request, msg, extra_tags='vendor_login')
    return redirect('vendor_dashboard')

def vendor_logout(request):
    if 'vendor_id' in request.session:
        del request.session['vendor_id']
        del request.session['vendor_name']
    return redirect('vendor_login')