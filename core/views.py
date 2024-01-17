from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.contrib import messages
from core.models import Product, Category, Vendor, CartOrder, CartOrderProducts, ProductImages, ProductReview, Wishlist_model, Address
from userauths.models import ContactUs, Profile
from core.models import RATING
from core.forms import ProductReviewForm
from taggit.models import Tag
from django.db.models import Avg, Count
from django.contrib.auth.decorators import login_required
import calendar
from django.db.models.functions import ExtractMonth
from django.core import serializers

from django.urls import reverse
from django.conf import settings
from paypal.standard.forms import PayPalPaymentsForm

def index(request):
    products = Product.objects.filter(product_status="published", featured=True).order_by("-id")
    latest_products = Product.objects.order_by('-date')[:3]
    top_rated_products = Product.objects.annotate(reviews_count=Count('reviews')).order_by('-reviews_count')[:3]
    cheapest_products = Product.objects.filter(product_status="published").order_by('price')[:3]
    
    sorted_products = sorted(products, key=lambda x: x.get_percentage(), reverse=True)
    highest_discount_products = sorted_products[:3]
    
    context = {
        "products": products,
        "latest_products": latest_products,
        "top_rated_products": top_rated_products,
        "cheapest_products": cheapest_products,
        "highest_discount_products": highest_discount_products,
    }

    return render(request, 'core/index.html', context)

def product_list_view(request):
    products = Product.objects.filter(product_status="published").order_by("-id")

    context = {
        "products": products,
    }
    return render(request, 'core/product-list.html', context)

def category_list_view(request):
    categories = Category.objects.all()

    context = {
        "categories": categories
    }
    return render(request, 'core/category-list.html', context)

def category_product_list_view(request, cid):
    category = Category.objects.get(cid=cid)
    products = Product.objects.filter(product_status="published", category=category)

    context = {
        "category": category,
        "products": products,
    }
    return render(request, "core/category-product-list.html", context)

def vendor_list_view(request):
    vendors = Vendor.objects.all()

    context = {
        "vendors": vendors,
    }
    return render(request, "core/vendor-list.html", context)

def vendor_detail_view(request, vid):
    vendor = Vendor.objects.get(vid=vid)
    products = Product.objects.filter(vendor=vendor, product_status="published").order_by("-id")

    context = {
        "vendor": vendor,
        "products": products,
    }
    return render(request, "core/vendor-detail.html", context)

def product_detail_view(request, pid):
    product = Product.objects.get(pid=pid)
    products = Product.objects.filter(category=product.category).exclude(pid=pid)
    reviews = ProductReview.objects.filter(product=product).order_by("-date")

    average_rating = ProductReview.objects.filter(product=product).aggregate(rating=Avg('rating'))
    review_form = ProductReviewForm()
    make_review = True 

    address = None

    if request.user.is_authenticated:
        if Address.objects.filter(status=True, user=request.user).exists():
            address = Address.objects.get(status=True, user=request.user)
        
        user_review_count = ProductReview.objects.filter(user=request.user, product=product).count()
        if user_review_count > 0:
            make_review = False
    else:
        address = "Login To Continue"

    p_image = product.p_images.all()

    average_rating_prc = ProductReview.objects.filter(product=product).aggregate(rating=Avg('rating')*20)
    stars_count = reviews.values('rating').annotate(count=Count('rating')).order_by('rating')
    # Trova il dizionario corrispondente al rating nel queryset
    rating_1_dict = next((item for item in stars_count if item['rating'] == 1), {'count': 0})
    rating_2_dict = next((item for item in stars_count if item['rating'] == 2), {'count': 0})
    rating_3_dict = next((item for item in stars_count if item['rating'] == 3), {'count': 0})
    rating_4_dict = next((item for item in stars_count if item['rating'] == 4), {'count': 0})
    rating_5_dict = next((item for item in stars_count if item['rating'] == 5), {'count': 0})
    # Ottieni il conteggio del rating
    count_rating_1 = rating_1_dict['count']
    count_rating_2 = rating_2_dict['count']
    count_rating_3 = rating_3_dict['count']
    count_rating_4 = rating_4_dict['count']
    count_rating_5 = rating_5_dict['count']
    # Calcola la percentuale
    if reviews.count() > 0:
        review_prc_1 = (count_rating_1 / reviews.count()) * 100
        review_prc_2 = (count_rating_2 / reviews.count()) * 100
        review_prc_3 = (count_rating_3 / reviews.count()) * 100
        review_prc_4 = (count_rating_4 / reviews.count()) * 100
        review_prc_5 = (count_rating_5 / reviews.count()) * 100
    else:
        review_prc_1 = review_prc_2 = review_prc_3 = review_prc_4 = review_prc_5 = 0

    context = {
        "product": product,
        "products": products,
        "reviews": reviews,
        "average_rating": average_rating,
        "average_rating_prc": average_rating_prc,
        "address": address,
        "make_review": make_review,
        "review_form": review_form,
        "p_image": p_image,

        "RATING": RATING,
        "stars_count": stars_count,
        "review_prc_1": review_prc_1,
        "review_prc_2": review_prc_2,
        "review_prc_3": review_prc_3,
        "review_prc_4": review_prc_4,
        "review_prc_5": review_prc_5,
    }
    return render(request, "core/product-detail.html", context)

