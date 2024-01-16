from django.urls import path, include
from core import views

app_name = 'core'

urlpatterns = [
    path('', views.index, name='index'),

    path('products/', views.product_list_view, name='product-list'),
    path('products/<pid>', views.product_detail_view, name='product-detail'),
    
    path('category/', views.category_list_view, name='category-list'),
    path('category/<cid>/', views.category_product_list_view, name='category-product-list'),
    
    path('vendor/', views.vendor_list_view, name='vendor-list'),
    path('vendor/<vid>/', views.vendor_detail_view, name='vendor-detail'),

    path('tag/<slug:tag_slug>/', views.tag_list_view, name='tags'),

    path('ajax-add-review/<int:pid>', views.ajax_add_review, name='ajax-add-review'),

    path('search/', views.search_view, name='search'),
    path('search-category/', views.search_category_view, name='search-category'),
    path('search-vendor/', views.search_vendor_view, name='search-vendor'),

    path("filter-products/", views.filter_product, name="filter-product"),

    path("add-to-cart/", views.add_to_cart, name="add-to-cart"),

    path("cart/", views.cart_view, name="cart"),

    path("delete-from-cart/", views.delete_item_from_cart, name="delete-from-cart"),

    path("update-cart/", views.update_cart, name="update-cart"),

    path("checkout/", views.checkout_view, name="checkout"),

    path('paypal/', include('paypal.standard.ipn.urls')),
    path("payment-completed/", views.payment_completed_view, name="payment-completed"),
    path("payment-failed/", views.payment_failed_view, name="payment-failed"),

    path('dashboard/', views.customer_dashboard, name="dashboard"),
    path('dashboard/order-detail/<int:id>/', views.order_detail, name="order-detail"),

    path('make-default-address',views.make_address_default, name='make-default-address'),

    path("wishlist/", views.wishlist_view, name="wishlist"),
    path("add-to-wishlist/", views.add_to_wishlist, name="add-to-wishlist"),
    path("remove-from-wishlist/", views.remove_wishlist, name="remove-from-wishlist"),

    path("contact/", views.contact, name="contact"),
    path("ajax-contact-form/", views.ajax_contact_form, name="ajax-contact-form"),

    path("about_us/", views.about_us, name="about_us"),
    path("purchase_guide/", views.purchase_guide, name="purchase_guide"),
    path("privacy_policy/", views.privacy_policy, name="privacy_policy"),
    path("terms_of_service/", views.terms_of_service, name="terms_of_service"),
]
