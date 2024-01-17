from core.models import Product, Category, Vendor, CartOrder, CartOrderProducts, ProductImages, ProductReview, Wishlist_model, Address
from django.db.models import Min, Max
from django.contrib import messages

def default(request):
    categories = Category.objects.all()
    vendors = Vendor.objects.all()

    min_max_price = Product.objects.aggregate(Min('price'), Max('price'))

    if request.user.is_authenticated:
        try:
            wishlist = Wishlist_model.objects.filter(user=request.user)
        except:
            messages.warning(request, "You need to login before accessing your wishlist.")
            wishlist = 0
    else:
        wishlist = 0

    try:
        address = Address.objects.get(user=request.user)
    except:
        address = None

    return {
        'categories' : categories,
        'vendors' : vendors,
        'address' : address,
        'min_max_price': min_max_price,
        'wishlist': wishlist,
    }

# def average_rating_prc(request):
#     if 'pid' in request.GET:
#         pid = request.GET['pid']
#         product = Product.objects.get(pid=pid)
#         average_rating_prc = ProductReview.objects.filter(product=product).aggregate(rating=Avg('rating')*20)
#         return {'average_rating_prc': average_rating_prc}
#     else:
#         return {}