def ajax_add_review(request, pid):
    product = Product.objects.get(pk=pid)
    user = request.user 

    review = ProductReview.objects.create(
        user=user,
        product=product,
        review = request.POST['review'],
        rating = request.POST['rating'],
    )

    context = {
        'user': user.username,
        'review': request.POST['review'],
        'rating': request.POST['rating'],
    }

    average_reviews = ProductReview.objects.filter(product=product).aggregate(rating=Avg("rating"))

    return JsonResponse(
       {
        'bool': True,
        'context': context,
        'average_reviews': average_reviews
       }
    )

def tag_list_view(request, tag_slug=None):
    products = Product.objects.filter(product_status="published").order_by("-id")
    tag = None 
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        products = products.filter(tags__in=[tag])

    context = {
        "products": products,
        "tag": tag
    }
    return render(request, "core/tag.html", context)

def search_view(request):
    query = request.GET.get("q")

    products = Product.objects.filter(title__icontains=query).order_by("-date")

    context = {
        "products": products,
        "query": query,
    }
    return render(request, "core/search.html", context)

def search_category_view(request):
    query = request.GET.get("c")

    categories = Category.objects.filter(title__icontains=query).order_by("title")

    context = {
        "categories": categories,
        "query": query,
    }
    return render(request, "core/search-category.html", context)

def search_vendor_view(request):
    query = request.GET.get("v")

    vendors = Vendor.objects.filter(title__icontains=query).order_by("title")

    context = {
        "vendors": vendors,
        "query": query,
    }
    return render(request, "core/search-vendor.html", context)

def filter_product(request):
    categories = request.GET.getlist("category[]")
    vendors = request.GET.getlist("vendor[]")


    min_price = request.GET['min_price']
    max_price = request.GET['max_price']

    products = Product.objects.filter(product_status="published").order_by("-id").distinct()

    products = products.filter(price__gte=min_price)
    products = products.filter(price__lte=max_price)


    if len(categories) > 0:
        products = products.filter(category__id__in=categories).distinct() 

    if len(vendors) > 0:
        products = products.filter(vendor__id__in=vendors).distinct() 
    
    
    data = render_to_string("core/async/product-list.html", {"products": products})
    return JsonResponse({"data": data})

def add_to_cart(request):
    cart_product = {}

    cart_product[str(request.GET['id'])] = {
        'title': request.GET['title'],
        'qty': request.GET['qty'],
        'price': request.GET['price'],
        'image': request.GET['image'],
        'pid': request.GET['pid'],
    }

    if 'cart_data_obj' in request.session:
        if str(request.GET['id']) in request.session['cart_data_obj']:

            cart_data = request.session['cart_data_obj']
            cart_data[str(request.GET['id'])]['qty'] = int(cart_product[str(request.GET['id'])]['qty'])
            cart_data.update(cart_data)
            request.session['cart_data_obj'] = cart_data
        else:
            cart_data = request.session['cart_data_obj']
            cart_data.update(cart_product)
            request.session['cart_data_obj'] = cart_data

    else:
        request.session['cart_data_obj'] = cart_product
    return JsonResponse({"data":request.session['cart_data_obj'], 'totalcartitems': len(request.session['cart_data_obj'])})

