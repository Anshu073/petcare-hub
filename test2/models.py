import os

from django.db import models

from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.core.validators import RegexValidator

phone_regex = RegexValidator(regex=r'^\d{10}$', message="Contact number must be 10 digits.")
name_regex = RegexValidator(regex=r'^[a-zA-Z\s]*$', message="Name can only contain letters and spaces.")
#1
class Area(models.Model):
    area_id = models.AutoField(primary_key=True)
    area_name = models.CharField(max_length=10)
    pincode = models.IntegerField()

    class Meta:
        db_table = 'AREA_TABLE'

from django.core.validators import RegexValidator
#2
class Customer(models.Model):
    phone_regex = RegexValidator(regex=r'^\d{10}$', message="Contact number must be 10 digits.")
    name_regex = RegexValidator(regex=r'^[a-zA-Z\s]*$', message="Name can only contain letters and spaces.")
    
    cust_id = models.AutoField(primary_key=True)
    area_id = models.ForeignKey(Area, on_delete=models.CASCADE)
    cust_name = models.CharField(max_length=15,validators=[name_regex])
    password = models.CharField(max_length=128)  # Increased length for hashed passwords
    email = models.EmailField(max_length=20, unique=True)
    contact = models.CharField(max_length=10, validators=[phone_regex])
    address = models.CharField(max_length=200)
    user_profile = models.ImageField(upload_to='customer_profiles/', null=True, blank=True)    # Real-world ImageField
    is_admin = models.IntegerField(default=0) # Default: 0 (Normal User)
    otp = models.CharField(max_length=10 , null=True)
    otp_used = models.IntegerField(default=0)
    strike_count = models.IntegerField(default=0) # 0 to 3
    is_cash_blocked = models.BooleanField(default=False) # True if 3 strikes reached
    payment_credit = models.BooleanField(default=False) # For rescheduling/cancel refund

    class Meta: 
        db_table = 'CUSTOMER_TABLE'
        
# Jab bhi Customer ka data save hoga, ye function purani photo check karega
@receiver(pre_save, sender=Customer)
def auto_delete_file_on_change(sender, instance, **kwargs):
    # Agar ye naya data nahi hai (yani update ho raha hai)
    if not instance.pk:
        return False

    try:
        # Database se purana record uthao
        old_file = sender.objects.get(pk=instance.pk).user_profile
    except sender.DoesNotExist:
        return False

    # Nayi file jo upload ho rahi hai
    new_file = instance.user_profile
    
    # Agar purani file exist karti hai aur wo nayi file se alag hai
    if old_file and old_file != new_file:
        if os.path.isfile(old_file.path):
            os.remove(old_file.path) # Purani file ko storage se uda do        

#3
class Vet(models.Model):
        # Defining specific options for the dropdown
        SPECIALIST_CHOICES = [
            ('Dog Specialist', 'Dog Specialist'),
            ('Cat Specialist', 'Cat Specialist'),
            ('General (Both)', 'General (Both Dog & Cat)'),        
        ]
        
        vet_id = models.AutoField(primary_key=True)
        area_id = models.ForeignKey(Area, on_delete=models.CASCADE)
        vet_name = models.CharField(max_length=15,validators=[name_regex])
        password = models.CharField(max_length=128)  # Increased length for hashed passwords
        email = models.EmailField(max_length=20, unique=True)
        vet_profile = models.ImageField(upload_to='vet_profiles/', null=True, blank=True)
        specialization = models.CharField(
            max_length=20, 
            choices=SPECIALIST_CHOICES, # This creates a dropdown in Admin Panel
            default='General (Both)'
        )
        contact = models.CharField(max_length=10,validators=[phone_regex])
        documents = models.FileField(upload_to='vet_docs/', null=True, blank=True)
        status = models.IntegerField(default=0) # Default: 0 (Pending approval)
        charges = models.IntegerField()
        address = models.CharField(max_length=200)
        otp = models.CharField(max_length=10, null=True)
        otp_used = models.IntegerField(default=0)
        open_time = models.TimeField(null=True, blank=True)
        close_time = models.TimeField(null=True, blank=True)
        last_timing_update = models.DateTimeField(null=True, blank=True) # Lock check ke liye
        is_first_login = models.BooleanField(default=True) # To show mandatory timing pop-up
        availability_status = models.IntegerField(default=0) # 0:Offline, 1:Online, 2:Vacation/Leave
        cancel_count = models.IntegerField(default=0) # Hidden counter to track vet cancellations
        
        class Meta:
            db_table = 'VET_TABLE'
        
