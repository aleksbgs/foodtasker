import json
from django.utils import timezone
from django.http import JsonResponse
from foodtaskerapp.models import Restaurant,Meal,Order,OrderDetails,Driver
from foodtaskerapp.serializers import  RestaurantSerializer,MealSerializer
from oauth2_provider.models import AccessToken
from django.views.decorators.csrf import csrf_exempt


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
    return JsonResponse({})