def cart_view(request):
    cart_total_amount = 0
    if 'cart_data_obj' in request.session:
        for p_id, item in request.session['cart_data_obj'].items():
            cart_total_amount += int(item['qty']) * float(item['price'])
        return render(request, "core/cart.html", {"cart_data":request.session['cart_data_obj'], 'totalcartitems': len(request.session['cart_data_obj']), 'cart_total_amount':cart_total_amount})
    else:
        messages.warning(request, "Your cart is empty")
        return redirect("core:index")

def delete_item_from_cart(request):
    product_id = str(request.GET['id'])
    if 'cart_data_obj' in request.session:
        if product_id in request.session['cart_data_obj']:
            cart_data = request.session['cart_data_obj']
            del request.session['cart_data_obj'][product_id]
            request.session['cart_data_obj'] = cart_data
    
    cart_total_amount = 0
    if 'cart_data_obj' in request.session:
        for p_id, item in request.session['cart_data_obj'].items():
            cart_total_amount += int(item['qty']) * float(item['price'])

    context = render_to_string("core/async/cart-list.html", {"cart_data":request.session['cart_data_obj'], 'totalcartitems': len(request.session['cart_data_obj']), 'cart_total_amount':cart_total_amount})
    return JsonResponse({"data": context, 'totalcartitems': len(request.session['cart_data_obj'])})

def update_cart(request):
    product_id = str(request.GET['id'])
    product_qty = request.GET['qty']

    if 'cart_data_obj' in request.session:
        if product_id in request.session['cart_data_obj']:
            cart_data = request.session['cart_data_obj']
            cart_data[str(request.GET['id'])]['qty'] = product_qty
            request.session['cart_data_obj'] = cart_data
    
    cart_total_amount = 0
    if 'cart_data_obj' in request.session:
        for p_id, item in request.session['cart_data_obj'].items():
            cart_total_amount += int(item['qty']) * float(item['price'])

    context = render_to_string("core/async/cart-list.html", {"cart_data":request.session['cart_data_obj'], 'totalcartitems': len(request.session['cart_data_obj']), 'cart_total_amount':cart_total_amount})
    return JsonResponse({"data": context, 'totalcartitems': len(request.session['cart_data_obj'])})

@login_required
def checkout_view(request):
    cart_total_amount = 0
    total_amount = 0

    # Checking if cart_data_obj session exists
    if 'cart_data_obj' in request.session:

        # Getting total amount for Paypal Amount
        for p_id, item in request.session['cart_data_obj'].items():
            total_amount += int(item['qty']) * float(item['price'])

        # Create Order Object
        order = CartOrder.objects.create(
            user=request.user,
            price=total_amount
        )

        # Getting total amount for The Cart
        for p_id, item in request.session['cart_data_obj'].items():
            cart_total_amount += int(item['qty']) * float(item['price'])

            cart_order_products = CartOrderProducts.objects.create(
                order=order,
                invoice_no="INVOICE_NO-" + str(order.id), # INVOICE_NO-5,
                item=item['title'],
                image=item['image'],
                qty=item['qty'],
                price=item['price'],
                total=float(item['qty']) * float(item['price'])
            )

        host = request.get_host()
        paypal_dict = {
            'business': settings.PAYPAL_RECEIVER_EMAIL,
            'amount': cart_total_amount,
            'item_name': "Order-Item-No-" + str(order.id),
            'invoice': "INVOICE_NO-" + str(order.id),
            'currency_code': "USD",
            'notify_url': 'http://{}{}'.format(host, reverse("core:paypal-ipn")),
            'return_url': 'http://{}{}'.format(host, reverse("core:payment-completed")),
            'cancel_url': 'http://{}{}'.format(host, reverse("core:payment-failed")),
        }

        paypal_payment_button = PayPalPaymentsForm(initial=paypal_dict)

        try:
            active_address = Address.objects.get(user=request.user, status=True)
        except:
            messages.warning(request, "There are multiple addresses, only one should be activated.")
            active_address = None

        return render(request, "core/checkout.html", {"cart_data":request.session['cart_data_obj'], 'totalcartitems': len(request.session['cart_data_obj']), 'cart_total_amount':cart_total_amount, 'paypal_payment_button':paypal_payment_button, "active_address":active_address})