class VetSchedule(models.Model):
    DAYS = [
        (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), 
        (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday')
    ]
    schedule_id = models.AutoField(primary_key=True)
    vet_id = models.ForeignKey(Vet, on_delete=models.CASCADE)
    day_of_week = models.IntegerField(choices=DAYS)
    open_time = models.TimeField()
    close_time = models.TimeField()

    class Meta:
        db_table = 'VET_SCHEDULE_TABLE'
#4

class Vendor(models.Model):
    vendor_id = models.AutoField(primary_key=True)
    area_id = models.ForeignKey(Area, on_delete=models.CASCADE)
    vendor_name = models.CharField(max_length=15)
    password = models.CharField(max_length=128)  # Increased length for hashed passwords
    email = models.EmailField(max_length=20, unique=True)
    contact = models.CharField(max_length=10)
    address = models.CharField(max_length=200)
    vendor_profile = models.CharField(max_length=200,null=True)

    class Meta:
        db_table = 'VENDOR_TABLE'
#5
class DeliveryBoy(models.Model):
    deliveryboy_id = models.AutoField(primary_key=True)
    vendor_id = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    deliveryboy_name = models.CharField(max_length=15)
    password = models.CharField(max_length=128)  # Increased length for hashed passwords
    email = models.EmailField(max_length=20, unique=True)
    contact = models.CharField(max_length=10)
    is_available = models.IntegerField(default=1) # Default: 1 (Available)
    deliveryboy_profile = models.CharField(max_length=200,null=True)

    class Meta:
        db_table = 'DELIVERY_BOY_TABLE'
#6
class Appointment(models.Model):
    appointment_id = models.AutoField(primary_key=True)
    cust_id = models.ForeignKey(Customer, on_delete=models.CASCADE)
    vet_id = models.ForeignKey(Vet, on_delete=models.CASCADE)
    app_for = models.CharField(max_length=5)
    description = models.CharField(max_length=50)
    appointment_date = models.DateTimeField()
    appointment_status = models.IntegerField(default=0) # 0:Pending, 1:Selection, 2:Cancelled, 3:Approved, 4:Done, 5:Absent, 6:Reschedule Requested
    payment_timer_start = models.DateTimeField(null=True, blank=True) # 30-60 min timer
    medical_report = models.FileField(upload_to='reports/', null=True, blank=True) #
    payment_mode = models.IntegerField(default=0) # 1: Online, 2: Cash
    cancel_reason = models.TextField(null=True, blank=True)
    

    class Meta:
        db_table = 'APPOINTMENT_TABLE'
#7
class ProductCategory(models.Model):
    category_id = models.AutoField(primary_key=True)
    category_name = models.CharField(max_length=15)
    description = models.CharField(max_length=50)

    class Meta:
        db_table = 'PRODUCT_CATEGORY_TABLE'
#8
class Product(models.Model):
    prod_id = models.AutoField(primary_key=True)
    category_id = models.ForeignKey(ProductCategory, on_delete=models.CASCADE)
    vendor_id = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    prod_name = models.CharField(max_length=15)
    qty = models.IntegerField(default=0) # Default: 0 (Out of stock)
    description = models.CharField(max_length=50)
    price = models.IntegerField()
    cover_img_path = models.CharField(max_length=200)

    class Meta:
        db_table = 'PRODUCT_TABLE'
#9
class Order(models.Model):
    order_id = models.AutoField(primary_key=True)
    cust_id = models.ForeignKey(Customer, on_delete=models.CASCADE)
    deliveryboy_id = models.ForeignKey(DeliveryBoy, on_delete=models.CASCADE)
    area_id = models.ForeignKey(Area, on_delete=models.CASCADE)
    total_amount = models.IntegerField()
    address = models.CharField(max_length=200)
    order_date = models.DateField(auto_now_add=True) # Automatically sets to today
    order_status = models.IntegerField(default=0) # Default: 0 (Placed/Pending)
    delivery_date = models.DateField()

    class Meta:
        db_table = 'ORDER_TABLE'
#10
class OrderDetail(models.Model):
    order_details_id = models.AutoField(primary_key=True)
    order_id = models.ForeignKey(Order, on_delete=models.CASCADE)
    prod_id = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.IntegerField()

    class Meta:
        db_table = 'ORDER_DETAIL_TABLE'
#11
class AppointmentPayment(models.Model):
    app_payment_id = models.AutoField(primary_key=True)
    appointment_id = models.ForeignKey(Appointment, on_delete=models.CASCADE)
    payment_mode = models.CharField(max_length=6)
    amount = models.IntegerField()
    payment_status = models.IntegerField(default=0) # Default: 0 (Unpaid)
    payment_token = models.CharField(max_length=50)
    payment_date = models.DateField(auto_now_add=True)
    payment_time = models.TimeField(auto_now_add=True)

    class Meta:
        db_table = 'APPOINTMENT_PAYMENT_TABLE'
#12
class OrderPayment(models.Model):
    ord_payment_id = models.AutoField(primary_key=True)
    order_id = models.ForeignKey(Order, on_delete=models.CASCADE)
    payment_mode = models.CharField(max_length=6) # e.g., Cash, Online
    amount = models.IntegerField()
    payment_status = models.IntegerField()
    payment_token = models.CharField(max_length=50)
    payment_date = models.DateField(auto_now_add=True)
    payment_time = models.TimeField(auto_now_add=True)

    class Meta:
        db_table = 'ORDER_PAYMENT_TABLE'        
#13
class Feedback(models.Model):
    feedback_id = models.AutoField(primary_key=True)
    cust_id = models.ForeignKey(Customer, on_delete=models.CASCADE)
    prod_id = models.ForeignKey(Product, on_delete=models.CASCADE,null=True)
    vet_id = models.ForeignKey(Vet,on_delete=models.CASCADE,null=True)
    appointment_id = models.ForeignKey(Appointment, on_delete=models.CASCADE, null=True, blank=True)
    comments = models.CharField(max_length=200)
    rating = models.IntegerField()
    feedback_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'FEEDBACK_TABLE'
#14
class Gallery(models.Model):
    gallery_id = models.AutoField(primary_key=True)
    prod_id = models.ForeignKey(Product, on_delete=models.CASCADE)
    image_path = models.CharField(max_length=100)

    class Meta:
        db_table = 'GALLERY_TABLE'

# 15. WHISLIST_TABLE
class Wishlist(models.Model):
    whislist_id = models.AutoField(primary_key=True)
    cust_id = models.ForeignKey(Customer, on_delete=models.CASCADE)
    prod_id = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'WHISLIST_TABLE'

# 16. CART_TABLE
class Cart(models.Model):
    cart_id = models.AutoField(primary_key=True)
    cust_id = models.ForeignKey(Customer, on_delete=models.CASCADE)
    prod_id = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.IntegerField()
    total_price = models.IntegerField()
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.IntegerField(default=1)

    class Meta:
        db_table = 'CART_TABLE'