# bis_module.py
import requests
import xml.etree.ElementTree as ET
import config

def get_station_id_by_name(station_name: str) -> str | None:
    """ (실제) 정류소 이름으로 정류소 ID를 검색합니다. """
    print(f"\n--- [🔧 1. 정류소 ID 검색 시도: '{station_name}'] ---")
    
    params = {'serviceKey': config.DAEJEON_API_KEY, 'keyWord': station_name} 
    
    try:
        response = requests.get(config.URL_SEARCH_STATION, params=params, timeout=5)
        response.raise_for_status() 
        root = ET.fromstring(response.content)
        
        item = root.find('./msgBody/itemList') 

        if item is not None:
            bus_stop_id_tag = item.find('BUSSTOP_ID') 
            bus_stop_name_tag = item.find('BUSSTOP_NAME')
            
            if bus_stop_id_tag is not None and bus_stop_name_tag is not None:
                bus_stop_id = bus_stop_id_tag.text
                found_name = bus_stop_name_tag.text
                print(f"--- [🔧 1. ID 검색 성공 (8자리 ID): {found_name} ({bus_stop_id})] ---")
                return bus_stop_id
            else:
                 print(f"--- [🔧 1. ID 검색 실패: XML 응답 태그(BUSSTOP_ID)를 찾을 수 없습니다.] ---")
                 return None
        else:
            header_msg = root.find('./msgHeader/headerMsg').text
            print(f"--- [🔧 1. ID 검색 실패: {header_msg}] ---")
            return None
            
    except Exception as e:
        print(f"--- [🔧 1. ID 검색 오류: {e}] ---")
        return None

def get_arrival_info_by_id(bus_stop_id: str) -> dict:
    """ (실제) 정류소 ID로 버스 도착 정보를 조회합니다. """
    print(f"\n--- [🔧 2. 도착 정보 조회 시도 (ID: {bus_stop_id})] ---")
    params = {'serviceKey': config.DAEJEON_API_KEY, 'BusStopID': bus_stop_id}
    results = {"station_id": bus_stop_id, "buses": []}
    
    try:
        response = requests.get(config.URL_GET_ARRIVAL, params=params, timeout=5)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        items = root.findall('./msgBody/itemList')
        
        if not items:
            header_msg = root.find('./msgHeader/headerMsg').text
            print(f"--- [🔧 2. 조회 결과 없음: {header_msg}] ---")
            results["error"] = header_msg
            return results

        for item in items:
            bus_info = {
                "bus_no": item.find('ROUTE_NO').text,
                "arrival_min": int(item.find('EXTIME_MIN').text),
                "destination": item.find('DESTINATION').text, 
                "status_pos": int(item.find('STATUS_POS').text)
            }
            results["buses"].append(bus_info)
        
        print(f"--- [🔧 2. 도착 정보 성공: {len(results['buses'])}개 노선 발견] ---")
        return results
        
    except Exception as e:
        print(f"--- [🔧 2. 도착 정보 조회 오류: {e}] ---")
        results["error"] = str(e)
        return results

# --- Gemini Tool Functions ---

def get_bus_arrival_info(station_name: str) -> dict:
    """(도구 1) 사용자가 '정류장'의 도착 정보를 물어볼 때 사용합니다."""
    bus_stop_id = get_station_id_by_name(station_name)
    if bus_stop_id is None:
        return {"station_name": station_name, "buses": [], "error": "정류소 ID를 찾을 수 없습니다."}
    arrival_data = get_arrival_info_by_id(bus_stop_id)
    arrival_data["station_name"] = station_name 
    return arrival_data

def find_direct_bus_from_city_hall(destination_name: str) -> dict:
    """(도구 2) 사용자가 '대전광역시청'에서 '목적지'로 가는 버스를 물어볼 때 사용합니다."""
    print(f"\n--- [🔧 '대전광역시청' 출발 -> '{destination_name}' 도착' 로직 실행] ---")
    
    destination_id = get_station_id_by_name(destination_name)
    if destination_id:
        print(f"--- [ℹ️  도착지 '{destination_name}'의 검색된 정류소 ID: {destination_id}] ---")
    else:
        print(f"--- [ℹ️  도착지 '{destination_name}'에 대한 정확한 정류소 ID를 찾지 못했습니다.] ---")

    arrival_data = get_arrival_info_by_id(config.CITY_HALL_STATION_ID)
    
    if arrival_data.get("error"):
        return {"start_station": config.CITY_HALL_STATION_NAME, "destination_request": destination_name, "matching_buses": [], "error": arrival_data["error"]}

    matching_buses = []
    for bus in arrival_data["buses"]:
        if destination_name in bus["destination"]:
            matching_buses.append(bus)
            
    print(f"--- [🔧 필터링 완료: {len(matching_buses)}개 버스 찾음] ---")

    return {
        "start_station": config.CITY_HALL_STATION_NAME,
        "destination_request": destination_name,
        "destination_id_found": destination_id,
        "matching_buses": matching_buses
    }

# Gemini에서 호출할 함수 목록
available_functions = {
    "get_bus_arrival_info": get_bus_arrival_info, 
    "find_direct_bus_from_city_hall": find_direct_bus_from_city_hall
}