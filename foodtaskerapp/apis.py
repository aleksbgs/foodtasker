import json
from django.utils import timezone
from django.http import JsonResponse
from foodtaskerapp.models import Restaurant,Meal,Order,OrderDetails,Driver
from foodtaskerapp.serializers import  RestaurantSerializer,MealSerializer,OrderSerializer
from oauth2_provider.models import AccessToken
from django.views.decorators.csrf import csrf_exempt
############
#CUSTOMERS
############

def customer_get_restaurants(request):
    restaurants = RestaurantSerializer(
        Restaurant.objects.all().order_by("-id"),
        many=True,
        context={"request":request}
    ).data
    return JsonResponse({"restaurants": restaurants})


def customer_get_meals(request,restaurant_id):

    meals = MealSerializer(
        Meal.objects.filter(restaurant_id = restaurant_id).order_by("-id"),
        many=True,
        context={"request":request}
    ).data

    return JsonResponse({"meals":meals})
@csrf_exempt
def customer_add_order(request):
    """
    params:
       access_token
       restaurant_id
       address
       order_details(json format) example:
          [{"meal_id":1,"quantity":2},{"meal_id":2,"quantity":3}]
          stripe token

       return:
       {"status":"success"}
    """
    #Get token
    access_token = AccessToken.objects.get(token = request.POST.get("access_token"),
                                           expires__gt = timezone.now())


    #get profile
    customer = access_token.user.customer

    #check customer has any order that is not delivered
    if Order.objects.filter(customer = customer).exclude(status=Order.DELIVERED):
        return JsonResponse({"status":"fail","error":"Your last order must be completed"})

    #Check Address
    if not request.POST["address"]:
        return JsonResponse({"status":"failed","error":"Address is required"})

    #Get Order Details
    order_details = json.loads(request.POST["order_details"])

    order_total = 0
    for meal in order_details:
        order_total += Meal.objects.get(id = meal["meal_id"]).price * meal["quantity"]

    if len(order_details) > 0:
       #Step 1 Create an order
       order = Order.objects.create(
           customer = customer,
           restaurant_id = request.POST["restaurant_id"],
           total = order_total,
           status = Order.COOKING,
           address = request.POST["address"]

       )

       #Step2 Create Order details
       for meal in order_details:
            OrderDetails.objects.create(
                order = order,
                meal_id = meal["meal_id"],
                quantity = meal["quantity"],
                sub_total = Meal.objects.get(id = meal["meal_id"]).price * meal["quantity"]
            )

       return JsonResponse({"status":"success"})



def customer_get_latest_order(request):
    access_token = AccessToken.objects.get(token=request.GET.get("access_token"),expires__gt=timezone.now())

    customer = access_token.user.customer

    order = OrderSerializer(Order.objects.filter(customer=customer).last()).data


    return JsonResponse({"order":order})

#######

#RESTAURANT

#######
def restaurant_order_notification(request,last_request_time):
    notification = Order.objects.filter(restaurant= request.user.restaurant,created_at__gt=last_request_time).count()
    return JsonResponse({"notification":notification})

#######

#DRIVER

#######

def driver_get_ready_orders(request):
    orders = OrderSerializer(
        Order.objects.filter(status=Order.READY,driver=None).order_by("-id"),
        many=True
    ).data



    return JsonResponse({"orders":orders})

@csrf_exempt
#Post params: access token,order_id
def driver_pick_order(request):

    if request.method == "POST":
        #get tokent
        access_token = AccessToken.objects.get(token=request.POST.get("access_token"), expires__gt=timezone.now())
        #get driver
        driver = access_token.user.driver

        #check if driver can only pick one order at the same time
        if Order.objects.filter(driver=driver).exclude(status=Order.ONTHEWAY):
            return JsonResponse({"status":"failed","error":"You can only pick one order"})
        try:
            order = Order.objects.get(
                id = request.POST["order_id"],
                driver = None,
                status = Order.READY
            )
            order.driver = driver
            order.status = Order.ONTHEWAY
            order.picked_at = timezone.now()
            order.save()
            return JsonResponse({"status":"success"})
        except Order.DoesNotExist:
            return JsonResponse({"status":"failed","error":"this order has been picked up by another"})

    return JsonResponse({})
#Get params :access token
def driver_get_latest_order(request):
    access_token = AccessToken.objects.get(token=request.GET.get("access_token"), expires__gt=timezone.now())
    # get driver
    driver = access_token.user.driver
    order = OrderSerializer(
        Order.objects.filter(driver=driver).order_by("picked_at").last()

    ).data
    return JsonResponse({"order":order})

def driver_complete_order(request):
    return JsonResponse({})

def driver_get_revenue(request):
    return JsonResponse({})