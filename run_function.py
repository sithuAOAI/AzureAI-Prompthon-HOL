from promptflow import tool
import json
import requests
from urllib import parse
import pytz
from datetime import datetime


# Kakao REST API를 활용하는 함수 (주소를 위경도 좌표로 변환 포함)
headers = {
    "Authorization": "KakaoAK " + "202817d911eee9f135ea90f83678533a",
    "Content-Type": "application/json",
}    

# Kakao 키워드 기반 위경도 좌표 찾기
def get_location_xy(keyword="한국마이크로소프트"):
    params = {
        "query": keyword
    }
    url = "https://dapi.kakao.com/v2/local/search/keyword.json?" + parse.urlencode(params)
    response = requests.get(url, headers=headers)
    return (response.json()["documents"][0])

# Convert from seconds to hours, minutes and seconds
def convert_second(seconds):
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    
    return "%d시간 %d분 %d초" % (hour, minutes, seconds)

# Convert from meter to kilometer
def convert_meter(meter):
    return str(round(meter / 1000, 2))


# Kakao 길찾기 API
def get_directions(origin, destination, waypoints="", priority="RECOMMEND", car_fuel="GASOLINE", car_hipass="true", alternatives="false", road_details="false"):
    # 키워드 기반 위경도 좌표 정보 수집
    xy_info = get_location_xy(origin)
    origin_xy_info = xy_info["x"] + "," + xy_info["y"] + ",name=" + xy_info["place_name"]
    xy_info = get_location_xy(destination)
    destin_xy_info = xy_info["x"] + "," + xy_info["y"] + ",name=" + xy_info["place_name"]
    
    params = {
        "origin": origin_xy_info,
        "destination": destin_xy_info,
        "waypoints": waypoints,
        "priority": priority,
        "car_fuel": car_fuel,
        "car_hipass": car_hipass,
        "alternatives": alternatives,
        "road_details": road_details,
    }
    url = "https://apis-navi.kakaomobility.com/v1/directions?{}".format("&".join([f"{k}={v}" for k, v in params.items()]))
    response = requests.get(url, headers=headers)
    
    response_summary = response.json()["routes"][0]["summary"]
    return_data = {
        "origin_name": response_summary["origin"]["name"],
        "destination_name": response_summary["destination"]["name"],
        "taxi_fare": response_summary["fare"]["taxi"],
        "toll_fare": response_summary["fare"]["toll"],
        "distance": convert_meter(response_summary["distance"]) + "km",
        "duration": convert_second(response_summary["duration"]),
    }
    
    return json.dumps(return_data)

# Kakao 미래 운행 시간 기준 길찾기 API
def get_future_directions(origin, destination, departure_time, waypoints="", priority="RECOMMEND", car_fuel="GASOLINE", car_hipass="true", alternatives="false", road_details="false"):
    # 키워드 기반 위경도 좌표 정보 수집
    xy_info = get_location_xy(origin)
    origin_xy_info = xy_info["x"] + "," + xy_info["y"] + ",name=" + xy_info["place_name"]
    xy_info = get_location_xy(destination)
    destin_xy_info = xy_info["x"] + "," + xy_info["y"] + ",name=" + xy_info["place_name"]
    
    # 시간 포맷팅을 API에 맞게 수정 요청합니다. (이미 Function Calling 함수내 파라미터 값에 정의하였기에 실행할 필요가 없음)
    # print("원래 시간: ")
    # print(departure_time)
    # time_format = openai.ChatCompletion.create(
    #     deployment_id=deployment_id,
    #     messages=[
    #         {"role": "system", "content": "You are an agent that converts a date or time value to a format of the form: %Y%m%d%H%M"},
    #         {"role": "user", "content": "2023-11-26T15:30:00"},
    #         {"role": "assistant", "content": "202311261530"},
    #         {"role": "user", "content": departure_time}
    #     ]
    # )
    # print("변경 포맷: ")
    # print(time_format["choices"][0]["message"]["content"])
    
    params = {
        "origin": origin_xy_info,
        "destination": destin_xy_info,
        "waypoints": waypoints,
        "priority": priority,
        "car_fuel": car_fuel,
        "car_hipass": car_hipass,
        "alternatives": alternatives,
        "road_details": road_details,
        "departure_time": departure_time,
    }
    url = "https://apis-navi.kakaomobility.com/v1/future/directions?{}".format("&".join([f"{k}={v}" for k, v in params.items()]))
    response = requests.get(url, headers=headers)
    
    response_summary = response.json()["routes"][0]["summary"]
    return_data = {
        "origin_name": response_summary["origin"]["name"],
        "destination_name": response_summary["destination"]["name"],
        "taxi_fare": response_summary["fare"]["taxi"],
        "toll_fare": response_summary["fare"]["toll"],
        "distance": convert_meter(response_summary["distance"]) + "km",
        "duration": convert_second(response_summary["duration"]),
    }
    
    return json.dumps(return_data)

def get_current_time(location):
    try:
        # Get the timezone for the city
        timezone = pytz.timezone(location)

        # Get the current time in the timezone
        now = datetime.now(timezone)
        current_time = now.strftime("%Y%m%d%H%M")

        return current_time
    except:
        return "죄송합니다. 해당 지역의 TimeZone을 찾을 수 없습니다."

# 특정 지역의 날씨를 가져오는 함수
def get_current_weather(location="서울시청"):
    xy_info = get_location_xy(location)
    params = {
        "lat": xy_info["y"],
        "lon": xy_info["x"],
        "units": "metric",
        "lang":  "en",
        "appid": "78218cd3ddb21931da600b89b89db815"
    }
    url = "https://api.openweathermap.org/data/2.5/weather?{}".format("&".join([f"{k}={v}" for k, v in params.items()]))
    response = requests.get(url, headers=headers)

    return_data = {
        "Weather_main": response.json()["weather"][0]["main"],
        "Weather_description": response.json()["weather"][0]["description"],
        "Temperature_Celsius": response.json()["main"]["temp"],
        "Humidity": response.json()["main"]["humidity"],
        "Cloudiness": response.json()["clouds"]["all"]
    }

    return json.dumps(return_data)


@tool
def run_function(response_message: dict) -> str:
    if "function_call" in response_message and response_message["function_call"] is not None:
        function_name = response_message["function_call"]["name"]
        function_args = json.loads(response_message["function_call"]["arguments"])
        print(function_args)
        result = globals()[function_name](**function_args)
    else:
        print("No function call")
        if isinstance(response_message, dict):
            result = response_message.get("content", "")
        else:
            result = response_message
    return result