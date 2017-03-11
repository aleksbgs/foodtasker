from django.http import JsonResponse
from foodtaskerapp.models import Restaurant,Meal,Order,OrderDetails
from foodtaskerapp.serializers import  RestaurantSerializer,MealSerializer


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


    return JsonResponse({})


def customer_get_latest_order(request):
    return JsonResponse({})