@login_required
def payment_completed_view(request):
    cart_total_amount = 0
    if 'cart_data_obj' in request.session:
        for p_id, item in request.session['cart_data_obj'].items():
            cart_total_amount += int(item['qty']) * float(item['price'])
    return render(request, 'core/payment-completed.html',  {'cart_data':request.session['cart_data_obj'],'totalcartitems':len(request.session['cart_data_obj']),'cart_total_amount':cart_total_amount})

@login_required
def payment_failed_view(request):
    return render(request, 'core/payment-failed.html')

@login_required
def customer_dashboard(request):
    orders_list = CartOrder.objects.filter(user=request.user).order_by("-id")
    address = Address.objects.filter(user=request.user)

    orders = CartOrder.objects.annotate(month=ExtractMonth("order_date")).values("month").annotate(count=Count("id")).values("month", "count")
    month = []
    total_orders = []

    for i in orders:
        month.append(calendar.month_name[i["month"]])
        total_orders.append(i["count"])

    if request.method == "POST":
        address = request.POST.get("address")
        mobile = request.POST.get("mobile")

        new_address = Address.objects.create(
            user=request.user,
            address=address,
            mobile=mobile,
        )
        messages.success(request, "Address Added Successfully.")
        return redirect("core:dashboard")
    else:
        print("Error")
    
    user_profile = Profile.objects.get(user=request.user)

    context = {
        "user_profile": user_profile,
        "orders": orders,
        "orders_list": orders_list,
        "address": address,
        "month": month,
        "total_orders": total_orders,
    }
    return render(request, 'core/dashboard.html', context)

def order_detail(request, id):
    order = CartOrder.objects.get(user=request.user, id=id)
    order_items = CartOrderProducts.objects.filter(order=order)

    context = {
        "order_items": order_items,
    }
    return render(request, 'core/order-detail.html', context)

def make_address_default(request):
    id = request.GET['id']
    Address.objects.update(status=False)
    Address.objects.filter(id=id).update(status=True)
    return JsonResponse({"boolean": True})

@login_required
def wishlist_view(request):
    wishlist = Wishlist_model.objects.all()
    context = {
        "w":wishlist
    }
    return render(request, "core/wishlist.html", context)

def add_to_wishlist(request):
    product_id = request.GET['id']
    product = Product.objects.get(id=product_id)
    print("Product id is:" + product_id)

    context = {}

    wishlist_count = Wishlist_model.objects.filter(product=product, user=request.user).count()
    print(wishlist_count)

    if wishlist_count > 0:
        context = {
            "bool": True
        }
    else:
        new_wishlist = Wishlist_model.objects.create(user=request.user, product=product)
        context = {
            "bool": True
        }
    return JsonResponse(context)

def remove_wishlist(request):
    pid = request.GET['id']
    wishlist = Wishlist_model.objects.filter(user=request.user)
    wishlist_d = Wishlist_model.objects.get(id=pid)
    delete_product = wishlist_d.delete()
    
    context = {
        "bool":True,
        "w":wishlist
    }
    wishlist_json = serializers.serialize('json', wishlist)
    t = render_to_string('core/async/wishlist-list.html', context)
    return JsonResponse({'data':t,'w':wishlist_json})

def contact(request):
    return render(request, "core/contact.html")

def ajax_contact_form(request):
    full_name = request.GET['full_name']
    email = request.GET['email']
    phone = request.GET['phone']
    subject = request.GET['subject']
    message = request.GET['message']

    contact = ContactUs.objects.create(
        full_name=full_name,
        email=email,
        phone=phone,
        subject=subject,
        message=message,
    )

    data = {
        "bool": True,
        "message": "Message Sent Successfully"
    }

    return JsonResponse({"data":data})

def about_us(request):
    return render(request, "core/about_us.html")

def purchase_guide(request):
    return render(request, "core/purchase_guide.html")

def privacy_policy(request):
    return render(request, "core/privacy_policy.html")

def terms_of_service(request):
    return render(request, "core/terms_of_service.html")